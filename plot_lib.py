import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from engineering_notation import EngNumber
import numpy as np
import sys
import math
import cmath
import types


def from_to(n_from, n_to, s_type):
    '''Return a list, either linear or decade

    >>> from_to(1, 5, ['linear', 1])
    [1, 2, 3, 4, 5]
    >>> from_to(0.0, 0.5, ['linear', 0.1])
    [0.0, 0.1, 0.2, 0.30000000000000004, 0.4, 0.5]
    >>> from_to(1e-2, 1e1, ['decade', 2])
    [0.01, 0.03162277660168379, 0.1, 0.31622776601683794, 1.0, 3.1622776601683795, 10.0]
    '''
    if s_type[0] == 'linear':
        x = n_from
        ret = [x]
        while (x < n_to):
            x += s_type[1]
            if (not (x > n_to)):
                ret.append(x)
        return ret
    if s_type[0] == 'decade':
        x = n_from
        ret = [x]
        while (x < n_to):
            x = pow(10, math.log10(x) + 1.0/s_type[1])
            if (not (x > n_to)):
                ret.append(x)
        if ret[-1] < n_to:
            ret.append(n_to)
        return ret
    if s_type[0] == 'points':
        return [n_from + (n_to - n_from) / (s_type[1]-1) * i for i in range(s_type[1]-1)] + [n_to]
    else:
        print('Error: no such options, {}.'.format(s_type[0]), file=sys.stderr)
        exit()

def dB10(x):
    if type(x) == list or isinstance(x, np.ndarray):
        return [10*math.log10(ele) for ele in x]
    elif isinstance(x, types.FunctionType):
        return lambda s, *args, **kw: 10*math.log10(x(s, *args, **kw))
    else:
        return 10*math.log10(x)

def dB20(x):
    if type(x) == list or isinstance(x, np.ndarray):
        return [20*math.log10(ele) for ele in x]
    elif isinstance(x, types.FunctionType):
        return lambda s, *args, **kw: 20*math.log10(x(s, *args, **kw))
    else:
        return 20*math.log10(x)


def pts(fig, ax, ary, color=None, subsamples=1, Fs=1, window=False):
    if window != False:
        subsamples = 1
    return ax.plot([i*subsamples/Fs for i in range(len(ary) - int(window*Fs) if (window and len(ary) > int(window*Fs)) else 0,len(ary)//subsamples)],
            [ary[i*subsamples] for i in range(len(ary) - int(window*Fs) if (window and len(ary) > int(window*Fs)) else 0,len(ary)//subsamples)],
            color=color), 0 if window == False else [ary[i*subsamples] for i in range(len(ary) - int(window*Fs) if (window and len(ary) > int(window*Fs)) else 0,len(ary)//subsamples)], 0 if window == False else [i*subsamples/Fs for i in range(len(ary) - int(window*Fs) if (window and len(ary) > int(window*Fs)) else 0,len(ary)//subsamples)]
    # ax.plot([_ for _ in range(len(ary))], ary, color=color)




def subplot(ax, f, cfg):
    labelsize=14
    if isinstance(f, types.FunctionType):
        xvals = cfg['xvals']
        if 'input' in cfg and cfg['input'] == 'array':
            y = f(cfg['xvals'])
        else:
            y = [f(_) for _ in cfg['xvals']]
    elif type(f) == list:
        xvals = f[0]
        y = f[1]
    else:
        print('plot.subplot Error, incorrect f input')
        exit()


    if cfg['xscale'] == 'log':
        ax.semilogx(xvals, y,
                    '-' if 'line' not in cfg else cfg['line'],
                    label = '' if 'label' not in cfg else cfg['label'],
                    color = 'C0' if 'color' not in cfg else cfg['color'])
    else:
        ax.plot(xvals, y,
                '-' if 'line' not in cfg else cfg['line'],
                label = '' if 'label' not in cfg else cfg['label'],
                color = 'C0' if 'color' not in cfg else cfg['color'])

    ax.set_xlabel('' if 'xlabel' not in cfg else cfg['xlabel'], fontsize=labelsize)
    ax.set_ylabel('' if 'ylabel' not in cfg else cfg['ylabel'], fontsize=labelsize)
    ax.set_title('' if 'title' not in cfg else cfg['title'])


def tick_semilogx(ax, label=True):
    # ticks
    locmaj = ticker.LogLocator(base=10,numticks=12)
    ax.xaxis.set_major_locator(locmaj)
    locmin = ticker.LogLocator(base=10.0,subs=(0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9),numticks=12)
    ax.xaxis.set_minor_locator(locmin)
    ax.xaxis.set_minor_formatter(ticker.NullFormatter())
    if label == False:
        ax.xaxis.set_ticklabels([])
    # grid
    ax.grid(which='both',linestyle='--')




def bode(fig, axs, h, fstart = 1, fend = 1e9, enable_pm=True, enable_z=False, fsample=1, enable_bw=False, legend_label=''):

    def to_phase(h):
        def helper(xvals):
            new_h = lambda x: cmath.phase(h(complex(0, 2*math.pi*x)))*360/2/math.pi
            ret = [new_h(xvals[0])]
            for x in xvals[1:]:
                tmp = new_h(x)
                if abs(tmp-ret[-1]) >= 180 and tmp > ret[-1]:
                    ret.append(tmp-360)
                elif abs(tmp-ret[-1]) >= 180 and tmp < ret[-1]:
                    ret.append(tmp+360)
                else:
                    ret.append(tmp)
            return ret
        return helper

    def phase_margin(h, fstart = 1, fend = 1e9):
        magnitude = lambda f: abs(h(complex(0, 2*math.pi*f)))
        phase = to_phase(h)
        phases = phase(from_to(fstart, fend, ['decade',100]))
        min_diff = abs(magnitude(fstart) - 1)
        pm_freq = fstart
        pm = 0
        pm_idx = 0
        for freq in from_to(fstart, fend, ['decade',100]):
            if abs(magnitude(freq)-1) < min_diff:
                min_diff = magnitude(freq) - 1
                pm_freq = freq
                pm = phases[pm_idx] - (-180)
            pm_idx += 1
        return pm, pm_freq


    magnitude = lambda f: abs(h(complex(0, 2*math.pi*f)))
    phase = to_phase(h)
    if enable_z:
        hz = lambda s: h(pow(math.e, s/fsample))
        magnitude = lambda f: abs(hz(complex(0, 2*math.pi*f)))
        phase = to_phase(hz)

    cfg = {'xscale': 'log',
           'xvals': from_to(fstart, fend, ['decade',100]),
           'ylabel': 'Magnitude (dB)',
           'label': legend_label}
    subplot(axs[0], dB20(magnitude), cfg)
    cfg = {'xscale': 'log',
           'input':'array',
           'xvals': from_to(fstart, fend, ['decade',100]),
           'xlabel': 'Frequency (Hz)',
           'ylabel': 'Phase (deg)',
           'label': legend_label}
    subplot(axs[1], phase, cfg)
    axs[1].set_yticks([0,-45,-90,-135,-180])
    if enable_pm:
        # draw phase margin dashed lines
        pm, pm_freq = phase_margin(h, fstart, fend)
        axs[0].set_title('Phase Margin = {:.1f} deg (at {} Hz)'.format(pm, EngNumber(pm_freq)))
        axs[0].axvline(x=pm_freq, ymin=0, ymax=(dB20(magnitude)(pm_freq) - axs[0].get_ylim()[0])/(axs[0].get_ylim()[1] - axs[0].get_ylim()[0]),color='black', linestyle='--')
        axs[1].axvline(x=pm_freq, ymin=(-180+pm - axs[1].get_ylim()[0])/(axs[1].get_ylim()[1] - axs[1].get_ylim()[0]), ymax=1 ,color='black', linestyle='--')
        axs[1].axvline(x=pm_freq, ymin=(-180 - axs[1].get_ylim()[0])/(axs[1].get_ylim()[1] - axs[1].get_ylim()[0]), ymax=(-180+pm - axs[1].get_ylim()[0])/(axs[1].get_ylim()[1] - axs[1].get_ylim()[0]) ,color='seagreen', linestyle='--')
        axs[0].axhline(y=0, color='gray', xmin=0.05, xmax=0.95,linestyle='--')
        axs[1].axhline(y=-180, color='gray', xmin=0.05, xmax=0.95,linestyle='--')
    # Styles
    tick_semilogx(axs[0],label=False)
    tick_semilogx(axs[1])
    fig.suptitle('Bode Diagram', fontweight='bold')
    fig.set_size_inches(8,6)
    fig.subplots_adjust(hspace=0.05)

    # Bandwidth Calculation
    if enable_bw:
        bw_calc = psd_bw(lambda f: pow(magnitude(f), 2), fstart, fend)
        axs[0].axvline(x=bw_calc, color='gray', linestyle='--')
        axs[1].axvline(x=bw_calc, color='gray', linestyle='--')
    return fig, axs

def plot_psd(fig, ax, h, fstart=1, fend=1e9, line='-', label='', fsample=1, sumover_N = 1, atten=1, color='C0'):
    ''' plot the power spectral density
    h = lambda freq: psd
    '''
    cfg = {'xscale': 'log',
           'xvals': from_to(fstart, fend, ['decade',10000]),
           'ylabel': 'Magnitude (dB)',
           'xlabel': 'Frequency (Hz)',
           'title': 'Power Spectral Density',
           'line': line,
           'label': label,
           'color': color}

    tick_semilogx(ax)
    if isinstance(h, types.FunctionType):
        subplot(ax, dB10(h), cfg)
    elif type(h) == list:
        yvals, xvals = fft_psd(even_ary(h), fsample)
        if sumover_N != 1:
            yvals, xvals = sumover(sumover_N)(yvals, xvals)
        if atten != 1:
            for i in range(len(yvals)):
                yvals[i] = yvals[i]*atten
        subplot(ax, [[xvals[i] for i in range(len(xvals)) if yvals[i] > 0], dB10([yvals[i] for i in range(len(yvals)) if yvals[i] > 0])], cfg)

def phase_noise(fig, ax, tps, Fout, line='-', label='', sumover_N = 1, only_noise=False, color='C0'):
    if only_noise == False:
        tmp = []
        i = 0
        for t in tps:
            tmp.append( t - (i/Fout) )
            i = i + 1
    else:
        tmp = tps

    plot_psd(fig, ax, tmp, fend=Fout/2, line=line, label=label, fsample=Fout, sumover_N = sumover_N, atten=0.5*pow(Fout*2*math.pi, 2), color=color)
    ax.set_title( 'Phase Noise L' )

def dist_psd_plots(fig, ax, tps, Fs, psd_type='psd', sumover_N = 1, color='C0'):
    if psd_type == 'psd':
        plot_psd(fig, ax, tps, fsample=Fs, sumover_N=sumover_N, color=color)
    elif psd_type == 'abs_jitter':
        phase_noise(fig, ax, tps, Fout=Fs, sumover_N=sumover_N, color=color, only_noise=True)
    elif psd_type == 'osc_times':
        phase_noise(fig, ax, tps, Fout=Fs, sumover_N=sumover_N, color=color, only_noise=False)
    else:
        print('plot lib: dist_psd_plots Error! No such psd_type')
        exit()


def jitter(tps, Fout, only_noise=False, tstab=0):
    tmp = 0
    if only_noise == False:
        tmp = np.array([value - index/Fout for index, value in enumerate(np.array(tps))])
    else:
        tmp = np.array(tps)
    tmp = tmp[int(tstab*Fout):]
    if len(tmp) == 0:
        return 0
    else:
        return np.std(tmp)

def period_jitter(tps, Fout, tstab=0):
    tmp = np.array([tps[i] - tps[i-1] for i in range(1, len(tps))])
    tmp = tmp[int(tstab*Fout):]
    if len(tmp) == 0:
        return 0
    else:
        return np.std(tmp)

def osc_period(tps):
    tmp = []
    for i in range(1, len(tps)):
        tmp.append(tps[i] - tps[i-1])
    return np.mean(tmp)

def tf2psd(h, var='s', sample_freq=1):
    if var == 'z':
        psd = lambda freq: pow( abs(h(pow(math.e, complex(0, 2*math.pi*freq/sample_freq)))) ,2)
    else:
        assert var == 's'
        psd = lambda freq: pow(abs(h(complex(0,2*math.pi*freq))),2)
    return psd



def psd_bw(S, fstart=1, fend=1e9, tol=1):
    v1 = S(fstart)/2
    f1 = fstart
    f2 = fend
    while True:
        assert f2 > f1
        if f2 - f1 < tol:
            break
        if S((f1+f2)/2) < v1:
            f2 = (f1+f2)/2
        elif S((f1+f2)/2) == v1:
            return (f1+f2)/2
        else:
            f1 = (f1+f2)/2
    return (f1+f2)/2


def fft_psd(sig, Fs):
    N = len(sig)
    assert N%2 == 0
    spectrum = np.fft.fft(sig) / N
    psd = pow(np.abs(spectrum),2)
    psd = psd[0:int(N/2)+1]
    psd[1:int(N/2)] = 2*psd[1:int(N/2)]
    r1 = psd / (Fs/N)
    r2 = np.array(from_to(0, Fs/2, ['points', N//2 + 1]))
    assert len(r1) == len(r2)
    return r1, r2

def sumover(num_N):
    def helper(ys, xs):
        assert len(ys) == len(xs)
        rety = []
        retx = []
        tmp_sum = 0
        for i in range(len(ys)):
            tmp_sum += ys[i]
            if i % num_N == num_N - 1:
                rety.append(tmp_sum/num_N)
                retx.append(xs[i - (num_N - 1)])
                tmp_sum = 0
        return rety, retx

    def new_helper(ys, xs):
        assert len(ys) == len(xs)
        rety = list(ys[:num_N])
        retx = list(xs[:num_N])
        tmp_sum = 0
        for i in range(num_N, len(ys)):
            tmp_sum += ys[i]
            if (i - num_N) % num_N == num_N - 1:
                rety.append(tmp_sum/num_N)
                retx.append(xs[i - (num_N - 1)])
                tmp_sum = 0
        return rety, retx
    return new_helper


def even_ary(ary):
    if len(ary) % 2 == 0:
        return ary
    else:
        return ary[0:-1]




