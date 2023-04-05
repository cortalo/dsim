import math
import matplotlib.pyplot as plt
from engineering_notation import EngNumber
import plot_lib as plot

frac = lambda nom, denom: nom/denom
exp = lambda x: pow(math.e, x)


# Init
def sig_init(f_caller, mem):
    '''
    PARAMETERS
    f_caller = lambda: lambda idx: 1
    mem = []

    RETURN

    f_mem = lambda idx: some_value
    '''
    def f_mem(idx):
        if idx < len(mem):
            return mem[idx]
        else:
            assert len(mem) == idx
            tmp = f_caller()(idx)
            mem.append(tmp)
            return tmp
    return f_mem

def sig_automem_init(f_caller, length_mem):
    assert isinstance(length_mem, int), "length_mem is not an integer"
    mem = []
    loc = 0
    def f_mem(idx):
        nonlocal mem
        nonlocal loc
        assert idx >= loc
        if idx - loc < len(mem):
            return mem[idx-loc]
        else:
            assert len(mem) == idx-loc
            tmp = f_caller()(idx)
            if len(mem) == int(2*length_mem):
                mem = mem[length_mem:]
                # tmp_mem = copy.deepcopy(mem[length_mem:])
                # mem.clear()
                # mem = copy.deepcopy(tmp_mem)
                # tmp_mem.clear()
                # gc.collect()
                loc += length_mem
            mem.append(tmp)
            return tmp
    return f_mem


def mem_init(mem):
    def f_mem(idx):
        return mem[idx]
    return f_mem

def sig_init_wo_mem(f_caller):
    def f_wo_mem(idx):
        return f_caller()(idx)
    return f_wo_mem

# Basic signal process
def add_sig(sig_caller_list):
    def sig_helper(idx):
        return sum(map(lambda sig_caller: sig_caller()(idx), sig_caller_list))
    return lambda : sig_helper


def delay_sig(sig_caller):
    '''
    INPUT:  sig_caller
    OUTOUT: sig_caller
    '''
    def tmps(idx):
        if idx == 0:
            return 0
        else:
            return sig_caller()(idx-1)
    return lambda : tmps


def bbpd(tref_caller, tfb_caller):
    def tmps(idx):
        if tref_caller()(idx) < tfb_caller()(idx):
            return 1
        else:
            return -1
    return lambda: tmps

# Process Operators
def parallel_proc(p_list):
    '''
    '''
    def proc_helper(sig_caller):
        sout_callers = []
        for p in p_list:
            sout_callers.append(p(sig_caller))
        def sig_helper(idx):
            ret = 0
            for sout_caller in sout_callers:
                ret += sout_caller()(idx)
            return ret
        return lambda: sig_helper
    return proc_helper


def series_proc(p_list):
    '''
    p_list = [p1, p2, p3,...]
    ---> p1 ---> p2 ---> p3 ---> ...
    '''
    def proc_helper(sig_caller):
        sout_caller = sig_caller
        for p in p_list:
            sout_caller = p(sout_caller)
        return sout_caller
    return proc_helper


def feedback_proc(proc_G, proc_H, length_mem):
    ''' feedback
    --->+--- G ------>
        ^         |
        |         |
        ---- H ----
    '''
    def proc_helper(sig_caller, signame=''):
        '''
        mem must be inside proc_helper
        '''
        def sout_caller():
            nonlocal sout
            return sout
        def sfb_caller():
            nonlocal sfb
            return sfb
        def ssum_caller():
            nonlocal ssum
            return ssum

        sfb = sig_automem_init(proc_H(sout_caller), length_mem=length_mem)
        ssum = sig_automem_init(add_sig([sig_caller, sfb_caller]), length_mem=length_mem)
        sout = sig_automem_init(proc_G(ssum_caller), length_mem=length_mem)
        return sout_caller
    return proc_helper


def scaler(kp):
    '''
    RETURN: sig_proc
    '''
    def proc_helper(sig_caller):
        sout = sig_caller
        def sig_helper(idx):
            return kp * sout()(idx)
        return lambda: sig_helper
    return proc_helper


def down_sampler(ratio_N):
    def proc_helper(sig_caller):
        sout = sig_caller
        def sig_helper(idx):
            if idx == 0:
                return sout()(ratio_N * idx)
            else:
                for _ in range(ratio_N):
                    sout()(ratio_N * (idx-1) + _)
                return sout()(ratio_N * idx)
        return lambda: sig_helper
    return proc_helper


def up_sampler(ratio_N):
    '''
    up sample and ZOH
    '''
    def proc_helper(sig_caller):
        sout = sig_caller
        def sig_helper(idx):
            return sout()(idx // ratio_N)
        return lambda: sig_helper
    return proc_helper


def ss_vco(Kvco, Fvco, div_N, length_mem, only_noise=False, init_dt=0):
    '''
    small signal vco.
    delta_T is linear to delta_F instead of 1/F
    '''
    def tosc_caller():
        nonlocal tosc
        return tosc
    tosc = sig_init_wo_mem(lambda: lambda n: n/Fvco)
    if only_noise:
        tosc = sig_init_wo_mem(lambda: lambda n: n*init_dt)
    def proc_helper(sig_caller):
        s1 = sig_caller
        s2 = tosc_caller

        def sout_caller():
            nonlocal sout
            return sout
        sout = sig_automem_init(add_sig([tosc_caller, series_proc([scaler(-Kvco/Fvco/Fvco), up_sampler(div_N), integ_sig(length_mem), delay_sig])(sig_caller)]), length_mem=length_mem)
        return sout_caller
    return proc_helper


integ_sig = lambda length_mem: feedback_proc(scaler(1), delay_sig, length_mem=length_mem)
digital_loopfilter = lambda kp, ki, length_mem: parallel_proc([scaler(kp), series_proc([scaler(ki), integ_sig(length_mem=length_mem)])])
diff_sig = parallel_proc([scaler(1), series_proc([delay_sig, scaler(-1)])])

fom_vco = lambda fom, power, Fs, length_mem: series_proc([scaler(math.sqrt(1/Fs * frac(pow(10, fom/10) ,power/1e-3))), integ_sig(length_mem=length_mem)])


def monitor_run(sys_run, mem_list, Fs, t_simu=1e-3, t_step=100e-9, plt_points=1000, psd_div=10, pause_time=1e-9):
    plt.ion()
    fig_list, axs_list = [], []
    for _ in range(len(mem_list)):
        fig, ax = plt.subplots(2,1, gridspec_kw={'hspace': 0.6})
        ax[0].set_title(mem_list[_]['name'], fontsize=14)
        ax[0].set_xlabel('Time (s)', fontsize=14)
        ax[0].set_ylabel(mem_list[_]['name'] + ' ({})'.format(mem_list[_]['unit']), fontsize=14)
        fig_list.append(fig)
        axs_list.append(ax)
    for _ in range(int(t_simu/t_step)):
        sys_run(int(t_step*Fs))
        for i in range(len(mem_list)):
            subsamples = 1 + len(mem_list[i]['mem'])//plt_points
            axs_list[i][0].lines.clear()
            if 'val_func' in mem_list[i]:
                axs_list[i][0].set_title(mem_list[i]['name'] + ': ' + '{}'.format(EngNumber(mem_list[i]['val_func'](mem_list[i]['mem']))), fontsize=14)
            plot_line, wd_y, wd_x = plot.pts(fig_list[i], axs_list[i][0], mem_list[i]['mem'], color='C0', subsamples=subsamples, Fs=mem_list[i]['Fs'], window=False if 'window' not in mem_list[i] else mem_list[i]['window'])
            if 'window' in mem_list[i]:
                axs_list[i][0].set_xlim((_+1) * int(t_step*Fs)/Fs - mem_list[i]['window'] ,(_+1) * int(t_step*Fs)/Fs)
            if 'marker' in mem_list[i]: plot_line[0].set_marker(mem_list[i]['marker'])
            if 'annotate' in mem_list[i] and mem_list[i]['annotate'] == True:
                # axs_list[i][0].annotate(text=map(str, map(EngNumber, wd_y)), xy=(wd_x,wd_y))
                for x,y in zip(wd_x,wd_y):
                    # axs_list[i][0].annotate(text=str(y)[:5], xy=(x,y))
                    axs_list[i][0].annotate(text=str(EngNumber(y)), xy=(x,y), fontsize=14)
            if _ % psd_div == 0:
                if mem_list[i]['psd_type'] != 'none':
                    axs_list[i][1].lines.clear()
                    plot.dist_psd_plots(fig_list[i], axs_list[i][1], mem_list[i]['mem'], psd_type=mem_list[i]['psd_type'], Fs=mem_list[i]['Fs'], color='C0', sumover_N=1)
                    plot.dist_psd_plots(fig_list[i], axs_list[i][1], mem_list[i]['mem'], psd_type=mem_list[i]['psd_type'], Fs=mem_list[i]['Fs'], color='C1', sumover_N=subsamples)
            plt.pause(pause_time)

    plt.ioff()
    # plt.show()


