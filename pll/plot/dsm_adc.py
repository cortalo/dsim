#!/usr/bin/env python3

import sys
sys.path.append('../../../dsim/')
import math
from engineering_notation import EngNumber
import matplotlib.pyplot as plt
import plot_lib as plot
import csv
import numpy as np
import scipy.integrate as integrate

sqrt = math.sqrt
pi = math.pi
frac = lambda x,y: x/y




# List to hold the values from the second column
tran_x_csv = []
tran_y_csv = []

# Open the CSV file and read the second column
with open('dsm_adc_tran_wo_noise.vcsv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for _ in range(6):
        next(reader)
    for row in reader:
        if row:  # Check if row is not empty
            tran_x_csv.append(float(row[0]))  # Convert string to float and append
            tran_y_csv.append(float(row[1]))  # Convert string to float and append


# List to hold the values from the second column
tran_x_noise_csv = []
tran_y_noise_csv = []

# Open the CSV file and read the second column
with open('dsm_adc_tran_noise.vcsv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for _ in range(6):
        next(reader)
    for row in reader:
        if row:  # Check if row is not empty
            tran_x_noise_csv.append(float(row[0]))  # Convert string to float and append
            tran_y_noise_csv.append(float(row[1]))  # Convert string to float and append





Fs = 1/1.65e-9
fig, ax = plt.subplots(1,2)


cur_ax = ax[0]
xvals, yvals = plot.plot_psd(fig, cur_ax, tran_y_csv, Fs=Fs, color='C0')
plot.plot_psd(fig, cur_ax, tran_y_csv, Fs=Fs, color='C1', sumover_N=200)
cur_ax.set_title('PSD (resolution {} Hz)'.format(EngNumber(xvals[0])))


Lbbq = lambda f: (1/8)/Fs
Hdsm_ns = lambda z: (1 - (1/z))
Lbbq_out = lambda f: Lbbq(f)*plot.tf2psd(Hdsm_ns, var='z', Fs=Fs)(f)
plot.plot_psd(fig, cur_ax, Lbbq_out, fstart=1e4, fend=Fs/2, color='C2', label='comparator Q output', linewidth=2)

cur_ax = ax[1]

plot.plot_psd(fig, cur_ax, tran_y_noise_csv, Fs=Fs, color='C0')
plot.plot_psd(fig, cur_ax, tran_y_noise_csv, Fs=Fs, color='C1', sumover_N=100)
plot.plot_psd(fig, cur_ax, Lbbq_out, fstart=1e4, fend=Fs/2, color='C2', label='comparator Q output', linewidth=2)

print(integrate.quad(Lbbq_out, 1e4, Fs/2))

plt.show()
