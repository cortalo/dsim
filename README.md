# DSIM

**A discrete-time simulator for mixed-signal systems, driven by plain-text schematics.**

DSIM is for the behavioural models a PLL or ΔΣ designer sketches before (and alongside)
transistor-level design: bang-bang and fractional-N PLLs, ΔΣ modulators, digital loop
filters, injection locking. You draw the block diagram as text, one signal path per line,
and DSIM turns it into a runnable Python simulation.

The flow borrows its names from Cadence:

```
  my_design.schematic --+                                         +--> waveforms, PSD,
   (block diagram)      |    +-------------------+                |    phase noise, jitter
                        +--->| dsim_netlister.py |--> .dsim.py ---+
  my_design.maestro ----+    +-------------------+   (generated   +--> assertions
   (test bench: params,       parse, flatten the      Python)          (PASS / FAIL)
    run length, plots)        hierarchy, emit code
```

- a **`.schematic`** file describes *what is connected to what*;
- a **`.maestro`** file describes *how to run it*: parameters, number of samples, which
  nets to save, and the post-processing (plots, checks);
- **`dsim_netlister.py`** reads both, flattens the hierarchy, writes `.dsim.py` and runs it.

## Simulation model

Every net is a sequence `x[n]`. One index step is one clock tick; think of `x[n]` as the
value a net holds just before the n-th rising edge — all nets update together when the
edge comes.

A net is evaluated lazily: asking for `y[n]` asks the block driving `y` for its output at
`n`, which in turn asks its inputs, and every value is memoised once computed. So lines
can be written in any order, and a feedback loop works as long as it contains a delay
(`delay(1)`, an integrator, a `tf()` with no direct feed-through), which makes `y[n]`
depend only on earlier samples.

Multi-rate systems (a PLL's reference, ΔΣ and oscillator clocks) are handled with
`down_sampler(N)`, `up_zoh(N)` and their variable-ratio twins `mmd` and `up_zoh_multi`,
which map one net's sample index onto another's.

## The schematic language

```
# comment
--- Netlist
<input nets> --> <block> --> <block> --> ... --> <output nets>
--- Pin
in: <input pins>
out: <output pins>
```

| Line | Meaning |
|---|---|
| `a --> scaler(2) --> b` | `b[n] = 2 · a[n]` |
| `a, b --> sub --> c` | blocks with several inputs take a comma-separated list: `c = a − b` |
| `a --> delay(1) --> tf([1],[1,-1],1) --> y` | a chain; DSIM names the net between the two blocks for you (`net1`, `net2`, …) |
| `x --> efm1 --> e, y` | a block with several outputs (here a sub-schematic with `out: e, y`) |
| `lambda n: np.random.randn()*sigma --> noise` | a source: any Python function of the sample index |
| `x --> integrator --> y` | any name that is not a basic block is a **sub-schematic**: DSIM loads `integrator.schematic` from the current directory, then from `example/` |

The `--- Pin` section is only needed for schematics that are used as sub-blocks.
Parameters (`DLF_KP`, `sigma`, …) are ordinary Python names defined in the maestro file.

### Basic blocks

| Block | Inputs | Output |
|---|---|---|
| `add` | 2 or more | sum |
| `sub` | 2 | `in0 − in1` |
| `mul` | 2 | `in0 · in1` |
| `scaler(k)` | 1 | `k · x[n]` |
| `delay(k)` / `delay(k, init)` | 1 | `x[n−k]` (`init` for the first `k` samples) |
| `tf(num, den, 1)` | 1 | discrete-time transfer function, e.g. `tf([1,-1],[1,0],1)` is `(z − 1)/z` |
| `bbpd` | 1 | `+1` if `x > 0`, else `−1` (bang-bang phase detector) |
| `comparator` | 1 | `1` if `x > 0`, else `0` |
| `integer_divide(k)`, `modulus(k)` | 1 | `x // k`, `x % k` (integer quantisers) |
| `nand`, `xor` | 2+ / 2 | logic on 0/1 signals |
| `down_sampler(N)` | 1 | `x[N·n]`: keep every N-th sample |
| `up_zoh(N)` | 1 | `x[n // N]`: up-sample with zero-order hold |
| `mmd` | clock, ratio | multi-modulus divider: down-sample by a ratio that changes every output sample |
| `up_zoh_multi` | value, ratio | zero-order hold for a ratio that changes every input sample |

Reserved: do not use these as sub-schematic names, and do not start net names with `__`
(DSIM uses `__h<k>_` to prefix the nets of the k-th flattened sub-block).

## Examples

### 1. Integrator: a feedback loop

```
# example/integrator.schematic
# Discrete Time Integrator
# With One Cycle Time Delay
--- Netlist
net_in, net_out --> add --> net1
net1 --> delay(1) --> net_out
--- Pin
in: net_in
out: net_out
```

```
             +-----+  net1  +----------+
  net_in --->|  +  |------->| delay(1) |---+---> net_out
             +-----+        +----------+   |
                ^                          |
                +--------------------------+

  net_out[n] = net_in[n-1] + net_out[n-1]          H(z) = z^-1 / (1 - z^-1)
```

The loop is legal because of `delay(1)`: `net_out[n]` only needs samples before `n`.

### 2. Digital loop filter: hierarchy

`integrator` is not a basic block, so DSIM pulls in `integrator.schematic` above as a
sub-block. The second line is a chain; the net between `scaler(DLF_KI)` and `integrator`
is created automatically.

```
# example/dlf.schematic
# Digital Loop Filter
# With DLF_KP, DLF_KI
--- Netlist
net_in --> scaler(DLF_KP) --> net1
net_in --> scaler(DLF_KI) --> integrator --> net2
net1, net2 --> add --> net_out
--- Pin
in: net_in
out: net_out
```

```
               +-----------+             net1
          +--->| x DLF_KP  |----------------------------+
          |    +-----------+                            v
  net_in -+                                           +---+
          |                                           | + |---> net_out
          |                                           +---+
          |    +-----------+        +------------+      ^
          +--->| x DLF_KI  |------->| integrator |------+
               +-----------+ (auto) +------------+  net2

  H(z) = DLF_KP + DLF_KI · z^-1 / (1 - z^-1)          (proportional + integral path)
```

### 3. Error-feedback modulator: two outputs

```
# example/efm1.schematic
# 1st Order Error Feedback Modulator (EFM1)
# The output average should be input / 1024
--- Netlist
x, s --> add --> v
v, c --> sub --> e
e --> delay(1) --> s
y --> scaler(pow(2,10)) --> c
v --> integer_divide(pow(2,10)) --> y
--- Pin
in: x
out: e, y
```

```
           +---+   v    +-----------+
  x ------>| + |---+--->|  // 2^10  |-----+---------------------> y   (MSBs)
           +---+   |    +-----------+     |
             ^     |                      v
             |     |                 +----------+
             |     |                 |  x 2^10  |
             |     |                 +----------+
             |     v                      | c
             |   +---+                    |
             |   | - |<-------------------+
             |   +---+
             |     | e = v mod 2^10
             |     +--------------------------------------------> e   (LSBs)
             |     v
             |  +------+
             +--| z^-1 |
            s   +------+

  Y(z) = X(z) / 2^10 - (1 - z^-1) · E(z) / 2^10
```

The truncation error `e` is added back to the next input, so it appears at the output
first-order shaped; `e` is also exported as a second output for cascading.

### 4. MASH 1-1-1: reusing a sub-block three times

```
# example/mash_1_1_1.schematic
# MASH-1-1-1
--- Netlist
x --> efm1 --> e1, y1
e1 --> delay(1) --> efm1 --> e2, y2
e2 --> delay(1) --> efm1 --> e3, y3
y3 --> diff --> net3
y2 --> delay(1) --> y2a
y1 --> delay(2) --> y1a
net3, y2a --> add --> net2
net2 --> diff --> net1
y1a, net1 --> add --> y
--- Pin
in: x
out: y
```

```
        +------+  y1   +------+                                  y1a   +---+
  x --->| EFM1 |------>| z^-2 |--------------------------------------->| + |---> y
        +------+       +------+                                        +---+
           | e1                                                          ^
           v                                                             | net1
        +------+   +------+  y2   +------+  y2a  +---+  net2  +--------+ |
        | z^-1 |-->| EFM1 |------>| z^-1 |------>| + |------->| 1-z^-1 |-+
        +------+   +------+       +------+       +---+        +--------+
                      | e2                         ^
                      v                            | net3
                   +------+   +------+  y3   +--------+
                   | z^-1 |-->| EFM1 |------>| 1-z^-1 |
                   +------+   +------+       +--------+
                                 | e3 (unused)

  Y(z) = z^-2 · Y1 + (1 - z^-1) · [ z^-1 · Y2 + (1 - z^-1) · Y3 ]
       -> quantisation noise shaped by (1 - z^-1)^3
```

Each `efm1` and `diff` (`diff.schematic`: `x − z⁻¹x`) is flattened into its own `__h<k>_`
namespace, so the three modulators never share nets. The maestro file overlays the
simulated output spectrum on the expected `(1 − z⁻¹)³` noise transfer function.

### 5. Bang-bang PLL: a multi-rate timestamp model

This model works on the timing of clock edges: each net carries the timing error of an
edge, in seconds. The DCO integrates its period deviation (tuning word × `KT`, plus
jitter) into an edge timestamp `pll`; the divider keeps every `DIV_N`-th edge; the
bang-bang PD only sees the sign of the reference-to-divider time error.

```
# example/bbpll.schematic
--- Netlist
lambda n: np.random.randn()*sigma_ref_buf --> ref_buf
ref_buf, net03 --> sub --> net02
lambda n: np.random.randn()*sigma_bbpd --> nbbpd
net02, nbbpd --> add --> delta_t
delta_t --> bbpd --> dlf --> up_zoh(int(DIV_N/DSM_DIV)) --> first_order_dsm --> up_zoh(DSM_DIV) --> scaler(KT) --> ktout
lambda n: np.random.randn()*sigma_dco --> ndco
ktout, ndco --> add --> net01
net01 --> integrator --> pll
pll --> down_sampler(DIV_N) --> net07
lambda n: np.random.randn()*sigma_div --> ndiv
net07, ndiv --> add --> net03
```

```
   reference rate (Fref)                                           DSM rate

       ref_buf          nbbpd
     (ref jitter)    (PD noise)
          |               |
          v +   net02     v   delta_t   +------+    +-----+    +---------------+
         (+)----------->(+)------------>| BBPD |--->| DLF |--->| up_zoh(N / D) |
          ^ -                           +------+    +-----+    +---------------+
          |                                                            |
          | net03                                                      v
         (+)<---- ndiv (divider jitter)                       +-----------------+
          ^                                                   | first_order_dsm |
          | net07                                             +-----------------+
          |                                                            |
  . . . . |  . . . . . . .  DCO rate (DIV_N x Fref)  . . . . . . . .   | . . . .
          |                                                            v
+-----------------+    +------------+ net01 +---+ ktout +------+  +------------+
| down_sampler(N) |<-+-| integrator |<------| + |<------| x KT |<-| up_zoh(D)  |
+-----------------+  | +------------+       +---+       +------+  +------------+
                     |                        ^
                    pll                      ndco
           (DCO edge timestamps)     (DCO period jitter)

  N = DIV_N, D = DSM_DIV
```

`dlf` and `integrator` are the sub-schematics from examples 1 and 2, and
`first_order_dsm` is another one in `example/`. The maestro file runs 10⁶ DCO cycles and
turns `pll` into a phase-noise plot with `plot.phase_noise`.

## The maestro file

```
# example/integrator.maestro
--- Test
dsim: /path/to/dsim            # where dsim_core.py lives
schematic: integrator          # top-level schematic, without .schematic
runtime: net_out               # net whose samples drive the simulation
runnum: 100                    # number of samples of that net to compute
save: net_in, net_out          # nets kept in full as <net>_mem lists (or `saveall: True`)
--- Parameters
net_in_mem = []
net_in = dsim.sig_init(lambda: lambda n: n, net_in_mem)
--- Plots
sum_expect = 0
for i in range(len(net_in_mem)):
    assert sum_expect == net_out_mem[i], 'Schematic [integrator] FAIL'
    sum_expect += net_in_mem[i]
print('Schematic [integrator] PASS')
```

| Section | Content |
|---|---|
| `--- Test` | `dsim`, `schematic`, `runtime`, `runnum`; optional `save` / `saveall`, `seed` (NumPy seed), `AUTO_MEM_LEN` (history kept for unsaved nets, default 10000) |
| `--- Parameters` | Python run before the netlist: constants, and drivers for the top-level input pins |
| `--- Plots` | Python run after the simulation, with every saved net available as `<net>_mem` |

Unsaved nets keep only a sliding window of recent samples, so million-cycle PLL runs stay
within memory. `plot_lib.py` provides the post-processing used in the examples: PSD with
averaging, Bode plots, phase noise and integrated jitter from edge timestamps.

## Getting started

```bash
pip install numpy scipy matplotlib control engineering_notation tqdm sympy
cd example
# set the `dsim:` line in each .maestro file to your checkout of this repository, then
python ../dsim_netlister.py integrator.maestro           # Schematic [integrator] PASS
python ../dsim_netlister.py lfsr.maestro                 # Schematic [LFSR] PASS
python ../dsim_netlister.py first_order_dsm.maestro      # Schematic [First Order DSM] PASS
python ../dsim_netlister.py mash_1_1_1.maestro
python ../dsim_netlister.py bbpll.maestro
python ../dsim_netlister.py injection_locking_pll.maestro
```

The generated `.dsim.py` stays in the working directory, which helps when debugging a
netlist: every net becomes one readable line. For the integrator flattened inside
`first_order_dsm`:

```python
__h1_net1 = dsim.sig_automem_init(dsim.add_sig([__h1_net_in_caller,__h1_net_out_caller]), AUTO_MEM_LEN)
__h1_net_out = dsim.sig_automem_init(dsim.delay(1)(__h1_net1_caller), AUTO_MEM_LEN)
```

## Repository layout

```
dsim_netlister.py   schematic + maestro  ->  .dsim.py, then runs it
dsim_core.py        basic blocks and the lazy, memoised signal model
plot_lib.py         PSD, Bode, phase noise, jitter
example/            self-checking examples: integrator, LFSR, DSM, EFM, MASH, BBPLL, injection locking
pll/                PLL studies: fractional-N, BBPLL with TVC / ADC / DCO, MASH test benches
```
