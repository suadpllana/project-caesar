"""The graded decisions as rows of features the agent can read, for tools/onelinecheck.py.

The features are the raw facts a pipeline file and the shipped tree put in front of the agent
for one partition: whether it is published, how many partitions its declared reads name, how
many of those no longer exist, how many of the missing ones belong to a source, how many are
published, whether it reads the corrected partition directly, whether a roll-up is declared for
an hourly dataset it reads by the day, how old it is and its keep. Nothing says whether the
correction reached it, whether a read changed, whether a read agrees, or whether an expired
read can be computed, because none of those is a field anywhere: each is what the settle
produces. The labels are the sealed model's.

The verdict to want is that no line decision has a short rule over those facts. If one did,
the plan could be written from the file without settling anything.

    python3 tools/onelinecheck.py restate-hold-plan
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402


def features(model, plan, name, i):
    pp = plan.pp
    reads = [(src, p) for _kind, src, parts in model.declared(pp, name, i) for p in parts]
    missing = [(s, p) for s, p in reads if not plan.exists(s, p)]
    rolls = any(kind == "day" and pp.roll.get(src) not in (None, name)
                for kind, src, _parts in model.declared(pp, name, i))
    return {
        "pinned": int((name, i) in pp.pins),
        "reads": len(reads),
        "missing": len(missing),
        "missing_src": sum(1 for s, _p in missing if s not in pp.reads),
        "read_pinned": sum(1 for r in reads if r in pp.pins),
        "reads_fix": int(pp.fix in reads),
        "rolls": int(rolls),
        "age": pp.now - model.ends(pp, name, i),
        "keep": pp.keep[name],
    }


def samples():
    _cases, gen, model = lab.sealed()
    rows = {"held-or-run": [], "same-among-holds": [], "part-among-runs": [],
            "temp-printed": []}
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for k in range(20):
            lines = gen.build(fam, random.Random("decisions|%s|%d" % (fam, k)))
            plan = model.Plan(model.Pipe("\n".join(lines) + "\n"))
            printed = set()
            for line in plan.plan():
                ws = line.split()
                if ws[0] == "temp":
                    printed.add((ws[1], int(ws[2])))
            for name, i in sorted(plan.reached):
                if name not in plan.pp.reads or not plan.exists(name, i):
                    continue
                rec = plan.settle(name, i)
                f = features(model, plan, name, i)
                rows["held-or-run"].append((f, rec["line"] == "hold"))
                if rec["line"] == "hold":
                    rows["same-among-holds"].append((f, rec["word"] == "same"))
                else:
                    rows["part-among-runs"].append((f, rec["word"] == "part"))
                for _kind, src, parts in model.declared(plan.pp, name, i):
                    for p in parts:
                        if src in plan.pp.reads and not plan.exists(src, p):
                            g = features(model, plan, src, p)
                            g["reader_pinned"] = f["pinned"]
                            rows["temp-printed"].append((g, (src, p) in printed))
    return rows
