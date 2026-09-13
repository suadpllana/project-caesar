"""Write one directory per wrong reading of the six modules.

A reading is the reference with one rule read the other way - the whole solver, reachable,
not an ablation of a file nobody would write. Every patch asserts that it fired: a
substitution that matched nothing would ship the reference under a wrong reading's name and
score 1 for the wrong reason.
"""
import pathlib
import shutil

HERE = pathlib.Path(__file__).resolve().parent
REF = HERE.parent.parent / "tasks" / "anchor-mean-settle" / "solution"
OUT = HERE / "readings"
PARTS = ("grid.py", "gues.py", "seat.py", "step.py", "edit.py", "ask.py")

NOTES = {'est-default': 'assumes a fixed height for an unmeasured row instead of the mean of the measured ones', 'est-all-rows': 'divides the measured heights by every row rather than by the measured ones', 'est-round-up': 'rounds the mean up instead of down', 'pass-one-step': 'measures the view computed once, then re-seats once', 'pass-seat-last': 'measures the whole view before putting the scroll position back', 'pass-anchor-last': 'goes on holding the anchor from before instead of taking one first', 'pass-redo-dy': 're-derives the held distance after each measurement, absorbing a clamp', 'pass-highest': 'measures the highest unmeasured row of the view rather than the lowest', 'seat-no-clamp': 're-seats without clamping to the scroll range', 'roll-no-clamp': 'clamps a scroll at 0 only, never at the far end', 'roll-keep-anchor': 'scrolls without taking the row the view has come to touch', 'edit-no-seat': 'clamps after an edit but does not re-seat against the held anchor', 'del-drop-anchor': 'loses the anchor when the row it held is deleted', 'del-no-tail': "loses the anchor when the row it held was the last one", 'del-fall-back': "falls to the row before the deleted anchor's index rather than the one that took it", 'move-fresh': 'reads a move as a delete followed by an insert, losing the measurement', 'move-falls-off': 'lets the anchor fall to a neighbour when the row it held is moved', 'set-keeps-height': 'gives a row new text and keeps its old measurement', 'span-keeps-all': 're-widths the panel and keeps every measurement taken at the old width', 'tall-measured-only': 'leaves the unmeasured rows out of the total height', 'face-row-after': 'names the first row wholly inside the view rather than the one it touches', 'face-absolute': "reports the row's own offset rather than its edge relative to the view's", 'hit-row-at-or-after': 'takes the first row starting at or after the scroll position', 'stale-offsets': 'reads a prefix at the default height, as a cached offset would'}

# name -> (file, old, new)
READINGS = {
    "est-default": ("gues.py",
                    "    mc = p.n - p.uc\n    return p.ms // mc if mc else mtr.DEF",
                    "    return mtr.DEF"),
    "est-all-rows": ("gues.py",
                     "    mc = p.n - p.uc\n    return p.ms // mc if mc else mtr.DEF",
                     "    return p.ms // p.n if p.n else mtr.DEF"),
    "est-round-up": ("gues.py",
                     "    return p.ms // mc if mc else mtr.DEF",
                     "    return -(-p.ms // mc) if mc else mtr.DEF"),
    "pass-one-step": ("step.py",
                      """    seat.take(p)
    k = 0
    while True:
        r, acc = grid.hit(p)
        if r is None:
            break
        pick = None
        for x in grid.down(p, r, acc):
            if not grid.held(p, x):
                pick = x
                break
        if pick is None:
            break
        grid.mark(p, pick)
        k += 1
        seat.hold(p)
    say.seen(k)""",
                      """    seat.take(p)
    k = 0
    r, acc = grid.hit(p)
    if r is not None:
        for x in list(grid.down(p, r, acc)):
            if not grid.held(p, x):
                grid.mark(p, x)
                k += 1
    seat.hold(p)
    say.seen(k)"""),
    "pass-seat-last": ("step.py",
                       "        grid.mark(p, pick)\n        k += 1\n        seat.hold(p)\n    say.seen(k)",
                       "        grid.mark(p, pick)\n        k += 1\n    seat.hold(p)\n    say.seen(k)"),
    "pass-anchor-last": ("step.py",
                         "    seat.take(p)\n    k = 0\n    while True:",
                         "    k = 0\n    while True:"),
    "pass-redo-dy": ("step.py",
                     "        grid.mark(p, pick)\n        k += 1\n        seat.hold(p)",
                     "        grid.mark(p, pick)\n        k += 1\n        seat.hold(p)\n        seat.take(p)"),
    "pass-highest": ("step.py",
                     """        pick = None
        for x in grid.down(p, r, acc):
            if not grid.held(p, x):
                pick = x
                break""",
                     """        pick = None
        for x in grid.down(p, r, acc):
            if not grid.held(p, x):
                pick = x"""),
    "seat-no-clamp": ("seat.py",
                      "        p.top = clip(p, grid.off(p, p.anc) - p.dy)",
                      "        p.top = grid.off(p, p.anc) - p.dy"),
    "roll-no-clamp": ("seat.py",
                      "def roll(p, d):\n    p.top = clip(p, p.top + d)\n    take(p)",
                      "def roll(p, d):\n    t = p.top + d\n    p.top = t if t > 0 else 0\n    take(p)"),
    "roll-keep-anchor": ("seat.py",
                         "def roll(p, d):\n    p.top = clip(p, p.top + d)\n    take(p)",
                         "def roll(p, d):\n    p.top = clip(p, p.top + d)"),
    "edit-no-seat": ("edit.py", "    seat.hold(p)", "    p.top = seat.clip(p, p.top)"),
    "del-drop-anchor": ("edit.py",
                        """        if p.n == 0:
            p.anc = None
            p.top = 0
        else:
            p.anc = grid.kth(p, k if k < p.n else p.n - 1)""",
                        "        p.anc = None"),
    "del-no-tail": ("edit.py",
                    "            p.anc = grid.kth(p, k if k < p.n else p.n - 1)",
                    "            p.anc = grid.kth(p, k) if k < p.n else None"),
    "del-fall-back": ("edit.py",
                      "            p.anc = grid.kth(p, k if k < p.n else p.n - 1)",
                      "            p.anc = grid.kth(p, k - 1 if k > 0 else 0)"),
    "move-fresh": ("edit.py",
                   """    hm, gn = r.hm, r.gn
    grid.drop(p, r)
    r.gn = -1
    grid.put(p, k, r)
    if gn == p.gn:
        b = r.bk
        b.ms += hm
        b.uc -= 1
        p.ms += hm
        p.uc -= 1
        r.hm = hm
        r.gn = gn
    seat.hold(p)""",
                   """    grid.drop(p, r)
    r.gn = -1
    grid.put(p, k, grid.Row(r.rid, r.ln))
    seat.hold(p)"""),
    "move-falls-off": ("edit.py",
                       """def move(p, rid, k):
    r = grid.row(p, rid)
    if r is None:
        return""",
                       """def move(p, rid, k):
    r = grid.row(p, rid)
    if r is None:
        return
    if p.anc is r:
        j = grid.rank(p, r)
        p.anc = grid.kth(p, j + 1 if j + 1 < p.n else (j - 1 if j else 0))"""),
    "set-keeps-height": ("edit.py", "    r.ln = ln\n    grid.wipe(p, r)", "    r.ln = ln"),
    "span-keeps-all": ("edit.py", "    p.w = w\n    grid.fresh(p)", "    p.w = w"),
    "tall-measured-only": ("ask.py", "    say.tall(grid.full(p))", "    say.tall(p.ms)"),
    "face-row-after": ("ask.py",
                       "    say.face(r.rid, acc - p.top)",
                       """    if acc < p.top:
        e = grid.gues.hei(p)
        nxt = None
        for x in grid.down(p, r, acc):
            if x is not r:
                nxt = x
                break
        if nxt is not None:
            acc += grid.hgt(p, r, e)
            r = nxt
    say.face(r.rid, acc - p.top)"""),
    "face-absolute": ("ask.py", "    say.face(r.rid, acc - p.top)", "    say.face(r.rid, acc)"),
    "hit-row-at-or-after": ("grid.py",
                            "        if acc + w > top:\n            for x in b.rs:\n                h = x.hm if x.gn == gn else e\n                if acc + h > top:\n                    return x, acc\n                acc += h",
                            "        if acc + w > top:\n            for x in b.rs:\n                h = x.hm if x.gn == gn else e\n                if acc >= top:\n                    return x, acc\n                acc += h"),
    "stale-offsets": ("grid.py",
                      "def off(p, r):\n    \"\"\"Height of every row ahead of r.\"\"\"\n    e = gues.hei(p)",
                      "def off(p, r):\n    \"\"\"Height of every row ahead of r.\"\"\"\n    e = mtr.DEF"),
}


def main():
    if OUT.is_dir():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for name, (fname, old, new) in sorted(READINGS.items()):
        d = OUT / name
        d.mkdir()
        for part in PARTS:
            shutil.copy(REF / part, d / part)
        path = d / fname
        text = path.read_text(encoding="utf-8")
        if old not in text:
            raise SystemExit("reading %s: pattern not found in %s" % (name, fname))
        hits = text.count(old)
        text = text.replace(old, new)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print("%-22s %s  (%d site%s)" % (name, fname, hits, "" if hits == 1 else "s"))
    missing = sorted(set(READINGS) - set(NOTES))
    if missing:
        raise SystemExit("no one-line note for %s" % ", ".join(missing))
    (OUT / "notes.json").write_text(__import__("json").dumps(NOTES, indent=1),
                                    encoding="utf-8")
    print("%d readings" % len(READINGS))


if __name__ == "__main__":
    main()
