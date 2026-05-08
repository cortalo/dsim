#!/usr/bin/env python3

import sys
sys.path.append('../../../dsim/')
import math
from engineering_notation import EngNumber
import matplotlib
matplotlib.use('TkAgg')   # or 'Qt5Agg', 'GTK3Agg'
import matplotlib.pyplot as plt
import plot_lib as plot
import csv
import numpy as np
from scipy import integrate, signal as sig

sqrt = math.sqrt
pi = math.pi
frac = lambda x,y: x/y
sin = math.sin


Fref=1e6

Icp = 50e-9
Kvco = 250e3*2*pi
N = 1

Rs = 4.976e6
Cs = 1.794e-12 * 14
Cp = 1.098e-12

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

# ── Closed-loop TF (phase domain) ────────────────────────────────────────────
# Hopen(s)  = K·(τ₁·s+1) / [s²·(τ₂·s+b)]
# Hclose(s) = Hopen / (1+Hopen)
#   num = [K·τ₁, K]
#   den = [τ₂, b, K·τ₁, K]

K    = Icp * Kvco / (2 * pi * N)
tau1 = Rs * Cs
tau2 = Rs * Cs * Cp
b    = Cp + Cs

tf_close = sig.TransferFunction([K * tau1, K], [tau2, b, K * tau1, K])

# ── Step response and ramp phase error shown together ────────────────────────
# The ramp phase error is the integral of (1 - step response):
#   θ_err(t) = Δω · ∫₀ᵗ [1 - y_step(τ)] dτ
# The error grows while y_step < 1, shrinks during overshoot, and goes negative
# only if the overshoot area exceeds the initial deficit area.

t, y_step = sig.step(tf_close)
integrand  = 1 - y_step
ramp_err   = np.cumsum(integrand) * (t[1] - t[0])  # numerical integration

# Ramp phase error via direct simulation (lsim with actual ramp input)
delta_f     = 10e3
delta_omega = 2 * pi * delta_f
t2          = np.linspace(0, 500e-6, 500_000)
theta_in    = delta_omega * t2
_, theta_out, _ = sig.lsim(tf_close, U=theta_in, T=t2)
theta_err   = theta_in - theta_out
# Convert phase error (rad) to time offset (ns) at the carrier frequency
err_ns      = theta_err / (2 * pi * Fref) * 1e9

fig2, axs = plt.subplots(2, 1, figsize=(9, 7), sharex=False)

axs[0].plot(t * 1e6, np.ones_like(t), linestyle='--', color='gray', label='Input (step = 1)')
axs[0].plot(t * 1e6, y_step, label='Step response y_step(t)')
axs[0].fill_between(t * 1e6, y_step, 1, where=(y_step < 1), alpha=0.2, color='blue',  label='deficit area (+)')
axs[0].fill_between(t * 1e6, y_step, 1, where=(y_step > 1), alpha=0.2, color='orange', label='overshoot area (−)')
axs[0].set_xlabel('Time (µs)')
axs[0].set_ylabel('Phase (rad)')
axs[0].set_title('Step response and its areas')
axs[0].legend()
axs[0].grid(True)

axs[1].plot(t2 * 1e6, err_ns, color='tab:red', label='Phase error (direct simulation)')
axs[1].axhline(0, linestyle='--', color='gray')
axs[1].set_xlabel('Time (µs)')
axs[1].set_ylabel('Phase error (ns)')
axs[1].set_title('Ramp phase error — 10 kHz frequency step')
axs[1].legend()
axs[1].grid(True)

plt.tight_layout()
plt.show()
