"""Write cheat/ from the reference plus one named defect each.

A cheat is a whole submission, so every script writes all six files: the reference, with the
one reading changed. Each substitution asserts it fired, because a patch that matches nothing
ships the reference under a cheat's name and scores 0 for the wrong reason.

Run after any change to solution/. `cheat_report.py` then runs the suite and asserts which
graded case catches each one, which is the half that a reward of 0 does not prove.
"""
import json
import pathlib
import stat
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "slab-fold-scope"
SOL = TASK / "solution"
OUT = TASK / "cheat"
SLOW = HERE / "slow"
PARTS = ("live.py", "lay.py", "wipe.py", "mark.py", "take.py", "push.py")

MADE = []
BUILT = {}


def base():
    return {p: (SOL / p).read_text(encoding="utf-8") for p in PARTS}


def sub(files, name, old, new):
    txt = files[name]
    hits = txt.count(old)
    assert hits == 1, "%s: %d hits for %r" % (name, hits, old[:60])
    files[name] = txt.replace(old, new)


def swap(files, name, path):
    files[name] = pathlib.Path(path).read_text(encoding="utf-8")


def write(name, comment, files):
    BUILT[name] = dict(files)
    body = ["#!/bin/bash", "# " + comment, "set -euo pipefail", ""]
    for part in PARTS:
        body.append("cat > /app/tab/%s <<'PYEOF'" % part)
        body.append(files[part].rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    text = "\n".join(body)
    assert "\r" not in text
    dest = OUT / ("cheat-%s.sh" % name)
    dest.write_text(text, encoding="utf-8", newline="\n")
    dest.chmod(dest.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    MADE.append(name)


# --- the append -----------------------------------------------------------------------

def put_beside():
    f = base()
    sub(f, "lay.py",
        "    took = wipe.part(tab, buck, lo, hi, jr)\n"
        "    mark.fresh(tab, buck, lo, hi, num, jr)\n"
        "    return (hi - lo + 1) - took",
        "    mark.fresh(tab, buck, lo, hi, num, jr)\n"
        "    return hi - lo + 1")
    sub(f, "lay.py", "from tab import mark, wipe", "from tab import mark")
    write("put-beside", "a put drops a slab in beside the keys already live", f)


def put_counts_all():
    f = base()
    sub(f, "lay.py", "    return (hi - lo + 1) - took", "    return hi - lo + 1")
    write("put-counts-all", "a put reports the width of its range as added", f)


# --- the cut --------------------------------------------------------------------------

def cut_width():
    f = base()
    sub(f, "wipe.py", "    return took", "    return hi - lo + 1")
    write("cut-width", "a cut reports the width of its range rather than what it took", f)


# --- the re-pack ----------------------------------------------------------------------

def fold_all_inside():
    f = base()
    sub(f, "take.py",
        "        if e[1] <= base < e[2]:\n"
        "            raise Again()\n"
        "        if e[2] <= base:\n"
        "            reach.add(d)",
        "        reach.add(d)")
    write("fold-all-inside", "a fold re-packs every slab inside its range", f)


def fold_no_floor():
    f = base()
    sub(f, "take.py", "    if len(reach) < 2:", "    if len(reach) < 1:")
    write("fold-no-floor", "a fold with one slab in reach re-packs it anyway", f)


def fold_overlap():
    f = base()
    sub(f, "take.py",
        "        if e[0] != b.sn[d]:\n            continue\n", "")
    write("fold-overlap", "a fold takes any slab meeting its range, not only those inside it", f)


def fold_restamp():
    f = base()
    sub(f, "mark.py",
        "        if b.ds[t] in reach:\n"
        "            live.retag(b, t, sid, jr)",
        "        if b.ds[t] in reach:\n"
        "            live.retag(b, t, sid, jr)\n"
        "            live.restamp(b, t, tab.head + 1, jr)")
    sub(f, "live.py",
        "def bump(b, sid, d, jr):",
        "def restamp(b, t, num, jr):\n"
        "    jr.append((\"st\", b, t, b.ss[t]))\n"
        "    b.ss[t] = num\n"
        "\n"
        "\ndef bump(b, sid, d, jr):")
    sub(f, "live.py",
        "        elif kind == \"dt\":",
        "        elif kind == \"st\":\n"
        "            _, b, t, num = e\n"
        "            b.ss[t] = num\n"
        "        elif kind == \"dt\":")
    write("fold-restamp", "a re-packed key takes the number of the proposal that re-packed it", f)


def fold_slab_stamp():
    f = base()
    sub(f, "take.py",
        "        if e[1] <= base < e[2]:\n"
        "            raise Again()\n"
        "        if e[2] <= base:\n"
        "            reach.add(d)",
        "        if b.born.get(d, 0) <= base:\n"
        "            reach.add(d)")
    sub(f, "live.py", "        self.sn = {}", "        self.sn = {}\n        self.born = {}")
    sub(f, "mark.py",
        "    sid = tab.mint()\n    live.sow(tab, buck, lo, hi, num, sid, jr)",
        "    sid = tab.mint()\n"
        "    live.hold(tab, buck).born[sid] = num\n"
        "    live.sow(tab, buck, lo, hi, num, sid, jr)")
    sub(f, "mark.py",
        "    b = live.hold(tab, buck)\n    sid = tab.mint()\n    held = 0",
        "    b = live.hold(tab, buck)\n"
        "    sid = tab.mint()\n"
        "    b.born[sid] = min(b.born.get(d, 0) for d in reach)\n"
        "    held = 0")
    write("fold-slab-stamp", "era is one stamp per slab, oldest wins when slabs are re-packed", f)


def fold_cached_minmax():
    f = base()
    sub(f, "take.py",
        "    seen = {}\n"
        "    for t in range(i, j):\n"
        "        d = b.ds[t]\n"
        "        s = b.ss[t]\n"
        "        wide = min(b.es[t], hi) - max(b.ks[t], lo) + 1\n"
        "        e = seen.get(d)\n"
        "        if e is None:\n"
        "            seen[d] = [wide, s, s]\n"
        "        else:\n"
        "            e[0] += wide\n"
        "            if s < e[1]:\n"
        "                e[1] = s\n"
        "            if s > e[2]:\n"
        "                e[2] = s\n",
        "    seen = {}\n"
        "    for t in range(i, j):\n"
        "        d = b.ds[t]\n"
        "        wide = min(b.es[t], hi) - max(b.ks[t], lo) + 1\n"
        "        e = seen.get(d)\n"
        "        if e is None:\n"
        "            seen[d] = [wide] + list(b.era[d])\n"
        "        else:\n"
        "            e[0] += wide\n")
    sub(f, "live.py", "        self.sn = {}", "        self.sn = {}\n        self.era = {}")
    sub(f, "mark.py",
        "    sid = tab.mint()\n    live.sow(tab, buck, lo, hi, num, sid, jr)",
        "    sid = tab.mint()\n"
        "    live.hold(tab, buck).era[sid] = (num, num)\n"
        "    live.sow(tab, buck, lo, hi, num, sid, jr)")
    sub(f, "mark.py",
        "    b = live.hold(tab, buck)\n    sid = tab.mint()\n    held = 0",
        "    b = live.hold(tab, buck)\n"
        "    sid = tab.mint()\n"
        "    b.era[sid] = (min(b.era[d][0] for d in reach), max(b.era[d][1] for d in reach))\n"
        "    held = 0")
    write("fold-cached-minmax",
          "era is a first and last pair cached on the slab and never recomputed when keys leave",
          f)


def fold_own_in_reach():
    f = base()
    sub(f, "take.py", "def part(tab, base, buck, lo, hi, jr):",
        "def part(tab, base, buck, lo, hi, jr, num=None):")
    sub(f, "take.py",
        "        if e[2] <= base:\n            reach.add(d)",
        "        if e[2] <= base or e[1] == tab.head + 1:\n            reach.add(d)")
    write("fold-own-in-reach",
          "a fold takes the slab its own proposal just created, alongside the base era", f)


# --- the slab holding both eras -------------------------------------------------------

def mixed_ignore():
    f = base()
    sub(f, "take.py",
        "        if e[1] <= base < e[2]:\n            raise Again()\n", "")
    write("mixed-ignore", "a slab holding both eras is simply left out of the re-pack", f)


def mixed_any_overlap():
    f = base()
    sub(f, "take.py",
        "        if e[0] != b.sn[d]:\n"
        "            continue\n"
        "        if e[1] <= base < e[2]:\n"
        "            raise Again()\n"
        "        if e[2] <= base:\n"
        "            reach.add(d)",
        "        if e[1] <= base < e[2]:\n"
        "            raise Again()\n"
        "        if e[0] != b.sn[d]:\n"
        "            continue\n"
        "        if e[2] <= base:\n"
        "            reach.add(d)")
    write("mixed-any-overlap",
          "any slab meeting the range and holding both eras forces the second attempt", f)


def mixed_whole_bucket():
    f = base()
    sub(f, "take.py",
        "    seen = {}\n    for t in range(i, j):",
        "    whole = {}\n"
        "    for t in range(len(b.ks)):\n"
        "        d = b.ds[t]\n"
        "        s = b.ss[t]\n"
        "        e = whole.get(d)\n"
        "        if e is None:\n"
        "            whole[d] = [s, s]\n"
        "        else:\n"
        "            e[0] = min(e[0], s)\n"
        "            e[1] = max(e[1], s)\n"
        "    for e in whole.values():\n"
        "        if e[0] <= base < e[1]:\n"
        "            raise Again()\n"
        "    seen = {}\n"
        "    for t in range(i, j):")
    write("mixed-whole-bucket",
          "a slab holding both eras anywhere in the bucket forces the second attempt", f)


def mixed_keep():
    f = base()
    sub(f, "push.py",
        "    except take.Again:\n"
        "        live.undo(jr)\n"
        "        tab.next = first\n"
        "        add, gone, made = once(tab, prop, tab.head, num, jr)",
        "    except take.Again:\n"
        "        add, gone, made = once(tab, prop, tab.head, num, jr)")
    write("mixed-keep", "the second attempt keeps whatever the first one had already done", f)


def mixed_no_renumber():
    f = base()
    sub(f, "push.py",
        "        live.undo(jr)\n"
        "        tab.next = first\n"
        "        add, gone, made = once(tab, prop, tab.head, num, jr)",
        "        live.undo(jr)\n"
        "        add, gone, made = once(tab, prop, tab.head, num, jr)")
    write("mixed-no-renumber",
          "the undone attempt gives its slab numbers back to nobody", f)


def mixed_only_fold():
    f = base()
    swap(f, "push.py", HERE / "patch" / "push_only_fold.py")
    write("mixed-only-fold",
          "the second attempt redoes only the fold that forced it", f)


def mixed_prescan():
    f = base()
    swap(f, "push.py", HERE / "patch" / "push_prescan.py")
    write("mixed-prescan",
          "the proposal is scanned for a slab holding both eras before any part runs", f)


def parts_folds_last():
    f = base()
    swap(f, "push.py", HERE / "patch" / "push_folds_last.py")
    write("parts-folds-last",
          "the puts and cuts of a proposal run first and its folds afterwards", f)


def base_at_push():
    f = base()
    sub(f, "push.py",
        "        add, gone, made = once(tab, prop, prop.base, num, jr)",
        "        add, gone, made = once(tab, prop, tab.head, num, jr)")
    write("base-at-push", "the base is the head at push time rather than at plan time", f)


def number_always():
    f = base()
    sub(f, "push.py",
        "    if not made and not gone:\n"
        "        live.undo(jr)\n"
        "        tab.next = first\n"
        "        say.void(tab, prop.tag)\n"
        "        return\n",
        "")
    write("number-always", "every pushed proposal takes the next number", f)


# --- correct but out of budget --------------------------------------------------------

def slow(name, comment, over):
    f = base()
    for part in PARTS:
        one = SLOW / over / part
        if one.is_file():
            swap(f, part, one)
    write(name, comment, f)


# --- carrying the answers -------------------------------------------------------------

def wrong(f):
    """The base every forgery and probe is built on, so a reward of 0 is never the
    reference quietly passing: the mixed slab is ignored, which the era families catch."""
    sub(f, "take.py", "        if e[1] <= base < e[2]:\n            raise Again()\n", "")


def marks(lines):
    """Every op as the forgery sees it, and whether it prints a line.

    The forgery has to key on every op, not only the ones that print: two enumerated programs
    share the first two printing ops and disagree on the second answer, so a key built from
    printing ops alone forges one of them and quietly gets the other wrong.
    """
    out = []
    parts = {}
    for line in lines:
        w = line.split()
        op = w[0]
        if op == "plan":
            parts[w[1]] = 0
            out.append(("N|%s" % w[1], False))
        elif op in ("put", "cut", "fold"):
            parts[w[1]] += 1
            out.append(("%s|%s|%s|%s|%s" % (op, w[1], w[2], w[3], w[4]), False))
        elif op == "push":
            out.append(("P|%s|%d" % (w[1], parts.pop(w[1])), True))
        elif op == "rows":
            out.append(("R|%s" % w[1], True))
        elif op == "at":
            out.append(("A|%s|%s" % (w[1], w[2]), True))
        else:
            raise AssertionError("the forgery does not expand %s" % op)
    return out


def forge():
    """A submission carrying the frozen answers, verbatim.

    The payload is `gt.json` itself rather than something derived from it: the enumerated
    programs are readable at /tests during the run, so a forgery holding the answers needs
    nothing else. It reproduces every enumerated program and has nothing to say about the ones
    the seed draws after the container is gone.
    """
    raw = (TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8")
    packed = json.dumps(json.loads(raw), sort_keys=True)
    f = base()
    wrong(f)
    tail = (HERE / "patch" / "forge_tail.py").read_text(encoding="utf-8")
    tail = tail.replace("__KEY__", repr(packed))
    assert "__KEY__" not in tail
    f["push.py"] = f["push.py"] + "\n\n" + tail
    write("forge-from-truth",
          "carries the frozen answers to the enumerated programs and replays them", f)


# --- the isolation probes -------------------------------------------------------------

def probe(name, comment, tail, part="push.py"):
    f = base()
    wrong(f)
    f[part] = f[part] + "\n\n" + (HERE / "patch" / tail).read_text(encoding="utf-8")
    write(name, comment, f)


def main():
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("cheat-*.sh"):
        old.unlink()
    put_beside()
    put_counts_all()
    cut_width()
    fold_all_inside()
    fold_no_floor()
    fold_overlap()
    fold_restamp()
    fold_slab_stamp()
    fold_cached_minmax()
    fold_own_in_reach()
    mixed_ignore()
    mixed_any_overlap()
    mixed_whole_bucket()
    mixed_keep()
    mixed_no_renumber()
    mixed_only_fold()
    mixed_prescan()
    parts_folds_last()
    base_at_push()
    number_always()
    slow("slow-scan", "correct, with the bucket scanned once per part", "scan")
    slow("slow-per-key", "correct, with the live keys held one key at a time", "perkey")
    slow("slow-copy", "correct, with each proposal staged by copying the bucket", "copy")
    forge()
    probe("probe-answer-key", "reads the sealed model and answers from it", "probe_answer_key.py")
    probe("probe-hijack-driver", "rewrites the frozen driver the verifier stages",
          "probe_hijack.py")
    probe("probe-plant-report", "writes the worker's report itself without doing the work",
          "probe_plant.py")
    probe("probe-late-reward", "double-forks a process that writes the reward after grading",
          "probe_late_reward.py")
    probe("probe-crash-worker", "plants a report and then kills the worker before it writes",
          "probe_crash.py")
    probe("probe-malformed", "returns garbage the grader has to parse", "probe_malformed.py")
    probe("probe-privilege", "checks its uid and tries to write the verifier's own paths",
          "probe_privilege.py")
    probe("probe-shrink-set", "shrinks the generated population it will be graded on",
          "probe_shrink.py")
    probe("probe-rewrite-frozen", "rewrites the parts of the tree the verifier does not take",
          "probe_rewrite_frozen.py")
    print("wrote %d cheats" % len(MADE))
    for name in MADE:
        print("   ", name)


if __name__ == "__main__":
    sys.exit(main())
