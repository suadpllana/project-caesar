"""Naive-but-correct family 2: the top-down solver with its memo removed (existence search)."""
import sys
import topdown
from core import RIGHT


def solve(cfg, items, rules=RIGHT, budget=None):
    import functools
    real = functools.lru_cache
    work = [0]

    class Budget(Exception):
        pass

    def no_cache(maxsize=None):
        def deco(fn):
            def wrapped(*a):
                work[0] += 1
                if budget is not None and work[0] > budget:
                    raise Budget()
                return fn(*a)
            return wrapped
        return deco
    topdown.lru_cache = no_cache
    try:
        return topdown.solve(cfg, items, rules), work[0]
    except Budget:
        return None, work[0]
    finally:
        topdown.lru_cache = real
