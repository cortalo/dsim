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


Icp = 2e-3
Kvco = 5e6
N = 80

Cs = 5e-9
Cp = 150e-12
Rs = 8e3

Hlf_1 = lambda s: Rs + (1/s/Cs)
Hlf_2 = lambda s: (1/s/Cp)
Hlf = lambda s: Hlf_1(s)*Hlf_2(s) / (Hlf_1(s)+Hlf_2(s))
Hopen = lambda s: Icp/2/pi * Hlf(s) * Kvco / s / N

fig, ax = plt.subplots(2,1)
plot.bode(fig, ax, lambda s: Hopen(s))
plt.show()
