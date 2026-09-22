#!/usr/bin/env python3
"""The graded decisions this reference makes, as rows of features plus the choice.

Read by tools/onelinecheck.py, which searches for the shortest exact rule over the features.
The features are the numbers a submission can read at the moment it decides and nothing else:
the chunk header as the segment file writes it, the granularity, the survivors that chunk still
holds and how many of them carry an update in the column, whether it has already been read or its
dictionary charged, the dictionary's size, and the condition's kind, value and position. Nothing derived is offered - no interpolation, no score, no count of hits -
because those are the things the task is about and handing them over would measure the wrong
question.

Three questions are exported.

  chunk-verdict   What happens to this chunk under this condition: dropped unread, kept
                  unread, settled from its dictionary, or read.
  next-pair       Is this the pending pair the engine takes next?
  report-read     What the report pass does for this chunk: nothing, a consult, or a read.

Run it directly to see the rows.
"""
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "scan-chunk-pick"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import cases  # noqa: E402
import gen  # noqa: E402
import host  # noqa: E402

KIND = {"ge": 0, "le": 1, "eq": 2, "ne": 3, "nn": 4, "nu": 5}


def feats(seg, st, cd, ch, live):
    up = seg.up[ch.c]
    moved = sum(1 for r in range(ch.start, ch.start + ch.n) if st.alive[r] and r in up)
    return {
        "moved": moved,
        "held": live.count(st, ch.c, ch.j) - moved,
        "dk": len(ch.dic) if ch.dic is not None else 0,
        "n": ch.n,
        "u": ch.nulls,
        "mn": -1 if ch.mn is None else ch.mn,
        "mx": -1 if ch.mx is None else ch.mx,
        "ex": 1 if ch.exact else 0,
        "enc": 1 if ch.enc == "d" else 0,
        "lit": 1 if (ch.lit) else 0,
        "sv": live.count(st, ch.c, ch.j),
        "read": 1 if (ch.c, ch.j) in st.vals else 0,
        "charged": 1 if (ch.c, ch.j) in st.dread else 0,
        "kind": KIND[cd.kind],
        "v": cd.v,
        "g": seg.g,
        "pos": cd.pos,
        "j": ch.j,
    }


def _rows(app):
    sys.path.insert(0, str(app))
    import run_scan
    from scn import hdr, live, pick, proj, step

    verdict, pair, report = [], [], []
    plain_decide = step.decide
    plain_load = step.load

    def watched_decide(seg, q, st, cond, j, out):
        ch = seg.cols[cond.c][j]
        row = feats(seg, st, cond, ch, live)
        before = len(out.lines)
        plain_decide(seg, q, st, cond, j, out)
        marks = out.lines[before:]
        after = live.count(st, cond.c, j)
        if any(x.startswith("dc ") for x in marks):
            label = 3
        elif marks:
            label = 2
        elif after == 0 and row["sv"] > 0:
            label = 0
        else:
            label = 1
        verdict.append((row, label))

    def watched_pick(seg, q, st, out):
        while True:
            best = None
            here = []
            for cd in q.conds:
                for ch in seg.cols[cd.c]:
                    if ch.j in st.done[cd.pos]:
                        continue
                    have = live.count(st, cd.c, ch.j)
                    if have <= 0:
                        continue
                    b = pick.bound(seg, st, ch, cd)
                    if b > have:
                        b = have
                    here.append((b, cd, ch))
                    if best is None or b < best[0]:
                        best = (b, cd, ch.j)
            if best is None:
                return
            if len(here) > 1:
                for b, cd, ch in here:
                    pair.append((feats(seg, st, cd, ch, live),
                                 cd.pos == best[1].pos and ch.j == best[2]))
            watched_decide(seg, q, st, best[1], best[2], out)
            st.done[best[1].pos].add(best[2])

    def watched_proj(seg, q, st, rows, out):
        seen = []
        rowsof = {}
        for c in q.cols:
            if c in seen:
                continue
            seen.append(c)
            cd = next((x for x in q.conds if x.c == c), q.conds[0])
            for ch in seg.cols[c]:
                rowsof[(c, ch.j)] = feats(seg, st, cd, ch, live)
        label = {k: 0 for k in rowsof}
        plain_source = proj._source

        def watched_source(seg_, q_, st_, ch, out_):
            before = len(out_.lines)
            got = plain_source(seg_, q_, st_, ch, out_)
            marks = out_.lines[before:]
            key = (ch.c, ch.j)
            if label.get(key, 0) == 0:
                label[key] = 2 if any(x.startswith("dc ") for x in marks) else (1 if marks else 0)
            return got

        proj._source = watched_source
        try:
            plain_proj(seg, q, st, rows, out)
        finally:
            proj._source = plain_source
        for key, row in rowsof.items():
            report.append((row, label[key]))

    plain_proj = proj.run
    pick.run = watched_pick
    proj.run = watched_proj
    step.decide = watched_decide
    run_scan.pick = pick
    run_scan.proj = proj

    work = [cases.prog(n) for n in cases.ORDER]
    work += [l for f, n, l in gen.programs("decisions", 4) if f not in ("wide", "deep")]
    for lines in work:
        run_scan.run("\n".join(lines) + "\n")
    return verdict, pair, report


def thin(rows, cap=240):
    """Keep at most `cap` rows, spread evenly, so the depth-2 search finishes."""
    if len(rows) <= cap:
        return rows
    step = len(rows) / float(cap)
    return [rows[int(i * step)] for i in range(cap)]


def samples():
    room = pathlib.Path(tempfile.mkdtemp(prefix="dec-"))
    try:
        app = host.tree(TASK / "solution")
        verdict, pair, report = _rows(app)
        return {"chunk-verdict": thin(verdict), "next-pair": thin(pair),
                "report-read": thin(report)}
    finally:
        shutil.rmtree(room, ignore_errors=True)


if __name__ == "__main__":
    for name, rows in sorted(samples().items()):
        print("%s: %d rows" % (name, len(rows)))
        for feat, label in rows[:2]:
            print("   ", feat, "->", label)
