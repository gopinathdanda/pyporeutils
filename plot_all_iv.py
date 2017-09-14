#!/usr/bin/env python

# PLOT AND SAVE IV FROM ALL HKR FILES IN FOLDERS

import numpy as np
import csv
import matplotlib.pyplot as plt
import os

def csv_reader(file_obj, invert = False, limit = []):
    '''
    Read hkr files and return current (in nA) and voltage (in V) in a numpy array
    Options:
        invert (boolean)                = Invert both current and voltage
        limit (float) [limit1, limit2]  = Limit data extraction based on voltage limit; order of list not important 
    '''
    reader = csv.DictReader(file_obj, delimiter="\t")
    i = []
    v = []
    inverter = 1 if invert == False else -1
    for line in reader:
        curr = inverter*float(line["Current Avg"])*1e9   # Current in nA
        volt = inverter*float(line["Voltage"])           # Voltage in V
        if(len(limit) == 2 and (volt > max(limit) or volt < min(limit))):
            continue
        i.append(curr)    
        v.append(volt)        
    return np.asarray([i,v])

def linear(m, b, x):
    '''
    Returns a linear function of the form:  m * x + b
    '''
    return m*x+b

def unique(arr):
    '''
    Returns an ascendingly sorted array with only unique elements
    '''
    return sorted(list(set(arr)))

def avg_currents(currents, voltages):
    '''
    Returns average currents (for each voltage) and the corresponding voltages in a numpy array
    '''
    u_voltages = unique(voltages)
    u_current = []
    for v in u_voltages:
        u_indices = [i for i, x in enumerate(voltages) if x == v]
        u_current.append(np.mean(currents[u_indices]))
    return np.asarray([u_current, u_voltages])

def di_dv(currents, voltages):
    '''
    Return discrete slope (dI/dV) and the corresponding voltages in a numpy array
    '''
    if(len(unique(voltages)) != len(voltages)):
        currents, voltages = avg_currents(currents, voltages)
    v_step = (max(voltages)-min(voltages))/len(voltages)*1.0
    di = np.diff(currents)/v_step
    dv = voltages+v_step
    return ([di, dv[:-1]])

def plot_iv(fname, save_plot = False, save_data = True, location = [], didv = False, avg = True, fit = False, show_g = True, invert = False, limit = []):
    '''
    Plot or save IV, linear fit and dI/dV characteristics in .png and .csv files, respectively
    Options:
        save_plot (boolean)                                 = Save plot in a .png file in same location as file or (location) option, if provided
        save_data (boolean)                                 = Save data in a .csv file in same location as file or (location) option, if provided
        location (strings) [raw filename, directory name]   = Location of file to be saved
        
        didv (boolean)                                      = Plot or save dI/dV characteristics 
        avg (boolean)                                       = Plot or save averaged currents and corresponding voltages
        fit (boolean)                                       = Plot best linear fit
        show_g (boolean)                                    = Show G from best linear fit in graph
        
        invert (boolean)                                    = Invert both current and voltage
        limit (float) [limit1, limit2]                      = Limit data extraction based on voltage limit; order of list not important
    '''
    with open(fname, 'rU') as f_obj:
        i, v = csv_reader(f_obj, invert = invert, limit = limit)
        if(avg == True):
            i, v = avg_currents(i, v)
        fig = plt.figure("IV")
        ax = plt.subplot(111)
        ax.scatter(v, i)
        
        if(didv == True):
            fig2 = plt.figure("dI_dV")
            ax2 = plt.subplot(111)
            di, dv = di_dv(i, v)
            ax2.scatter(dv, di)
            dv_lim = (max(dv)-min(dv))/len(dv)*10.0
            ax2.set_xlim([min(dv)-dv_lim, max(dv)+dv_lim])
            ax2.set_xlabel("Voltage (V)", size = "large")
            ax2.set_ylabel("dI/dV (nS)", size = "large")
       
        g, b = np.polyfit(v, i, 1)
        if(fit == True):
            ax.plot(v, linear(g, b, v))
        print("G = %0.2f nS" % g)
    
        v_lim = (max(v)-min(v))/len(v)*10.0
        ax.set_xlim([min(v)-v_lim, max(v)+v_lim])
        ax.set_xlabel("Voltage (V)", size = "large")
        ax.set_ylabel("Ionic current (nA)", size = "large")
        if(show_g == True):
            ax.text(0.7, 0.1,("G = %0.2f nS" % (g)),
             horizontalalignment='left',
             verticalalignment='center',
             transform = ax.transAxes)
        
        if(len(location) == 2): # If location is given
            [raw_fname, dirname] = location
            final_fname = dirname+"/"+raw_fname[-19:-4]
            d_final_fname = dirname+"/"+raw_fname[-19:-4]+"_didv"
        else:   # Or else store in folder of file
            final_fname = fname[:-4]
            d_final_fname = fname[:-4]+"_didv"
        
        if(save_data == True):
            # Save in csv with voltage in V and current in A
            np.savetxt(final_fname+".csv", np.transpose([v, i*1e-9]), delimiter=",")
            if(didv == True):
                # Save in csv with voltage in V and current in nS
                np.savetxt(d_final_fname+".csv", np.transpose([dv, di]), delimiter=",")
        
        if(save_plot == True):
            fig.savefig(final_fname+".png", dpi=300, bbox_inches = "tight")
            fig.clf()
            if(didv == True):
                fig2.savefig(d_final_fname+".png", dpi=300, bbox_inches = "tight")
                fig2.clf()
        else:
            plt.show()

def recursive_plot(main_dirname, sub_folder = ""):
    '''
    Plot or save recursively from a folder
    Options:
        sub_folder (string)     = Name of subdirectory where plots and generated data will be saved
    '''
    for dirname, dirnames, filenames in os.walk(main_dirname):
        print("------------------")
        print(dirname)
        print("------------------")
        for filename in filenames:
            if(filename[-4:] == '.hkr'):
                if(not os.path.isdir(dirname+sub_folder)):
                    os.mkdir(dirname+sub_folder)
                plot_iv(os.path.join(dirname, filename), save_plot = True, location = [filename, dirname+sub_folder], didv = True)



plot_iv("Data/Chip_PF.hkr", save_plot = False, save_data = False, didv = True)
dirname = './Data/IV/Final'
img_folder = "/IV"
#recursive_plot(dirname, img_folder)