"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
raw ones: whether a side still holds the node, which of its three parts that side changed, what
kind it is, how many children the record gives it, and for a contested name, which side shows
that name and what number the node carries. Nothing derived is offered, because the derivation
is the task - a feature called "survives" would answer the question it is supposed to pose.

The verdict to want is that at least one graded quantity has no short rule. Whether a folder is
kept cannot have one: it depends on what happens to the nodes the record put inside it, and on
where those settle, rather than on any property of the folder. Neither can the name contest,
which is an ordering over the other candidates in the same folder.

    python authoring/move-clash-merge/decisions.py
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "move-clash-merge"
sys.path.insert(0, str(TASK / "tests"))

import gen  # noqa: E402
import model  # noqa: E402


def parts(rec, side, letter, key):
    if key not in side:
        return (0, 0, 0, 0)
    kind, par, nm, c = side[key]
    return (1,
            int(model.tag(rec, letter, par) != rec[key][1]),
            int(nm != rec[key][2]),
            int(c != rec[key][3]))


def facts(rec, lo, ro, key):
    hl, lf, ln, lc = parts(rec, lo, "L", key)
    hr, rf, rn, rc = parts(rec, ro, "R", key)
    return {
        "on_workstation": hl,
        "on_server": hr,
        "workstation_moved": lf,
        "workstation_renamed": ln,
        "workstation_wrote": lc,
        "server_moved": rf,
        "server_renamed": rn,
        "server_wrote": rc,
        "is_folder": int(rec[key][0] == "d"),
        "record_children": len(model.kids(rec, key)),
        "record_depth": model.pth(rec, key).count("/"),
    }


def samples():
    stays, folder_kept, keeps_name, walked_up = [], [], [], []
    for name, text in gen.batch("decisions", 8):
        base, nxt, rounds = model.parse(text.split("\n"))
        rec = dict(base)
        lo, ro = dict(base), dict(base)
        made = [0]

        def fresh():
            made[0] += 1
            return "w%d" % made[0]

        for lops, rops in rounds:
            for op in lops:
                model.do(lo, op, False, fresh)
            for op in rops:
                model.do(ro, op, True, fresh)
            raw = model.where(rec, lo, ro)
            alive = model.survive(rec, lo, ro, raw)
            place = model.settle(rec, alive, raw)
            body, twins = model.hold(rec, lo, ro, place)
            for key in twins:
                place["C:" + key] = (place[key][0], place[key][1], "c", "c")
            ids, _ = model.number(rec, lo, ro, place, twins, nxt)

            for key in rec:
                if key == model.ROOT or (key not in lo and key not in ro):
                    continue
                row = facts(rec, lo, ro, key)
                stays.append((row, int(key in alive)))
                if row["is_folder"]:
                    folder_kept.append((dict(row), int(key in alive)))
                if key in alive:
                    walked_up.append((dict(row), int(raw[key][0] != place[key][0])))

            groups = {}
            for key in place:
                groups.setdefault((place[key][0], place[key][1].lower()), []).append(key)
            for spot, members in groups.items():
                if len(members) < 2:
                    continue
                for key in members:
                    nm = place[key][1]
                    keeps_name.append(({
                        "held_the_name": int(model.kept_name(rec, key, spot[0], nm)),
                        "server_shows_it": int(model.on_side(rec, ro, "R", key, nm)),
                        "workstation_shows_it": int(model.on_side(rec, lo, "L", key, nm)),
                        "is_second_file": int(key.startswith("C:")),
                        "number": int(ids[key]),
                        "wanting_it": len(members),
                        "is_folder": int(model.species(rec, lo, ro, key) == "d"),
                    }, int(key in members and final_keeper(rec, lo, ro, place, ids,
                                                           spot, members) == key)))

            tgt, nxt, ml, mr = model.merge(rec, nxt, lo, ro)
            for cur, m, fold in ((lo, ml, False), (ro, mr, True)):
                for op in model.emit(cur, tgt, m, fold):
                    model.do(cur, op, fold, fresh)
            lo = model.rekey(lo, tgt, fresh)
            ro = model.rekey(ro, tgt, fresh)
            rec = tgt
    return {"stays": stays, "folder_kept": folder_kept,
            "keeps_name": keeps_name, "walked_up": walked_up}


def final_keeper(rec, lo, ro, place, ids, spot, members):
    best, score = None, None
    for key in members:
        nm = place[key][1]
        if key.startswith("C:"):
            rank = 4
        elif model.kept_name(rec, key, spot[0], nm):
            rank = 0
        elif model.on_side(rec, ro, "R", key, nm):
            rank = 1
        elif model.on_side(rec, lo, "L", key, nm):
            rank = 2
        else:
            rank = 3
        got = (rank, int(ids[key]))
        if score is None or got < score:
            best, score = key, got
    return best


if __name__ == "__main__":
    got = samples()
    for k, v in sorted(got.items()):
        print("%-12s %5d rows, %d positive" % (k, len(v), sum(1 for _, y in v if y)))
