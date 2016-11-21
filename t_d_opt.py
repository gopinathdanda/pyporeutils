#!/usr/bin/env python

# CALCULATE POSSIBLE THICKNESS AND PORE DIAMETER FROM OPEN PORE CONDUCTANCE AND CHANGE IN CONDUCTANCE DURING NANOPARTICLE TRANSLOCATION

import numpy as np
import math
import scipy.optimize
import matplotlib.pyplot as plt

# G0 = open pore conductance (nS)
# dG = change in pore conductance when DNA translocates (nS)
# sig = conductivity of KCl solution (S/m)
# dnp = diameter of nanoparticle (nm)
# dmax = maximum diameter of nanopore (nm)

def t_d_opt(g0, dg, sig = 11.8, dnp = 2.15, dmax = 10):

    # thickness as a function of diameter and change in conductance
    def tdna(d):
        return (math.pi*sig*(d**2-dnp**2)/(g0-dg)/4-math.pi*np.sqrt(d**2-dnp**2)/4)

    # thickness as a function of diameter and open pore conductance
    def topen(d):
        return (math.pi*sig*(d**2)/(4*g0)-math.pi*d/4)
    
    def twofuncs(x):
        y = [ tdna(x[0])-x[1], topen(x[0])-x[1] ]
        return y
    
    # range of diameter for nanopores with dmin = dnp
    d = np.arange(dnp,dmax,0.001) # in nm
    t_dg = tdna(d)
    t_g0 = topen(d)

    fig = plt.figure()
    sp = fig.add_subplot(111)

    myplot = sp.plot(d,t_dg)
    myplot2 = sp.plot(d,t_g0)

    # start from d,t = 8,10 as guess for both functions
    xsolv = scipy.optimize.fsolve(twofuncs, [8, 10])
    print "d = %0.1f nm\nt = %0.1f nm" % (xsolv[0],xsolv[1])

    # plot solution with red marker 'o'
    myplot3 = sp.plot(xsolv[0],xsolv[1],'ro')
    plt.xlim([dnp,dmax])
    plt.ylim([0,np.max([t_dg, t_g0])])
    plt.xlabel('Effective nanopore diameter (nm)')
    plt.ylabel('Effective nanopore thickness (nm)')

    #plt.show()

t_d_opt(69, 3)
