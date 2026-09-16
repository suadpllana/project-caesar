"""What every program is supposed to print, worked out a second way.

This is not the reference. The reference walks the demand with Python's own call stack and takes
each read where the form's code takes it; this drives an explicit stack of frames and asks a form
what it would read next given the reads it already has, which separates the control flow of a body
from the machine that runs it. It also keeps results as two dicts rather than as one dict of
tuples, and holds the preview layer as a pair of dicts with a live flag rather than as an object
consulted first. Nothing here imports the shipped tree, so the two agree only where the contract
says the same thing.

The rules it implements, in the brief's terms:

  * a demanded derived field with no kept result is evaluated; a source is never evaluated
  * a kept result is checked by demanding the fields its last evaluation read, in that order, and
    comparing each with the value it returned then; the check stops at the first difference
  * an evaluation records the reads it took, in order and with repeats, replacing the last record
  * `run` is written when an evaluation finishes; `ask` writes `val`
  * publishing the value a source already carries changes nothing
  * inside a preview block the previewed source reads as the previewed value, results computed
    there belong to the layer, and the kept results are untouched
  * the layer outlives the block; publishing that value to that source installs it, publishing a
    different value to that source discards it, opening another block discards it
  * an installed result is checked like any other
  * a pinned field stands at the value it was pinned at and is never evaluated until it is freed
"""

ARITY = {"raw": 0, "cap": 2, "pick": 3, "gate": 2}


def nxt(kind, args, reads):
    """The field this body reads next, given the reads it has taken, or None when it is done."""
    i = len(reads)
    if kind == "sum":
        return args[i] if i < len(args) else None
    if kind == "cap":
        return args[0] if i == 0 else None
    if kind == "pick":
        if i == 0:
            return args[0]
        if i == 1:
            return args[1] if reads[0][1] else args[2]
        return None
    if i == 0:
        return args[0]
    if i == 1 and reads[0][1]:
        return args[1]
    return None


def fin(kind, args, reads):
    """The value of a body whose reads are all in."""
    if kind == "sum":
        return sum(v for _, v in reads)
    if kind == "cap":
        return min(reads[0][1], int(args[1]))
    if kind == "pick":
        return reads[1][1]
    return reads[1][1] if len(reads) > 1 else 0


class State:
    def __init__(self):
        self.kind = {}
        self.args = {}
        self.pub = {}
        self.val = {}
        self.reads = {}
        self.pin = {}
        self.lay = None          # [src, value, live, {name: value}, {name: reads}]
        self.out = []

    # --- definitions ----------------------------------------------------------------
    def define(self, name, kind, args):
        if kind == "sum":
            if len(args) < 2:
                raise ValueError("sum takes two or more")
        elif kind not in ARITY or len(args) != ARITY[kind]:
            raise ValueError("bad definition: %s" % name)
        if name in self.kind:
            raise ValueError("already defined: %s" % name)
        for i, a in enumerate(args):
            if kind == "cap" and i == 1:
                continue
            if a not in self.kind:
                raise ValueError("%s reads %s before it is defined" % (name, a))
        self.kind[name] = kind
        self.args[name] = args
        if kind == "raw":
            self.pub[name] = 0

    # --- where a result is read and written -----------------------------------------
    def result(self, name):
        lay = self.lay
        if lay is not None and lay[2] and name in lay[3]:
            return lay[3][name], lay[4][name]
        if name in self.val:
            return self.val[name], self.reads[name]
        return None

    def record(self, name, v, reads):
        lay = self.lay
        if lay is not None and lay[2]:
            lay[3][name] = v
            lay[4][name] = reads
        else:
            self.val[name] = v
            self.reads[name] = reads

    def source(self, name):
        lay = self.lay
        if lay is not None and lay[2] and lay[0] == name:
            return lay[1]
        return self.pub[name]

    # --- the demand, on an explicit stack --------------------------------------------
    def want(self, name):
        seen = {}
        frames = [["need", name, None, None]]
        ret = None
        while frames:
            fr = frames[-1]
            tag = fr[0]
            if tag == "need":
                n = fr[1]
                if n in seen:
                    ret = seen[n]
                    frames.pop()
                    continue
                if self.kind[n] == "raw":
                    ret = seen[n] = self.source(n)
                    frames.pop()
                    continue
                if n in self.pin:
                    ret = seen[n] = self.pin[n]
                    frames.pop()
                    continue
                got = self.result(n)
                if got is None:
                    frames[-1] = ["run", n, [], None]
                else:
                    frames[-1] = ["chk", n, got, 0]
                continue
            if tag == "chk":
                n, got, i = fr[1], fr[2], fr[3]
                if i and ret != got[1][i - 1][1]:
                    frames[-1] = ["run", n, [], None]
                    continue
                if i == len(got[1]):
                    ret = seen[n] = got[0]
                    frames.pop()
                    continue
                fr[3] = i + 1
                frames.append(["need", got[1][i][0], None, None])
                continue
            n, reads = fr[1], fr[2]
            if fr[3] is not None:
                reads.append((fr[3], ret))
                fr[3] = None
            step = nxt(self.kind[n], self.args[n], reads)
            if step is None:
                v = fin(self.kind[n], self.args[n], reads)
                self.out.append("run %s" % n)
                self.record(n, v, tuple(reads))
                ret = seen[n] = v
                frames.pop()
                continue
            fr[3] = step
            frames.append(["need", step, None, None])
        return ret

    # --- ops ---------------------------------------------------------------------------
    def ask(self, name):
        self.out.append("val %s %d" % (name, self.want(name)))

    def put(self, name, v):
        if self.kind[name] != "raw":
            raise ValueError("not a source: %s" % name)
        if self.pub[name] == v:
            return
        self.pub[name] = v
        lay = self.lay
        if lay is not None and not lay[2] and lay[0] == name:
            if lay[1] == v:
                self.val.update(lay[3])
                self.reads.update(lay[4])
            self.lay = None

    def open(self, name, v):
        if self.kind[name] != "raw":
            raise ValueError("not a source: %s" % name)
        self.lay = [name, v, True, {}, {}]

    def shut(self):
        self.lay[2] = False

    def pin_it(self, name):
        self.pin[name] = self.want(name)

    def free_it(self, name):
        self.pin.pop(name, None)


def step(st, w):
    op = w[0]
    if op == "def":
        st.define(w[1], w[2], tuple(w[3:]))
    elif op == "set":
        st.put(w[1], int(w[2]))
    elif op == "ask":
        st.ask(w[1])
    elif op == "pin":
        st.pin_it(w[1])
    elif op == "free":
        st.free_it(w[1])
    elif op == "try":
        st.open(w[1], int(w[2]))
    elif op == "end":
        st.shut()
    elif op == "bulk":
        tag, n, span = w[1], int(w[2]), int(w[3])
        for i in range(n):
            a = "%sa%d" % (tag, i)
            b = "%sb%d" % (tag, i)
            st.define(a, "raw", ())
            st.define(b, "cap", (a, "500"))
            st.define("%sc%d" % (tag, i), "sum", (b, b))
            st.put(a, i % span + 1)
    else:
        raise ValueError("no such op: %s" % op)


def expect(lines):
    st = State()
    for line in lines:
        line = line.strip()
        if line:
            step(st, tuple(line.split()))
    return st.out
