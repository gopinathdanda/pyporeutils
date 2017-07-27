#!/usr/bin/env python

# CALCULATE NOISE PSD FOR A TIME TRACE

from pypore.i_o import get_reader_from_filename as heka
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy.optimize import curve_fit

def invf(x, a, b, c, d):
    return a/x+b+c*x+d*x**2

def extract(fname, start = 0, stop = 0, dec = True, Vapp = 0.1, molarity = 1):
    dec_rate = 2500
    reader = heka(fname)
    data = reader.get_all_data(decimate=dec)[0]
    sample_rate = reader.get_sample_rate()
    total_length = len(data)
    
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
    
    f, psd = signal.welch(i, fs = 1e4, nperseg = 2**16)
    
    return np.asarray([psd,f, i, t])

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
psd, f, i, t = extract('Data/ChipAU.hkd', start = 0, stop = 250, dec = False)
print len(f)
x, popt, pcov = fit(f, psd, invf, 1e3, 1)
print popt

#plt.plot(t, i)
plt.loglog(f, psd)
plt.loglog(x, invf(x, *popt), 'g--')
plt.ylim(1e-2, 1e4)
#plt.xlim(5,1e4)
ax = plt.gca()
ax.minorticks_on()
ax.tick_params('both', length = 8, width = 1, which = 'major')
ax.tick_params('both', length = 4, width = 1, which = 'minor')
plt.show()