
import matplotlib.pyplot as plt
import numpy as np
import math
import plot_lib as plot
import dsim_lib as dsim
import transfer_function_lib as tf_lib
import gc
np.random.seed(7)


frac = dsim.frac
exp = dsim.exp
sqrt = math.sqrt

sig_init = dsim.sig_init
tf_proc = dsim.tf_proc
dtf = tf_lib.dtf

x_caller = lambda : x
y_caller = lambda : y
x_mem, y_mem = [],[]
H = dtf([0.5, -0.2],[1, -0.5, -0.25, 0.3])


Fs = 1e6

x = sig_init(lambda: lambda n: np.random.randn()*sqrt(Fs/2), x_mem)
y = sig_init(tf_proc(H)(x_caller), y_mem)

for i in range(1000000):
    y(i)

fig, ax = plt.subplots(1,1)
plot.dist_psd_plots(fig, ax, y_mem, Fs=1e6, color='C0')
plot.dist_psd_plots(fig, ax, y_mem, Fs=1e6, sumover_N=1000, color='C1')
H.plot_psd(fig, ax, fstart=1, Fs=1e6, color='C2')
plt.show()
