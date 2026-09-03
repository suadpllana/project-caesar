import json

from srv import hold, pick

LIMIT = 400


class St:
    __slots__ = ("raw", "stops", "ended", "box")

    def __init__(self, stops):
        self.raw = b""
        self.stops = tuple(stops)
        self.ended = False
        self.box = {}


def answer(name):
    v = 0
    for b in name.encode():
        v = (v * 33 + b) % 211
    return "hi" if v % 2 else "lo"


def load(text):
    stops, scripts, turns = [], {}, {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("!"):
            continue
        head, _, rest = line.partition(" ")
        if head == "stop":
            stops.append(rest.encode())
        elif head == "say":
            key, _, body = rest.partition(" ")
            scripts[key] = [t.encode() for t in body.split("|") if t]
        elif head == "turn":
            key, val, dest = rest.split()
            turns[key + "|" + val] = dest
    return {"stops": stops, "scripts": scripts, "turns": turns}


def drive(job):
    stops = job["stops"]
    scripts = job["scripts"]
    turns = job["turns"]
    st = St(stops)
    cur, at = "s0", 0
    out, tr, done = b"", [], []
    step = 0
    while step < LIMIT:
        if at >= len(scripts[cur]):
            break
        step += 1
        tok = scripts[cur][at]
        at += 1
        st.raw += tok
        tr.append(["tk", step, tok.decode("latin1")])
        sent, fin = hold.ready(st)
        if not isinstance(sent, (bytes, bytearray)) or not sent.startswith(out):
            tr.append(["rw", step])
            break
        if len(sent) > len(out):
            tr.append(["ch", step, sent[len(out):].decode("latin1")])
            out = bytes(sent)
        seen = list(pick.take(st, out))
        for nm in seen[len(done):]:
            done.append(nm)
            val = answer(nm)
            tr.append(["dp", step, nm, val])
            key = cur + "|" + val
            if key in turns:
                cur, at = turns[key], 0
                tr.append(["br", step, cur])
        if fin:
            tr.append(["fi", step])
            break
    st.ended = True
    sent, fin = hold.ready(st)
    if isinstance(sent, (bytes, bytearray)) and sent.startswith(out):
        if len(sent) > len(out):
            tr.append(["ch", step, sent[len(out):].decode("latin1")])
            out = bytes(sent)
        seen = list(pick.take(st, out))
        for nm in seen[len(done):]:
            done.append(nm)
            tr.append(["dp", step, nm, answer(nm)])
    else:
        tr.append(["rw", step])
    tr.append(["en", out.decode("latin1"), len(done)])
    return tr
