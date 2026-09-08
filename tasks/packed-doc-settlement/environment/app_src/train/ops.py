import json

from train import again, box, fold, keep, lay, norm, pick, turn


def _f(x):
    if x == 0:
        x = 0.0
    return "%.6f" % x


def _step(run, out):
    c = run.cfg
    want = c["grp"] * c["wrk"] * c["seq"]
    run.took = min(want, run.feed.ready(c["lim"]))
    seqs = run.feed.cut(run.took, c["lim"]) if run.took else []
    mbs = lay.split(seqs, c["grp"], c["wrk"], c["seq"])
    run.nmb = len(mbs)
    for mb in mbs:
        pick.take(run, mb)
    done = pick.close(run)
    if turn.hold(run, done):
        out.append("nil")
        return
    parts = [fold.one(run, key) for key in done]
    loss, grad, gn = norm.step(run, parts)
    lr = turn.apply(run, grad)
    out.append("up %d %s %s %s %s" % (
        run.applied, _f(lr), _f(loss), _f(gn), " ".join(_f(x) for x in run.w)))
    for name in again.after(run, done, parts):
        out.append("rq " + name)


def ex(run, op, out):
    k = op[0]
    if box.setting(run, op):
        return
    if k == "doc":
        run.feed.add(op[1], int(op[2]), int(op[3]))
        out.append("ad " + op[1])
    elif k == "mdoc":
        run.feed.add(op[1], int(op[2]), -1)
        out.append("ad " + op[1])
    elif k == "resh":
        run.cfg["grp"] = int(op[1])
        run.cfg["wrk"] = int(op[2])
        run.cfg["seq"] = int(op[3])
        out.append("rs")
    elif k == "save":
        run.slot = json.loads(json.dumps(
            {"feed": run.feed.state(), "pol": keep.dump(run)}))
        out.append("ck %d" % run.applied)
    elif k == "load":
        if run.slot is not None:
            back = json.loads(json.dumps(run.slot))
            run.feed.restore(back["feed"])
            keep.load(run, back["pol"])
        out.append("ld %d" % run.applied)
    elif k == "emit":
        out.append("em " + " ".join(_f(x) for x in run.ema))
    elif k == "step":
        _step(run, out)
    else:
        raise ValueError(k)
