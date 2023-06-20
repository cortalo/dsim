
import numpy as np
import math
import plot_lib as plot


def identical(a,b):
    if len(a) != len(b):
        return False
    else:
        for i in range(0, len(a)):
            if a[i]!=b[i]:
                return False
    return True

def check_same(num1, num2, tol):
    if num2 == 0:
        return abs(num1) < tol
    else:
        return abs((num1/num2)-1) < tol


class dtf:
    def __init__(self, a, b):
        assert len(a) >= 1
        assert len(b) >= len(a)
        assert b[0] != 0
        new_a = []
        new_b = []
        for i in range(len(b)):
            if i < len(a):
                new_a.append(a[i]/b[0])
            else:
                new_a.append(0)
        for i in b:
            new_b.append(i/b[0])
        self.a=new_a
        self.b=new_b
        assert len(self.a) == len(self.b)
        # assert self.pole_zero_cancel(1e-3) == False

    def pole_zero_cancel(self,tol):
        root_a = np.roots(self.a)
        root_b = np.roots(self.b)
        for ele_a in root_a:
            for ele_b in root_b:
                if check_same(ele_a, ele_b, tol):
                    return True
        return False

    def get_a_order(self):
        return len(self.a)-1
    def get_b_order(self):
        return len(self.b)-1
    def get_order(self):
        return self.get_b_order()
    def show(self):
        print((self.a, self.b))
    def __add__(self, other):
        if isinstance(other, dtf):
            (s1_a, s1_b) = (self.a, self.b)
            (s2_a, s2_b) = (other.a, other.b)
            s1_a_order = self.get_a_order()
            s1_b_order = self.get_b_order()
            s2_a_order = other.get_a_order()
            s2_b_order = other.get_b_order()
            s1_order = s1_b_order
            s2_order = s2_b_order

            s3_order = s1_order + s2_order
            s3_a_order = max(s1_a_order + s2_order, s1_order + s2_a_order)
            s3_a = [0] * (s3_a_order + 1)
            s3_b = [0] * (s3_order+1)
            for i in range(0, s1_order+1):
                for j in range(0, s2_order+1):
                    s3_b[i+j] += s1_b[i]*s2_b[j]

            for i in range(0, s1_a_order+1):
                for j in range(0, s2_order+1):
                    s3_a[i+j] += s1_a[i]*s2_b[j]

            for i in range(0, s1_order+1):
                for j in range(0, s2_a_order+1):
                    s3_a[i+j] += s1_b[i]*s2_a[j]
            return dtf(s3_a, s3_b)
        else:
            raise TypeError("Unsupported operand type: +")

    def __mul__(self, other):
        if isinstance(other, dtf):
            (s1_a, s1_b) = (self.a, self.b)
            (s2_a, s2_b) = (other.a, other.b)
            s1_a_order = self.get_a_order()
            s1_b_order = self.get_b_order()
            s2_a_order = other.get_a_order()
            s2_b_order = other.get_b_order()
            s1_order = s1_b_order
            s2_order = s2_b_order

            s3_order = s1_order + s2_order
            s3_a_order = s1_a_order + s2_a_order
            s3_a = [0] * (s3_a_order + 1)
            s3_b = [0] * (s3_order+1)
            for i in range(0, s1_order+1):
                for j in range(0, s2_order+1):
                    s3_b[i+j] += s1_b[i]*s2_b[j]

            for i in range(0, s1_a_order+1):
                for j in range(0, s2_a_order+1):
                    s3_a[i+j] += s1_a[i]*s2_a[j]

            return dtf(s3_a, s3_b)
        else:
            raise TypeError("Unsupported operand type: *")

    def inv(self):
        return dtf(self.b, self.a)

    def __truediv__(self, other):
        if isinstance(other, dtf):
            if identical(self.b, other.b):
                return dtf(self.a, other.a)
            return self * other.inv()
        else:
            raise TypeError("Unsupported operand type: /")

    def to_func(self):
        a = self.a
        b = self.b
        def f(z):
            nom = 0
            for i in range(0, len(self.a)):
                nom += a[i]*pow(z, i)
            denom = 0
            for i in range(0, len(self.b)):
                denom += b[i]*pow(z,i)
            return nom/denom
        return f

    def plot_psd(self, fig, ax, fstart=1, Fs=1e6, line='-', label='', color='C0', atten=1):
        psd_f = plot.tf2psd(self.to_func(), var='z', sample_freq=Fs)
        plot.plot_psd(fig, ax, psd_f, fstart=fstart, fend=Fs/2, line=line, label=label, color=color, atten=atten)


# Boundary

def scaler(x):
    return dtf([x],[1])

def parallel(s1, s2):
    return scaler(1) / (s1.inv()+s2.inv())

def d_integ(x):
    return dtf([x],[1,-1])

def d_delay():
    return dtf([0, 1],[1])


def int_solution(H):
    psd = plot.tf2psd(H.to_func(), var='z', sample_freq=1)
    # step = 0.1
    # int_sum = 0
    # cur = 0
    # while cur + step <= 0.5:
    #     int_sum += integrate.quad(psd,cur,cur+step)[0]
    #     cur += step
    int_sum = integrate.quad(psd, 0, 0.5)[0]
    return math.sqrt(2*int_sum)


def dt_output(H):
    ''' Exact solution for white noise passing a DT transfer function
    Return the output standard deviation, if the input is white noise with std=1
    '''
    ifrac = lambda x, y: x // y
    if H.a[0] != 0:
        H = H * d_delay()
    assert H.a[0] == 0
    assert H.b[0] != 0
    max_len = max(len(H.a), len(H.b))
    new_a = [0]*max_len
    new_b = [0]*max_len
    a = H.a
    b = H.b
    for i in range(0, len(a)):
        new_a[i] = a[i]/b[0]
    for i in range(0, len(b)):
        new_b[i] = -b[i]/b[0]
    a = new_a
    b = new_b
    n = len(b)-1
    matrix_dim = (n*n+n)//2
    matrix = np.zeros((matrix_dim,matrix_dim))
    vector = np.zeros((matrix_dim,1))
    for j in range(1,n):
        for i in range(1, j+1):
            row = ifrac(j*(j-1),2)+i-1
            matrix[row][0] += b[i]*b[j]
            matrix[row][ifrac((i+1)*i,2)] += b[j]
            matrix[row][ifrac((j+1)*j,2)] += b[i]
            matrix[row][ifrac((j+1)*j,2)+i] += 1
            matrix[row][row] += -1
            vector[row] = -a[i]*a[j]
    for i in range(1, n):
        j = n
        row = ifrac(j*(j-1),2)+i-1
        matrix[row][0] += b[i]*b[j]
        matrix[row][ifrac((i+1)*i,2)] += b[j]
        matrix[row][row] += -1
        vector[row] = -a[i]*a[j]
    i = n
    j = n
    row = ifrac(j*(j-1),2)+i-1
    matrix[row][0] += b[i]*b[j]
    matrix[row][row] += -1
    vector[row] = -a[i]*a[j]
    result = math.sqrt(np.linalg.solve(matrix, vector)[0,0])
    assert check_same(result, int_solution(H), 1e-9) == True
    return result

def test_2nd(H):
    a = H.a
    b = H.b
    frac = lambda x, y: x/y
    assert a[0] == 0
    assert b[0] == 1
    assert len(a) == 3
    assert len(b) == 3
    return math.sqrt(frac((a[1]-a[2])*(a[1]-a[2])*(1+b[2])+2*a[1]*a[2]*(1-b[1]+b[2]),(1-b[2])*(1+b[1]+b[2])*(1-b[1]+b[2])))

def test_1nd(H):
    a = H.a
    b = H.b
    frac = lambda x, y: x/y
    assert b[0] == 1
    assert len(a) <= 2
    assert len(b) == 2
    if len(a) == 1:
        a.append(0)
    return math.sqrt(frac(a[0]*a[0] + a[1]*a[1] - 2*a[0]*a[1]*b[1],1-b[1]*b[1]))


