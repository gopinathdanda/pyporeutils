#!/usr/bin/env python

"""
Extract time traces of current or conductance from .hkd file
"""

import heka_reader as heka
import numpy as np
import matplotlib.pyplot as plt

reader = heka.HekaReader('Data/ChipAU.hkd')
i, t, sample_rate, v, total_length = reader.extract_data(start = 0, stop = 0, decimate = True)
i = i*1e9

fig, ax1 = plt.subplots()

ax2 = ax1.twinx()

ax1.plot(t, i, 'black')
ax1.minorticks_on()
ax1.tick_params('both', length=8, width=1, which='major')
ax1.tick_params('both', length=4, width=1, which='minor')
ax1.set_xlabel('Time (s)')
ax1.set_ylabel('Current (nA)', color='black')

ax2.plot(t, v, 'red')
ax2.minorticks_on()
ax2.tick_params('both', length=8, width=1, which='major')
ax2.tick_params('both', length=4, width=1, which='minor')
ax2.set_ylabel('Voltage (V)', color='red')

plt.show()
plt.close('all')