"""The graded decisions as rows of features read off the written tree.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
primitives an agent has once it has the written structure in hand - whether a definition is
written at the path, what kind of marker stands nearest above it, whether the path the marker
redirects to has a definition written, how many definitions are written under the path and
under its image. Nothing derived is offered, because the derivation is the task.

The verdict to want is that at least one graded quantity has no short rule. Two should not:
whether a path shows a definition, because a chain of ties redirects more than once and a
mask stands between; and how many paths show under a prefix, because what the image counts is
reduced by what is written under the prefix, and a written child can itself be a region.

    python3 authoring/fix-layered-config/decisions.py
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
TESTS = HERE.parents[1] / "tasks" / "fix-layered-config" / "tests"
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(TESTS / "seal"))

import gen  # noqa: E402
import model  # noqa: E402

KIND = {None: 0, "cut": 1, "tie": 2, "copy": 3}


def _kind(mark):
    if mark is None:
        return 0
    m = mark.m
    return KIND[m] if m == "cut" else KIND[m[0]]


def _written_under(node):
    if node is None:
        return 0
    return int(node.d is not None) + sum(_written_under(k) for k in node.k.values())


def _image(root, mark, taken, segs):
    if mark is None or mark.m == "cut":
        return None, None
    m = mark.m
    rest = segs[taken:]
    if m[0] == "tie":
        return root, m[1] + rest
    return m[1], m[2] + rest


def features(root, segs):
    node = model.local(root, segs)
    mark, taken = model.nearest(root, segs)
    if node is not None and node.m is not None:
        mark, taken = node, len(segs)
    iroot, ipath = _image(root, mark, taken, segs)
    inode = None if iroot is None else model.local(iroot, ipath)
    imark, _t = (None, 0) if iroot is None else model.nearest(iroot, ipath)
    return {
        "written_here": int(node is not None and node.d is not None),
        "marker_kind": _kind(mark),
        "marker_depth": taken,
        "image_written": int(inode is not None and inode.d is not None),
        "image_marker_kind": _kind(imark),
        "depth": len(segs),
        "written_under": _written_under(node),
        "image_written_under": _written_under(inode),
        "local_kids": 0 if node is None else len(node.k),
    }


def samples():
    show_rows, count_rows = [], []
    for name, fn in gen.FAMS:
        if not name.startswith("tie"):
            continue
        for i in range(6):
            text = fn(random.Random("decisions/%s/%d" % (name, i)))
            layers, asks = model.parse(text)
            run = model.Run(layers)
            for kind, path, _shown, named in asks:
                view = run.view[run.top if named is None else named]
                row = features(view, path)
                if kind == "ask":
                    show_rows.append((row, model.shows(view, path)))
                else:
                    count_rows.append((row, run.sizes.count(view, path, model.BOUND - len(path))))
    return {"shows": show_rows, "count": count_rows}


if __name__ == "__main__":
    got = samples()
    for k, v in sorted(got.items()):
        print("%-8s %5d rows, %d distinct labels" % (k, len(v), len({y for _, y in v})))
