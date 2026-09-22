"""Assemble tests/seal/gt.json from cases.json (enumerated cases, fences) and heavy.json.

    python build_gt.py [--heavy N]

If gt.json already exists, every session it holds under the same name must come out
byte-identical (the frozen expected lines are a contract; a change is a contract change and
is refused here - delete the file deliberately to rebuild from scratch).
"""
import json
import os
import sys

from lab import APP, HERE, SEAL, model

OUT = os.path.join(SEAL, "gt.json")


def main():
    cases = json.load(open(os.path.join(HERE, "cases.json")))
    heavy = json.load(open(os.path.join(HERE, "heavy.json")))
    if "--heavy" in sys.argv:
        heavy = heavy[:int(sys.argv[sys.argv.index("--heavy") + 1])]
    doc = {"samples": [], "cases": [], "fences": [], "heavy": []}
    sdir = os.path.join(APP, "samples")
    for name in sorted({f.rsplit(".", 1)[0] for f in os.listdir(sdir)}):
        img = open(os.path.join(sdir, name + ".img")).read()
        tape = [int(v) for v in open(os.path.join(sdir, name + ".tape")).read().split()]
        cmds = open(os.path.join(sdir, name + ".cmd")).read().splitlines()
        doc["samples"].append({"name": "sample-" + name, "image": img, "tape": tape, "cmds": cmds,
                               "want": model.play(img, tape, cmds), "recheck": name != "long"})
    for name, s in sorted(cases["cases"].items()):
        doc["cases"].append({"name": "case-" + name, "reading": name, "image": s["image"],
                             "tape": s["tape"], "cmds": s["cmds"], "want": s["want"]})
    for i, s in enumerate(cases["fences"]):
        doc["fences"].append({"name": "fence-%d" % i, "image": s["image"], "tape": s["tape"],
                              "cmds": s["cmds"], "want": s["want"]})
    for i, s in enumerate(heavy):
        doc["heavy"].append({"name": "heavy-%02d" % i, "image": s["image"], "tape": s["tape"],
                             "cmds": s["cmds"], "want": s["want"], "volume": s["volume"],
                             "in_frame": s["in_frame"]})
    for s in doc["cases"] + doc["fences"]:
        s["recheck"] = True
        assert model.play(s["image"], s["tape"], s["cmds"]) == s["want"], s["name"]
    if os.path.exists(OUT):
        old = json.load(open(OUT))
        for grp in doc:
            prev = {s["name"]: s for s in old.get(grp, [])}
            for s in doc[grp]:
                if s["name"] in prev:
                    p = prev[s["name"]]
                    for k in ("image", "tape", "cmds", "want"):
                        assert p[k] == s[k], "frozen session %s changed its %s" % (s["name"], k)
    text = json.dumps(doc, indent=0)
    assert "\r" not in text
    with open(OUT, "w", newline="\n") as f:
        f.write(text + "\n")
    print("gt.json: %d samples, %d cases, %d fences, %d heavy (%d bytes)" % (
        len(doc["samples"]), len(doc["cases"]), len(doc["fences"]), len(doc["heavy"]), len(text)))


if __name__ == "__main__":
    main()
