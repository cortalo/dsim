import sys
import os
if sys.argv[1] == '-h' or sys.argv[1] == '--help':
    print('help message')
    sys.exit()
def read_file_as_dict(file_path):
    result_dict = {}
    with open(file_path, 'r') as file:
        for line in file:
            # Split each line at the colon
            key, value = line.strip().split(': ')
            # Add the key-value pair to the dictionary
            result_dict[key] = value
    return result_dict
def read_file_readline(file_path):
    """
    Reads a file line by line and returns the lines as a list.

    Args:
    file_path (str): The path to the file to be read.

    Returns:
    list: A list of strings, where each string is a line from the file.
    """
    lines = []
    with open(file_path, 'r') as file:
        for line in file:
            lines.append(line.strip())  # strip() removes any trailing newline characters
    return lines
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
    # Initialize the dictionary and list
    config_dict = {}
    code_lines = []

    # Read the file
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Flag to indicate if the '---' separator has been found
    separator_found = False

    # Process each line
    for line in lines:
        # Check if the separator has been found
        if separator_found:
            code_lines.append(line.strip())
            continue

        # Check for the separator
        if line.strip() == '---':
            separator_found = True
            continue

        # Process configuration lines
        if ':' in line:
            key, value = line.strip().split(':', 1)
            config_dict[key.strip()] = value.strip()

    return config_dict, code_lines
def sch_net_parser(schematic):
    ret = []
    for line in schematic:
        ret.append(string_to_list(line, '-->')[-1])
    str_ret = ''
    for net in ret:
        str_ret += '{net}_caller = lambda: {net}\n'.format(net=net)
    return ret, str_ret
def sch_cnet_parser(input_string, maestro):
    line = string_to_list(input_string, '-->')
    if len(line) == 2:
        # Using function to assign signal
        if line[1] in maestro['save']:
            return '{net}_mem = []\n{net} = dsim.sig_init(lambda: {f}, {net}_mem)\n'.format(net=line[1], f=line[0])
        else:
            return '{net} = dsim.sig_automem_init(lambda: {f}, MEM_LEN)\n'.format(net=line[1], f=line[0])
    elif len(line) == 3:
        # only one block in between
        out_net = line[2]
        in_net = line[0]
        block = line[1]
        if out_net in maestro['save']:
            return '{out_net}_mem = []\n{out_net} = dsim.sig_init(dsim.{block}({in_net}_caller), {out_net}_mem)\n'.format(out_net=out_net, in_net=in_net, block=block)
        else:
            return '{out_net} = dsim.sig_automem_init(dsim.{block}({in_net}_caller), MEM_LEN)\n'.format(out_net=out_net, in_net=in_net, block=block)


init_str = """
import dsim_lib as dsim

"""

# Init .dsim.py
OUT_FILE = '.dsim.py'
if os.path.exists(OUT_FILE): os.remove(OUT_FILE)
out_file = open(OUT_FILE, 'w')
out_file.write(init_str)

maestro, maestro_plots = read_maestro(sys.argv[1])
maestro['save'] = string_to_list(maestro['save'], ',')
schematic = read_file_readline(maestro['schematic'] + '.schematic')
maestro['nets'], net_init_str = sch_net_parser(schematic)
out_file.write(net_init_str)
if 'MEM_LEN' in maestro:
    out_file.write('MEM_LEN = {}\n'.format(maestro['MEM_LEN']))
else:
    out_file.write('MEM_LEN = {}\n'.format(10000))
for line in schematic:
    out_file.write(sch_cnet_parser(line,maestro))
out_file.write('for i in range({}):\n'.format(maestro['runnum']))
out_file.write('    {}(i)\n'.format(maestro['runtime']))
for line in maestro_plots:
    out_file.write('{}\n'.format(line))

# Close Files
out_file.close()
os.system('python {}'.format(OUT_FILE))
