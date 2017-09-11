#!/usr/bin/env python

# PLOT AND SAVE IV FROM ALL HKR FILES IN FOLDER & SUB-FOLDER

import numpy as np
import csv
import matplotlib.pyplot as plt

fname = "Data/IV/Chip PE/032717 Chip PE_LD4_1M_100mV_-100mV_03272017_162344.hkr"

def csv_reader(file_obj):
    reader = csv.DictReader(file_obj, delimiter="\t")
    i = []
    v = []
    for line in reader:
        i.append(float(line["Current Avg"])*1e9)    # Current in nA
        v.append(float(line["Voltage"])*1e3)        # Voltage in mV
    return ([i,v])

def linear(m, b, x):
    return list(map(lambda y:m*y+b, x))

with open(fname, 'r') as f_obj:
    i, v = csv_reader(f_obj)
    fig = plt.figure("IV")
    ax = plt.subplot(111)
    ax.scatter(v, i)
    m, b = np.polyfit(v, i, 1)
    type(m)
    ax.plot(v, linear(m, b, v))
    g = m*1e3   # Conductance in nS
    print(g)
    
    ax.set_xlim([min(v)-50, max(v)+50])
    ax.set_xlabel("Voltage (mV)", size = "large")
    ax.set_ylabel("Ionic current (nA)", size = "large")
    plt.show()