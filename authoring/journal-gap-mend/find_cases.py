"""Search small journals for the hand cases: for each wrong reading, the shortest journal
that it gets wrong, preferring one that no other reading gets wrong (so a failure names the
rule); and for the ordinary side of each fence, journals whose right answer has a given shape.

Search, not choice (CLAUDE.md, reach-pair-sweep): the case that decides a reading is found by
running every reading on every candidate. Writes nothing into the task folder; prints the
chosen journals and saves them to a scratch JSON for make_cases.py.

    python authoring/journal-gap-mend/find_cases.py <journals> <out.json> [workers]
"""
import json
import multiprocessing as mp
import random
import sys

sys.dont_write_bytecode = True  # never leave __pycache__ inside the bundle

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import readings  # noqa: E402

readings._sealed()
import gen  # noqa: E402
import model  # noqa: E402


def small(rng):
    """A small journal of random shape, from the generator's own building blocks."""
    cfg = (rng.randint(1, 3), rng.randint(2, 4), rng.randint(1, 3))
    lean = rng.choice([None, ("again", "keep"), ("wait", "pass"), ("grant", "free")])
    wb = rng.choice([1, 2, 3])
    ev = gen.run(rng, *cfg, rng.randint(6, 14), gen.weighted(5, 4, wb, lean))
    n = len(ev)
    if n < 4:
        return None
    lo = 0 if rng.random() < 0.08 else 1
    spans = gen.pick_spans(rng, n, rng.randint(1, 3), lo, rng.choice([2, 3, 4]))
    if not spans:
        return None
    rate = rng.choice([0.0, 0.15, 0.3])
    auds = gen.some_auds(rng, n, rate, spans)
    if rng.random() < 0.35:
        s0, s1 = rng.choice(spans)
        auds.add(rng.randint(s0, s1))
    return gen.text_of(cfg, ev, spans, auds)


def shape(lines):
    """Per span: ('full'|'partial'|'none'|'empty', restored count, has dash)."""
    out = []
    cur = None
    for line in lines:
        if line.startswith("gap"):
            if cur is not None:
                out.append(tuple(cur))
            cur = ["empty", 0, False]
        elif line.startswith("?"):
            cur[0] = "partial" if cur[1] else "none"
            cur[2] = "-" in line.split(" | ")[0].split()
            cur[2] = " - " in (" " + line[2:] + " ").replace(" | ", "  ")
        else:
            cur[1] += 1
            cur[0] = "full"
    if cur is not None:
        out.append(tuple(cur))
    return out


class Slow(BaseException):
    pass


def _alarm(*_a):
    raise Slow()


def _limits():
    import resource
    import signal
    resource.setrlimit(resource.RLIMIT_AS, (2500 * 1024 * 1024, 2500 * 1024 * 1024))
    signal.signal(signal.SIGALRM, _alarm)


def _timed(fn, *args):
    import signal
    signal.alarm(3)
    try:
        return fn(*args)
    finally:
        signal.alarm(0)


def judge(seed):
    """(text, want, moved) for one small journal, or None when it is unusable. A journal on
    which any solver runs past 3 s, or out of memory, is skipped rather than counted: a
    timeout is not a difference in what is printed."""
    rng = random.Random(seed)
    text = small(rng)
    if text is None:
        return None
    try:
        want = tuple(_timed(model.expect, text))
        ref = _timed(readings.run, readings.REFERENCE, text)
        if ref != want:
            return ("MISMATCH", seed, text, want, ref)
        moved = []
        for name, files in readings.READINGS.items():
            if _timed(readings.run, _pol(name, files), text) != ref:
                moved.append(name)
    except (Slow, MemoryError):
        return None
    return (text, want, moved)


_pols = {}


def _pol(name, files):
    if name not in _pols:
        import pathlib
        import shutil
        import tempfile
        d = pathlib.Path(tempfile.mkdtemp(prefix="jgm-reading-"))
        for p in pathlib.Path(readings.REFERENCE).glob("*.py"):
            shutil.copy(p, d / p.name)
        for fn, src in files.items():
            (d / fn).write_text(src, encoding="utf-8")
        _pols[name] = str(d)
    return _pols[name]


def main():
    total = int(sys.argv[1])
    out = sys.argv[2]
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    best = {}
    fences = {}
    seen = 0
    moved_count = {k: 0 for k in readings.READINGS}
    with mp.Pool(workers, initializer=_limits, maxtasksperchild=150) as pool:
        for res in pool.imap_unordered(judge, range(total), chunksize=10):
            if res is None:
                continue
            if res[0] == "MISMATCH":
                print("REFERENCE DISAGREES WITH MODEL on seed", res[1])
                print(res[2])
                print(res[3])
                print(res[4])
                sys.exit(1)
            text, want, moved = res
            seen += 1
            size = len(text.splitlines())
            for name in moved:
                moved_count[name] += 1
                width = sum(len(w.split(" | ")) for w in want if w.startswith("? "))
                key = (len(moved) > 1, len(moved), size + len(want) + width // 2)
                if name not in best or key < best[name][0]:
                    best[name] = (key, text, list(want), moved)
            tags = set()
            shp = shape(want)
            for i, (kind, nres, dash) in enumerate(shp):
                tags.add(kind + ("-dash" if dash else ""))
                if kind == "full" and nres >= 3:
                    tags.add("full-long")
            if len(shp) >= 3:
                tags.add("three-spans")
            for line in want:
                if line.startswith("? "):
                    kinds = {c.split()[0] for c in line[2:].split(" | ")}
                    if len(kinds) >= 3:
                        tags.add("text-order")
            lines_ = text.splitlines()
            if any(a.startswith("dig") and b == "gap" for a, b in zip(lines_, lines_[1:])):
                tags.add("digest-before-gap")
            width = sum(len(w.split(" | ")) for w in want if w.startswith("? "))
            for tag in tags:
                key = (size + width // 2,)
                if tag not in fences or key < fences[tag][0]:
                    fences[tag] = (key, text, list(want), moved)
    print("judged %d journals" % seen)
    for name in readings.READINGS:
        print("  %-20s moves %5.1f%%" % (name, 100.0 * moved_count[name] / max(seen, 1)))
    json.dump({"readings": {k: v[1:] for k, v in best.items()},
               "fences": {k: v[1:] for k, v in fences.items()}},
              open(out, "w", encoding="utf-8", newline="\n"), indent=1)
    for name in sorted(best):
        key, text, want, moved = best[name]
        print("\n== %s (alone=%s, %d lines, also moves %s)" % (name, not key[0], key[2],
                                                               [m for m in moved if m != name]))
        print(text)
        print("->", want)
    for tag in sorted(fences):
        key, text, want, moved = fences[tag]
        print("\n== fence %s (%d lines, moves %s)" % (tag, key[0], moved))
        print(text)
        print("->", want)


if __name__ == "__main__":
    main()
