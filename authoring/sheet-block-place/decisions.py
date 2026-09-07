"""The graded decisions of the reference, as rows of features an agent can read.

tools/onelinecheck.py searches for the shortest exact rule over these. The point is not
that no question has a short rule - some genuinely do, and a decision that is short is
honest - but whether EVERY question does, because a task all of whose answers are one
comparison away is one a model writes cold.

Three questions are sampled, all of them things the reference decides on every sheet:

  placed         does this owner's rectangle stand, or is it refused
  loops          does this owner's value come out as a loop
  covered        does this cell show a block's entry rather than its own content

The features are what is on the table at the moment the question is asked, and no more.
"Is any cell of the rectangle already taken" is deliberately absent: answering that is the
work, and handing it over as a feature would measure nothing.
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
TASK = HERE.parents[1] / "tasks" / "sheet-block-place"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "environment" / "app_src"))

import gen  # noqa: E402

from sheet import addr, form, grid  # noqa: E402


def reference_state(text):
    """Replay a script under the reference policy and stop at the last command."""
    import shutil
    import tempfile

    home = pathlib.Path(tempfile.mkdtemp(prefix="sbp-dec-"))
    shutil.copytree(TASK / "environment" / "app_src", home / "app",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for f in ("val.py", "see.py", "lay.py", "memo.py"):
        shutil.copyfile(TASK / "solution" / f, home / "app" / "sheet" / f)
    return home


def rows_for(text, sheet_mod, lay, memo):
    sheet = sheet_mod.Sheet()
    for raw in text.split("\n"):
        toks = raw.split()
        if not toks:
            continue
        spot = addr.parse(toks[1])
        if toks[0] == "put":
            sheet.put(spot, " ".join(toks[2:]))
        else:
            sheet.clr(spot)
    st = memo.State(sheet)
    owners = sheet.owners()

    placed, loops, covered = [], [], []
    for o in owners:
        node = sheet.node(o)
        refs = form.refs(node)
        below = sum(1 for r in refs if r[0] >= o[0] and r[1] >= o[1])
        cone = sum(1 for p in owners if p[0] <= o[0] and p[1] <= o[1] and p != o)
        v = memo.value(st, o)
        loops.append(({
            "refs": len(refs),
            "refs_into_own_quadrant": below,
            "owners_before_it": sum(1 for p in owners if p < o),
            "owners_in_its_cone": cone,
            "row": o[0],
            "col": o[1],
        }, type(v) is tuple and v[:2] == ("err", "#cyc")))
        if grid.is_blk(v):
            h, w = v[1], v[2]
            span = addr.span(o, h, w)
            placed.append(({
                "height": h,
                "width": w,
                "row": o[0],
                "col": o[1],
                "held_cells_in_the_rectangle":
                    sum(1 for c in span if c != o and sheet.held(c)),
                "fits_the_sheet":
                    int(o[0] + h - 1 <= addr.ROWH and o[1] + w - 1 < addr.COLW),
                "owners_before_it": sum(1 for p in owners if p < o),
                "owners_in_its_cone": cone,
            }, lay.rect(st, o) is not None))
    for a in addr.walk():
        holder = None
        for o in lay.cone(st, a):
            got = lay.rect(st, o)
            if got and a[0] < o[0] + got[0] and a[1] < o[1] + got[1]:
                holder = o
                break
        if holder is None and not sheet.held(a):
            continue
        covered.append(({
            "row": a[0],
            "col": a[1],
            "holds_content": int(sheet.held(a)),
            "owners_in_its_cone": sum(1 for p in owners if p[0] <= a[0] and p[1] <= a[1]),
            "block_owners_in_its_cone": sum(
                1 for p in owners
                if p[0] <= a[0] and p[1] <= a[1] and grid.is_blk(memo.value(st, p))),
        }, holder is not None))
    return placed, loops, covered


def samples():
    home = reference_state("")
    sys.path.insert(0, str(home / "app"))
    for name in [n for n in sys.modules if n == "sheet" or n.startswith("sheet.")]:
        del sys.modules[name]
    from sheet import grid as sheet_mod, lay, memo

    placed, loops, covered = [], [], []
    for _, text in gen.batch("decisions", 8):
        a, b, c = rows_for(text, sheet_mod, lay, memo)
        placed.extend(a)
        loops.extend(b)
        covered.extend(c)
    return {"placed": placed, "loops": loops, "covered": covered}
