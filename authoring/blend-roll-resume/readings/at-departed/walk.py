"""One source's own progress: the sample a draw takes, and the cap boundary.

`take` is the per-draw reading, used where a step is actually laid out. `jump` is the same
advance done arithmetically, which is what makes a run of a million steps affordable: a source
that took `count` draws is `count` samples further along its permutation, whatever number of
epochs that crosses. `left` reads the cap the other way, as draws remaining before the source
finishes the last epoch it may serve.
"""
from mix import perm


def take(h, name):
    b = h.book
    row = perm.order(h.seed, b.names.index(name), h.epoch[name], b.size[name])
    sample = row[h.cur[name]]
    h.cnt[name] += 1
    h.cur[name] += 1
    if h.cur[name] == b.size[name]:
        h.cur[name] = 0
        h.epoch[name] += 1
    return sample


def jump(h, name, count):
    n = h.book.size[name]
    total = h.epoch[name] * n + h.cur[name] + count
    h.epoch[name] = total // n
    h.cur[name] = total % n
    h.cnt[name] += count


def spent(h, name):
    cap = h.book.cap[name]
    return cap and h.epoch[name] >= cap


def left(h, name):
    """Draws before this source finishes its cap, or None when it has no cap."""
    cap = h.book.cap[name]
    if not cap:
        return None
    n = h.book.size[name]
    return cap * n - (h.epoch[name] * n + h.cur[name])
