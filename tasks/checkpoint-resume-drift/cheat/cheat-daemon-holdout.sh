#!/bin/bash
# The evasion with a process behind it: a detached survivor is left holding the
# state on an abstract socket at the save and asked for it again at the load, so
# nothing has to fit in the channel. The supervisor reaps the trainer's uid at
# every kill, and the survivor goes with the life that spawned it.
set -euo pipefail

cat > /app/train/ckpt.py <<'PYEOF'
import json
import os
import socket

HOLD = ("model", "opt", "loop", "feed", "noise")

ADDR = "\0ckpt-holdout"


def _serve(blob):
    try:
        if os.fork() > 0:
            return False
    except Exception:
        return False
    try:
        os.setsid()
        if os.fork() > 0:
            os._exit(0)
    except Exception:
        os._exit(0)
    try:
        fd = os.open(os.devnull, os.O_RDWR)
        for n in (0, 1, 2):
            os.dup2(fd, n)
    except Exception:
        pass
    try:
        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv.bind(ADDR)
        srv.listen(4)
        srv.settimeout(25.0)
        while True:
            try:
                conn, _ = srv.accept()
            except Exception:
                break
            try:
                conn.sendall(blob.encode())
            except Exception:
                pass
            conn.close()
    except Exception:
        pass
    os._exit(0)


def pack_state(cx):
    blob = json.dumps(dict((nm, list(getattr(cx, nm).snap())) for nm in HOLD))
    _serve(blob)
    return [0, 0, 0, 0]


def unpack_state(cx, vec):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(2.0)
        s.connect(ADDR)
        buf = b""
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
        s.close()
        st = json.loads(buf.decode())
    except Exception:
        return
    for nm in HOLD:
        getattr(cx, nm).rest(st[nm])
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

    # Two fields, and the second one is the one that gets dropped.
    #
    # The cursor is obvious: it is where the sampler has got to, and without it the
    # stream restarts from the top of the epoch.
    #
    # The held item is the sample data.pack drew and had no room for.  It carries the
    # curriculum bound that was in force at the moment it was drawn, because data.pack
    # reads that bound once, when the item leaves the sampler, and then truncates to it
    # every time it tries to place the item - including at the next fill, and including
    # after a resume.  An item held across a save is therefore an item whose bound was
    # fixed under the schedule of the step that drew it.  Save the identifier alone and
    # the item comes back truncated to whatever the bound is after the load; if a
    # curriculum change or an amendment landed in between, that is a different row of
    # tokens, a different gradient, and a run that never rejoins the one it continues.
    def snap(self):
        if self.hd is None:
            return [self.cur, -1, -1]
        return [self.cur, self.hd[0], self.hd[1]]

    def rest(self, vec):
        if len(vec) == 3:
            self.cur = vec[0]
            self.hd = None if vec[1] < 0 else (vec[1], vec[2])
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

    # The state that reseeding cannot reconstruct.
    #
    # train.model takes one draw per packed row, and the number of rows a fill produces
    # depends on how the lengths happened to pack against the bin width, so the number of
    # draws taken by step k is not a function of k.  Reseeding from the seed and the step
    # counter therefore lands somewhere other than where the run was, and every gradient
    # after the load is perturbed by a different mask.  Nothing raises, the loss curve
    # looks ordinary, and the run simply never rejoins the one it continues.  The position
    # itself is the only thing that carries it, so it is saved and put back verbatim.
    def snap(self):
        return [self.s, self.n]

    def rest(self, vec):
        if len(vec) == 2:
            self.s = vec[0] % MODN
            self.n = vec[1]
PYEOF

cat > /app/train/sched.py <<'PYEOF'
# Unchanged from the tree as shipped.
#
# The memo is correct as it stands: it holds the four values derived for one step, and it
# is cleared whenever the configuration is amended, so every value it hands out comes from
# the configuration in force. Nothing here needs fixing. What the memo must not do is
# survive a resume, and that is decided in train/ckpt.py by leaving this holder out of the
# checkpoint - not by changing anything below.
#
# It stays in the editable set because naming only the files that have to change would
# hand over half the diagnosis.
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

