"""Build the three correct-but-infeasible readings from the reference, for timing.

Each keeps the semantics exactly and changes only what it walks:
  fam    the family test walks the box's slots instead of reading a tally
  all    the sweep reconsiders every waiting request in the store after every change
  ring   the stuck check runs after every operation over every waiting job
"""
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent
REF = ROOT.parent.parent / "tasks" / "claim-cover-lift" / "solution"


def swap(path, old, new):
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit("pattern hit %d times in %s" % (text.count(old), path))
    path.write_text(text.replace(old, new), encoding="utf-8", newline="\n")


def base(name):
    out = ROOT / "slow" / name
    if out.is_dir():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for part in ("book", "line", "fit", "lift", "snarl", "door"):
        shutil.copy(REF / (part + ".py"), out / (part + ".py"))
    return out


def fam():
    out = base("fam")
    swap(out / "book.py",
         'one = st.by_node[node] = {"h": {}, "s": {}}',
         'one = st.by_node[node] = {"h": {}, "s": {}, "k": set()}')
    swap(out / "book.py",
         '    sum_ = cell(st, box)["s"].setdefault(job, [0, 0])\n',
         '    sum_ = cell(st, box)["s"].setdefault(job, [0, 0])\n'
         '    cell(st, box)["k"].add(node)\n')
    swap(out / "book.py",
         '        if sum_[0] == 0 and sum_[1] == 0:\n'
         '            del st.by_node[box]["s"][job]\n',
         '        if sum_[0] == 0 and sum_[1] == 0:\n'
         '            del st.by_node[box]["s"][job]\n'
         '        if not one["h"]:\n'
         '            st.by_node[box]["k"].discard(node)\n')
    swap(out / "book.py",
         'def under(st, box):\n'
         '    one = st.by_node.get(box)\n'
         '    return one["s"] if one else {}\n',
         'def kids(st, box):\n'
         '    one = st.by_node.get(box)\n'
         '    return list(one["k"]) if one else []\n')
    swap(out / "fit.py",
         '        for other, sum_ in book.under(st, box).items():\n'
         '            if other != job and (mode == "w" or sum_[1] > 0):\n'
         '                out.add(other)\n',
         '        for kid in book.kids(st, box):\n'
         '            for other, got in book.at(st, kid).items():\n'
         '                if other != job and any(clash(mode, m) for m in got):\n'
         '                    out.add(other)\n')


def every():
    out = base("all")
    swap(out / "door.py",
         'def sweep(st, hit):\n'
         '    live = set(hit)\n'
         '    while live:\n'
         '        best = None\n'
         '        for box in list(live):\n'
         '            cand = first(st, box)\n'
         '            if cand is None:\n'
         '                live.discard(box)\n'
         '            elif best is None or cand["seq"] < best["seq"]:\n'
         '                best = cand\n'
         '        if best is None:\n'
         '            return\n'
         '        line.pull(st, best)\n'
         '        live.add(boxof(best["node"]))\n'
         '        live |= give(st, best)\n',
         'def sweep(st, hit):\n'
         '    while True:\n'
         '        best = None\n'
         '        for box in sorted(st.pend):\n'
         '            cand = first(st, box)\n'
         '            if cand is not None and (best is None or cand["seq"] < best["seq"]):\n'
         '                best = cand\n'
         '        if best is None:\n'
         '            return\n'
         '        line.pull(st, best)\n'
         '        give(st, best)\n')


def ring():
    out = base("ring")
    swap(out / "door.py",
         'def settle(st, job):\n'
         '    while True:\n'
         '        bad = snarl.ring(st, job)\n'
         '        if not bad:\n'
         '            return\n'
         '        sweep(st, snarl.kill(st, snarl.pick(st, bad)))\n',
         'def settle(st, job):\n'
         '    while True:\n'
         '        bad = set()\n'
         '        for one in sorted(st.by_job):\n'
         '            bad |= snarl.ring(st, one)\n'
         '        if not bad:\n'
         '            return\n'
         '        sweep(st, snarl.kill(st, snarl.pick(st, bad)))\n')
    swap(out / "door.py",
         '    if book.sub(st, job, node) is not None:\n'
         '        tell.free(st, job, node)\n'
         '        sweep(st, {boxof(node)})\n',
         '    if book.sub(st, job, node) is not None:\n'
         '        tell.free(st, job, node)\n'
         '        sweep(st, {boxof(node)})\n'
         '        settle(st, job)\n')
    swap(out / "door.py",
         '    else:\n'
         '        sweep(st, give(st, {"job": job, "node": node, "mode": mode, "trig": trig}))\n',
         '    else:\n'
         '        sweep(st, give(st, {"job": job, "node": node, "mode": mode, "trig": trig}))\n'
         '        settle(st, job)\n')


if __name__ == "__main__":
    fam()
    every()
    ring()
    print("built", ", ".join(sorted(p.name for p in (ROOT / "slow").iterdir())))
