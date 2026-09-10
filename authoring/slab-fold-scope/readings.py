"""Does the enumerated set separate the wrong readings a solver will actually have?

Per-rule coverage on paper is not coverage: `cut-keeps-empty` was written as a wrong reading of
this task and turned out to be no reading at all - it scored 1 in the container because a slab
with no keys is invisible, so the rule it broke was a sentence in the brief with nothing behind
it. That rule is gone. `fold-cached-minmax` scored 1 for the opposite reason: the reading was
real and the two unmixing cases could not tell it apart, because after a second attempt the
reach came out the same set either way. Both were found by running the reading, not by reading
the case list.

The readings come from `emit.py`, so the cheats that ship and the readings measured here are
the same files and cannot drift apart.

    python tools/readingcheck.py slab-fold-scope [rounds]
"""
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
import cases  # noqa: E402
import gen  # noqa: E402

REFERENCE = str(lab.TASK / "solution")

# Every semantic reading emit.py knows how to build. The slow families, the forgery and the
# isolation probes are not readings of the rules and are not measured here.
BUILDERS = (
    emit.put_beside, emit.put_counts_all, emit.cut_width, emit.fold_all_inside,
    emit.fold_no_floor, emit.fold_overlap, emit.fold_restamp, emit.fold_slab_stamp,
    emit.fold_cached_minmax, emit.fold_own_in_reach, emit.mixed_ignore,
    emit.mixed_any_overlap, emit.mixed_whole_bucket, emit.mixed_keep,
    emit.mixed_no_renumber, emit.mixed_only_fold, emit.mixed_prescan,
    emit.parts_folds_last, emit.base_at_push, emit.number_always,
)

for _build in BUILDERS:
    _build()
READINGS = dict(emit.BUILT)

_TREES = {}


def run(policy, text):
    """Drive one program under one directory of the six files."""
    here = _TREES.get(str(policy))
    if here is None:
        here = _TREES[str(policy)] = lab.tree(policy)
    room = pathlib.Path(tempfile.mkdtemp(prefix="sfs-read-"))
    prog = room / "p.txt"
    prog.write_text(text.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
    try:
        return lab.run(here, prog, timeout=120)
    except RuntimeError as exc:
        return ["RAISED", str(exc).splitlines()[-1]]


def enumerated():
    return [(name, "\n".join(cases.ops(name))) for name in cases.ORDER]


def generated(n):
    out = []
    per = max(1, n // 10)
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(per):
            name = "%s-%d" % (fam, i)
            out.append((name, "\n".join(gen.one(fam, "reading/%s" % name))))
    return out


def reductions(text):
    """Structure-aware shrinking: a program is lines, but a proposal is a group of them.

    Dropping a `plan` line alone leaves its parts and its push orphaned and the program stops
    meaning anything, so the shrinker plateaus. These candidates drop a whole proposal, or one
    part of one, or one query.
    """
    lines = text.split("\n")
    tags = []
    for line in lines:
        w = line.split()
        if w and w[0] in ("plan", "bulk") and w[1] not in tags:
            tags.append(w[1])
    for tag in tags:
        yield "\n".join(x for x in lines
                        if not (x.split() and len(x.split()) > 1 and x.split()[1] == tag))
    for i in range(len(lines) - 1, -1, -1):
        w = lines[i].split()
        if w and w[0] in ("put", "cut", "fold", "at", "rows"):
            yield "\n".join(lines[:i] + lines[i + 1:])
    for i in range(len(lines) - 1, -1, -1):
        yield "\n".join(lines[:i] + lines[i + 1:])
