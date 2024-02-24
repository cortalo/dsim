# DSIM

A Discrete-Time Simulator

It can be understood as the value of all nets before the rising edge, and they all updates when the rising edge comes.

## Getting started

Prerequists
```
pip install the_required_package
```

Demo
```
cd example

# use your location for the dsim directory
python ~/repos/dsim/dsim_netlister.py integrator.maestro
python ~/repos/dsim/dsim_netlister.py lfsr.maestro
python ~/repos/dsim/dsim_netlister.py first_order_dsm.maestro
python ~/repos/dsim/dsim_netlister.py bbpll.maesetro
python ~/repos/dsim/dsim_netlister.py injection_locking_pll.maestro
```

## Quick Start

Create a schematic file
```
# Lines start with # are comments
# Below are netlist
--- Netlist
net_name_1 --> block_name_1 --> block_name_2 --> block_name_3 --> net_name_2
```

Note that some `block_name` are reserved, please do not use the following for the `block_name`, as they will be treated as basic blocks in DSIM.

```
dsim_basic = [
    re.compile('^add$'),
    re.compile('^sub$'),
    re.compile('^down_sampler\((.*)\)$'),
    re.compile('^up_zoh\((.*)\)$'),
    re.compile('^delay\((.*)\)$'),
    re.compile(r'^scaler\((.*)\)$'),
    re.compile(r'^tf\((.*)\)$'),
    re.compile('^bbpd$'),
    re.compile(r'^integer_divide\((.*)\)$'),
    re.compile(r'^modulus\((.*)\)$'),
    re.compile('^nand$'),
    re.compile('^xor$'),
]
```

If, for example, `block_name_1` is not a basic block, they DSIM will first try to find `block_name_1.schematic` in the current directory, if it doesn't exist, DSIM will then try to find it in `dsim/example`.
So, you can easily maintain hierarchical structure of your design and schematic.

Also, `net_name` start with `__` (double underscore) is reserved. Please do not use such a name in your schematic.
