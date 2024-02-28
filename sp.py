import sympy as sp
from engineering_notation import EngNumber

sqrt = sp.sqrt
symbols = sp.symbols
solve = sp.solve
frac = lambda x, y: x/y

# Constants given in the image
mu_nCox = 134e-6 # in A/V^2
W_L_1 = 100
W_L_2 = 200
R_D = 2e3 # in ohms
I = symbols('I')

# Equations from the image
gm1 = sqrt(2 * mu_nCox * (W_L_1) * I)
gm2 = sqrt(2 * mu_nCox * (W_L_2) * I)

# Transconductance equation
# g_0 = 1 / (gm1 + (1/2)*gm2*R_D)
g_0 = frac(1, gm1) * frac(1, 1 + 0.5*gm2*R_D)

# Now we solve for I using sympy
I_solution = solve(g_0 - 50, I)

print(EngNumber(float(I_solution[0])))
