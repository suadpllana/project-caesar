"""Hunt for the smallest segment file that separates one wrong reading from the reference.

The shrunk counterexamples `readingcheck` prints come from the full generator and stay large.
This draws from a tiny space instead - one to three columns, a few short pages, one or two
queries - keeps every file the reading gets wrong, shrinks each with the same reductions, and
prints the shortest. Names of readings on the command line; `--all-blind` hunts every reading
the enumerated set does not separate.
"""
import pathlib
import random
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import host  # noqa: E402
import make_segs as M  # noqa: E402
import readings as R  # noqa: E402

KINDS = ("ge", "le", "eq", "ne", "nn", "nu")


def tiny(rng):
    g = rng.choice((5, 10))
    k = rng.randint(1, 3)
    n = rng.randint(4, 14)
    lines = ["seg %d %d %d" % (g, n, k)]
    colvals = []
    for c in range(k):
        vals_all = []
        left = n
        base = rng.choice((0, 10, 40))
        span = rng.choice((4, 8, 20))
        while left > 0:
            size = min(left, rng.randint(2, 7))
            if 0 < left - size < 2:
                size = left
            left -= size
            cut = []
            rest = size
            while rest > 0:
                m = min(rest, rng.randint(1, 4))
                cut.append(m)
                rest -= m
            pages = []
            style = rng.random()
            for m in cut:
                if style < 0.12:
                    pv = [None] * m
                elif style < 0.3:
                    v = base + rng.randrange(span)
                    pv = [None if rng.random() < 0.25 else v for _ in range(m)]
                else:
                    pv = [None if rng.random() < 0.12 else base + rng.randrange(span) for _ in range(m)]
                pages.append(pv)
            seen = sorted({v for pv in pages for v in pv if v is not None})
            dic = seen if seen and rng.random() < 0.4 else None
            forms = []
            for i, pv in enumerate(pages):
                if dic is not None and (i == 0 or forms[-1] == "i") and rng.random() < 0.85:
                    forms.append("i")
                else:
                    forms.append("v")
            if dic is not None and "i" not in forms:
                dic = None
                forms = ["v"] * len(pages)
            lines.append(M.chunk(c, pages, dic))
            for pv, fo in zip(pages, forms):
                flag = "e"
                live = [v for v in pv if v is not None]
                if live and rng.random() < 0.3:
                    lo, hi = -(-min(live) // g) * g, (max(live) // g) * g
                    if lo <= hi:
                        flag = "w"
                lines.append(M.page(g, pv, flag, fo, dic if fo == "i" else None))
            vals_all.extend(v for pv in pages for v in pv)
        colvals.append(vals_all)
    for c in range(k):
        for r in range(n):
            if rng.random() < 0.06:
                v = rng.choice([x for x in colvals[c] if x is not None] or [0])
                lines.append("up %d %d %s" % (c, r, "-" if rng.random() < 0.15 else v))
    for r in range(n):
        if rng.random() < 0.05:
            lines.append("del %d" % r)
    for _ in range(rng.randint(1, 2)):
        lines.append("qry")
        for _ in range(rng.randint(1, 3)):
            c = rng.randrange(k)
            kind = rng.choice(KINDS)
            if kind in ("nn", "nu"):
                lines.append("prd %s %d" % (kind, c))
            else:
                vs = [x for x in colvals[c] if x is not None] or [0]
                lines.append("prd %s %d %d" % (kind, c, rng.choice(vs)))
        lines.append("prj " + " ".join(str(c) for c in rng.sample(range(k), rng.randint(1, k))))
        lines.append("end")
    return "\n".join(lines) + "\n"


def engine(files):
    d = pathlib.Path(tempfile.mkdtemp(prefix="hunt-"))
    for p in (R.TASK / "solution").glob("*.py"):
        shutil.copyfile(p, d / p.name)
    for fn, src in files.items():
        (d / fn).write_text(src, encoding="utf-8")
    return host.engine(host.tree(d))


def safe(eng, text):
    try:
        return eng.run(text)
    except Exception as ex:
        return repr(ex)


def shrink(ref, bad, text):
    best = text
    changed = True
    while changed:
        changed = False
        for cand in R.reductions(best):
            cand = cand.strip("\n") + "\n"
            try:
                want = ref.run(cand)
            except Exception:
                continue
            if safe(bad, cand) != want and len(cand) < len(best):
                best = cand
                changed = True
                break
    return best


def hunt(name, tries=20000, seed=1):
    files = R.previous() if name == "previous" else R.READINGS[name]
    ref = R._engine(R.TASK / "solution")
    bad = engine(files)
    rng = random.Random(seed)
    found = []
    for _ in range(tries):
        text = tiny(rng)
        try:
            want = ref.run(text)
        except Exception:
            continue
        if safe(bad, text) != want:
            found.append(shrink(ref, bad, text))
            if len(found) >= 6:
                break
    found.sort(key=len)
    return found


def main():
    names = [a for a in sys.argv[1:] if not a.startswith("--")]
    for name in names:
        got = hunt(name)
        print("==", name, "found", len(got))
        if got:
            print(got[0])


if __name__ == "__main__":
    main()
