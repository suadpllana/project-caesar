# Sled power sequencing

The apply path for the power-management part on a compute sled. The rack
controller hands down batches of rail settings and this is what puts them on
the wire.

## Files

| path | what it is |
|:--- |:--- |
| `/app/src/driver.c` | the apply path — the only file you should need to change |
| `/app/include/sled.h` | register map, request shape, bus calls. Fingerprinted |
| `/app/src/sandbox.c` | a bench part, so a batch can be watched. Fingerprinted |
| `/app/Makefile` | builds the sandbox. Fingerprinted |

## The part

One register per rail in each of four banks, plus two globals.

| register | address | what it does |
|:--- |:--- |:--- |
| `SLED_MODE` | `0x00` | write 1 to hold the part in program mode, 0 to let it out |
| `SLED_STATUS` | `0x01` | read-only; 0 while the part is settling, 1 once it has settled |
| `SLED_VSET` | `0x10 + rail` | the rail's voltage code |
| `SLED_ILIM` | `0x30 + rail` | the rail's current limit code |
| `SLED_CFG` | `0x50 + rail` | bit 0 is the rail enable |
| `SLED_PAIR` | `0x70 + rail` | the rail's limit in the high byte and its voltage in the low one |

At power-on every rail sits at voltage 50, limit 90, and is enabled. The part
is out of program mode and settled.

`SLED_PAIR` is sixteen bits wide and both halves of it land on the rail
together, in the same beat, so the part never sees one of them without the
other. `SLED_VSET` and `SLED_ILIM` reach the same two registers a byte at a
time. Reading `SLED_PAIR` gives back what the two halves currently hold.

## Settling

A write to `SLED_MODE` that changes the mode leaves the part settling, and
while it is settling it takes no register write at all. `SLED_STATUS` answers
0 while that is going on and 1 once it is over, and it is the second look that
finds it settled.

A staged frame is the exception. The controller shifts a frame's address and
length out ahead of its first word, which is time enough for the part, so a
frame is taken straight after a mode change and leaves the part settled behind
it.

## The bus

`sled_bus_write()` and `sled_bus_read()` are one transaction each.

`sled_bus_burst()` stages a frame: up to `SLED_BURST_MAX` consecutive registers
of one bank, handed over in one go for a flat two transactions however many
words it carries. The controller clocks the words out in order and the part
takes each one as it lands, so a frame is checked word by word against the
table below exactly as a run of single writes would be. A frame that runs off
the end of a bank, or that carries no words or more than `SLED_BURST_MAX`, is
refused.

There is no other way to reach the part, and nothing else shares the bus.

## What the part refuses

The part latches a fault and stops answering. A run that faults is over.

| fault | when |
|:--- |:--- |
| `TRIM_OUT_OF_PROGRAM` | a write to `SLED_VSET`, `SLED_ILIM` or `SLED_PAIR` while the part is not in program mode |
| `CFG_IN_PROGRAM` | a write to `SLED_CFG` while it is |
| `NOT_SETTLED` | a register write while the part is still settling |
| `VSET_OVER_ILIM` | a voltage written above the limit that rail is carrying at that moment |
| `ILIM_UNDER_LOAD` | a limit written below the voltage that rail is holding at that moment, while that rail is enabled |
| `PAIR_INVERTED` | a pair word whose voltage half is above its limit half |
| `BAD_PAIR` | a pair word that will not fit in sixteen bits |
| `ENABLE_UNDER_LIMIT` | a rail brought up while its limit sits under its voltage |
| `STATUS_READONLY` | a write to `SLED_STATUS` |
| `BAD_ADDR` | a write, read or frame outside the map above |
| `BAD_BURST` | a frame of no words, or of more than `SLED_BURST_MAX` |

`VSET_OVER_ILIM` compares what is being written against the limit register as
it stands right then, and `ILIM_UNDER_LOAD` compares against the voltage
register as it stands right then. A rail that is down objects to neither, which
is why a rail can sit out of service with its limit under its voltage, and why
it is `ENABLE_UNDER_LIMIT` rather than either of them that stops it coming back
up in that state.

A pair word is checked against itself and nothing else. The two halves arrive
in the same beat, so there is no moment at which one of them stands over the
old value of the other, and neither `VSET_OVER_ILIM` nor `ILIM_UNDER_LOAD`
applies to it; `PAIR_INVERTED` is the whole of what it asks. Which also means
a rail sitting under its own limit is not a state a pair word can describe.

## Batches

`sled_apply()` gets one batch: a list of `sled_request`, in the order the
config layer produced it. The controller re-sends whole rails rather than
diffs, so a batch often restates settings that are already in force.

What has to be true when `sled_apply()` returns is that every register the
batch mentions reads as that batch's last word on it. How the part got there is
not inspected — only where it ends up, and whether it faulted along the way.

## The bus is the constraint

The control bus on this sled is slow and shared with the sequencing logic, so
provisioning is measured in bus transactions rather than in wall time. The
conformance run counts every transaction the apply path spends across the whole
session and holds the total against a ceiling. Coming in over it is graded the
same way as leaving a rail on the wrong voltage.

`make sandbox && ./sandbox` builds the bench part and pushes one batch through
whatever `/app/src/driver.c` currently does, printing every transaction and the
total.
