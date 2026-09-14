"""One attempted step."""

from rig import cut, draw, keep, say, scal


def once(run, st):
    got = draw.window(run, st, cut.width(run, st))
    for r, ids in enumerate(draw.deal(run, st, got)):
        say.feed(run, r, ids)
    if any(one in st["nf"] for one in got):
        st["sc"], st["gt"] = scal.after_skip(st["sc"], st["gt"])
        say.skip(run, st["sc"])
        return
    st["done"] += 1
    st["sc"], st["gt"] = scal.after_step(st["sc"], st["gt"], run.grow)
    say.step(run, st["done"], st["sc"])
    keep.checkpoint(run, st)
