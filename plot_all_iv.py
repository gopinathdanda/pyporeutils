#!/usr/bin/env python

# PLOT AND SAVE IV FROM ALL HKR FILES IN FOLDERS

import numpy as np
import csv
import matplotlib.pyplot as plt
import os

def csv_reader(file_obj, invert = False, limit = []):
    """Extract current and voltage information from .hkr files
    
    :param file_obj: File to be read
    :param invert: Invert both current and voltage (Default = False)
    :param limit: Limit data extraction based on voltage limit provided as a list of 2 floats; order of list not important (Default = [])
    :returns: Numpy array of current and voltage in nA and V, respectively          
    
    """
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
    """Generate a linear function
    
    :param m: Slope of linear equation
    :param b: Intercept of linear equation
    :param x: Independent variable
    :returns: Linear function of the form m * x + b
    
    """
    return m*x+b

def unique(arr):
    """Ascendingly sort array with only unique elements
    
    :param arr: Array to be processed
    :returns: Sorted unique array
    
    """
    return sorted(list(set(arr)))

def avg_currents(currents, voltages):
    """Generate average currents for corresponding voltages
    
    :param currents: Current numpy array
    :param voltages: Voltage numpy array
    :returns: Numpy array of average currents and corresponding voltages
    
    """
    u_voltages = unique(voltages)
    u_current = []
    for v in u_voltages:
        u_indices = [i for i, x in enumerate(voltages) if x == v]
        u_current.append(np.mean(currents[u_indices]))
    return np.asarray([u_current, u_voltages])

def di_dv(currents, voltages):
    """Generate change in conductance with voltage
    
    :param currents: Current numpy array
    :param voltages: Voltage numpy array
    :returns: Numpy array of discrete dI/dV and corresponding voltages in nS and V, respectively
    
    """
    if(len(unique(voltages)) != len(voltages)):
        currents, voltages = avg_currents(currents, voltages)
    v_step = (max(voltages)-min(voltages))/len(voltages)*1.0
    dS = np.diff(currents)/v_step
    dv = voltages+v_step
    return ([dS, dv[:-1]])

def plot_iv(fname, save_plot = False, save_data = True, location = [], didv = False, avg = True, fit = False, show_g = True, invert = False, limit = []):
    """Plot or save IV, linear fit and dI/dV characteristics in .png and .csv files, respectively
    
    :param fname: Filename of .hkr file to be processed
    :param save_plot: Save plot in a .png file in same location as file or (location) option, if provided (Default = False)
    :param save_data: Save data in a .csv file in same location as file or (location) option, if provided (Default = True)
    :param location: Location of file to be saved as a 2 string list of the format [raw filename, directory name] (Default = [])
    :param didv: Plot or save dI/dV characteristics (Default = False)
    :param avg: Plot or save averaged currents and corresponding voltages (Default = True)
    :param fit: Plot best linear fit (Default = False)
    :param show_g: Show G from best linear fit in graph (Default = True)
    :param invert: Invert both current and voltage (Default = False)
    :param limit: Limit data extraction based on voltage limit provided as a list of 2 floats; order of list not important (Default = [])
    
    """
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
            dS, dv = di_dv(i, v)
            ax2.scatter(dv, dS)
            dv_lim = (max(dv)-min(dv))/len(dv)*10.0
            dS_lim = max(dS)/len(dS)*10.0
            ax2.set_xlim([min(dv)-dv_lim, max(dv)+dv_lim])
            ax2.set_ylim([0, max(dS)+dS_lim])
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
                np.savetxt(d_final_fname+".csv", np.transpose([dv, dS]), delimiter=",")
        
        if(save_plot == True):
            fig.savefig(final_fname+".png", dpi=300, bbox_inches = "tight")
            fig.clf()
            if(didv == True):
                fig2.savefig(d_final_fname+".png", dpi=300, bbox_inches = "tight")
                fig2.clf()
        else:
            plt.show()

def recursive_plot(main_dirname, sub_folder = ''):
    """Process IV data recursively from a folder
    
    :param main_dirname: Name of directory to look for .hkr files
    :param sub_folder: Name of subdirectory where plots and generated data will be saved (Default = '')
    
    """
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