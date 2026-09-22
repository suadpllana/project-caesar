"""The graded decisions as rows of features the agent can read off a journal before solving it.

`tools/onelinecheck.py` searches for the shortest exact rule over these. One row per lost span,
from the journal text alone: the configuration, where the span sits, how many digests and audits
it lists, and - where the nearest audit on each side is reached without crossing another span -
the totals the span must account for, which is the first thing anyone computes. `lost` is their
sum, the exact number of entries the span held; it is offered on purpose, because it is the
obvious derived quantity and a rule over it would be the short answer the task must not have.

The labels are what the reference prints for the span: whether it prints without a `?` line,
how many entries it restores, and for the spans that do part, whether the end is a candidate and
how many candidates there are.

    python3 authoring/journal-gap-mend/decisions.py        print the rows' sizes
"""
import pathlib
import sys

sys.dont_write_bytecode = True  # never leave __pycache__ inside the bundle

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import readings  # noqa: E402

readings._sealed()
import gen  # noqa: E402

sys.path.insert(0, str(readings.SHIPPED))
from jl import read  # noqa: E402

REFERENCE = str(readings.TASK / "solution")


def _adds(rec):
    """What one surviving entry adds to (grants, requests, releases, heartbeats)."""
    if rec.kind == "acq":
        return (int(rec.out == "grant"), 1, 0, 0)
    if rec.kind == "rel":
        return (int(rec.out == "pass"), 0, 1, 0)
    return (0, 0, 0, 1)


def _plus(a, b, sign=1):
    return tuple(x + sign * y for x, y in zip(a, b))


def _before(items, at):
    """Totals at the start of the span at `at`, if reached from an audit or the start of the
    journal without crossing another span; else None."""
    tot = (0, 0, 0, 0)
    for rec in reversed(items[:at]):
        if isinstance(rec, read.Gap):
            return None
        if isinstance(rec, read.Aud):
            return _plus((rec.grants, rec.asks, rec.rels, rec.beats), tot)
        if isinstance(rec, read.Entry):
            tot = _plus(tot, _adds(rec))
    return tot


def _after(items, at):
    """Totals the next audit after the span shows, less what the surviving entries between add;
    None if another span comes first. Also the number of surviving entries in between."""
    tot = (0, 0, 0, 0)
    seen = 0
    for rec in items[at + 1:]:
        if isinstance(rec, read.Gap):
            return None, seen
        if isinstance(rec, read.Aud):
            return _plus((rec.grants, rec.asks, rec.rels, rec.beats), tot, -1), seen
        if isinstance(rec, read.Entry):
            tot = _plus(tot, _adds(rec))
            seen += 1
    return None, seen


def _spans(lines):
    out = []
    for line in lines:
        if line.startswith("gap "):
            out.append({"restored": 0, "cands": None})
        elif line.startswith("? "):
            out[-1]["cands"] = line[2:].split(" | ")
        else:
            out[-1]["restored"] += 1
    return out


def samples(seed="decisions", per=12):
    determined, restored, dash, width = [], [], [], []
    for _fam, _name, text in gen.programs(seed, per):
        journal = read.parse(text)
        items = list(journal.items)
        printed = _spans(readings.run(REFERENCE, text))
        gaps = [i for i, rec in enumerate(items) if isinstance(rec, read.Gap)]
        entries = [i for i, rec in enumerate(items) if isinstance(rec, read.Entry)]
        for no, (at, out) in enumerate(zip(gaps, printed), 1):
            marks = items[at].marks
            start = _before(items, at)
            end, between = _after(items, at)
            if start is not None and end is not None:
                need = _plus(end, start, -1)
            else:
                need = (-1, -1, -1, -1)
            row = {
                "locks": journal.locks,
                "sessions": journal.sessions,
                "period": journal.period,
                "span_no": no,
                "spans": len(gaps),
                "digs_in": sum(isinstance(m, read.Dig) for m in marks),
                "auds_in": sum(isinstance(m, read.Aud) for m in marks),
                "entries_before": sum(1 for i in entries if i < at),
                "entries_after": sum(1 for i in entries if i > at),
                "entries_to_audit": between,
                "need_grants": need[0],
                "need_requests": need[1],
                "need_releases": need[2],
                "need_beats": need[3],
                "lost": -1 if need[1] < 0 else need[1] + need[2] + need[3],
            }
            determined.append((row, out["cands"] is None))
            restored.append((row, out["restored"]))
            if out["cands"] is not None:
                dash.append((row, "-" in out["cands"]))
                width.append((row, len(out["cands"])))
    return {
        "span prints in full": determined,
        "entries restored": restored,
        "end is a candidate": dash,
        "number of candidates": width,
    }


if __name__ == "__main__":
    for name, rows in samples().items():
        print("%-24s %d rows" % (name, len(rows)))
