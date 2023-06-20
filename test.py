
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
pi = math.pi

sig_init = dsim.sig_init
add_sig = dsim.add_sig
tf_proc = dsim.tf_proc
dtf = tf_lib.dtf


# Independent Parameters
Fref = 50e6
alpha_ref = 300e6
Av = 10
Svn = (70e-9)**2
fABW = 20e6
Fosc = 2e9
KT = 75e-12
sigma_dco = 5e-15
HLF=2.8e-3


H_alpha_ref = dtf([alpha_ref],[1])
H_amp = dtf([Av],[1]) * dtf([2*pi*fABW*Fosc],[2*pi*fABW*Fosc+1, -1])
H_KT = dtf([0,1],[1,0]) * dtf([KT],[1])
H_sum = dtf([1],[1,-1])
H_to_phase = dtf([2*pi*Fosc],[1])

x_caller = lambda : x
y_caller = lambda : y
a_caller = lambda: a

x_mem,a_mem,y_mem=[],[],[]



Fs = 1e6

x = sig_init(lambda: lambda n: np.random.randn()*sqrt(Fs/2), x_mem)
a = sig_init(add_sig([x_caller,y_caller]), a_mem)
y = sig_init(tf_proc(H_amp*H_KT)(a_caller), y_mem)



for i in range(10):
    y(i)

print(x_mem)
print(y_mem)
# fig, ax = plt.subplots(1,1)
# plot.dist_psd_plots(fig, ax, y_mem, Fs=1e6, color='C0')
# plot.dist_psd_plots(fig, ax, y_mem, Fs=1e6, sumover_N=1000, color='C1')
# H.plot_psd(fig, ax, fstart=1, Fs=1e6, color='C2')
# plt.show()
