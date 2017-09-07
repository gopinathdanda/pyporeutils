#!/usr/bin/env python

# CALCULATE NOISE PSD AND 1/F NOISE FOR A TIME TRACE

import heka_reader as heka
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams['agg.path.chunksize'] = 20000
from matplotlib.widgets import Slider, Button
from scipy import signal
from scipy.optimize import curve_fit

# FILENAME
fname = 'Data/PK_2ndDay_163239.hkd'

# LIMITS FOR DATA EXTRACTION (0 = ENTIRE RANGE)
extract_lims = [[0, 0], [44, 52]]

# LIMITS FOR 1/F NOISE CURVE FITTING
noise_lims = [1, 1e3]

# PLOT OPTIONS: [VOLTAGE & CURRENT, CURRENT, NOISE_FIT]
options = [[True, False, False], [True, True, True]]

# SELECT PLOT OPTION (0 PLOTS ENTIRE RANGE, OTHER INDICES PLOT THE SECOND RANGE FROM extract_lims)
option_select = 0

def invf(x, a, alpha):
    return a/(x**alpha)

def extract(fname, start = 0, stop = 0, decimate = True, Vapp = 0.1, molarity = 1):
    dec_rate = 2500
    reader = heka.HekaReader(fname)
    all_data = reader.get_all_data(decimate=decimate)
    data = all_data[0][0]
    voltages = all_data[1][0]
    sample_rate = reader.get_sample_rate()
    total_length = len(data)
    if stop == 0:
        stop = total_length*1.0/sample_rate
    
    start_len = int(start*sample_rate)
    stop_len = int(stop*sample_rate)
    if decimate:
        start_len = int(start_len/dec_rate)
        stop_len = int(stop_len/dec_rate)
    
    if stop == 0:
        stop_len = total_length
        stop = int(stop_len/sample_rate*1.0)
        if decimate:
            stop = int(stop_len*dec_rate/sample_rate*1.0)
    length = stop_len - start_len
    
    i = data[start_len:stop_len]*1e12
    t = np.linspace(0, (stop-start), num = length)
    v = voltages[start_len:stop_len]
    
    return np.asarray([i, t, sample_rate, v])

def noise(i, fs):
    f, psd = signal.welch(i, fs, nperseg = 2**16)
    fspec, pspec = signal.welch(i, fs, 'flattop', nperseg = 2**16, scaling = 'spectrum')
    return np.asarray([psd, f, pspec, fspec])

def find_nearest(array, value):
    return (np.abs(array-value)).argmin()  #return index of the closest value in a numpy array

def fit(f, psd, func, stop = 1000, start = 1):
    start_idx = find_nearest(f, start)
    stop_idx = find_nearest(f, stop)
    xdata = f[start_idx:stop_idx]
    ydata = psd[start_idx:stop_idx]
    popt, pcov = curve_fit(func, xdata, ydata)
    return np.asarray([xdata, popt, pcov])

range_to_show = extract_lims[0 if option_select == 0 else 1]
i, t, fs, v = extract(fname, decimate = False, start = range_to_show[0], stop = range_to_show[1])
mean_current = (np.mean(i)/1e3)
print("Mean current = %0.2f nA" % mean_current)

view_traces, view_current_trace, view_noise_fit = options[option_select]

if view_traces == True:
    fig_traces, ax_traces = plt.subplots(2, sharex=True)
    ax_traces[0].plot(t, v*1000)
    ax_traces[1].plot(t, i*1e-3)

if view_current_trace == True:
    plt.figure(figsize=(10,8.25))
    plt.plot(t, i*1e-3)
    plt.tick_params(axis='both', which='major', labelsize=16)
    #plt.ylim(1.5, 5)
    #plt.xlim(0, 155)

psd, f, pspec, fspec = noise(i, fs)
I_rms = np.sqrt(pspec.max())
print("I_rms = %0.2f pA" % I_rms)

#plt.loglog(fspec, np.sqrt(pspec))
fig = plt.figure(figsize=(10,10))
ax = fig.add_subplot(111)
ax.tick_params(axis='both', which='major', labelsize=16)

if view_noise_fit == True:
    fig.subplots_adjust(bottom=0.25)
    ax.loglog(f, psd)
    x, popt, pcov = fit(f, psd, invf, start = noise_lims[0], stop = noise_lims[1])
    print("-------------------------")
    print("1/f Noise Characteristics")
    print("-------------------------")
    Avalue = popt[0]/(np.mean(i)**2)
    print("A = %0.2e" % Avalue)
    print(u"\u03B1 = %0.2f" % popt[1])
    a_0 = popt[0]
    alpha_0 = popt[1]
    t = ax.text(0.05, 0.1,(u"A = %0.2e; \u03B1 = %0.2f" % (Avalue, popt[1])),
     horizontalalignment='left',
     verticalalignment='center',
     transform = ax.transAxes)
    t2 = ax.text(0.05, 0.15,("I = %0.2f nA; I_rms = %0.2f pA" % (mean_current, I_rms)),
     horizontalalignment='left',
     verticalalignment='center',
     transform = ax.transAxes)
    [fit_line] = ax.loglog(x, invf(x, a_0, alpha_0), 'r--')
    
    # Add two sliders for tweaking the parameters
    a_slider_ax  = fig.add_axes([0.15, 0.15, 0.75, 0.03])
    a_slider = Slider(a_slider_ax, r'$Log(A*I^2)$', -4, 4, valinit=np.log10(a_0), dragging=True)
    alpha_slider_ax = fig.add_axes([0.15, 0.1, 0.75, 0.03])
    alpha_slider = Slider(alpha_slider_ax, r'$\alpha$', 0, 2, valinit=alpha_0, dragging=True)
    def sliders_on_changed(val):
        fit_line.set_ydata(invf(x, 10**a_slider.val, alpha_slider.val))
        new_Aval = 10**(a_slider.val)/(np.mean(i)**2)
        t.set_text(u"A = %0.2e; \u03B1 = %0.2f" % (new_Aval, alpha_slider.val))
        fig.canvas.draw_idle()
    a_slider.on_changed(sliders_on_changed)
    alpha_slider.on_changed(sliders_on_changed)

    # Add a button for resetting the parameters
    reset_button_ax = fig.add_axes([0.8, 0.025, 0.1, 0.05])
    reset_button = Button(reset_button_ax, 'Reset', hovercolor='red')
    def reset_button_on_clicked(mouse_event):
        alpha_slider.reset()
        a_slider.reset()
    reset_button.on_clicked(reset_button_on_clicked)
else:
    ax.loglog(f, psd)

#ax = plt.gca()
#plt.ylim(1e-2, 1e4)
ax.set_xlim(5,2e4)
ax.minorticks_on()
ax.tick_params('both', length = 8, width = 1, which = 'major')
ax.tick_params('both', length = 4, width = 1, which = 'minor')

plt.show()