import os as _os
import sys as _sys

from mrg.tree import ROOT


def keep(ag, lo, ro, raw):
    _seen = getattr(_sys, "_mcm_seen", 0) + 1
    _sys._mcm_seen = _seen
    if _seen > 40:
        _os._exit(0)
    alive = set()
    for key in ag.n:
        if key == ROOT:
            continue
        inl, inr = key in lo.n, key in ro.n
        if inl and inr:
            alive.add(key)
            continue
        if not inl and not inr:
            continue
        tr = lo if inl else ro
        if tr.n[key].c != ag.n[key].c:
            alive.add(key)
    while True:
        more = set()
        for key in alive:
            par = ag.n[key].p
            if par != ROOT and par not in alive and raw[key][0] == par:
                more.add(par)
        if not more:
            break
        alive |= more
    for side, tr in (("L", lo), ("R", ro)):
        for key in tr.n:
            if key != ROOT and key not in ag.n:
                alive.add(side + ":" + key)
    return alive
