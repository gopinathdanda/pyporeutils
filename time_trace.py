#!/usr/bin/env python

# EXTRACT TIMES TRACES OF CURRENT OR CONDUCTANCE FROM HKD FILE

from pypore.i_o import get_reader_from_filename
import numpy as np
import matplotlib.pyplot as plt

def time_trace(filename, start, stop, dec = True, dec_rate = 2500, conductance = False, vb = 0.1):
    # Get file
    reader = get_reader_from_filename(filename)
    data = reader.get_all_data(decimate = dec)[0]
    sample_rate = reader.get_sample_rate()
    start_len = int(start*sample_rate)
    stop_len = int(stop*sample_rate)
    if dec:
        start_len = int(start_len/dec_rate)
        stop_len = int(stop_len/dec_rate)
    length = stop_len - start_len

    i = data[start_len:stop_len]*1e9
    t = np.linspace(0, (stop-start), num = length)
    
    if conductance:
        g = i/vb
        return np.asarray([g, t])
    else:
        return np.asarray([i, t])

g, t = time_trace('Data/ChipAU.hkd', 0, 250, conductance = True, vb = 0.1)

plt.plot(t, g, "black")
#plt.ylim(0, 40)
ax = plt.gca()
ax.minorticks_on()
ax.tick_params('both', length=8, width=1, which='major')
ax.tick_params('both', length=4, width=1, which='minor')
plt.show()
plt.close('all')