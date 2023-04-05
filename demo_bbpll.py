# BBPLL Behavior Model Simulation
import matplotlib.pyplot as plt
import numpy as np
import math
import plot_lib as plot
import dsim_lib as dsim
import gc
np.random.seed(7)

frac = dsim.frac
exp = dsim.exp

sig_init = dsim.sig_init
sig_automem_init = dsim.sig_automem_init
sig_init_wo_mem = dsim.sig_init_wo_mem
digital_loopfilter = dsim.digital_loopfilter
small_signal_vco = dsim.ss_vco
add_sig = dsim.add_sig
down_sampler = dsim.down_sampler
fom_vco_generator = dsim.fom_vco
bbpd = dsim.bbpd

# Memory Control For DSIM
MEM_LEN = 100000

# Independent Parameters
Fref = 50e6
Kdco = 400e3
M = 50
Kp = 1
Ki = 0.001
fom_vco = -200
sigma_dco = 1e-14

# Dependent Parameters
Tref = lambda: 1/Fref
Fvco = lambda: M * Fref
p_vco = lambda: 4*math.pi*math.pi*frac(Fvco(), pow(sigma_dco, 2)) * pow(10, fom_vco/10) * 1e-3 * pow( frac(1, 2*math.pi*Fvco()) , 2) * 2

# System Declaration
t_ref=bb_out=v_control=t_vco=t_out=t_fb=wn1=t_nvco=lambda : None
t_ref_caller = lambda : t_ref
t_fb_caller = lambda : t_fb
bb_out_caller = lambda : bb_out
v_control_caller = lambda : v_control
t_out_caller = lambda : t_out
wn1_caller = lambda : wn1
t_nvco_caller = lambda : t_nvco
t_vco_caller = lambda : t_vco
v_control_mem, t_out_mem, t_fb_mem = [],[],[]
mem_list = [v_control_mem, t_out_mem, t_fb_mem]


# System Initialization
def sys_init():
    # Signal Prepration and Garbage Collection
    global t_ref, bb_out, v_control, t_vco, t_out, t_fb, wn1, t_nvco
    global sys_idx; sys_idx = 0
    for mem in mem_list: mem.clear()
    gc.collect()
    # Signal Connections
    t_ref = sig_init_wo_mem(lambda: lambda n: 0)
    bb_out = sig_automem_init(bbpd(t_ref_caller, t_fb_caller), MEM_LEN)
    v_control = sig_init(digital_loopfilter(Kp, Ki, MEM_LEN)(bb_out_caller), v_control_mem)
    t_vco = sig_automem_init(small_signal_vco(Kdco, Fvco(), M,only_noise=True,init_dt=frac(Kdco*Ki,2*Fvco()*Fvco()), length_mem=MEM_LEN)(v_control_caller), MEM_LEN)
    t_out = sig_init(add_sig([t_vco_caller, t_nvco_caller]), t_out_mem)
    t_fb = sig_init(down_sampler(M)(t_out_caller), t_fb_mem)
    wn1 = sig_automem_init(lambda: lambda n: np.random.randn(), MEM_LEN)
    t_nvco = sig_automem_init(fom_vco_generator(fom=fom_vco, power=p_vco(), Fs=Fvco(), length_mem=MEM_LEN)(wn1_caller), MEM_LEN)

# System Runtime Function
def sys_run(n_num):
    global sys_idx
    n_num=int(n_num)
    for idx in range(sys_idx, sys_idx+n_num):
        t_out(idx)
    sys_idx += n_num

# A simple test
test1 = lambda : dsim.monitor_run(sys_run, Fs = Fvco(), t_simu=150e-6, t_step = 100e-9,
                 mem_list=[{'mem': t_out_mem, 'Fs': Fvco(), 'name':'Tout, Absolute Jitter', 'unit': 's', 'psd_type': 'abs_jitter', 'val_func': lambda tps: plot.jitter(tps, Fvco(), only_noise=True), 'window': 1e-6, 'marker': 'o'},\
                           # {'mem': v_control_mem, 'Fs': Fref, 'name': 'Vc', 'unit': 'V', 'psd_type': 'psd'},\
                           {'mem': t_fb_mem, 'Fs': Fref, 'name': 'Terror', 'unit': 's', 'psd_type': 'abs_jitter', 'window': 1e-6, 'marker': 'o'},\
                                  ])

# Start Simulation
sigma_dco = 1e-30; sys_init(); test1(); plt.show()
sigma_dco = 1e-11; sys_init(); test1(); plt.show()
