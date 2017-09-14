#!/usr/bin/env python

# PLOT AND SAVE IV FROM ALL HKR FILES IN FOLDERS

import numpy as np
import csv
import matplotlib.pyplot as plt
import os

def csv_reader(file_obj, invert = False, limit = []):
    reader = csv.DictReader(file_obj, delimiter="\t")
    i = []
    v = []
    inverter = 1 if invert == False else -1
    for line in reader:
        curr = inverter*float(line["Current Avg"])*1e9   # Current in nA
        volt = inverter*float(line["Voltage"])*1e3       # Voltage in mV
        if(len(limit) == 2 and (volt > max(limit) or volt < min(limit))):
            continue
        i.append(curr)    
        v.append(volt)        
    return np.asarray([i,v])

def linear(m, b, x):
    return list(map(lambda y:m*y+b, x))

def avg_voltages(currents, voltages):
    u_voltages = sorted(list(set(voltages)))
    u_current = []
    for v in u_voltages:
        u_indices = [i for i, x in enumerate(voltages) if x == v]
        u_current.append(np.mean(currents[u_indices]))
    return np.asarray([u_current, u_voltages])

def plot_iv(fname, save_plot = False, save_data = True, location = [], avg = True, fit = False, show_g = True, limit = [], invert = False):
    with open(fname, 'rU') as f_obj:
        i, v = csv_reader(f_obj, invert = invert, limit = limit)
        if(avg == True):
            i, v = avg_voltages(i, v)
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
        if(save_data == True):
            if(len(location) == 3): # If location is given
                [raw_fname, dirname, img_folder] = location
                path = dirname+"/"+img_folder+"/"
                final_fname = path+raw_fname[-19:-4]+".csv"
            else:   # Or else store in folder of file
                final_fname = fname[:-4]+".csv"
            # Save in csv with voltage in V and current in A
            np.savetxt(final_fname, np.transpose(np.asarray([[k*1e-3 for k in v], [l*1e-9 for l in i]])), delimiter=",")
        
        if(save_plot == True):
            if(len(location) == 3): # If location is given
                [raw_fname, dirname, img_folder] = location
                final_fname = dirname+"/"+img_folder+"/"+raw_fname[-19:-4]+".png"
            else:   # Or else store in folder of file
                final_fname = fname[:-4]+".png"
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
                    plot_iv(os.path.join(dirname, filename), save_plot = True, save_data = True, location = [filename, dirname, img_folder], fit = False)



plot_iv("Data/Chip_PF.hkr", save_plot = False, save_data = False, invert = True, limit = [500, -500])
dirname = './Data/IV/Final'
img_folder = "IV_avg"
#recursive_plot(dirname, img_folder)