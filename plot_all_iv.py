#!/usr/bin/env python

# PLOT AND SAVE IV FROM ALL HKR FILES IN FOLDERS

import numpy as np
import csv
import matplotlib.pyplot as plt
import os

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

def avg_voltages(currents, voltages, limit_trace, limit_v, invert):
    u_voltages = list(set(voltages))
    inverter = 1.0
    if(invert == True):
        u_voltages = [i*-1 for i in u_voltages]
        inverter = -1.0
    if(limit_trace == True):
        u_v = []
        for v in u_voltages:
            if(int(v) <= limit_v and int(v) >= -limit_v):
                u_v.append(v)
        u_voltages = u_v
    c = np.asarray(currents)
    u_current = []
    for v in u_voltages:
        u_indices = [i for i, x in enumerate(voltages) if x == inverter*v]
        u_current.append(inverter*np.mean(c[u_indices]))
    return([u_current, u_voltages])

def plot_iv(fname, save = False, location = [], avg = True, fit = True, show_g = True, limit_trace = False, limit_v = 400, invert = False):
    with open(fname, 'rU') as f_obj:
        i, v = csv_reader(f_obj)
        
        if(avg == True):
            i, v = avg_voltages(i, v, limit_trace, limit_v, invert)
        
        fig = plt.figure("IV")
        ax = plt.subplot(111)
        ax.scatter(v, i)
        m, b = np.polyfit(v, i, 1)
        type(m)
        if(fit == True):
            ax.plot(v, linear(m, b, v))
        g = m*1e3   # Conductance in nS
        print("G = %0.2f nS" % g)
    
        ax.set_xlim([min(v)-50, max(v)+50])
        ax.set_xlabel("Voltage (mV)", size = "large")
        ax.set_ylabel("Ionic current (nA)", size = "large")
        if(show_g == True):
            ax.text(0.7, 0.1,("G = %0.2f nS" % (g)),
             horizontalalignment='left',
             verticalalignment='center',
             transform = ax.transAxes)
        if(save == True):
            if(len(location) == 3): # If location is given
                [raw_fname, dirname, img_folder] = location
                final_fname = dirname+"/"+img_folder+"/"+raw_fname[-19:-4]+".png"
            else:   # Or else store in folder of file
                final_fname = fname[:-4]+".png"
            print(final_fname)
            plt.savefig(final_fname, dpi=300, bbox_inches = "tight")
            plt.clf()
        else:
            plt.show()

def recursive_plot(main_dirname, img_folder, avg = True):    
    for dirname, dirnames, filenames in os.walk(main_dirname):
        if(dirname != main_dirname):
            print("------------------")
            print(dirname)
            print("------------------")
            for filename in filenames:
                if(filename[-4:] == '.hkr'):
                    if(not os.path.isdir(dirname+"/"+img_folder)):
                        os.mkdir(dirname+"/"+img_folder)
                    plot_iv(os.path.join(dirname, filename), save = True, location = [filename, dirname, img_folder], fit = False)



plot_iv("Data/Chip_PF.hkr", save = False, avg = True, fit = False, show_g = True, invert = True)
dirname = './Data/IV/Final'
img_folder = "IV_avg"
#recursive_plot(dirname, img_folder)