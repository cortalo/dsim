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
with open('tvc_tran.vcsv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for _ in range(6):
        next(reader)
    for row in reader:
        if row:  # Check if row is not empty
            tran_x_csv.append(float(row[0]))  # Convert string to float and append
            tran_y_csv.append(float(row[1]))  # Convert string to float and append



Tref = 1.65e-9
Fref = 1/Tref
Sin = lambda f: pow(29e-15,2) / (Fref/2)
H = lambda s: frac(1,Tref) * frac(1, 1 + s/2/pi/13e6)


fig, ax = plt.subplots(1,1)

plot.plot_psd(fig, ax, tran_y_csv, Fs=Fref, color='C0', label='cadence simulation')
plot.plot_psd(fig, ax, tran_y_csv, Fs=Fref, color='C1', sumover_N=50, label='cadence simulation')
plot.plot_psd(fig, ax, lambda f: Sin(f)*plot.tf2psd(H)(f), fstart=1e5, fend=Fref/2, color='C2', label='theory')





plt.show()
