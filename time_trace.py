#!/usr/bin/env python

"""
Extract time traces of current or conductance from .hkd file
"""

import heka_reader as heka
import numpy as np
import matplotlib.pyplot as plt

reader = heka.HekaReader('Data/ChipAU.hkd')
i, t, sample_rate, v = reader.extract_data(start = 14, stop = 51, decimate = True)
i = i*1e9

plt.plot(t, i, "black")
a = np.polyfit(t, i, 1)
p = np.poly1d(a)
plt.plot(t, p(t))
print("dI/dt = %0.02fnA/s " % a[0])
#plt.ylim(0, 40)
ax = plt.gca()
ax.minorticks_on()
ax.tick_params('both', length=8, width=1, which='major')
ax.tick_params('both', length=4, width=1, which='minor')
plt.show()
plt.close('all')