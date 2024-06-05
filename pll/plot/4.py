#!/usr/bin/env python3

import sys
sys.path.append('../../../dsim/')
import math
from engineering_notation import EngNumber
import matplotlib.pyplot as plt
import plot_lib as plot
import csv
import numpy as np

sqrt = math.sqrt
pi = math.pi
frac = lambda x,y: x/y




# List to hold the values from the second column
tran_x_csv = []
tran_y_csv = []

# Open the CSV file and read the second column
with open('4_tran.vcsv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for _ in range(6):
        next(reader)
    for row in reader:
        if row:  # Check if row is not empty
            tran_x_csv.append(float(row[0]))  # Convert string to float and append
            tran_y_csv.append(float(row[1]))  # Convert string to float and append



Fosc = 12.12e9
Tosc = 1/Fosc
Ldco_num = -127
Ldco_offset = 1e6
sigma_dco = plot.VCO_L2jitter(Ldco_num, Fosc, Ldco_offset)




fig, ax = plt.subplots(1,1)


cur_ax = ax
Fout = Fosc
auto_freq=False
plot.phase_noise(fig, cur_ax, tran_y_csv, Fout=Fout, auto_freq=auto_freq, color='C0', label='cadence simulation', integ_to=600e3)
plot.phase_noise(fig, cur_ax, tran_y_csv, Fout=Fout, auto_freq=auto_freq, sumover_N=50, color='C1', label='cadence simulation')


Ldco = lambda f: frac((2*pi*Ldco_offset)**2 * pow(10,Ldco_num/10), (2*pi*f)**2)
plot.plot_psd(fig, cur_ax, Ldco, fstart=1e3, fend=7e9, color='C2', label='dco output', linewidth=2)




plt.show()
