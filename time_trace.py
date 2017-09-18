#!/usr/bin/env python

"""
Extract time traces of current or conductance from .hkd file
"""

import heka_reader as heka
import numpy as np
import matplotlib.pyplot as plt

def linear(m, b, x):
    """Generate a linear function
    
    :param m: Slope of linear equation
    :param b: Intercept of linear equation
    :param x: Independent variable
    :returns: Linear function of the form m * x + b
    
    """
    return m*x+b

def extract(fname, start = 0, stop = 0, decimate = False):
    dec_rate = 2500
    reader = heka.HekaReader(fname)
    all_data = reader.get_all_data(decimate = decimate)
    data = all_data[0][0]
    voltages = all_data[1][0]
    sample_rate = reader.get_sample_rate()
    total_length = len(data)
    
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
    
    i = data[start_len:stop_len]
    t = np.linspace(0, (stop-start), num = length)
    v = voltages[start_len:stop_len]
    
    return np.asarray([i, t, sample_rate, v])

i, t, sample_rate, v = extract('Data/ChipAU.hkd', start = 14, stop = 51)
i = i*1e9

plt.plot(t, i, "black")
a = np.polyfit(t, i, 1)
plt.plot(t, linear(a[0], a[1], t))
print("dI/dt = %0.02fnA/s " % a[0])
#plt.ylim(0, 40)
ax = plt.gca()
ax.minorticks_on()
ax.tick_params('both', length=8, width=1, which='major')
ax.tick_params('both', length=4, width=1, which='minor')
plt.show()
plt.close('all')