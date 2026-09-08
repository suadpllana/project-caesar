"""The same variant's emission: the model's greedy loop over flat records."""
from mrg.book import ROOT, at, cut, emit, flatten, glue, inside, kids, pth, small, taken  # noqa: F401


def plan(cur, tgt, m, fold):
    return [tuple(op) for op in emit(flatten(cur), flatten(tgt), m, fold)]
