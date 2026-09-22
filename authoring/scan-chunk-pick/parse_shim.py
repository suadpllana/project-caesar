import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent
                       / "tasks" / "scan-chunk-pick" / "environment" / "app_src"))

from scn import parse  # noqa: E402


def load(text):
    return parse.load(text)


def fp(seg, q):
    heads = tuple((ch.n, ch.nulls, ch.mn, ch.mx, ch.exact, ch.enc)
                  for col in seg.cols for ch in col)
    return repr((seg.g, seg.n, seg.k, heads,
                 tuple((cd.kind, cd.c, cd.v) for cd in q.conds), tuple(q.cols)))
