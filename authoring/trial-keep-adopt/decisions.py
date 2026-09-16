"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
structural ones the tree exposes at the moment each decision is made: for a field being checked,
how many reads its last evaluation recorded, whether it is a branching form, how deep it sits,
and a shipped-style bit saying whether any source beneath it has been republished since - the
reverse-reachability the shipped engine actually computes. Nothing is offered that names which
recorded read moved, because that first-difference is the derivation and the derivation is the
task.

The verdict to want is that at least one graded quantity has no short rule. Two should not: the
check decision (evaluate or keep), because the answer is which recorded read moved first and the
tree offers only that something beneath changed, and the in-block decision, which is the same
question asked under a previewed value. The adopt decision is allowed a short rule - matching
source and value is exactly install - because it is an ordinary fence, not the discovery.

    python3 tools/onelinecheck.py trial-keep-adopt
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
import gen  # noqa: E402

ROWS = {"check-stands": [], "block-eval": [], "adopt": []}


def _depth(f, name, memo):
    if name in memo:
        return memo[name]
    if f.kind[name] == "raw":
        memo[name] = 0
        return 0
    d = 1 + max((_depth(f, a, memo) for a in f.args[name] if a in f.kind), default=0)
    memo[name] = d
    return d


def samples():
    here = lab.tree(lab.TASK / "solution")
    sys.path.insert(0, str(here))
    import ops
    from fld import look, make, need, feed, hold, store  # noqa: F401
    from fld import prog

    plain_stands = look.stands
    plain_body = make.body
    dirty = {"since": {}}          # source -> a running publication tick
    tick = {"n": 0}
    depths = {}

    def bumped(f, name):
        """Shipped-style: has any source under this field been republished since it was kept?"""
        seen = set()
        fringe = [name]
        while fringe:
            one = fringe.pop()
            if one in seen:
                continue
            seen.add(one)
            if f.kind[one] == "raw":
                if dirty["since"].get(one, -1) >= f.keptat.get(name, -1):
                    return 1
            else:
                fringe.extend(a for a in f.args[one] if a in f.kind)
        return 0

    def feats(f, name, rec):
        return {
            "reads": len(rec[1]),
            "depth": _depth(f, name, depths),
            "pick": int(f.kind[name] == "pick"),
            "gate": int(f.kind[name] == "gate"),
            "sum": int(f.kind[name] == "sum"),
            "bumped": bumped(f, name),
        }

    def watched_stands(f, rec, want, seen):
        # name is not passed in; recover it by identity from the kept results
        got = plain_stands(f, rec, want, seen)
        watched_stands.last = (rec, got)
        return got

    def watched_body(f, name, want, seen):
        rec = need.keep.get(f, name)
        in_block = f.pre is not None and f.pre.live
        if rec is not None:
            row = feats(f, name, rec)
            # the body is being evaluated, so the check did NOT hold: label False = re-evaluated
            (ROWS["block-eval"] if in_block else ROWS["check-stands"]).append((row, False))
        v = plain_body(f, name, want, seen)
        f.keptat[name] = tick["n"]
        return v

    # wrap the check so a kept result that stands is recorded as label True
    def check_and_record(f, name, want, seen):
        rec = need.keep.get(f, name)
        if rec is None or need.keep.pinned(f, name) or need.defs.src(f, name):
            return None
        in_block = f.pre is not None and f.pre.live
        stands = plain_stands(f, rec, want, seen)
        if stands:
            (ROWS["block-eval"] if in_block else ROWS["check-stands"]).append(
                (feats(f, name, rec), True))
        return stands

    # reimplement need.want minimally so we can observe both outcomes with features
    def watched_want(f, name, seen):
        if name in seen:
            return seen[name]
        if need.defs.src(f, name):
            v = need.over(f, name)
        elif need.keep.pinned(f, name):
            v = need.keep.held(f, name)
        else:
            rec = need.keep.get(f, name)
            if rec is not None:
                in_block = f.pre is not None and f.pre.live
                if look.stands(f, rec, watched_want, seen):
                    (ROWS["block-eval"] if in_block else ROWS["check-stands"]).append(
                        (feats(f, name, rec), True))
                    v = rec[0]
                else:
                    (ROWS["block-eval"] if in_block else ROWS["check-stands"]).append(
                        (feats(f, name, rec), False))
                    v = make.body(f, name, watched_want, seen)
                    f.keptat[name] = tick["n"]
            else:
                v = make.body(f, name, watched_want, seen)
                f.keptat[name] = tick["n"]
        seen[name] = v
        return v

    plain_put = feed.put
    plain_on = hold.on

    def watched_put(f, name, v):
        had = f.pre is not None and not f.pre.live
        if had:
            ROWS["adopt"].append(({
                "src_match": int(f.pre.src == name),
                "val_match": int(f.pre.val == v),
                "no_change": int(f.pub.get(name) == v),
            }, int(f.pre.src == name and f.pre.val == v and f.pub.get(name) != v)))
        if f.pub.get(name) != v:
            tick["n"] += 1
            dirty["since"][name] = tick["n"]
        plain_put(f, name, v)

    look.stands = look.stands           # unchanged; watched_want calls it directly
    make.orig_body = plain_body
    need.get = lambda f, name: watched_want(f, name, {})
    need.pin = lambda f, name: need.keep.hold(f, name, watched_want(f, name, {}))
    feed.put = watched_put

    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(10):
            lines = gen.one(fam, "decide/%s-%d" % (fam, i))
            f = store.Fld()
            f.keptat = {}
            for w in prog.walk(lines):
                ops.ex(f, w)
    return ROWS


if __name__ == "__main__":
    got = samples()
    for name, rows in sorted(got.items()):
        pos = sum(1 for _r, y in rows if y)
        print("%-14s %d rows, %d positive" % (name, len(rows), pos))
