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
with open('tran_mmd_opt.vcsv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for _ in range(6):
        next(reader)
    for row in reader:
        if row:  # Check if row is not empty
            tran_x_csv.append(float(row[0]))  # Convert string to float and append
            tran_y_csv.append(float(row[1]))  # Convert string to float and append





fig, ax = plt.subplots(1,1)


# Fig 3
cur_ax = ax
Fout = 600e6
Tout = 1/Fout
auto_freq=False

plot.phase_noise(fig, cur_ax, tran_y_csv, Fout=Fout, auto_freq=auto_freq, color='C0', label='cadence simulation', integ_to=600e3)
# plot.phase_noise(fig, cur_ax, tran_y_csv, Fout=Fout, auto_freq=auto_freq, sumover_N=10, color='C1', label='cadence simulation')


cur_ax.legend(fontsize=12)
# cur_ax.set_ylim(-190,-100)
# cur_ax.set_title('Phase Noise: using transient noise simulation')

plt.show()
