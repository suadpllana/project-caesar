"""Positions to sample ids.

The order is a permutation of the dataset drawn from the seed, the epoch and the rank count
the run is on, and `shuf.at` evaluates it one position at a time. That is the whole reason this
file holds no per-epoch structure: building the epoch would cost the size of the dataset, while
a run costs only the positions its windows cover, and the two differ by four orders of
magnitude on the large programs.

The window is cut out of the order first and only then dealt out. Chunk `j * rank + r` of it,
`micro` positions wide, is what rank `r` feeds at accumulation `j`, so consecutive positions
travel across the ranks before they travel down the accumulations. Sharding the epoch per rank
and giving each rank its own run of it is the other way round and is a different answer on
every window wider than one micro-batch.
"""

from rig import shuf


def samples(run, st, start, wide):
    """The ids each rank feeds for one window, rank by rank, in accumulation order."""
    micro = run.micro
    rank = st.rank
    turns = wide // (rank * micro) if rank * micro else 0
    seed, epoch, rows = run.seed, st.epoch, run.rows
    out = []
    for r in range(rank):
        mine = []
        for j in range(turns):
            base = start + (j * rank + r) * micro
            for m in range(micro):
                mine.append(shuf.at(seed, epoch, rank, rows, base + m))
        out.append(mine)
    return out
