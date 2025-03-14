#!/usr/bin/env python3

import sys
sys.path.append('/home/longhe/repos/dsim')
import dsim_core as dsim
import plot_lib as plot
import matplotlib.pyplot as plt
import numpy as np
import math
import control
from tqdm import tqdm
from engineering_notation import EngNumber
from adjustText import adjust_text

tf = control.TransferFunction
sqrt = math.sqrt
pi = math.pi
sin = math.sin
cos = math.cos
frac = lambda x,y: x/y

r = 10
L = 1e-3
C1 = 2.7e-15
C2 = 1e-12
CL = 10e-12
Rc = 1e5

z = lambda s: frac(1, frac(1,r+s*L + (1/s/C1)) + s*C2 + 1/Rc + s*CL)

v_psd = lambda f: plot.tf2psd(z)(f) * 4*1.38e-23*300/Rc


fig, ax = plt.subplots(1,1)
texts = []

Rc = 1e5
xvals = plot.from_to(1e3, 200e6, ['decade', 100000])
yvals = [plot.dB10(v_psd(xval)) for xval in xvals]
ax.semilogx(xvals, yvals, color='r')
special_x = [1e3, 1e4, 1e5, 1e6, 1e7]
special_y = [plot.dB10(v_psd(xval)) for xval in special_x]
ax.plot(special_x, special_y, 'ro', markersize=10)
for x, y in zip(special_x, special_y):
    texts.append(ax.text(x, y, f'({x:.0e}, {y:.0f})'))

Rc = 1e6
xvals = plot.from_to(1e3, 200e6, ['decade', 100000])
yvals = [plot.dB10(v_psd(xval)) for xval in xvals]
ax.semilogx(xvals, yvals,color='gold')
special_x = [1e3, 1e4, 1e5, 1e6, 1e7]
special_y = [plot.dB10(v_psd(xval)) for xval in special_x]
ax.plot(special_x, special_y, 'ro', markersize=10)
for x, y in zip(special_x, special_y):
    texts.append(ax.text(x, y, f'({x:.0e}, {y:.0f})'))

Rc = 1e7
xvals = plot.from_to(1e3, 200e6, ['decade', 100000])
yvals = [plot.dB10(v_psd(xval)) for xval in xvals]
ax.semilogx(xvals, yvals, color='limegreen')
special_x = [1e3, 1e4, 1e5, 1e6, 1e7]
special_y = [plot.dB10(v_psd(xval)) for xval in special_x]
ax.plot(special_x, special_y, 'ro', markersize=10)
for x, y in zip(special_x, special_y):
    texts.append(ax.text(x, y, f'({x:.0e}, {y:.0f})'))

ax.set_ylim(-220, -120)

adjust_text(texts, arrowprops=dict(arrowstyle='->', color='black', lw=0.5))

ax.set_xlabel('freq (Hz)')
ax.set_ylabel('Output Noise (dBV/Hz)')
ax.set_title('Output Noise Caused by Resistor')


plt.show()
