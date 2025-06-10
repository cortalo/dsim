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
sin = math.sin




# List to hold the values from the second column
tran_x_csv = []
tran_y_csv = []

# Open the CSV file and read the second column
with open('5_tran.csv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for _ in range(1):
        next(reader)
    for row in reader:
        if row:  # Check if row is not empty
            tran_x_csv.append(float(row[0]))  # Convert string to float and append
            tran_y_csv.append(float(row[1]))  # Convert string to float and append



Fosc = 600e6*20
Tosc = 1/Fosc
Ldco_num = -124
Ldco_offset = 1e6
sigma_dco = plot.VCO_L2jitter(Ldco_num, Fosc, Ldco_offset)




fig, ax = plt.subplots(1,1)


cur_ax = ax
Fout = Fosc
auto_freq=False
# plot.phase_noise(fig, cur_ax, tran_y_csv, Fout=Fout, auto_freq=auto_freq, color='C0', label='cadence simulation', integ_to=600e3)
plot.phase_noise(fig, cur_ax, tran_y_csv, Fout=12e9/(20+1/1024), auto_freq=auto_freq, sumover_N=1, color='C0', label='tran')
plot.phase_noise(fig, cur_ax, tran_y_csv, Fout=12e9/(20+1/1024), auto_freq=auto_freq, sumover_N=5000, color='C1', label='tran')
#plot.phase_noise(fig, cur_ax, tran_1_y_csv, Fout=Fout, auto_freq=auto_freq, sumover_N=1, color='C1', label='dco fixed code')

dsm_N = 1024
x1=1; mmd_n = 0;
v1=0; y1=0; c1=0; e1=0; s1=0;
v2=0; y2=0; c2=0; e2=0; s2=0;
v3=0; y3=0; c3=0; e3=0; s3=0;
y=0; yq2=0; yq3=0; ya=0;
e1q=0; e2q=0;
y1q=0; y1qq=0; y2q=0;
Fref=600e6

mmd_sum = 0;

ret_mmd = []
ret = []
for i in range(1000000):
    v1=x1+s1; y1=int(v1)//int(dsm_N); c1=y1*dsm_N; e1=v1-c1;
    v2=e1q+s2; y2=int(v2)//int(dsm_N); c2=y2*dsm_N; e2=v2-c2;
    v3=e2q+s3; y3=int(v3)//int(dsm_N); c3=y3*dsm_N; e3=v3-c3;
    ya=y2q+y3-yq3;
    y=y1qq+ya-yq2;
    mmd_n=y;
    s1=e1;
    s2=e2;
    s3=e3;
    yq3=y3;
    yq2=ya
    y1qq = y1q
    y1q = y1
    y2q = y2
    e1q = e1
    e2q = e2
    ret_mmd.append(mmd_n)
    ret.append((mmd_sum +20*i)/12e9 + tran_y_csv[0])
    mmd_sum = mmd_sum + mmd_n


# # debuging
# tran_y_mmd = []
# for i in range(len(tran_y_csv)-1):
#     tran_y_mmd.append((tran_y_csv[i+1]-tran_y_csv[i])*12e9-20)


# print(ret_mmd[0:22])
# print([round(i) for i in tran_y_mmd[0:22]])

for i in range(len(tran_y_csv)):
    if abs(tran_y_csv[i]-ret[i]) > 0.0001/12e9:
        print('divider error')
        print(i)
        break

# plot.phase_noise(fig, cur_ax, ret, only_noise=False, auto_freq=False, Fout=12e9/(20+1/1024), sumover_N=1000, color='C3', label='python')


plot.phase_noise(fig, cur_ax, [tran_y_csv[i]-ret[i] for i in range(len(tran_y_csv))], only_noise=True, auto_freq=False, Fout=12e9/(20+1/1024), sumover_N=1, color='C4', label='diff')
plot.phase_noise(fig, cur_ax, [tran_y_csv[i]-ret[i] for i in range(len(tran_y_csv))], only_noise=True, auto_freq=False, Fout=12e9/(20+1/1024), sumover_N=100, color='C5', label='diff')




Ldco = lambda f: frac((2*pi*Ldco_offset)**2 * pow(10,Ldco_num/10), (2*pi*f)**2)
Fref = 600e6
N = 20
Ldsm = lambda f: frac(4*pi*pi,12*Fref)*pow(2*sin(pi*f/Fref),2*(3-1)) / N / N
plot.plot_psd(fig, cur_ax, Ldsm, fstart=1e3, fend=7e9, color='C2', label='-124dBc/Hz at 1MHz', linewidth=2)
ax.legend(fontsize=16)



ax.set_title('8us to 18us')
plt.show()
