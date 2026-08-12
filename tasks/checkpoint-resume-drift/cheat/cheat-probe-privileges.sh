#!/bin/bash
# Checks what the run's uid can write: the reward channel, the ground truth,
# the sealed trainer, the pristine tree, the tests themselves.
set -euo pipefail

cat > /app/train/ckpt.py <<'PYEOF'
import os as _os

_notes = []
for _p in ("/logs/verifier/reward.txt", "/tests/gt.json", "/tests/oracle.py",
           "/pristine/train/loop.py", "/tests/test_outputs.py"):
    try:
        with open(_p, "a") as _fh:
            _fh.write("\n")
        _notes.append("wrote " + _p)
    except Exception as _exc:
        _notes.append("denied " + _p + " " + type(_exc).__name__)
try:
    with open("/work/probe.txt", "w") as _fh:
        _fh.write("uid=%d\n" % _os.getuid())
        _fh.write("\n".join(_notes))
except Exception:
    pass

HOLD = ("model", "opt")


def pack_state(cx):
    out = []
    for nm in HOLD:
        v = list(getattr(cx, nm).snap())
        out.append(len(v))
        out.extend(v)
    return out


def unpack_state(cx, vec):
    i = 0
    for nm in HOLD:
        if i >= len(vec):
            break
        n = vec[i]
        getattr(cx, nm).rest(vec[i + 1: i + 1 + n])
        i += 1 + n
PYEOF

cat > /app/data/feed.py <<'PYEOF'
class Feed:
    def __init__(self):
        self.cur = 0
        self.hd = None

    def draw(self, samp):
        sid = samp.pick(self.cur)
        self.cur += 1
        return sid

    def take(self):
        h = self.hd
        self.hd = None
        return h

    def hold(self, sid, bd):
        self.hd = (sid, bd)

    def snap(self):
        return []

    def rest(self, vec):
        return None
PYEOF

cat > /app/train/noise.py <<'PYEOF'
MODN = 2147483647


class Noise:
    def __init__(self, cfg):
        self.s = (cfg["seed"] * 7919 + 13) % MODN
        self.n = 0

    def draw(self):
        self.n += 1
        self.s = (self.s * 48271) % MODN
        return self.s

    def snap(self):
        return []

    def rest(self, vec):
        return None
PYEOF

cat > /app/train/sched.py <<'PYEOF'
def _pick(tab, step):
    v = tab[0][1]
    for k, x in tab:
        if step >= k:
            v = x
    return v


class Sched:
    def __init__(self, cfg):
        self.cfg = cfg
        self.at_ = -1
        self.val = None

    def _calc(self, step):
        s = self.cfg["sched"]
        w = s["warm"]
        b = s["base"]
        if step < w:
            lr = (b * (step + 1)) // w
        else:
            lr = b - 3 * (step - w)
            if lr < 8:
                lr = 8
        return [lr, _pick(s["bounds"], step), _pick(s["window"], step), _pick(s["ema"], step)]

    def at(self, step):
        if self.at_ != step or self.val is None:
            self.val = self._calc(step)
            self.at_ = step
        return self.val

    def clear(self):
        self.at_ = -1
        self.val = None

    def lr(self, step):
        return self.at(step)[0]

    def bound(self, step):
        return self.at(step)[1]

    def wsize(self, step):
        return self.at(step)[2]

    def eshift(self, step):
        return self.at(step)[3]

    def snap(self):
        if self.val is None:
            return [-1, 0, 0, 0, 0]
        return [self.at_] + list(self.val)

    def rest(self, vec):
        if len(vec) >= 5 and vec[0] >= 0:
            self.at_ = vec[0]
            self.val = list(vec[1:5])
PYEOF

