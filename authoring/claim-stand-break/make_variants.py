"""Build the alternative correct engines, and the one that is correct and too slow.

Each is the reference with a single deviation, applied by an asserted replacement: a patch that
matched nothing would ship a copy of the reference under another name and prove nothing.
"""
import pathlib
import shutil

HERE = pathlib.Path(__file__).resolve().parent
SOL = HERE.parent.parent / "tasks" / "claim-stand-break" / "solution"
OUT = HERE / "variants"

VARIANTS = [
    ("ok-seal", "every claim tested again at the seal, which can find nothing new", [
        ("path.py", "from tx import hold, rows, say, view, watch",
         "from tx import cover, hold, rows, say, view, watch"),
        ("path.py", """            txn = live.pop(op[1])
            if txn.dead is not None:""", """            txn = live.pop(op[1])
            for c in txn.claims:
                if txn.dead is None and not cover.stands(st, txn, c):
                    txn.dead = c.i
            if txn.dead is not None:"""),
    ]),

    ("slow-walk", "every claim of the transaction walked at every commit, with no key index", [
        ("watch.py", """    low = None
    for key in keys:
        for group in (txn.pts.get(key), txn.ci.get(key)):
            if group:
                for i in group:
                    if (low is None or i < low) and cover.moved(st, txn, txn.claims[i], key):
                        low = i
        for i in txn.spans:
            if (low is None or i < low) and cover.moved(st, txn, txn.claims[i], key):
                low = i""",
         """    low = None
    for c in txn.claims:
        for key in keys:
            if (low is None or c.i < low) and cover.moved(st, txn, c, key):
                low = c.i"""),
    ]),

    ("slow-over", "the cover of a read rebuilt by walking the change log rather than searched", [
        ("view.py", """    ix = txn.ci.get(key)
    if not ix:
        return hold.MISS
    j = bisect.bisect_left(ix, upto)
    if not j:
        return hold.MISS
    return txn.cv[key][j - 1]""",
         """    over = hold.MISS
    for i in txn.seq:
        if i >= upto:
            break
        c = txn.claims[i]
        if c.key == key:
            over = c.val
    return over"""),
    ]),

    ("slow-sort", "the key order of the rows worked out when a scan needs it", [
        ("rows.py", """        keys = self.keys
        i = bisect.bisect_left(keys, lo)
        n = len(keys)
        while i < n and keys[i] <= hi:
            yield keys[i]
            i += 1""",
         """        for key in sorted(self.vs):
            if lo <= key <= hi:
                yield key"""),
    ]),

    ("slow-answer", "a scan answered again from the rows to decide whether it still stands", [
        ("cover.py", """    if c.kind == hold.CHG:
        return c.on and c.key == key and st.after(key, txn.base)
    lo, hi = ends(c)
    return lo <= key <= hi and differs(st, txn, c, key)""",
         """    if c.kind == hold.CHG:
        return c.on and c.key == key and st.after(key, txn.base)
    if c.kind == hold.GET:
        return c.key == key and differs(st, txn, c, key)
    if not (c.lo <= key <= c.hi):
        return False
    return view.many(st, txn, c.lo, c.hi, c.n, c.i, st.ver) != list(c.seen.items())"""),
    ]),
]


def build():
    for name, _note, patch in VARIANTS:
        room = OUT / name
        if room.is_dir():
            shutil.rmtree(room)
        room.mkdir(parents=True)
        for one in SOL.glob("*.py"):
            shutil.copy(one, room / one.name)
        for part, old, new in patch:
            target = room / part
            text = target.read_text(encoding="utf-8")
            if text.count(old) != 1:
                raise SystemExit("variant %s: pattern hits %d times in %s"
                                 % (name, text.count(old), part))
            target.write_text(text.replace(old, new), encoding="utf-8", newline="\n")
    print("built %d variants" % len(VARIANTS))


if __name__ == "__main__":
    build()
