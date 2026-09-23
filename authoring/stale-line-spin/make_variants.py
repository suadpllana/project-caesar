"""Build the two correct variants that must score 1 (authoring/stale-line-spin/variants/).

  ok-model   the sealed model's own clock, written apart from solution/, behind the frozen
             interface: clock.py is tests/seal/model.py followed by an adapter from the shipped
             parser's instructions to the model's tuples and back to the blocks say.py reads.
             The other five files are left to the pristine tree; this clock uses none of them.
  ok-edges   the reference with a different fast path: it never works out when a line cached
             at a lane's start is pushed out. A lane is refused while any cached line lies in
             a sum's path, while a cached spinner shares its multiprocessor with a cached sum,
             or while two sums share a line; those cycles are stepped. Exact, and slower only
             by the few cycles at the start of each tile.

Every edit is asserted to fire exactly once (CLAUDE.md, reach-pair-sweep), and each variant is
written with newline="\\n" and checked for carriage returns.

usage: python3 authoring/stale-line-spin/make_variants.py [--check]
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "stale-line-spin"
OUT = HERE / "variants"
PARTS = ("line.py", "mem.py", "place.py", "turn.py", "step.py", "clock.py")

ADAPTER = '''

# --- the frozen interface -------------------------------------------------------------------

from sim import load as _load  # noqa: E402


def _value(x):
    kind, v = x
    if kind == "r":
        return ("r", v)
    if kind == "k":
        return ("i", v)
    return ("s", kind)


def _ins(ins):
    op = ins.op
    if op == "mov":
        return ("mov", ins.rd, _value(ins.a))
    if op in ARITH:
        return (op, ins.rd, _value(ins.a), _value(ins.b))
    if op == "mod":
        return ("mod", ins.rd, _value(ins.a), ins.b[1])
    if op in ("ld.ca", "ld.cg"):
        return (op, ins.rd, ins.at)
    if op == "st":
        return ("st", ins.at, _value(ins.a))
    if op == "atom.add":
        return ("atom.add", ins.rd, ins.at, _value(ins.a))
    if op in ("fence", "exit"):
        return (op,)
    if op in SPINS:
        return (op, ins.rd, ins.at, ins.cmp, _value(ins.b))
    if op in SUMS:
        return (op, ins.rd, ins.at, ins.b[1])
    if op in ("work", "out"):
        return (op, _value(ins.a))
    if op == "bra":
        return ("bra", ins.to)
    return (op, _value(ins.a), ins.to)


def run(launch):
    code = [_ins(ins) for ins in launch.code]
    m = Machine((launch.sms, launch.slots, launch.lines), launch.grid, launch.mem, code)
    hang = m.run()
    blocks = []
    for n in range(launch.grid):
        b = _load.Blk(n)
        b.sm, b.at, b.end = m.sm[n], m.placed[n], m.ended[n]
        b.outs, b.pc, b.reg = m.outs[n], m.pc[n], m.reg[n]
        blocks.append(b)
    return blocks, hang, (launch.grid - m.nxt if hang is not None else 0), m.gm
'''

EDGES = (
    # a cached line anywhere in a sum's path: step, do not compute when it goes
    ('''    if old and sums:
        ordered = sorted(old)
        for q, lo, hi in sums:
            i = bisect_left(ordered, lo)
            while i < len(ordered) and ordered[i] < hi:
                ln = ordered[i]
                u = q + (ln - lo) * k
                if u >= end:
                    break
                if fills(u) < room + where[ln] + 1:
                    end = u
                    break
                i += 1
''',
     '''    if old and sums:
        ordered = sorted(old)
        for q, lo, hi in sums:
            i = bisect_left(ordered, lo)
            if i < len(ordered) and ordered[i] < hi:
                return None
'''),
    # two sums sharing a line: step
    ('''            ub = qb + (first - lb) * k
            if qa + (first - la) * k < ub:
                end = min(end, ub)
''',
     '''            return None
'''),
    # a cached spinner next to a cached sum: step
    ('''            if p is None or test(cache.rows[ln][a % LW], want):
                end = min(end, q)
            elif m:
                need = room + p + 1
                end = min(end, q + max(0, -(-(need - ahead[q]) // m)) * k)
''',
     '''            if p is None or test(cache.rows[ln][a % LW], want) or m:
                end = min(end, q)
'''),
)


def texts():
    out = {}
    model = (TASK / "tests" / "seal" / "model.py").read_text(encoding="utf-8")
    out["ok-model/clock.py"] = model + ADAPTER
    for part in PARTS:
        src = (TASK / "solution" / part).read_text(encoding="utf-8")
        if part == "clock.py":
            for old, new in EDGES:
                n = src.count(old)
                if n != 1:
                    raise SystemExit("ok-edges: an edit fired %d times, not once:\n%s" % (n, old))
                src = src.replace(old, new)
        out["ok-edges/" + part] = src
    return out


def main():
    check = "--check" in sys.argv
    bad = 0
    for rel, text in sorted(texts().items()):
        assert "\r" not in text and text.isascii(), rel
        path = OUT / rel
        if check:
            if not path.is_file() or path.read_text(encoding="utf-8") != text:
                print("stale", rel)
                bad += 1
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        assert b"\r" not in path.read_bytes()
    print("%s %d variant files" % ("checked" if check else "wrote", len(texts())))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
