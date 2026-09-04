"""Write a policy directory from the reference plus declared overrides."""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REF = os.path.join(ROOT, "solution")


def swap(text, head, tail, fresh):
    at = text.index(head)
    end = len(text) if tail is None else text.index(tail, at)
    if text[at:end] == fresh:
        raise SystemExit("swap at %r is a no-op" % head)
    return text[:at] + fresh + text[end:]


def build(where, overrides):
    if not os.path.isdir(where):
        os.makedirs(where)
    bodies = {}
    for leaf in sorted(os.listdir(REF)):
        if leaf.endswith(".py"):
            bodies[leaf] = open(os.path.join(REF, leaf)).read()
    for leaf, head, tail, fresh in overrides:
        bodies[leaf] = swap(bodies[leaf], head, tail, fresh)
    for leaf in sorted(bodies):
        with open(os.path.join(where, leaf), "w", newline="\n") as fh:
            fh.write(bodies[leaf])
    return where
