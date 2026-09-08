"""Requeueing a settled document that the step found hard.

The decision is per document, on that document's own loss at settlement, and the
count that the cap applies to travels along the chain of requeues rather than
belonging to the name: two occurrences of the same name that were declared apart
are separate documents and each gets the full allowance. The requeued occurrence
joins the tail of the pending stream, after everything already waiting, which is
what makes the packing that follows depend on this decision.
"""


def after(run, done, parts):
    gen = run.st.setdefault("gen", {})
    out = []
    for key, part in zip(done, parts):
        born = gen.pop(key, 0)
        if part[0] > run.cfg["thr"] and born < run.cfg["cap"]:
            name, n, t = run.feed.info(key)
            gen[run.feed.add(name, n, t)] = born + 1
            out.append(name)
    return out
