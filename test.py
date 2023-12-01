import sys
# sys.path.append('../../../dsim/')
import plot_lib as plot
import dsim_lib as dsim
import matplotlib.pyplot as plt
import numpy as np
import math
import gc
import control
from engineering_notation import EngNumber
import pickle
tf = control.TransferFunction
np.random.seed(7)

# Math Basics
frac = dsim.frac
exp = dsim.exp
sqrt = math.sqrt
pi = math.pi
sin = math.sin
log10 = math.log10


# DSIM LIBs
MEM_LEN = 10000
sig_init = dsim.sig_init
cnet = lambda f_caller: dsim.sig_automem_init(f_caller, MEM_LEN)
sig_nomem = dsim.sig_init_wo_mem
add_sig = dsim.add_sig
sub_sig = dsim.sub_sig
tf_proc = dsim.tf_proc
bbpd = dsim.bbpd
up_sampler = dsim.up_sampler
down_sampler = dsim.down_sampler
scaler = dsim.scaler
int_div = dsim.integer_divide
mod = dsim.modulus
dd = dsim.delay_sig
def rand(sigma):
    return lambda: lambda n: np.random.randn()*sigma




# Declare Signals
net1_caller = lambda: net1

# Declare Memorys
net1_mem = []


# Connections
net1 = sig_init(lambda: lambda n: n, net1_mem)


# Runtime
for i in range(10):
    net1(i)

print(net1_mem)
