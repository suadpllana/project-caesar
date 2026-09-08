"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
raw ones the shipped tree exposes at that moment - whether the caller is up, how many live units
publish the name and where the first of them sits in the order, how many holds a unit has, how
many of its declared dependents are still up. Nothing derived is offered, because the derivation
is the task.

The verdict to want is that at least one graded quantity has no short rule. Two should not: what
a call does, because separating `run` from `dead` needs a distinction the tree does not
represent at all, and whether a unit goes down, because that is a fixed point over the whole
live set rather than a property of the unit.

    python3 authoring/publish-settle-order/decisions.py
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
TESTS = HERE.parents[1] / "tasks" / "publish-settle-order" / "tests"
sys.path.insert(0, str(TESTS))

import gen  # noqa: E402
import lab  # noqa: E402

KIND = {"miss": 1, "run": 2, "dead": 3}


def _pubs(rec):
    return [p[0] for p in rec.pubs]


def _live_publishers(h, sym):
    return [r for r in h.seq if sym in _pubs(r)]


def _dependents(h, rec, live_only, hard=None):
    pool = h.seq if live_only else list(h.units.values())
    out = []
    for o in pool:
        if o is rec:
            continue
        for named, kind in o.needs:
            if named == rec.name and (hard is None or kind == hard):
                out.append(o)
                break
    return out


def samples():
    lb = lab.Lab(lab.TASK / "solution")
    call_rows, target_rows, retire_rows = [], [], []
    seen_calls = set()
    for _fam, _name, lines in gen.programs("decisions", 8):
        if len(lines) > 400:
            continue
        h = lb.tab.Host()
        acc = []
        seen_calls.clear()
        for line in lines:
            op = tuple(line.split())
            mark = len(acc)
            if op[0] == "call":
                caller = lb.tab.get(h, op[1])
                sym = op[2]
                pubs = _live_publishers(h, sym)
                plain = [r for r in pubs if (sym, False) in r.pubs]
                row = {
                    "caller_up": int(caller.live),
                    "caller_holds": h.holds.get(caller.name, 0),
                    "caller_asked_before": int((op[1], sym) in seen_calls),
                    "live_units": len(h.seq),
                    "publishers_live": len(pubs),
                    "plain_publishers_live": len(plain),
                    "publisher_ever_declared": int(any(sym in _pubs(r) for r in h.units.values())),
                    "first_publisher_pos": h.seq.index(pubs[0]) if pubs else -1,
                    "caller_pos": h.seq.index(caller) if caller.live else -1,
                }
                seen_calls.add((op[1], sym))
                lb.ops.ex(h, op, acc)
                made = acc[mark:]
                call_rows.append((row, KIND.get(made[0].split()[0], 0) if made else 0))
                if made and made[0].startswith("run "):
                    answer = made[0].split()[3]
                    target_rows.append(({
                        "publishers_live": row["publishers_live"],
                        "first_publisher_pos": row["first_publisher_pos"],
                        "first_plain_pos": h.seq.index(plain[0]) if plain else -1,
                        "last_publisher_pos": h.seq.index(pubs[-1]) if pubs else -1,
                    }, [r.name for r in h.seq].index(answer)))
                continue
            if op[0] == "rel":
                before = list(h.seq)
                rows = []
                for rec in before:
                    rows.append((rec, {
                        "is_released_unit": int(rec.name == op[1]),
                        "holds": h.holds.get(rec.name, 0),
                        "declared_dependents": len(_dependents(h, rec, False)),
                        "live_dependents": len(_dependents(h, rec, True)),
                        "live_hard_dependents": len(_dependents(h, rec, True, True)),
                        "live_soft_dependents": len(_dependents(h, rec, True, False)),
                        "n_needs": len(rec.needs),
                        "pos_in_order": h.seq.index(rec),
                        "live_units": len(before),
                    }))
                lb.ops.ex(h, op, acc)
                left = {r.name for r in h.seq}
                for rec, row in rows:
                    retire_rows.append((row, int(rec.name not in left)))
                continue
            lb.ops.ex(h, op, acc)
    lb.close()
    return {"call_outcome": call_rows, "run_target": target_rows, "retire_now": retire_rows}


if __name__ == "__main__":
    got = samples()
    for k, v in sorted(got.items()):
        print("%-14s %5d rows, %d distinct labels" % (k, len(v), len({y for _, y in v})))
