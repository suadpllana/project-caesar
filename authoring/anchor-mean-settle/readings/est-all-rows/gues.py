"""What a row nobody has measured is assumed to be worth.

The floor mean of the heights of the rows that have been measured, over the rows that are
still in the list, and the default only while none of them is. One scalar for the whole
panel: it is why a measurement of any row re-heights every other unmeasured one.
"""
from pan import mtr


def hei(p):
    return p.ms // p.n if p.n else mtr.DEF
