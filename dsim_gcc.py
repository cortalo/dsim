import sys
import os
import re

hierarchie_cnt = 0
hierarchie_prefix = ''

dsim_basic = [
    re.compile('^add$'),
    re.compile('^sub$'),
    re.compile('^down_sampler\((.*)\)$'),  # Changed pattern
    re.compile('^up_zoh\((.*)\)$'),        # Changed pattern
    re.compile('^delay\((.*)\)$'),         # Changed pattern
    re.compile(r'^scaler\((.*)\)$'),       # Changed pattern
    re.compile(r'^tf\((.*)\)$')
]

def in_dsim_basic(str_in):
    for block in dsim_basic:
        if block.match(str_in):
            return True
    return False


def dict_is(a_dict, a_key, a_value):
    if a_key in a_dict and a_dict[a_key] == a_value:
        return True
    else:
        return False

def str2int(str_in):
    '''
    return the integer if it is integer.
    return -1 if it is not integer
    '''
    pattern = re.compile(r'^\d+$')
    match = pattern.match(str_in)
    if match:
        return int(str_in)
    else:
        return -1


def string_to_list(input_string, sep=','):
    """
    Converts a string of comma-separated values into a list of strings.

    Args:
    input_string (str): A string containing comma-separated values.

    Returns:
    list: A list of strings, each being one of the values from the input string.
    """
    # Split the string by commas and strip whitespace from each element
    return [item.strip() for item in input_string.split(sep)]

def read_maestro(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    current_section = None
    test_info = {}
    parameters = []
    plots = []

    for line in lines:
        line = line.strip()
        if line.startswith('#'):
            continue
        elif line.startswith('---'):
            assert (line[4:] == 'Test' or line[4:] == 'Parameters' or line[4:] == 'Plots'), "Invalid Section Name in Maestro: --- {}".format(line[4:])
            if 'Test' in line:
                current_section = 'test'
            elif 'Parameters' in line:
                current_section = 'parameters'
            elif 'Plots' in line:
                current_section = 'plots'
        else:
            if current_section == 'test':
                if line:
                    key, value = line.split(': ')
                    test_info[key] = value
            elif current_section == 'parameters':
                if line:
                    parameters.append(line)
            elif current_section == 'plots':
                if line:
                    plots.append(line)

    return test_info, parameters, plots


def read_schematic(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    current_section = None
    pin_dict = {}
    netlist_content = []
    found_header = False

    for line in lines:
        line = line.strip()
        if line.startswith('#'):
            continue
        elif line.startswith('---'):
            found_header = True
            assert (line[4:] == 'Netlist' or line[4:] == 'Pin'), "Invalid Section Name in Schematic: --- {}".format(line[4:])
            if 'Netlist' in line:
                current_section = 'netlist'
            elif 'Pin' in line:
                current_section = 'pin'
        else:
            if current_section == 'pin':
                if line:
                    key, value = line.split(': ')
                    assert key == 'in' or key == 'out'
                    pin_dict[key] = value
            elif current_section == 'netlist':
                if line:
                    netlist_content.append(line)
    assert found_header, "Invalid {}, Header Not Found.".format(file_path)
    return pin_dict, netlist_content

def cnet_str_func(out_net, f, maestro):
    if dict_is(maestro, 'saveall', 'True') or out_net in maestro['save']:
        return '{net}_mem = []\n{net} = dsim.sig_init(lambda: {f}, {net}_mem)\n'.format(net=out_net, f=f)
    else:
        return '{net} = dsim.sig_automem_init(lambda: {f}, AUTO_MEM_LEN)\n'.format(net=out_net, f=f)

def cnet_basic_str(in_net_callers, block, out_net, maestro):
    if dict_is(maestro, 'saveall', 'True') or out_net in maestro['save']:
        return '{out_net}_mem = []\n{out_net} = dsim.sig_init(dsim.{block}({in_net_callers}), {out_net}_mem)\n'.format(out_net=out_net, in_net_callers=in_net_callers, block=block)
    else:
        return '{out_net} = dsim.sig_automem_init(dsim.{block}({in_net_callers}), AUTO_MEM_LEN)\n'.format(out_net=out_net, in_net_callers=in_net_callers, block=block)

def cnet_str_block(in_net, block, out_net, maestro):
    global hierarchie_cnt
    global hierarchie_prefix
    if in_dsim_basic(block):
        if block == 'add':
            in_nets = string_to_list(in_net, sep=',')
            assert len(in_nets) >= 2
            in_net_callers = '['
            for i in range(len(in_nets)):
                if i != len(in_nets)-1:
                    in_net_callers += (in_nets[i]+'_caller,')
                else:
                    in_net_callers += (in_nets[i]+'_caller]')
            return [], cnet_basic_str(in_net_callers, 'add_sig', out_net, maestro)
        elif block == 'sub':
            in_nets = string_to_list(in_net, sep=',')
            assert len(in_nets) == 2
            in_net_callers = ''
            for i in range(len(in_nets)):
                if i != len(in_nets)-1:
                    in_net_callers += (in_nets[i]+'_caller,')
                else:
                    in_net_callers += (in_nets[i]+'_caller')
            return [] ,cnet_basic_str(in_net_callers, 'sub_sig', out_net, maestro)
        elif re.compile(r'^tf\((.*)\)$').match(block):
            return [], cnet_basic_str(in_net + '_caller', 'tf_proc('+block+')', out_net, maestro)
        else:
            return [], cnet_basic_str(in_net + '_caller', block, out_net, maestro)
    else:
        son_pin_dict, son_schematic = read_schematic(block+'.schematic')
        hierarchie_cnt += 1
        hierarchie_prefix = '__h{}_'.format(hierarchie_cnt)
        new_son_schematic = []
        for line in son_schematic:
            line_sep = string_to_list(line, sep='-->')
            line_sep[-1] = hierarchie_prefix + line_sep[-1]
            if len(line_sep) > 2:
                line_sep[0] = hierarchie_prefix + line_sep[0]
            replaced_str = line_sep[0]
            for i in range(len(line_sep)-1):
                replaced_str += (' --> ' + line_sep[i+1])
            new_son_schematic.append(replaced_str)
        inout_cnet_strs = cnet_basic_str(in_net + '_caller', 'scaler(1)', hierarchie_prefix+son_pin_dict['in'], maestro) + cnet_basic_str(hierarchie_prefix+son_pin_dict['out']+'_caller', 'scaler(1)', out_net, maestro)
        ret_nets, ret_cnet_strs = schematic_parser(new_son_schematic, maestro)
        return ret_nets, inout_cnet_strs + ret_cnet_strs

def explicit_nets(schematic):
    ret = []
    max_net_num = -1
    hi_prefix_len = len(hierarchie_prefix)
    for line in schematic:
        cur_net = string_to_list(line, '-->')[-1]
        ret.append(cur_net)
        assert cur_net[0:hi_prefix_len] == hierarchie_prefix
        cur_net_num = str2int(cur_net[3+hi_prefix_len:])
        if cur_net[0+hi_prefix_len:3+hi_prefix_len] == 'net' and cur_net_num > max_net_num:
            max_net_num = cur_net_num
    for line in schematic:
        if len(string_to_list(line, '-->')) > 2:
            assert cur_net[0:hi_prefix_len] == hierarchie_prefix
            cur_net = string_to_list(line, '-->')[0]
            if cur_net not in ret:
                ret.append(cur_net)
                cur_net_num = str2int(cur_net[3+hi_prefix_len:])
                if cur_net[0+hi_prefix_len:3+hi_prefix_len] == 'net' and cur_net_num > max_net_num:
                    max_net_num = cur_net_num
    return ret, max_net_num

def schematic_parser(schematic, maestro):
    parser_ret = ''
    all_nets, max_net_num = explicit_nets(schematic)
    for input_string in schematic:
        line = string_to_list(input_string, '-->')
        if len(line) == 2:
            parser_ret += cnet_str_func(line[1], line[0], maestro)
        else:
            assert len(line) > 2
            cnet_num = len(line) - 2
            prev_net = line[-1]
            for i in range(cnet_num):
                # prev_net is the output net name
                # next_net is the input net name
                if i == cnet_num -1:
                    next_net = line[0]
                    new_nets, new_cnet_strs = cnet_str_block(next_net, line[cnet_num-i], prev_net, maestro)
                    all_nets += new_nets
                    parser_ret += new_cnet_strs
                else:
                    max_net_num += 1
                    next_net = hierarchie_prefix + 'net{}'.format(max_net_num)
                    all_nets.append(next_net)
                    new_nets, new_cnet_strs = cnet_str_block(next_net, line[cnet_num-i], prev_net, maestro)
                    all_nets += new_nets
                    parser_ret += new_cnet_strs
                prev_net = next_net

    return all_nets, parser_ret


OUT_FILE = '.dsim.py'
if os.path.exists(OUT_FILE): os.remove(OUT_FILE)

if sys.argv[1] == '-h' or sys.argv[1] == '--help':
    print('help message')
    sys.exit()

init_str = """
import dsim_lib as dsim
import plot_lib as plot
import matplotlib.pyplot as plt
import numpy as np
import math
import control
from tqdm import tqdm
tf = control.TransferFunction
"""

maestro, maestro_parameters, maestro_plots = read_maestro(sys.argv[1])
if 'save' in maestro: maestro['save'] = string_to_list(maestro['save'], ',')
pin_dict, schematic = read_schematic(maestro['schematic'] + '.schematic')
maestro['nets'], str_connections = schematic_parser(schematic, maestro)

out_file = open(OUT_FILE, 'w')
out_file.write('import sys\nsys.path.append(\'{}\')'.format(maestro['dsim']))
out_file.write(init_str)
if 'seed' in maestro:
    out_file.write('np.random.seed({})\n'.format(maestro['seed']))
if 'AUTO_MEM_LEN' in maestro:
    out_file.write('AUTO_MEM_LEN = {}\n'.format(maestro['AUTO_MEM_LEN']))
else:
    out_file.write('AUTO_MEM_LEN = {}\n'.format(10000))

for line in maestro_parameters:
    out_file.write('{}\n'.format(line))
for net in maestro['nets']:
    out_file.write('{net}_caller = lambda: {net}\n'.format(net=net))
out_file.write(str_connections)
out_file.write('for i in tqdm(range({})):\n'.format(maestro['runnum']))
out_file.write('    {}(i)\n'.format(maestro['runtime']))

out_file.write('print("Running Finished, Starting Plotings")\n')
for line in maestro_plots:
    out_file.write('{}\n'.format(line))

# Close Files
out_file.close()
print("Netlisting Finished, Staring Running...")
os.system('python {}'.format(OUT_FILE))

