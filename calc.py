
import math
log10 = math.log10
pi = math.pi
sqrt = math.sqrt

# 2*L = the one sided PSD of phase (in radians).
L2jitter = lambda L, F: sqrt(pow(10, L/10) * F * pow(1/(2*pi*F),2)) # White PN
jitter2L = lambda t, F: 10*log10(t*t*4*pi*pi*F)
VCO_L2jitter = lambda L, Fout, Fm: sqrt(pow(10, L/10)*pow(Fm, 2) * pow(Fout, -3))
