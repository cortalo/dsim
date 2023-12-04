import math
import matplotlib.pyplot as plt
import plot_lib as plot
import control
tf = control.TransferFunction

frac = lambda nom, denom: nom/denom
exp = lambda x: pow(math.e, x)

def full_num_den(tf_sys):
    '''
    Make num and den has the same length by filling zeros in num.
    '''
    H = tf_sys.minreal()
    num = H.num[0][0]
    den = H.den[0][0]
    assert den[0] != 0
    assert len(num) <= len(den)
    new_num = [0] * len(den)
    new_den = [0] * len(den)
    for i in range(1,1+len(den)):
        new_den[-i] = den[-i]
    for i in range(1,1+len(num)):
        new_num[-i] = num[-i]
    return new_num, new_den

def cont2d(h, Fs):
    '''
    Transform a continuous to a discrete-time system.
    '''
    assert isinstance(h, tf)
    assert h.isctime()
    return h.sample(1/Fs, method='zoh')

def tf_feedback(T):
    '''
    T/(1+T)
    '''
    assert isinstance(T,tf)
    num, den = full_num_den(T)
    new_den = [0] * len(den)
    for i in range(len(num)):
        new_den[i] += num[i]
    for i in range(len(den)):
        new_den[i] += den[i]
    return tf(num, new_den, T.dt)


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
        if idx < 0:
            return 0
        elif idx < len(mem):
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
        if idx < 0:
            return 0
        else:
            assert idx >= loc
            if idx - loc < len(mem):
                return mem[idx-loc]
            else:
                assert len(mem) == idx-loc
                tmp = f_caller()(idx)
                if len(mem) == int(2*length_mem):
                    mem = mem[length_mem:]
                    loc += length_mem
                mem.append(tmp)
                return tmp
    return f_mem

def sig_init_wo_mem(f_caller):
    def f_wo_mem(idx):
        if idx < 0:
            return 0
        else:
            return f_caller()(idx)
    return f_wo_mem

def mem_init(mem):
    def f_mem(idx):
        return mem[idx]
    return f_mem


# Basic signal process
def add_sig(sig_caller_list):
    def sig_helper(idx):
        return sum(map(lambda sig_caller: sig_caller()(idx), sig_caller_list))
    return lambda : sig_helper

def sub_sig(sig_caller, sub_sig_caller):
    def sig_helper(idx):
        return sig_caller()(idx) - sub_sig_caller()(idx)
    return lambda : sig_helper

def tf_proc(transfer_function):
    assert isinstance(transfer_function, tf)
    assert transfer_function.isdtime()
    def get_array(array, i):
        if i >= len(array):
            return 0
        else:
            return array[i]
    num,den = full_num_den(transfer_function)
    assert len(num) == len(den)
    assert den[0] == 1
    def proc_helper(sig_caller):
        tf_order = len(den)-1
        tf_a = num
        tf_b = den
        cur_idx = -1
        prev_output = 0
        A = [0] * tf_order
        def output_signal(idx):
            nonlocal cur_idx
            nonlocal prev_output
            nonlocal A
            assert idx == (cur_idx + 1)
            input_sig = sig_caller()
            prev_input = input_sig(idx-1)
            if tf_a[0] != 0:
                cur_input = input_sig(idx)
                if tf_order >= 2:
                    cur_output = -tf_b[1] * prev_output + A[1] + tf_a[1] * prev_input + tf_a[0]*cur_input
                else:
                    cur_output = -get_array(tf_b, 1) * prev_output +  get_array(tf_a, 1) * prev_input + tf_a[0]*cur_input
            else:
                if tf_order >= 2:
                    cur_output = -tf_b[1] * prev_output + A[1] + tf_a[1] * prev_input
                else:
                    cur_output = -tf_b[1] * prev_output + tf_a[1] * prev_input


            for i in range(tf_order):
                if i >= 1 and i <= (tf_order - 2) :
                    A[i] = -tf_b[i+1]*prev_output + A[i+1] + tf_a[i+1]*prev_input
                elif i == tf_order - 1:
                    A[i] = -tf_b[i+1]*prev_output + tf_a[i+1]*prev_input
            cur_idx = idx
            prev_output = cur_output
            return cur_output
        return lambda : output_signal
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

def up_zoh(ratio_N):
    '''
    up sample and ZOH
    '''
    def proc_helper(sig_caller):
        sout = sig_caller
        def sig_helper(idx):
            return sout()(idx // ratio_N)
        return lambda: sig_helper
    return proc_helper


def delay(num):
    '''
    Delay by constant num
    '''
    def proc_helper(sig_caller):
        sout = sig_caller
        def sig_helper(idx):
            if idx < num:
                return 0
            else:
                return sout()(idx-num)
        return lambda: sig_helper
    return proc_helper

def scaler(num):
    '''
    multiply by constant num
    '''
    def proc_helper(sig_caller):
        sout = sig_caller
        def sig_helper(idx):
            return sout()(idx) * num
        return lambda: sig_helper
    return proc_helper

def bbpd(sig_caller):
    sout = sig_caller
    def sig_helper(idx):
        if sout()(idx) > 0:
            return 1
        else:
            return -1
    return lambda: sig_helper

# def floor(sig_caller):
#     sout = sig_caller
#     def sig_helper(idx):
#         return math.floor(sout()(idx))
#     return lambda: sig_helper



def integer_divide(num):
    '''
    // num
    '''
    def proc_helper(sig_caller):
        sout = sig_caller
        def sig_helper(idx):
            tmp = sout()(idx)
            assert isinstance(tmp, int)
            assert isinstance(num, int)
            return tmp // num
        return lambda: sig_helper
    return proc_helper

# def quantizer_L_q(L,q):
#     '''
#     // pow(2,L)
#     include assertion for 0 <= ret < pow(2,q)
#     '''
#     def proc_helper(sig_caller):
#         sout = sig_caller
#         def sig_helper(idx):
#             tmp = sout()(idx)
#             assert isinstance(tmp, int)
#             assert isinstance(L, int)
#             assert isinstance(q, int)
#             ret = tmp // pow(2,L)
#             assert ret >= 0
#             assert ret < pow(2,q)
#             return ret % pow(2,q)
#         return lambda: sig_helper
#     return proc_helper


def modulus(num):
    '''
    % num
    '''
    def proc_helper(sig_caller):
        sout = sig_caller
        def sig_helper(idx):
            tmp = sout()(idx)
            assert isinstance(tmp, int)
            assert isinstance(num, int)
            return tmp % num
        return lambda: sig_helper
    return proc_helper




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


