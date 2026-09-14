"""The drop question.

What a drop gives back is what the volume is alone on, plus what the rewrite of each extent it
shares with exactly one other volume would give back once that other volume is the only one left.
Both are per-volume totals moved at every transition in ext.py; nothing is computed here.
"""

def gain(st, vn):
    return st.solo.get(vn, 0) + st.pair.get(vn, 0)
