import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent
                       / "tasks" / "scan-chunk-pick" / "environment" / "app_src"))

from scn import parse  # noqa: E402


def load(text):
    return parse.load(text)


def segfp(seg):
    heads = tuple((ch.enc, ch.sum, tuple(ch.dic or ()),
                   tuple((pg.n, pg.nulls, pg.mn, pg.mx, pg.exact, pg.form, tuple(pg.toks))
                         for pg in ch.pages))
                  for col in seg.cols for ch in col)
    ups = tuple((c, r, repr(v)) for c, u in enumerate(seg.up) for r, v in sorted(u.items()))
    return repr((seg.g, seg.n, seg.k, heads, ups, tuple(sorted(seg.gone))))


def qfp(q):
    return repr((tuple((cd.kind, cd.c, cd.v) for cd in q.conds), tuple(q.cols)))


def fp(seg, history):
    """A query's key: the segment and every query of the file up to and including it, since
    what a query prints depends on what the queries before it read."""
    return repr((segfp(seg), tuple(qfp(q) for q in history)))
