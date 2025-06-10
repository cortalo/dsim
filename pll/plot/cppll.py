#!/usr/bin/env python3

import sys
sys.path.append('../../../dsim/')
import math
from engineering_notation import EngNumber
import matplotlib.pyplot as plt
import plot_lib as plot
import csv
import numpy as np
from scipy import integrate

sqrt = math.sqrt
pi = math.pi
frac = lambda x,y: x/y
sin = math.sin


Fref=600e3

Icp = 500e-6
Kvco = 1e5*2*pi
N = 1

Cs = 10e-9
Cp = 300e-12
Rs = 4e3

Hlf_1 = lambda s: Rs + (1/s/Cs)
Hlf_2 = lambda s: (1/s/Cp)
Hlf = lambda s: Hlf_1(s)*Hlf_2(s) / (Hlf_1(s)+Hlf_2(s))
Hopen = lambda s: Icp/2/pi * Hlf(s) * Kvco / s / N

Sdsm = lambda f: frac(4*pi*pi,12*Fref)*pow(2*sin(pi*f/Fref), 3*(2-1))
Hclose = lambda s: Hopen(s)/(1+Hopen(s))
Lout = lambda f: Sdsm(f)*plot.tf2psd(Hclose)(f)

fig, ax = plt.subplots(2,1)
plot.bode(fig, ax, lambda s: Hopen(s))
plt.show()

# result, error = integrate.quad(Lout, 1e3, 100e6)
# print(sqrt(2*result)/2/pi/N/Fref)

# fig, ax = plt.subplots(1,1)
# plot.plot_psd(fig, ax, Lout, fstart=1e3, fend=500e6)
plt.show()
