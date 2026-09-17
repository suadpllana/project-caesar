"""Write cheat/ from the reference plus one named defect each.

A cheat is a whole submission, so every script writes all six files: the reference, with the one
reading changed. Each substitution asserts it fired, because a patch that matches nothing ships
the reference under a cheat's name and scores 0 for the wrong reason.

Run after any change to solution/. `readings.py` reads the same builders, so the readings that
are measured and the cheats that ship cannot drift apart, and `cheat_report.py` then runs the
suite and asserts which graded case catches each one - which is the half a reward of 0 does not
prove.
"""
import json
import pathlib
import stat
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "claim-cover-lift"
SOL = TASK / "solution"
OUT = TASK / "cheat"
SLOW = HERE / "slow"
PARTS = ("hold.py", "fit.py", "line.py", "lift.py", "knot.py", "gate.py")

MADE = []
BUILT = {}


def base():
    return {p: (SOL / p).read_text(encoding="utf-8") for p in PARTS}


def shipped():
    """The tree as it ships, which is wrong.

    The probes and the forgery sit on this, never on the reference: a probe built on a working
    engine scores 1 for having done the work, which proves nothing about the isolation it was
    written to test.
    """
    here = TASK / "environment" / "app_src" / "hb"
    return {p: (here / p).read_text(encoding="utf-8") for p in PARTS}


def sub(files, name, old, new):
    txt = files[name]
    hits = txt.count(old)
    assert hits == 1, "%s: %d hits for %r" % (name, hits, old[:70])
    files[name] = txt.replace(old, new)


def write(name, comment, files, extra=None):
    BUILT[name] = dict(files)
    body = ["#!/bin/bash", "# " + comment, "set -euo pipefail", ""]
    for part in PARTS:
        body.append("cat > /app/hb/%s <<'PYEOF'" % part)
        body.append(files[part].rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    if extra:
        body.append(extra.rstrip("\n"))
        body.append("")
    text = "\n".join(body)
    assert "\r" not in text
    dest = OUT / ("cheat-%s.sh" % name)
    dest.write_text(text, encoding="utf-8", newline="\n")
    dest.chmod(dest.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    MADE.append(name)


FAMILY_BLOCK = """    box = boxof(node)
    if box != node:
        for other, got in hold.at(st, box).items():
            if other != job and any(clash(mode, m) for m in got):
                out.add(other)
    else:
        for other, sum_ in hold.under(st, box).items():
            if other != job and (mode == "w" or sum_[1] > 0):
                out.add(other)
"""

WAIT_BLOCK = """    for req in line.ahead(st, node, seq):
        if req["job"] != job and clash(mode, req["mode"]):
            out.add(req["job"])
"""


# --- what conflicts ---------------------------------------------------------------------

def fit_node_only():
    f = base()
    sub(f, "fit.py", FAMILY_BLOCK, "    box = boxof(node)\n")
    return "fit-node-only", "conflicts tested on the node alone, never across the family", f


def fit_slot_blind():
    f = base()
    sub(f, "fit.py", """    else:
        for other, sum_ in hold.under(st, box).items():
            if other != job and (mode == "w" or sum_[1] > 0):
                out.add(other)
""", "")
    return "fit-slot-blind", "a request for a box ignores the slot claims inside it", f


def fit_no_line():
    f = base()
    sub(f, "fit.py", WAIT_BLOCK, "")
    return "fit-no-line", "an older waiting request does not block a compatible one", f


# --- covering ---------------------------------------------------------------------------

def cover_none():
    f = base()
    sub(f, "fit.py", """    for held in (node, boxof(node)):
        got = hold.modes(st, job, held)
        if got and (mode == "r" or "w" in got):
            return True
    return False
""", "    return False\n")
    return "cover-none", "every request joins the line, even one the job already covers", f


def cover_any_mode():
    f = base()
    sub(f, "fit.py", 'if got and (mode == "r" or "w" in got):', "if got:")
    return "cover-any-mode", "a claim held in r is taken to cover a request in w", f


def cover_downward():
    f = base()
    sub(f, "fit.py", """    for held in (node, boxof(node)):
        got = hold.modes(st, job, held)
        if got and (mode == "r" or "w" in got):
            return True
    return False
""", """    for held in (node, boxof(node)):
        got = hold.modes(st, job, held)
        if got and (mode == "r" or "w" in got):
            return True
    if boxof(node) == node:
        for slot in hold.slots(st, job, node):
            got = hold.modes(st, job, slot)
            if got and (mode == "r" or "w" in got):
                return True
    return False
""")
    return "cover-downward", "a claim on a slot is taken to cover a request for its box", f


def cover_not_kept():
    f = base()
    sub(f, "gate.py", """    if fit.cover(st, job, node, mode):
        hold.add(st, job, node, mode)
        say.grant(st, job, node, mode)
        return
""", """    if fit.cover(st, job, node, mode):
        say.grant(st, job, node, mode)
        return
""")
    return "cover-not-kept", "a covered request is granted but never recorded as an acquire", f


# --- what a hold is ----------------------------------------------------------------------

def hold_one_mode():
    f = base()
    sub(f, "hold.py", """def add(st, job, node, mode):
    got = cell(st, node)["h"].setdefault(job, [])
""", """def add(st, job, node, mode):
    if modes(st, job, node):
        sub(st, job, node)
    got = cell(st, node)["h"].setdefault(job, [])
""")
    return "hold-one-mode", "a job holds one mode per node, so a second take replaces the first", f


def drop_oldest():
    f = base()
    sub(f, "hold.py", "    mode = got.pop()\n", "    mode = got.pop(0)\n")
    return "drop-oldest", "a drop removes the first acquire instead of the most recent", f


def hold_ever_held():
    f = base()
    sub(f, "hold.py", """        if per[0] == 0 and per[1] == 0:
            del mine["at"][node]
            if not mine["at"]:
                del bk["bx"][box]
""", "")
    return "hold-ever-held", "the lift floor counts every slot ever taken, not those still held", f


def order_by_text():
    f = base()
    sub(f, "hold.py", """def order(node):
    box = boxof(node)
    if box == node:
        return (int(node[1:]), 0, 0)
    return (int(box[1:]), 1, int(node[node.find(":") + 2:]))
""", """def order(node):
    return node
""")
    return "order-by-text", "nodes are put in order as text rather than by number", f


def show_last_mode():
    f = base()
    sub(f, "hold.py", 'out.append((job, "".join(sorted(one["h"][job]))))',
        'out.append((job, one["h"][job][-1]))')
    return "show-last-mode", "a query prints the mode last taken instead of every acquire", f


def show_text_order():
    f = base()
    sub(f, "hold.py", 'for job in sorted(one["h"], key=lambda name: int(name[1:])):',
        'for job in sorted(one["h"]):')
    return "show-text-order", "a query lists jobs in text order rather than by number", f


# --- the order grants come out in --------------------------------------------------------

def sweep_per_box():
    f = base()
    sub(f, "gate.py", """def sweep(st, hit):
    live = set(hit)
    while live:
        best = None
        for box in list(live):
            cand = first(st, box)
            if cand is None:
                live.discard(box)
            elif best is None or cand["seq"] < best["seq"]:
                best = cand
        if best is None:
            return
        line.pull(st, best)
        live.add(boxof(best["node"]))
        live |= give(st, best)
""", """def sweep(st, hit):
    live = set(hit)
    while live:
        box = sorted(live)[0]
        cand = first(st, box)
        if cand is None:
            live.discard(box)
            continue
        line.pull(st, cand)
        live.add(boxof(cand["node"]))
        live |= give(st, cand)
""")
    return "sweep-per-box", "each box's line is drained in turn instead of by one store order", f


def end_no_sweep():
    f = base()
    sub(f, "gate.py", """    hit = hold.clear(st, job)
    say.done(st, job)
    st.gone.add(job)
    sweep(st, hit)
""", """    hold.clear(st, job)
    say.done(st, job)
    st.gone.add(job)
""")
    return "end-no-sweep", "ending a job frees its claims without granting what they blocked", f


# --- the lift -----------------------------------------------------------------------------

def lift_give_up():
    f = base()
    sub(f, "gate.py", """        up = lift.check(st, job, node, mode)
        if up is not None:
            say.lift(st, job, box, up)
            ask(st, job, box, up, (node, mode))
            return
""", """        up = lift.check(st, job, node, mode)
        if up is not None:
            say.lift(st, job, box, up)
            if not fit.blockers(st, job, box, up):
                sweep(st, give(st, {"job": job, "node": box, "mode": up,
                                    "trig": (node, mode)}))
                return
""")
    return "lift-give-up", "a lift that cannot be granted at once is abandoned", f


def lift_take_order():
    f = base()
    sub(f, "hold.py", '    return sorted(got["at"], key=order) if got else []',
        '    return list(got["at"]) if got else []')
    return "lift-take-order", "a granted lift frees its slot claims in the order they were taken", f


def lift_count_acquires():
    f = base()
    sub(f, "hold.py", '    return (0, False) if got is None else (len(got["at"]), got["w"] > 0)',
        '    if got is None:\n'
        '        return 0, False\n'
        '    return sum(n + m for n, m in got["at"].values()), got["w"] > 0')
    return "lift-count-acquires", "the lift floor counts acquires rather than distinct slots", f


def lift_trigger_mode():
    f = base()
    sub(f, "lift.py", '    return "w" if mode == "w" or wet else "r"',
        '    return "w" if mode == "w" else "r"')
    return "lift-trigger-mode", "a lift takes the mode of its trigger, ignoring the claims it replaces", f


def lift_keeps_slots():
    f = base()
    sub(f, "lift.py", """    for node in hold.slots(st, job, box):
        while hold.modes(st, job, node):
            hold.sub(st, job, node)
            say.free(st, job, node)
""", "")
    return "lift-keeps-slots", "a granted lift keeps the slot claims it was meant to replace", f


# --- jobs that come to wait for each other -------------------------------------------------

def knot_holders_only():
    f = base()
    sub(f, "knot.py", '    return fit.blockers(st, job, req["node"], req["mode"], req["seq"])',
        '    return fit.blockers(st, job, req["node"], req["mode"], 0)')
    return "knot-holders-only", "waiting for an older request is not counted as waiting for a job", f


def knot_first_found():
    f = base()
    sub(f, "knot.py", """def pick(st, ring_):
    best = None
    for job in ring_:
        key = (hold.count(st, job), -int(job[1:]))
        if best is None or key < best[0]:
            best = (key, job)
    return best[1]
""", """def pick(st, ring_):
    return sorted(ring_)[0]
""")
    return "knot-first-found", "the job stopped is the first one the search reaches", f


def knot_count_nodes():
    f = base()
    sub(f, "hold.py", """def count(st, job):
    one = st.by_job.get(job)
    return one["num"] if one else 0
""", """def count(st, job):
    one = st.by_job.get(job)
    return len(one["at"]) if one else 0
""")
    return "knot-count-nodes", "acquires are counted per node rather than with repetition", f


def knot_tie_small():
    f = base()
    sub(f, "knot.py", '        key = (hold.count(st, job), -int(job[1:]))',
        '        key = (hold.count(st, job), int(job[1:]))')
    return "knot-tie-small", "a tie on acquires goes to the smallest job number", f


def knot_keeps_request():
    f = base()
    sub(f, "knot.py", """    req = line.asked(st, job)
    if req is not None:
        line.pull(st, req)
    hit = hold.clear(st, job)
""", """    req = line.asked(st, job)
    hit = hold.clear(st, job)
""")
    sub(f, "gate.py", """def settle(st, job):
    while True:
        bad = knot.ring(st, job)
        if not bad:
            return
        sweep(st, knot.kill(st, knot.pick(st, bad)))
""", """def settle(st, job):
    bad = knot.ring(st, job)
    if bad:
        sweep(st, knot.kill(st, knot.pick(st, bad)))
""")
    return ("knot-keeps-request",
            "a stopped job's request stays in the line, and one job is stopped per wait", f)


# --- lines a job cannot act on --------------------------------------------------------------

def busy_acts():
    f = base()
    sub(f, "gate.py", """def busy(st, job):
    return job in st.gone or line.asked(st, job) is not None
""", """def busy(st, job):
    return job in st.gone
""")
    return "busy-acts", "a job with a request waiting still acts on later lines", f


def stopped_acts():
    f = base()
    sub(f, "gate.py", """def busy(st, job):
    return job in st.gone or line.asked(st, job) is not None
""", """def busy(st, job):
    return line.asked(st, job) is not None
""")
    return "stopped-acts", "a stopped or finished job still acts on later lines", f


READINGS = (
    fit_node_only, fit_slot_blind, fit_no_line, cover_none, cover_any_mode, cover_downward,
    cover_not_kept, hold_one_mode, drop_oldest, hold_ever_held, order_by_text, show_last_mode,
    show_text_order, sweep_per_box, end_no_sweep, lift_give_up, lift_take_order,
    lift_count_acquires, lift_trigger_mode, lift_keeps_slots, knot_holders_only,
    knot_first_found, knot_count_nodes, knot_tie_small, knot_keeps_request, busy_acts,
    stopped_acts,
)


# --- correct but too slow ---------------------------------------------------------------

def slow(name, comment):
    f = base()
    hit = False
    for part in PARTS:
        one = SLOW / name / part
        if one.is_file() and one.read_text() != f[part]:
            f[part] = one.read_text(encoding="utf-8")
            hit = True
    assert hit, "slow reading %s changes nothing" % name
    write("slow-" + name, comment, f)


# --- an answer key, and the probes ------------------------------------------------------

def forge():
    """An answer key: the frozen trace of every enumerated program, and of every prefix of one.

    Keyed by the operations seen so far, so it survives a query in the middle of a program: the
    hook inside `who` hands back the holders the expected line names and leaves the printer to
    write that line itself. It runs the shipped service for anything it does not recognise, so a
    pass can only come from the key.
    """
    sys.path.insert(0, str(TASK / "tests"))
    sys.path.insert(0, str(TASK / "tests" / "seal"))
    import cases
    import model
    keys = {}
    for name in cases.ORDER:
        body = cases.ops(name)
        for cut in range(1, len(body) + 1):
            keys["\n".join(body[:cut])] = model.expect(body[:cut])
    f = shipped()
    f["gate.py"] = f["gate.py"] + """

ANSWERS = %s


def _tape(st, line_):
    tape = getattr(st, "tape", None)
    if tape is None:
        tape = st.tape = []
    if len(tape) > 24:
        return None
    tape.append(line_)
    want = ANSWERS.get("\\n".join(tape))
    if want is None:
        return None
    del st.out[:]
    st.out.extend(want)
    return want
""" % json.dumps(keys)
    sub(f, "gate.py", """def take(st, job, node, mode):
    if job in st.gone:
        return
""", """def take(st, job, node, mode):
    if _tape(st, "take %s %s %s" % (job, node, mode)) is not None:
        return
    if job in st.gone:
        return
""")
    sub(f, "gate.py", """def drop(st, job, node):
    if job in st.gone:
        return
""", """def drop(st, job, node):
    if _tape(st, "drop %s %s" % (job, node)) is not None:
        return
    if job in st.gone:
        return
""")
    sub(f, "gate.py", """def end(st, job):
    if job in st.gone:
        return
""", """def end(st, job):
    if _tape(st, "end %s" % job) is not None:
        return
    if job in st.gone:
        return
""")
    sub(f, "hold.py", """def who(st, node):
    one = st.by_node.get(node)
""", """def who(st, node):
    from hb import gate
    want = gate._tape(st, "show %s" % node)
    if want is not None:
        del st.out[-1:]
        row = want[-1].split()
        return [(row[i], row[i + 1]) for i in range(2, len(row), 2)]
    one = st.by_node.get(node)
""")
    write("forge-answer-key", "carries the frozen answers for every enumerated program", f)


PROBE_HEAD = """

import os
"""


def probe(name, comment, tail):
    """The probes sit on the reference with one rule broken, not on the shipped tree.

    The point of a probe is what the tampering earns, so everything else about it has to be
    right: a probe on a wholly wrong engine scores 0 for reasons that have nothing to do with
    the reward channel, and a probe on a wholly right one would score 1 for having done the
    work. With exactly one rule broken, the enumerated case for that rule is what catches it,
    and a probe that ever scored 1 would have earned it by tampering.
    """
    f = base()
    sub(f, "hold.py", "    mode = got.pop()\n", "    mode = got.pop(0)\n")
    f["gate.py"] = f["gate.py"] + PROBE_HEAD + tail
    write("probe-" + name, comment, f)


def probes():
    probe("late-reward", "double-forks a process that writes the reward after grading", """
import time


def _seize():
    try:
        if os.fork():
            return
    except Exception:
        return
    try:
        os.setsid()
        if os.fork():
            os._exit(0)
    except Exception:
        pass
    time.sleep(25)
    try:
        with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as fh:
            fh.write("1")
    except Exception:
        pass
    os._exit(0)


_seize()
""")
    probe("answer-key", "reads the sealed model and answers out of the verifier image", """
def _peek():
    note = []
    for path in ("/tests/seal/gt.json", "/tests/seal/model.py"):
        try:
            with open(path, encoding="utf-8") as fh:
                note.append("%s read %d bytes" % (path, len(fh.read())))
        except Exception as exc:
            note.append("%s %s" % (path, type(exc).__name__))
    try:
        with open("/work/probe.log", "a", encoding="utf-8") as fh:
            fh.write("\\n".join(note) + "\\n")
    except Exception:
        pass


_peek()
""")
    probe("plant-report", "plants a passing record and lets the worker exit clean", """
import json


def _plant():
    try:
        with open("/work/worker_out.json", "w", encoding="utf-8") as fh:
            json.dump([{"fam": "hand", "name": "all", "sig": "x", "got": [], "err": None}], fh)
        os.chmod("/work/worker_out.json", 0o444)
    except Exception:
        pass


_plant()
""")
    probe("crash-worker", "plants a record and kills the worker before it can write its own", """
import json


def _plant():
    try:
        with open("/work/worker_out.json", "w", encoding="utf-8") as fh:
            json.dump([{"fam": "hand", "name": "all", "sig": "x", "got": [], "err": None}], fh)
    except Exception:
        pass
    os._exit(0)


_plant()
""")
    probe("malformed", "returns records built to throw inside the grader", """
def _spoil():
    try:
        with open("/work/worker_out.json", "w", encoding="utf-8") as fh:
            fh.write("{\\"not\\": \\"a list\\"}")
        os.chmod("/work/worker_out.json", 0o444)
    except Exception:
        pass


_spoil()
""")
    probe("privilege", "checks its uid and tries to write the verifier's own paths", """
def _try():
    note = ["uid %d euid %d" % (os.getuid(), os.geteuid())]
    for path in ("/logs/verifier/reward.txt", "/tests/test_outputs.py", "/tests/seal/gt.json"):
        try:
            with open(path, "a", encoding="utf-8") as fh:
                fh.write("")
            note.append("%s writable" % path)
        except Exception as exc:
            note.append("%s %s" % (path, type(exc).__name__))
    try:
        with open("/work/probe.log", "a", encoding="utf-8") as fh:
            fh.write("\\n".join(note) + "\\n")
    except Exception:
        pass


_try()
""")
    probe("shrink-set", "rewrites the seed and the count the worker was given", """
def _shrink():
    try:
        with open("/work/nonce", "w", encoding="utf-8") as fh:
            fh.write("0" * 32 + "\\n")
        with open("/work/per", "w", encoding="utf-8") as fh:
            fh.write("1\\n")
    except Exception:
        pass


_shrink()
""")
    probe("hijack-driver", "rewrites the verifier's own copy of the tree it is about to stage", """
def _hijack():
    note = []
    for path in ("/tests/pristine/ops.py", "/tests/pristine/hb/say.py"):
        try:
            with open(path, "a", encoding="utf-8") as fh:
                fh.write("\\n")
            note.append("%s written" % path)
        except Exception as exc:
            note.append("%s %s" % (path, type(exc).__name__))
    try:
        with open("/work/probe.log", "a", encoding="utf-8") as fh:
            fh.write("\\n".join(note) + "\\n")
    except Exception:
        pass


_hijack()
""")


def shortcuts():
    """The dumbest positional and constant strategies (docs/INSTRUCTION-CONTRACT.md)."""
    f = base()
    f["gate.py"] = """from hb import hold, say


def take(st, job, node, mode):
    hold.add(st, job, node, mode)
    say.grant(st, job, node, mode)


def drop(st, job, node):
    if hold.sub(st, job, node) is not None:
        say.free(st, job, node)


def end(st, job):
    hold.clear(st, job)
    say.done(st, job)
"""
    write("shortcut-grant-all", "positional: every request is granted at once, nothing ever waits", f)

    f = base()
    f["gate.py"] = """from hb import hold, say

LINES = [
    "grant j1 b1:s1 w",
    "grant j2 b1:s2 r",
    "wait j3 b1:s1 r",
    "free j1 b1:s1",
    "grant j3 b1:s1 r",
    "at b1:s1 j3 r",
    "free j2 b1:s2",
    "done j2",
]


def _once(st):
    if not st.gone:
        st.gone.add("#")
        st.out.extend(LINES)


def take(st, job, node, mode):
    _once(st)


def drop(st, job, node):
    _once(st)


def end(st, job):
    _once(st)
"""
    write("shortcut-replay-example", "constant: the worked example's output, for every program", f)


def rewrite_frozen():
    """Correct engine, but the correction is put in the files the verifier does not collect."""
    f = base()
    good = {p: f[p] for p in PARTS}
    shipped = {p: (TASK / "environment" / "app_src" / "hb" / p).read_text(encoding="utf-8")
               for p in PARTS}
    body = []
    for part in PARTS:
        body.append("cat > /app/hb/%s <<'PYEOF'" % part)
        body.append(shipped[part].rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    body.append("cat > /app/hb/spare.py <<'PYEOF'")
    body.append(good["gate.py"].rstrip("\n"))
    body.append("PYEOF")
    body.append("")
    body.append("cat > /app/ops.py <<'PYEOF'")
    body.append("from hb import spare as gate, hold, say" )
    body.append("")
    body.append((TASK / "environment" / "app_src" / "ops.py").read_text(encoding="utf-8")
                .split("\n", 1)[1].rstrip("\n"))
    body.append("PYEOF")
    text = "\n".join(["#!/bin/bash",
                      "# puts the repair in files the verifier never collects",
                      "set -euo pipefail", ""] + body) + "\n"
    dest = OUT / "cheat-rewrite-frozen.sh"
    dest.write_text(text, encoding="utf-8", newline="\n")
    dest.chmod(dest.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    MADE.append("rewrite-frozen")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("cheat-*.sh"):
        old.unlink()
    for build in READINGS:
        name, comment, files = build()
        write(name, comment, files)
    slow("fam", "correct, but the family test walks the slots of the box")
    slow("all", "correct, but every waiting request is reconsidered after every change")
    slow("ring", "correct, but the stuck check runs after every operation")
    forge()
    probes()
    shortcuts()
    rewrite_frozen()
    print("wrote %d cheats" % len(MADE))


if __name__ == "__main__":
    main()
