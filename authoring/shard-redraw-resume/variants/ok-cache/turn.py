"""One attempted step."""

from rig import cut, draw, keep, say, scal


def once(run, st):
    start = st["seen"]
    wide = cut.width(run, st)
    lanes = draw.samples(run, st, start, wide)
    for r, ids in enumerate(lanes):
        say.feed(run, r, ids)
    st["seen"] = start + wide
    bad = any(one in st["nf"] for ids in lanes for one in ids)
    if bad:
        st["sc"], st["gt"] = scal.after_skip(st["sc"], st["gt"])
        say.skip(run, st["sc"])
        return
    st["done"] += 1
    st["sc"], st["gt"] = scal.after_step(st["sc"], st["gt"], run.grow)
    say.step(run, st["done"], st["sc"])
    keep.checkpoint(run, st)
