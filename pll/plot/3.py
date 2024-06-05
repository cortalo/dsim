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
with open('3_tran.vcsv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for _ in range(6):
        next(reader)
    for row in reader:
        if row:  # Check if row is not empty
            tran_x_csv.append(float(row[0]))  # Convert string to float and append
            tran_y_csv.append(float(row[1]))  # Convert string to float and append



N = 20
Fref = 600e6
Tref = 1/Fref
Fosc = N*Fref
Tosc = 1/Fosc

Lref = -166
sigma_ref = plot.L2jitter(Lref, Fref)
Ldco_num = -127
Ldco_offset = 1e6
sigma_dco = plot.VCO_L2jitter(Ldco_num, Fosc, Ldco_offset)


Kvco = 200e3
KT = (1/Fosc) - (1/(Fosc+Kvco))
frac_num = 1
Kp = 5
Ki = Kp/1000
Fdsm = Fref

adc_fb_gain = 0.01
adc_ff_gain = 1
cmp_gain = 1/adc_fb_gain/adc_ff_gain
Hadc = lambda s: frac(adc_ff_gain*Fref/s*cmp_gain, 1+adc_fb_gain*adc_ff_gain*Fref/s*cmp_gain)



omega_c = 2*pi*13e6
var_a = math.exp(-omega_c * Tref)

omega_d = 2*pi*10e6
var_d = math.exp(-omega_d * Tref)

Kp_tf = lambda s: Kp * frac(1,1+(s/omega_d)) * frac(1,1+(s/omega_d))



fig, ax = plt.subplots(1,1)


# Fig 3
cur_ax = ax
Fout = (1/1.65e-9)*(20+frac_num/1024)
Tout = 1/Fout
auto_freq=False

plot.phase_noise(fig, cur_ax, tran_y_csv, Fout=Fout, auto_freq=auto_freq, color='C0', label='cadence simulation', integ_to=600e3)
plot.phase_noise(fig, cur_ax, tran_y_csv, Fout=Fout, auto_freq=auto_freq, sumover_N=50, color='C1', label='cadence simulation')

Hopen_ref = lambda s: frac(1,2*pi)*frac(1,1+(s/omega_c))*Hadc(s)*(Kp_tf(s) + frac(Ki*Fref,s))*frac(2*pi*Kvco,s)
Hloop = lambda s: Hopen_ref(s) / N

# DCO noise output
Hclose_dco = lambda s: 1/(1+Hopen_ref(s)/N)
Ldco = lambda f: frac((2*pi*Ldco_offset)**2 * pow(10,Ldco_num/10), (2*pi*f)**2)
Ldco_out = lambda f: Ldco(f)*plot.tf2psd(Hclose_dco)(f)
plot.plot_psd(fig, cur_ax, Ldco_out, fstart=1e3, fend=7e9, color='C2', label='dco output', linewidth=2)

# reference noise output
Lref_f = lambda f: pow(10, Lref/10)
Hclose_ref = lambda s: Hopen_ref(s)/(1+Hopen_ref(s)/N)
Lref_out = lambda f: Lref_f(f)*plot.tf2psd(Hclose_ref)(f)
plot.plot_psd(fig, cur_ax, Lref_out, fstart=1e3, fend=1e7, color='C3', label='ref output', linewidth=2)

# # comparator noise output
# Lbbq = lambda f: (1/8)/(Fdsm)
# Hclose_bbq = lambda s: (Kp_tf(s) + frac(Ki*Fref,s))*frac(2*pi*Kvco,s)/(1+Hopen_ref(s)/N)
# Hdsm_ns = lambda s: 1/(1+Fdsm/s*adc_ff_gain*cmp_gain*adc_fb_gain)
# Lbbq_out = lambda f: Lbbq(f)*plot.tf2psd(Hclose_bbq)(f)*plot.tf2psd(Hdsm_ns)(f)
# plot.plot_psd(fig, cur_ax, Lbbq_out, fstart=1e3, fend=7e9, color='C4', label='comparator Q output', linewidth=2)


# # divider noise output
# Ldsm = lambda f: frac(pow(2*pi,2), 12*Fref)*pow(2*math.sin(pi*f/Fref), 2*2)
# Hclose_dsm = lambda s: (Hopen_ref(s)/N)/(1+(Hopen_ref(s)/N))
# plot.plot_psd(fig, cur_ax, lambda f: Ldsm(f)*plot.tf2psd(Hclose_dsm)(f), fstart=1e3, fend=7e9, color='C5', label='divider Q output', linewidth=2)

# dco quantization noise
Fdsm_dco = Fref
Ldco_q = lambda f: (1/12)/(Fdsm_dco)
Hclose_dco_q = lambda s: frac(2*pi*Kvco,s)/(1+Hopen_ref(s)/N)
Hdco_q_ns = lambda z: pow(1 - pow(z,-1),1)
Ldco_q_out = lambda f: Ldco_q(f)*plot.tf2psd(Hclose_dco_q)(f)*plot.tf2psd(Hdco_q_ns, var='z', Fs=Fdsm_dco)(f)
plot.plot_psd(fig, cur_ax, Ldco_q_out, fstart=10e3, fend=7e9, color='C4', label='dco q output', linewidth=2)


# # dco mismatch noise
# Fdsm_dco = Fref
# Ldco_q = lambda f: pow(0.10,2)/(Fdsm_dco)
# Hclose_dco_q = lambda s: frac(2*pi*Kvco,s)/(1+Hloop(s))
# Ldco_q_out = lambda f: Ldco_q(f)*plot.tf2psd(Hclose_dco_q)(f)
# plot.plot_psd(fig, cur_ax, Ldco_q_out, fstart=1e3, fend=7e9, color='C5', label='dco mismatch output', linewidth=2)

cur_ax.legend(fontsize=12)
cur_ax.set_title('DCO linear bank 10% mismatch')

plt.show()
