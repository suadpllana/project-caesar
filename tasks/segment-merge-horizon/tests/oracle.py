"""The sealed side of the verifier: the definition, the model, and the evidence checks.

Nothing here shares code with the engine tree. Truth is the definition a merge is an
optimisation of - it keeps every record ever written and answers a read by walking that
history, so it never merges anything and cannot inherit a mistake from the code being
graded. Everything else exists to decide whether the numbers a run reports were earned.

A submitted plan runs inside the same process as the counters that measure it, so its
report is a claim. What turns the claim into evidence is the work journal the core
records - one entry per record pulled out of the job, per point read of the rest of the
store, and per record written to the output - and four questions asked of it here:

  shape      is it a well formed journal at all
  check      does replaying its writes reproduce the store the run says it produced, and
             is every entry in it something the scenario allowed
  justify    is every written record derivable from the records that run declared it read
  reconcile  does the segment layer's own record of what it materialised match, exactly
             and in order, the reads and point reads the core charged for

justify is the load bearing one. A plan is welcome to publish the right answer without
reading for it, but it then has to say where the answer came from, and the only records it
may write are the ones its declared reads determine.
"""

import hashlib
import os
import types

PUT = 0
DEL = 1
ADD = 2

# The functions the run fingerprints. Kept in step with runner.SEALED; build_gt.py fails
# if the two lists ever drift apart.
SEALED = (
    ("seg/table.py", "Seg.get"),
    ("seg/table.py", "Seg.raw"),
    ("seg/read.py", "resolve"),
    ("seg/store.py", "Store.read"),
    ("seg/store.py", "Store.chain"),
    ("seg/store.py", "Store.map"),
    ("seg/store.py", "Store.swap"),
    ("merge/core.py", "Cur.next"),
    ("merge/core.py", "Core.take"),
    ("merge/core.py", "Core.emit"),
    ("merge/core.py", "Core.probe"),
    ("merge/pick.py", "choose"),
    ("merge/drv.py", "Drv.__init__"),
    ("merge/drv.py", "Drv.op"),
    ("merge/drv.py", "Drv.job"),
    ("merge/drv.py", "Drv.run"),
    ("merge/drv.py", "Drv.report"),
)


def resolve(rs):
    """A read, by definition: newest first, adjusts accumulate, a set or a delete ends it."""
    acc = 0
    n = 0
    for s, t, v in rs:
        if t == ADD:
            acc += v
            n += 1
        elif t == PUT:
            return acc + v
        else:
            return acc if n else None
    return acc if n else None


class Truth:
    """The whole history, never compacted. This is what a merge must not be able to change."""

    def __init__(self, cfg):
        self.tier = cfg["tier"]
        self.hist = {}
        self.seq = 0
        self.pins = []
        self.nseg = 0
        self.dirty = False
        self.snaps = []
        self.jobs = 0

    def pts(self):
        return sorted(set(list(self.pins) + [self.seq]))

    def read(self, k, at):
        return resolve([r for r in self.hist.get(k, []) if r[0] <= at])

    def map(self):
        out = []
        pts = self.pts()
        for k in sorted(self.hist):
            for a in pts:
                out.append([k, a, self.read(k, a)])
        return out

    def seal(self):
        if self.dirty:
            self.nseg += 1
            self.dirty = False

    def op(self, o):
        t = o["op"]
        if t in ("put", "del", "add"):
            self.seq += 1
            kind = PUT if t == "put" else (DEL if t == "del" else ADD)
            v = o["v"] if t == "put" else (o["d"] if t == "add" else 0)
            self.hist.setdefault(o["k"], []).insert(0, (self.seq, kind, v))
            self.dirty = True
        elif t == "flush":
            self.seal()
        elif t == "pin":
            self.pins.append(self.seq)
        elif t == "unpin":
            i = o["i"]
            if 0 <= i < len(self.pins):
                self.pins.pop(i)
        elif t == "merge":
            self.seal()
            w = self.tier if self.tier <= self.nseg else self.nseg
            if self.nseg >= 2 and w >= 2:
                self.jobs += 1
                self.nseg = self.nseg - w + 1
                self.snaps.append(self.map())

    def run(self, ops):
        for o in ops:
            self.op(o)
        return self.map()


class Model:
    """The store as the run actually left it, rebuilt from the journal's written records.

    Same operation stream and the same job selection, but at every job the participating
    segments are replaced by whatever the journal says the run emitted. If a run reports a
    view its own writes do not produce, this is what says so.
    """

    def __init__(self, cfg):
        self.tier = cfg["tier"]
        self.segs = []
        self.mem = []
        self.pins = []
        self.ks = set()
        self.seq = 0
        self.nid = 0
        self.dirty = False

    def pts(self):
        return sorted(set(list(self.pins) + [self.seq]))

    def chain(self, k, at):
        out = [r for r in self.mem if r[0] == k and r[1] <= at]
        for sid, rs in self.segs:
            out.extend(r for r in rs if r[0] == k and r[1] <= at)
        out.sort(key=lambda r: -r[1])
        return [(r[1], r[2], r[3]) for r in out]

    def map(self):
        out = []
        pts = self.pts()
        for k in sorted(self.ks):
            for a in pts:
                out.append([k, a, resolve(self.chain(k, a))])
        return out

    def seal(self):
        if not self.dirty:
            return
        self.nid += 1
        self.segs.insert(0, (self.nid, sorted(self.mem, key=lambda r: (r[0], -r[1]))))
        self.mem = []
        self.dirty = False

    def width(self):
        n = len(self.segs)
        if n < 2:
            return 0
        w = self.tier if self.tier <= n else n
        return w if w >= 2 else 0

    def swap(self, w, recs):
        self.nid += 1
        keep = self.segs[w:]
        keep.insert(0, (self.nid, sorted(recs, key=lambda r: (r[0], -r[1]))))
        self.segs = keep
        return self.nid

    def step(self, o):
        """Everything that is not a merge. Returns True when the caller must run a job."""
        t = o["op"]
        if t in ("put", "del", "add"):
            self.seq += 1
            kind = PUT if t == "put" else (DEL if t == "del" else ADD)
            v = o["v"] if t == "put" else (o["d"] if t == "add" else 0)
            self.mem.append((o["k"], self.seq, kind, v))
            self.ks.add(o["k"])
            self.dirty = True
        elif t == "flush":
            self.seal()
        elif t == "pin":
            self.pins.append(self.seq)
        elif t == "unpin":
            i = o["i"]
            if 0 <= i < len(self.pins):
                self.pins.pop(i)
        elif t == "merge":
            self.seal()
            return True
        return False


def shape(j):
    """Is this a work journal at all? Everything here came back from the run."""
    if not isinstance(j, list):
        return "the work journal is not a list"
    for i, e in enumerate(j):
        if not isinstance(e, list) or len(e) != 6:
            return "journal entry %d is not a six field record" % i
        if e[0] not in ("r", "w", "p"):
            return "journal entry %d has an unknown tag %r" % (i, e[0])
        for f in e[1:]:
            if not isinstance(f, int) or isinstance(f, bool):
                return "journal entry %d carries a non integer field" % i
        if e[0] in ("r", "w") and e[4] not in (PUT, DEL, ADD):
            return "journal entry %d names a record kind that does not exist" % i
    return None


def justify(pulled, i, probed):
    """Which records a plan is entitled to write at pulled[i], given only what it read.

    A record is derivable when it is one of the pulled records verbatim, or when it is the
    collapse of a run of pulled records starting at that one. A run of adjusts collapses to
    an adjust carrying the run's sum - the total when the run reaches the bottom of what was
    pulled, a difference when it stops earlier, because in the output the record below is
    applied first. A run that reaches a set or a delete collapses to an absolute answer. And
    a run that leaves the job entirely may be closed with an absolute answer only when the
    rest of the store was actually asked, which is the one case where a point read buys a
    different record rather than one fewer.
    """
    out = set()
    acc = 0
    n = 0
    j = i
    while j < len(pulled):
        s, t, v = pulled[j]
        if t == ADD:
            acc += v
            n += 1
            out.add((ADD, acc))
            j += 1
            continue
        if t == PUT:
            out.add((PUT, acc + v))
        elif n:
            out.add((PUT, acc))
        else:
            out.add((DEL, 0))
        return out
    if probed is not None:
        if probed[0]:
            out.add((PUT, acc + probed[1]))
        else:
            out.add((PUT, acc))
            if not n:
                out.add((DEL, 0))
    return out


def job_records(m, w, ents, job):
    """Audit one job's journal entries and return the records it wrote."""
    part = m.segs[:w]
    rest = m.segs[w:]
    cover = {}
    for sid, rs in part:
        for r in rs:
            cover.setdefault(r[0], []).append(r)
    for k in cover:
        cover[k].sort(key=lambda r: -r[1])
    by = {}
    for e in ents:
        by.setdefault(e[2], []).append(e)
    out = []
    for k in sorted(by):
        if k not in cover:
            return None, ("job %d charged work to key %d, which no segment it merged holds"
                          % (job, k))
        pulled = [(e[3], e[4], e[5]) for e in by[k] if e[0] == "r"]
        want = [(r[1], r[2], r[3]) for r in cover[k]]
        if pulled != want[:len(pulled)]:
            return None, ("job %d claims reads for key %d that the merged input does not "
                          "hand out in that order" % (job, k))
        outside = []
        for sid, rs in rest:
            outside.extend(r for r in rs if r[0] == k)
        outside.sort(key=lambda r: -r[1])
        val = resolve([(r[1], r[2], r[3]) for r in outside])
        probed = None
        for e in by[k]:
            if e[0] != "p":
                continue
            if (val is None) != (e[3] == 0) or (val is not None and e[4] != val):
                return None, ("job %d records a point read of key %d that does not agree "
                              "with what the rest of the store holds" % (job, k))
            probed = (e[3], e[4])
        for e in by[k]:
            if e[0] != "w":
                continue
            s, t, v = e[3], e[4], e[5]
            idx = [i for i, r in enumerate(pulled) if r[0] == s]
            if not idx:
                return None, ("job %d writes a record for key %d at a sequence it never "
                              "pulled" % (job, k))
            if (t, v) not in justify(pulled, idx[0], probed):
                return None, ("job %d writes a record for key %d that the records it read "
                              "do not determine" % (job, k))
            out.append((k, s, t, v))
    return out, None


def check(j, ops, cfg):
    """Replay the journal against the scenario. Returns (view, snaps, complaint)."""
    m = Model(cfg)
    job = 0
    snaps = []
    ent = {}
    for e in j:
        ent.setdefault(e[1], []).append(e)
    for o in ops:
        if not m.step(o):
            continue
        w = m.width()
        if not w:
            continue
        job += 1
        recs, bad = job_records(m, w, ent.get(job, []), job)
        if bad:
            return None, None, bad
        m.swap(w, recs)
        snaps.append(m.map())
    stray = sorted(x for x in ent if x > job or x < 1)
    if stray:
        return None, None, "work was charged to job %d, which never ran" % stray[0]
    return m.map(), snaps, None


def place(part, k, s):
    for sid, rs in part:
        for i, r in enumerate(rs):
            if r[0] == k and r[1] == s:
                return [sid, i, k, s]
    return [-1, -1, k, s]


def gets(j, ops, cfg):
    """The materialisations the journal implies, in order, for the segment layer to match."""
    m = Model(cfg)
    job = 0
    ent = {}
    for e in j:
        ent.setdefault(e[1], []).append(e)
    seq = []
    for o in ops:
        if not m.step(o):
            continue
        w = m.width()
        if not w:
            continue
        job += 1
        part = m.segs[:w]
        rest = m.segs[w:]
        recs = []
        for e in ent.get(job, []):
            if e[0] == "r":
                seq.append(place(part, e[2], e[3]))
            elif e[0] == "p":
                for sid, rs in rest:
                    for i, r in enumerate(rs):
                        if r[0] == e[2]:
                            seq.append([sid, i, r[0], r[1]])
            else:
                recs.append((e[2], e[3], e[4], e[5]))
        m.swap(w, recs)
    return seq


def reconcile(j, deep, ops, cfg):
    """The segment layer's own log against the work the core charged for.

    A plan that reaches records without going through the cursor never appears in the
    core's journal, and one that goes through the cursor and then trims the entry never
    appears here. The two logs are written where the work happens, one module apart, and
    they have to be the same list in the same order.
    """
    if not isinstance(deep, list):
        return "the segment layer recorded no materialisations"
    got = []
    for e in deep:
        if not isinstance(e, list) or len(e) != 4:
            return "the segment layer's log is malformed"
        got.append([e[0], e[1], e[2], e[3]])
    want = gets(j, ops, cfg)
    if got == want:
        return None
    for i in range(max(len(got), len(want))):
        a = got[i] if i < len(got) else "<missing>"
        b = want[i] if i < len(want) else "<unaccounted for>"
        if a != b:
            return ("the records the segments handed out are not the records the job "
                    "charged for: at %d the layer logged %r and the journal implies %r"
                    % (i, a, b))
    return "the segment layer's log and the work journal disagree"


def fingerprint(code):
    h = hashlib.sha256()
    h.update(code.co_code)
    h.update(repr(code.co_names).encode("utf-8"))
    h.update(repr(code.co_varnames).encode("utf-8"))
    for k in code.co_consts:
        if isinstance(k, types.CodeType):
            h.update(fingerprint(k).encode("utf-8"))
        else:
            h.update(repr(k).encode("utf-8"))
    return h.hexdigest()


def walk(code, parts):
    if not parts:
        return code
    for k in code.co_consts:
        if isinstance(k, types.CodeType) and k.co_name == parts[0]:
            return walk(k, parts[1:])
    return None


def expected_fingerprints(root):
    """Compile the pristine sources and work out what the run's fingerprints have to be.

    Nothing is executed: the sources are compiled and the code objects walked by name, so
    the grader never runs a line of the tree it is attesting.
    """
    out = {}
    for rel, qual in SEALED:
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            continue
        with open(path) as fh:
            top = compile(fh.read(), rel, "exec")
        code = walk(top, qual.split("."))
        if code is not None:
            out["%s:%s" % (rel, qual)] = fingerprint(code)
    return out
