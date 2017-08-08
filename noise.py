#!/usr/bin/env python

# CALCULATE NOISE PSD AND 1/F NOISE FOR A TIME TRACE

from pypore.i_o import get_reader_from_filename as heka
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy.optimize import curve_fit

def invf(x, a, alpha):
    return a/(x**alpha)

def extract(fname, start = 0, stop = 0, dec = True, Vapp = 0.1, molarity = 1):
    dec_rate = 2500
    reader = heka(fname)
    data = reader.get_all_data(decimate=dec)[0]
    sample_rate = reader.get_sample_rate()
    total_length = len(data)
    if stop == 0:
        stop = total_length*1.0/sample_rate
    
    start_len = int(start*sample_rate)
    stop_len = int(stop*sample_rate)
    if dec:
        start_len = int(start_len/dec_rate)
        stop_len = int(stop_len/dec_rate)
    
    if stop == 0:
        stop_len = total_length
        stop = int(stop_len/sample_rate*1.0)
        if dec:
            stop = int(stop_len*dec_rate/sample_rate*1.0)
    length = stop_len - start_len
    
    i = data[start_len:stop_len]*1e12
    t = np.linspace(0, (stop-start), num = length)
    
    return np.asarray([i, t, sample_rate])

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

# PV = 18-100
# PF = 19.7-26
# AU = 0-250

i, t, fs = extract('Data/ChipSA.hkd', dec = False)
print "Mean current = %0.2f nA" % (np.mean(i)/1e3)

view_trace = False
view_noise_fit = True

if view_trace == True:
    plt.plot(t, i*1e3)
else:
    psd, f, pspec, fspec = noise(i, fs)
    print "I_rms = %0.2f pA" % (np.sqrt(pspec.max()))
    #plt.loglog(fspec, np.sqrt(pspec))
    plt.loglog(f, psd)
    plt.ylim(1e-2, 1e4)
    plt.xlim(1, 2e4)
    if view_noise_fit == True:
        x, popt, pcov = fit(f, psd, invf, stop = 1e4)
        print "-------------------------"
        print "1/f Noise Characteristics"
        print "-------------------------"
        Avalue = popt[0]/(np.mean(i)**2)
        print "A = %0.2e" % Avalue
        print u"\u03B1","= %0.2f" % popt[1]
        plt.loglog(x, invf(x, *popt), 'g--')

ax = plt.gca()
ax.minorticks_on()
ax.tick_params('both', length = 8, width = 1, which = 'major')
ax.tick_params('both', length = 4, width = 1, which = 'minor')
plt.show()