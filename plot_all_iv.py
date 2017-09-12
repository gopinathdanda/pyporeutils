#!/usr/bin/env python

# PLOT AND SAVE IV FROM ALL HKR FILES IN FOLDERS

import numpy as np
import csv
import matplotlib.pyplot as plt
import os

#plot_iv("Data/IV/Chip PD/032417 Chip PD_LD4_1M_100mV_-100mV_03242017_163304.hkr")
main_dirname = './Data/IV'


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

def plot_iv(fname, save = False, raw_fname = "", dirname = ""):
    with open(fname, 'r') as f_obj:
        i, v = csv_reader(f_obj)
        fig = plt.figure("IV")
        ax = plt.subplot(111)
        ax.scatter(v, i)
        m, b = np.polyfit(v, i, 1)
        type(m)
        ax.plot(v, linear(m, b, v))
        g = m*1e3   # Conductance in nS
        print("G = %0.2f nS" % g)
    
        ax.set_xlim([min(v)-50, max(v)+50])
        ax.set_xlabel("Voltage (mV)", size = "large")
        ax.set_ylabel("Ionic current (nA)", size = "large")
        ax.text(0.7, 0.1,("G = %0.2f nS" % (g)),
             horizontalalignment='left',
             verticalalignment='center',
             transform = ax.transAxes)
        if(save == True and raw_fname != "" and dirname != ""):
            plt.savefig(dirname+"/IVs/"+raw_fname[:-4]+".png", dpi=300, bbox_inches = "tight")
            plt.clf()
        else:
            plt.show()

for dirname, dirnames, filenames in os.walk(main_dirname):
    if(dirname != './Data/IV'):
        print("------------------")
        print(dirname)
        print("------------------")
        for filename in filenames:
            if(filename[-4:] == '.hkr'):
                if(not os.path.isdir(dirname+"/IVs")):
                    os.mkdir(dirname+"/IVs")
                plot_iv(os.path.join(dirname, filename), save = True, raw_fname = filename, dirname = dirname)