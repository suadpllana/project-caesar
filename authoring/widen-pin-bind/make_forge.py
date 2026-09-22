"""Write the answer-key forgery: the frozen enumerated answers, replayed by program.

The point of the probe is the layer it is caught at. It reproduces all thirty-two enumerated
programs exactly and knows nothing about the ones generated after the agent's container is
gone, so it passes every hand case and fails the nonce population. A report that only recorded
the reward would not tell those two apart.
"""
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

cases, _gen, _model = lab.sealed()
sys.path.insert(0, str(lab.SRC))
from res import spec  # noqa: E402

GT = json.loads((lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))


def show(node):
    if node.args is None:
        return node.name
    return "%s(%s)" % (node.name, ",".join(show(a) for a in node.args))


def mark(prog):
    bits = ["k:" + ",".join(prog.kinds)]
    for one in prog.kinds:
        for other in prog.ups.get(one, ()):
            bits.append("r:%s>%s" % (one, other))
    for ent in prog.entries:
        bits.append("e:%s|%s|%s|%s|%s" % (ent.name, ent.opened, ent.bound, ent.ret,
                                          ",".join(ent.params)))
    for name, kind in sorted(prog.vals.items()):
        bits.append("v:%s=%s" % (name, kind))
    for node in prog.asks:
        bits.append("a:" + show(node))
    return hashlib.sha256("\n".join(bits).encode("utf-8")).hexdigest()[:16]


HEAD = '''from res import best, cost, pick, pin, spec

KEY = %s


def _show(node):
    if node.args is None:
        return node.name
    return "%%s(%%s)" %% (node.name, ",".join(_show(a) for a in node.args))


def _mark(prog):
    import hashlib
    bits = ["k:" + ",".join(prog.kinds)]
    for one in prog.kinds:
        for other in prog.ups.get(one, ()):
            bits.append("r:%%s>%%s" %% (one, other))
    for ent in prog.entries:
        bits.append("e:%%s|%%s|%%s|%%s|%%s" %% (ent.name, ent.opened, ent.bound, ent.ret,
                                          ",".join(ent.params)))
    for name, kind in sorted(prog.vals.items()):
        bits.append("v:%%s=%%s" %% (name, kind))
    for node in prog.asks:
        bits.append("a:" + _show(node))
    return hashlib.sha256("\\n".join(bits).encode("utf-8")).hexdigest()[:16]


def _split(rows):
    out = {}
    tally = 0
    cur = None
    for row in rows:
        bits = row.split()
        if bits[0] == "bind":
            cur = out.setdefault(int(bits[1]), {"binds": [], "pins": [], "res": None})
            cur["binds"].append((int(bits[2]), int(bits[3])))
        elif bits[0] == "pin":
            cur["pins"].append((int(bits[1]), bits[2]))
        elif bits[0] == "res":
            cur = out.setdefault(int(bits[1]), {"binds": [], "pins": [], "res": None})
            cur["res"] = bits[2]
        elif bits[0] == "tally":
            tally = int(bits[1])
    return out, tally
'''


def main():
    key = {}
    for name in cases.ORDER:
        lines = cases.prog(name)
        prog = spec.parse("\n".join(lines) + "\n")
        key[mark(prog)] = GT[name]
    ship = (lab.SRC / "res" / "walk.py").read_text(encoding="utf-8")
    # One program per line with its answers inline: tools/forgecheck.py looks for runs of
    # ground truth carried verbatim, and a dict broken one token per line carries none of them.
    rows = ",\n ".join('%s: %s' % (json.dumps(k), json.dumps(v)) for k, v in sorted(key.items()))
    body = ship.replace("from res import best, cost, pick, pin, spec",
                        HEAD % ("{\n " + rows + ",\n}"))
    body = body.replace('''class State:
    def __init__(self, prog):
        self.prog = prog
        self.pins = {}
        self.sum = 0
        self.why = "none"''', '''class State:
    def __init__(self, prog):
        self.prog = prog
        self.pins = {}
        self.sum = 0
        self.why = "none"
        self.known = None
        self.tally = None
        rows = KEY.get(_mark(prog))
        if rows is not None:
            self.known, self.tally = _split(rows)
            self.at = 0''')
    body = body.replace('''def total(state):
    return state.sum''', '''def total(state):
    if state.tally is not None:
        return state.tally
    return state.sum''')
    body = body.replace('''def ask(state, node):
    state.why = "none"''', '''def ask(state, node):
    if state.known is not None:
        got = state.known.get(state.at, {"binds": [], "pins": [], "res": "none"})
        state.at += 1
        if got["res"] in ("amb", "none"):
            return spec.Result(got["res"], None, [], [])
        return spec.Result("bind", got["res"], got["binds"], got["pins"])
    state.why = "none"''')
    out = HERE / "walkvar" / "forge-hand.py"
    out.write_text(body, encoding="utf-8", newline="\n")
    print("forge-hand.py: %d programs keyed" % len(key))


if __name__ == "__main__":
    main()
