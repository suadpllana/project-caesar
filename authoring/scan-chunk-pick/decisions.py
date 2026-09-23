#!/usr/bin/env python3
"""The graded decisions this reference makes, as rows of features plus the choice.

Read by tools/onelinecheck.py, which searches for the shortest exact rule over the features.
The features are the numbers a submission can read at the moment it decides and nothing else:
the page headers as the segment file writes them (summed or bounded over a chunk for the choice
and the chunk verdict, one page for the report pass), the granularity, the live rows and how many
carry an update in the column, how many pages have been read and whether the dictionary has been
charged, the dictionary's size, and the condition's kind, value and position. Nothing derived is offered - no interpolation, no score, no count of hits -
because those are the things the task is about and handing them over would measure the wrong
question.

Three questions are exported.

  chunk-verdict   What happens to this chunk under this condition: dropped unread, kept
                  unread, settled from its dictionary, or read.
  next-pair       Is this the pending pair the engine takes next?
  report-read     What the report pass does for this page: nothing, a consult of its chunk's
                  dictionary, or a read.

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
    """Chunk-level raw fields: what the page headers say, summed or bounded, and the state."""
    up = seg.up[ch.c]
    moved = 0
    for r in range(ch.start, ch.start + ch.n):
        if st.alive[r] and r in up:
            moved += 1
    mns = [pg.mn for pg in ch.pages if pg.mn is not None]
    mxs = [pg.mx for pg in ch.pages if pg.mx is not None]
    return {
        "moved": moved,
        "held": live.count(st, ch.c, ch.j) - moved,
        "dk": len(ch.dic) if ch.dic is not None else 0,
        "n": ch.n,
        "u": sum(pg.nulls for pg in ch.pages),
        "mn": min(mns) if mns else -1,
        "mx": max(mxs) if mxs else -1,
        "ex": sum(1 for pg in ch.pages if pg.exact),
        "pages": len(ch.pages),
        "ipages": sum(1 for pg in ch.pages if pg.form == "i"),
        "sv": live.count(st, ch.c, ch.j),
        "read": sum(1 for pg in ch.pages if (pg.c, pg.j, pg.p) in st.mem.vals),
        "charged": 1 if (ch.c, ch.j) in st.mem.dread else 0,
        "kind": KIND[cd.kind],
        "v": cd.v,
        "g": seg.g,
        "pos": cd.pos,
        "j": ch.j,
    }


def page_feats(seg, st, ch, pg, live):
    """Page-level raw fields for the report pass, with the chunk's own raw fields beside them."""
    held = live.held(st, pg.c, pg)
    up = seg.up[pg.c]
    moved = [r for r in range(pg.start, pg.start + pg.n) if st.alive[r] and r in up]
    return {
        "held": len(held),
        "moved": len(moved),
        "n": pg.n,
        "u": pg.nulls,
        "mn": -1 if pg.mn is None else pg.mn,
        "mx": -1 if pg.mx is None else pg.mx,
        "ex": 1 if pg.exact else 0,
        "chs": ch.sum,
        "pages": len(ch.pages),
        "form": 1 if pg.form == "i" else 0,
        "dk": len(ch.dic) if ch.dic is not None else 0,
        "read": 1 if (pg.c, pg.j, pg.p) in st.mem.vals else 0,
        "charged": 1 if (ch.c, ch.j) in st.mem.dread else 0,
        "g": seg.g,
        "p": pg.p,
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
                    if ch.j in st.done[cd.pos] or not live.pending(st, cd, ch.j):
                        continue
                    have = live.count(st, cd.c, ch.j)
                    b = st.cnt[(cd.pos, ch.j)]
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
            st.dirty.clear()

    def watched_proj(seg, q, st, rows, out):
        seen = []
        rowsof = {}
        for c in q.cols:
            if c in seen:
                continue
            seen.append(c)
            for ch in seg.cols[c]:
                for pg in ch.pages:
                    rowsof[(c, ch.j, pg.p)] = page_feats(seg, st, ch, pg, live)
        label = {k: 0 for k in rowsof}
        plain_chunk = proj._chunk

        def watched_chunk(seg_, q_, st_, ch, out_):
            before = len(out_.lines)
            got = plain_chunk(seg_, q_, st_, ch, out_)
            for x in out_.lines[before:]:
                f = x.split()
                if f[0] == "dc":
                    key = (int(f[1]), int(f[2]), int(f[3]))
                    if label.get(key, 0) == 0:
                        label[key] = 2
                elif f[0] == "rd":
                    for pg in ch.pages:
                        key = (ch.c, ch.j, pg.p)
                        if pg.form == "i" and label.get(key, 0) == 0:
                            label[key] = 1
            return got

        proj._chunk = watched_chunk
        try:
            plain_proj(seg, q, st, rows, out)
        finally:
            proj._chunk = plain_chunk
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
