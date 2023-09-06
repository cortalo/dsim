import plot_lib as plot
import dsim_lib as dsim
import matplotlib.pyplot as plt
import numpy as np
import math
import gc
import control
tf = control.TransferFunction
np.random.seed(7)

# Math Basics
frac = dsim.frac
exp = dsim.exp
sqrt = math.sqrt
pi = math.pi
sin = math.sin

# DSIM LIBs
MEM_LEN = 10000
sig_init = dsim.sig_init
sig_automem = lambda f_caller: dsim.sig_automem_init(f_caller, MEM_LEN)
sig_nomem = dsim.sig_init_wo_mem
add_sig = dsim.add_sig
sub_sig = dsim.sub_sig
tf_proc = dsim.tf_proc

# Signals
x_caller = lambda: x
y_caller = lambda: y
delta_caller = lambda: delta



# Memorys
x_mem, y_mem = [], []

# Parameters
Fs = 1e3
Ts = 1/Fs
H_integ_dt = tf([2*pi*Ts],[1,-1],Ts)
H_close = H_integ_dt/(1+H_integ_dt)
sigma_x = 0.1

# Connections
x = sig_init(lambda: lambda n: np.random.randn()*sigma_x, x_mem)
y = sig_init(tf_proc(H_integ_dt)(delta_caller), y_mem)
delta = sig_automem(sub_sig(x_caller,y_caller))


# Runtime
for i in range(100000):
    y(i)


# Loop gain bode plot
fig, axs = plt.subplots(2,1)
plot.bode(fig, axs, H_integ_dt, fstart=1e-2, fend=Fs/2)

# Plot of power spectral density
fig, ax = plt.subplots(1,1)
x_psd = lambda f: pow(sigma_x, 2) / (Fs/2)
y_psd_theory = lambda f: x_psd(f) * plot.tf2psd(H_close)(f)
plot.plot_psd(fig, ax, y_mem, fstart=1e-2, fend=Fs/2, fsample=Fs, label='Simulation')
plot.plot_psd(fig, ax, y_mem, fstart=1e-2, fend=Fs/2, fsample=Fs, sumover_N=50, color='C1',label='Averaged')
plot.plot_psd(fig, ax, y_psd_theory, fstart=1e-2, fend=Fs/2, color='C2',label='Theory')
ax.legend(fontsize=16)


plt.show()

