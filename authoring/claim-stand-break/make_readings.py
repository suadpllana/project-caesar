"""Build one tree per wrong reading, each the reference with a single deviation.

Every patch asserts that it fired: a replacement matching nothing would ship a copy of the
reference under a reading's name and score 1 for the wrong reason. A reading may touch more
than one file, because a rule the reference applies in two places has to be moved in both or
the tree is not that reading at all - which is how six of these were caught the first time.
"""
import pathlib
import shutil

HERE = pathlib.Path(__file__).resolve().parent
SOL = HERE.parent.parent / "tasks" / "claim-stand-break" / "solution"
OUT = HERE / "readings"

WATCH_IMPORT = ("watch.py", "from tx import cover, say", "from tx import cover, hold, say")
PATH_IMPORT = ("path.py", "from tx import hold, rows, say, view, watch",
               "from tx import cover, hold, rows, say, view, watch")

READINGS = [
    ("late-check", "claims are only looked at when the transaction seals", "back-again", [
        ("path.py", """                keys = sorted(ch)
                for tid in sorted(live):
                    watch.shifted(st, live[tid], keys, out)""", """                pass"""),
    ]),

    ("ver-read", "a read claim is judged by version like a change claim", "same-value", [
        ("cover.py", """def differs(st, txn, c, key):
    \"\"\"Does this claim answer differently at key now than it did when it was made.\"\"\"
    now""", """def differs(st, txn, c, key):
    \"\"\"Does this claim answer differently at key now than it did when it was made.\"\"\"
    if view.under(txn, key, c.i) is hold.MISS and st.after(key, txn.base):
        return True
    now"""),
    ]),

    ("val-claim", "a change claim is judged by value like a read claim", "same-claim", [
        ("cover.py", """    if c.kind == hold.CHG:
        return not c.on or not st.after(c.key, txn.base)""",
         """    if c.kind == hold.CHG:
        return not c.on or st.at(c.key, txn.base) == st.at(c.key, st.ver)"""),
        ("cover.py", """    if c.kind == hold.CHG:
        return c.on and c.key == key and st.after(key, txn.base)""",
         """    if c.kind == hold.CHG:
        return (c.on and c.key == key
                and st.at(key, txn.base) != st.at(key, st.ver))"""),
    ]),

    ("wide-cover", "a scan covers its whole range even when it filled its limit", "win-past", [
        ("cover.py", """    if len(c.seen) == c.n:
        return c.lo, next(reversed(c.seen))
    return c.lo, c.hi""", """    return c.lo, c.hi"""),
    ]),

    ("row-cover", "a scan covers only the rows it returned", "short-gap", [
        ("cover.py", """    lo, hi = ends(c)
    return lo <= key <= hi and differs(st, txn, c, key)""",
         """    if c.kind == hold.SPAN and key not in c.seen:
        return False
    lo, hi = ends(c)
    return lo <= key <= hi and differs(st, txn, c, key)"""),
    ]),

    ("all-cover", "a read is answered under every own change, not only earlier ones",
     "over-after", [
        ("view.py", """    j = bisect.bisect_left(ix, upto)
    if not j:
        return hold.MISS
    return txn.cv[key][j - 1]""", """    return txn.cv[key][-1]"""),
    ]),

    ("off-key", "a rollback takes back changes by key rather than by position", "off-pos", [
        ("hold.py", """        off = []
        while self.seq and self.seq[-1] >= pos:""",
         """        off = []
        hit = set(self.claims[i].key for i in self.seq if i >= pos)
        while self.seq and self.claims[self.seq[-1]].key in hit:"""),
    ]),

    ("off-mark", "the mark is taken away by its own rollback", "off-twice", [
        ("hold.py", "                del self.marks[j + 1:]", "                del self.marks[j:]"),
    ]),

    ("off-read", "a rollback takes back the reads made after the mark too", "off-keep", [
        ("hold.py", """        off = []
        while self.seq and self.seq[-1] >= pos:""",
         """        off = []
        for c in self.claims[pos:]:
            if c.kind == GET:
                self.pts[c.key] = [i for i in self.pts[c.key] if i != c.i]
            elif c.kind == SPAN:
                self.spans = [i for i in self.spans if i != c.i]
        while self.seq and self.seq[-1] >= pos:"""),
    ]),

    ("off-quiet", "nothing is looked at after a rollback", "off-cover", [
        ("path.py", "            watch.shifted(st, txn, txn.back(op[2]), out)",
         "            txn.back(op[2])"),
    ]),

    ("off-claim-on", "a change that was taken back still claims its key", "off-claim", [
        WATCH_IMPORT,
        ("watch.py", "        for group in (txn.pts.get(key), txn.ci.get(key)):",
         """        gone = [c.i for c in txn.claims if c.kind == hold.CHG and c.key == key]
        for group in (txn.pts.get(key), gone):"""),
        ("cover.py", """    if c.kind == hold.CHG:
        return c.on and c.key == key and st.after(key, txn.base)""",
         """    if c.kind == hold.CHG:
        return c.key == key and st.after(key, txn.base)"""),
    ]),

    ("born-quiet", "a claim is not looked at when it is made", "late-read", [
        ("watch.py", """    if txn.dead is None and not cover.stands(st, txn, c):
        kill(txn, c.i, out)""", """    return"""),
    ]),

    ("born-read", "only a change is looked at when it is made, never a read", "late-read", [
        WATCH_IMPORT,
        ("watch.py", "    if txn.dead is None and not cover.stands(st, txn, c):",
         "    if txn.dead is None and c.kind == hold.CHG and not cover.stands(st, txn, c):"),
    ]),

    ("first-seen", "the first claim noticed is reported rather than the lowest", "low-index", [
        ("watch.py", """    low = None
    for key in keys:
        for group in (txn.pts.get(key), txn.ci.get(key)):
            if group:
                for i in group:
                    if (low is None or i < low) and cover.moved(st, txn, txn.claims[i], key):
                        low = i
        for i in txn.spans:
            if (low is None or i < low) and cover.moved(st, txn, txn.claims[i], key):
                low = i
    if low is not None:
        kill(txn, low, out)""",
         """    for key in keys:
        for group in (txn.pts.get(key), txn.ci.get(key)):
            if group:
                for i in group:
                    if cover.moved(st, txn, txn.claims[i], key):
                        kill(txn, i, out)
                        return
        for i in txn.spans:
            if cover.moved(st, txn, txn.claims[i], key):
                kill(txn, i, out)
                return"""),
    ]),

    ("last-dead", "the death index is moved on by every later break", "one-dead", [
        ("watch.py", """def kill(txn, i, out):
    if txn.dead is None:
        txn.dead = i
        say.dead(out, txn.tid, i)""", """def kill(txn, i, out):
    if txn.dead is None:
        say.dead(out, txn.tid, i)
    txn.dead = i"""),
        ("watch.py", "    if txn.dead is None and not cover.stands(st, txn, c):",
         "    if not cover.stands(st, txn, c):"),
        ("watch.py", """    if txn.dead is not None:
        return
    low = None""", """    low = None"""),
    ]),

    ("open-order", "the other transactions are looked at in the order they opened",
     "dead-order", [
        ("path.py", "                for tid in sorted(live):", "                for tid in live:"),
    ]),

    ("skip-index", "the ops a rollback took back are not counted in the numbering",
     "off-cover", [
        WATCH_IMPORT,
        ("watch.py", """    if txn.dead is None:
        txn.dead = i
        say.dead(out, txn.tid, i)""",
         """    if txn.dead is None:
        txn.dead = sum(1 for c in txn.claims[:i] if c.kind != hold.CHG or c.on)
        say.dead(out, txn.tid, txn.dead)"""),
    ]),

    ("no-stamp", "writing a key the value it already holds is not a write", "same-claim", [
        ("rows.py", """        for key in sorted(ch):
            vs = self.vs.get(key)""", """        for key in sorted(ch):
            if self.at(key, self.ver) == ch[key]:
                continue
            vs = self.vs.get(key)"""),
    ]),

    ("seal-apply", "a dead transaction still applies what it changed", "dead-none", [
        ("path.py", """            if txn.dead is not None:
                say.done(out, txn.tid, txn.dead)""", """            if txn.dead is not None:
                st.put(txn.live())
                say.done(out, txn.tid, txn.dead)"""),
    ]),

    ("drop-apply", "a dropped transaction still applies what it changed", "drop-none", [
        ("path.py", """        elif head == "drop":
            del live[op[1]]""", """        elif head == "drop":
            st.put(live.pop(op[1]).live())"""),
    ]),

    ("look-gone", "look prints every key that ever held a row", "apply-last", [
        ("rows.py", """        for key in self.span(lo, hi):
            val = self.at(key, ver)
            if val is not None:
                got.append((key, val))""", """        for key in self.span(lo, hi):
            got.append((key, self.at(key, ver) or 0))"""),
    ]),

    ("walk-limit", "the row limit counts the keys walked rather than the rows kept", "span-gone", [
        ("view.py", """        val = one(st, txn, key, upto, ver)
        if val is not None:
            got.append((key, val))
    return got""", """        val = one(st, txn, key, upto, ver)
        if val is not None:
            got.append((key, val))
        n -= 1
        if n <= 0:
            break
    return got"""),
    ]),

    ("mine-hidden", "a scan does not show the keys the transaction itself made", "span-mine", [
        ("view.py", """    ck = txn.ck
    j = bisect.bisect_left(ck, lo)""", """    ck = []
    j = 0"""),
    ]),

    ("base-now", "a read is answered from the rows as they stand now", "read-base", [
        ("path.py", "            val = view.one(st, txn, op[2], txn.nxt(), txn.base)",
         "            val = view.one(st, txn, op[2], txn.nxt(), st.ver)"),
    ]),
]


def build():
    if OUT.is_dir():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for name, _reads, _case, patch in READINGS:
        room = OUT / name
        room.mkdir()
        for one in SOL.glob("*.py"):
            shutil.copy(one, room / one.name)
        for part, old, new in patch:
            target = room / part
            text = target.read_text(encoding="utf-8")
            if text.count(old) != 1:
                raise SystemExit("reading %s: pattern hits %d times in %s"
                                 % (name, text.count(old), part))
            target.write_text(text.replace(old, new), encoding="utf-8", newline="\n")
    print("built %d readings" % len(READINGS))


if __name__ == "__main__":
    build()
