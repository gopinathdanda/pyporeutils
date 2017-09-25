#!/usr/bin/env python

# CALCULATE NOISE PSD FOR A TIME TRACE

import heka_reader as heka
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams['agg.path.chunksize'] = 20000
from matplotlib.widgets import Slider, Button
from scipy import signal
from scipy.optimize import curve_fit

def invf(x, a, alpha):
    return a/(x**alpha)

def noise_psd(i, fs):
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

def plot_noise(option, data, view_controls = True, view_fit = True):
    # i in pA
    # v in V
    
    view_traces, view_current_trace, view_noise = option
    
    if view_traces == True and len(data) == 1:
        v, i, t, f, psd, Avalue, popt, mean_current, I_rms, x, invfx = data[0]
        fig_traces, ax_traces = plt.subplots(2, sharex=True)
        ax_traces[0].plot(t, v*1000)
        ax_traces[1].plot(t, i*1e-3)

    if view_current_trace == True:
        plt.figure(figsize=(10,8.25))
        plt.minorticks_on()
        plt.tick_params(axis = 'both', which = 'major', labelsize = 16)
        plt.tick_params(axis = 'both', which = 'major', length = 8, width = 1, direction = 'in')
        plt.tick_params(axis = 'both', which = 'minor', length = 4, width = 1, direction = 'in')
        
        for dataset in data:
            v, i, t, f, psd, Avalue, popt, mean_current, I_rms, x, invfx = dataset
            plt.plot(t, i*1e-3)
            #plt.ylim(1.5, 5)
            #plt.xlim(0, max(t))
    
    if view_noise == True:
        #plt.loglog(fspec, np.sqrt(pspec))
        fig = plt.figure(figsize=(10,8.25))
        ax = fig.add_subplot(111)
        ax.tick_params(axis='both', which='major', labelsize=16)
        #ax = plt.gca()
        #plt.ylim(1e-2, 1e4)
        ax.set_xlim(5,1e4)
        ax.minorticks_on()
        ax.tick_params('both', length = 8, width = 1, which = 'major', direction = 'in')
        ax.tick_params('both', length = 4, width = 1, which = 'minor', direction = 'in')
        ax.legend()
        
        for dataset in data:
            v, i, t, f, psd, Avalue, popt, mean_current, I_rms, x, invfx = dataset
        
            ax.loglog(f, psd)
        
            if len(data) == 1:
                t = ax.text(0.05, 0.1,(u"A = %0.2e; \u03B1 = %0.2f" % (Avalue, popt[1])),
                 horizontalalignment='left',
                 verticalalignment='center',
                 transform = ax.transAxes)
                t2 = ax.text(0.05, 0.15,("I = %0.2f nA; I_rms = %0.2f pA" % (mean_current, I_rms)),
                 horizontalalignment='left',
                 verticalalignment='center',
                 transform = ax.transAxes)
        
        
            if view_fit == True:
                [fit_line] = ax.loglog(x, invf(x, *popt))
            '''
                if view_controls == True and len(data) == 1:
                    fig.subplots_adjust(bottom=0.25)
                    a_0 = popt[0]
                    alpha_0 = popt[1]

                    # Add two sliders for tweaking the parameters
                    a_slider_ax  = fig.add_axes([0.15, 0.15, 0.75, 0.03])
                    a_slider = Slider(a_slider_ax, r'$Log(A*I^2)$', -4, 8, valinit=np.log10(a_0), dragging=True)
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
            '''
        legend = ax.legend(labels = ["SA_LD2.5", "PQ_LD2.5", "PI_LD3", "PK_LD3", "PB_LD4", "PV_LD2"])
    

def noise(fname, extract_lims, noise_lims, options = [[True, False, False], [True, True, True]], option_select = 0, view = True):
    range_to_show = extract_lims[0 if option_select == 0 else 1]
    reader = heka.HekaReader(fname)
    i, t, fs, v = reader.extract_data(start = range_to_show[0], stop = range_to_show[1])
    i = i*1e12
    mean_current = (np.mean(i)/1e3)
    print("--------------------------------------------------")
    print(fname)
    print("Mean current = %0.2f nA" % mean_current)

    current_option = options[option_select]

    psd, f, pspec, fspec = noise_psd(i, fs)
    I_rms = np.sqrt(pspec.max())
    print("I_rms = %0.2f pA" % I_rms)
    
    #threshold = 0.1
    #difference = np.abs(np.diff(psd))
    #outlier_idx = difference < threshold
    #new_idx = np.hstack((outlier_idx, (False)))
    #print(difference)
    #plt.loglog(difference[new_idx[:len(new_idx)-1]])
    #f = f[new_idx]
    #psd = psd[new_idx]
    
    x, popt, pcov = fit(f, psd, invf, start = noise_lims[0], stop = noise_lims[1])
    print("-------------------------")
    print("1/f Noise Characteristics")
    print("-------------------------")
    Avalue = popt[0]/(np.mean(i)**2)
    print("A = %0.2e" % Avalue)
    print(u"\u03B1 = %0.2f" % popt[1])
    
    if view == True:
        k = np.asarray([[v, i, t, f, psd, Avalue, popt, mean_current, I_rms, x, invf(x, *popt)]])
        plot_noise(current_option, k)
        plt.show()
    else:
        val = np.asarray([v, i, t, f, psd, Avalue, popt, mean_current, I_rms, x, invf(x, *popt)])
        return(val)

# LIMITS FOR DATA EXTRACTION ([0, 0] = ENTIRE RANGE)
extract_lims = [[0, 0], [4.5, 7]]

# LIMITS FOR 1/F NOISE CURVE FITTING
noise_lims = [3, 1e3]

# PLOT OPTIONS: [VOLTAGE & CURRENT, CURRENT, NOISE]
options = [[True, False, False], [True, True, True]]

# SELECT PLOT OPTION (0 PLOTS ENTIRE RANGE, OTHER INDICES PLOT THE SECOND RANGE FROM extract_lims)
option_select = 1

final = noise("Data/ChipSA2.hkd", [[0,0], [5, 9.3]], noise_lims, option_select = 1, view = False)                           #5-10
final2 = noise("Noise/PQ_Noise_1VPulse_181827.hkd", [[0,0], [23, 27.3]], noise_lims, option_select = 1, view = False)       #23-28
final3 = noise("Noise/PI_195331_2ndDay.hkd", [[0,0], [16, 20.3]], noise_lims, option_select = 1, view = False)              #16-20.8
final4 = noise("Noise/PK_2ndDay_163239.hkd", [[0,0], [17.9, 22.2]], noise_lims, option_select = 1, view = False)            #17.9-22.2
plot_noise([False, True, True], np.asarray([final, final2, final3, final4]), view_fit = False)
#plot_noise([True, True, True], [final6], view_fit = False)
plt.show()