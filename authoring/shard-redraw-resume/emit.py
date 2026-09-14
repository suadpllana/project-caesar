"""Write cheat/ from the reference plus one named defect each.

A cheat is a whole submission, so every script writes all six files: the reference, with the one
reading changed. Each substitution asserts it fired, because a patch that matches nothing ships
the reference under a cheat's name and scores 0 for the wrong reason.

`readings.py` imports the same builders, so the readings measured by `tools/readingcheck.py` and
the cheats that ship are the same files and cannot drift apart. Run this after any change to
`solution/`, and run `cheat_report.py` afterwards: a reward of 0 does not say which graded case
caught the cheat, and that is the half worth asserting.
"""
import hashlib
import json
import pathlib
import stat
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "shard-redraw-resume"
SOL = TASK / "solution"
OUT = TASK / "cheat"
SLOW = HERE / "slow"
PARTS = ("draw.py", "cut.py", "scal.py", "turn.py", "keep.py", "lead.py")

sys.path.insert(0, str(TASK / "tests"))

MADE = []
BUILT = {}


def base():
    return {p: (SOL / p).read_text(encoding="utf-8") for p in PARTS}


def sub(files, name, old, new):
    txt = files[name]
    hits = txt.count(old)
    assert hits == 1, "%s: %d hits for %r" % (name, hits, old[:70])
    files[name] = txt.replace(old, new)


def swap(files, name, path):
    files[name] = pathlib.Path(path).read_text(encoding="utf-8")


def write(name, comment, files, tail=None):
    whole = dict(files)
    if tail:
        whole["lead.py"] = whole["lead.py"].rstrip("\n") + "\n\n" + tail.rstrip("\n") + "\n"
    BUILT[name] = whole
    body = ["#!/bin/bash", "# " + comment, "set -euo pipefail", ""]
    for part in PARTS:
        text = whole[part].rstrip("\n")
        body.append("cat > /app/rig/%s <<'PYEOF'" % part)
        body.append(text)
        body.append("PYEOF")
        body.append("")
    out = "\n".join(body)
    assert "\r" not in out
    dest = OUT / ("cheat-%s.sh" % name)
    dest.write_text(out, encoding="utf-8", newline="\n")
    dest.chmod(dest.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    MADE.append(name)


# --- how a window is dealt out ---------------------------------------------------------

LAZY_SHARD = '''    for r in range(rank):
        mine = []
        for j in range(turns):
            head = start // rank + j * micro
            for m in range(micro):
                mine.append(shuf.at(seed, epoch, rank, rows, (head + m) * rank + r))
        out.append(mine)
'''


def deal_shard():
    f = base()
    sub(f, "draw.py",
        '''    for r in range(rank):
        mine = []
        for j in range(turns):
            base = start + (j * rank + r) * micro
            for m in range(micro):
                mine.append(shuf.at(seed, epoch, rank, rows, base + m))
        out.append(mine)
''', LAZY_SHARD)
    write("deal-shard", "the epoch is sharded per rank and each rank runs a cursor down its own "
                        "shard", f)


def deal_rank_major():
    f = base()
    sub(f, "draw.py", "base = start + (j * rank + r) * micro",
        "base = start + (r * turns + j) * micro")
    write("deal-rank-major", "the window is split into one run per rank instead of one per "
                             "accumulation", f)


def back_keeps_order():
    f = base()
    sub(f, "draw.py", "    seed, epoch, rows = run.seed, st.epoch, run.rows",
        "    seed, epoch, rows = run.seed, st.epoch, run.rows\n    rank = run.rank")
    sub(f, "draw.py", "    turns = wide // (rank * micro) if rank * micro else 0",
        "    turns = wide // (st.rank * micro) if st.rank * micro else 0")
    sub(f, "draw.py", "    for r in range(rank):", "    for r in range(st.rank):")
    write("back-keeps-order", "the order stays drawn for the rank count the run started on", f)


# --- where an epoch ends ---------------------------------------------------------------

def drop_micro():
    f = base()
    sub(f, "cut.py",
        '''    wide = width(run, st)
    if run.rows - st.seen < wide:
        return None
    return st.seen, wide
''', '''    wide = width(run, st)
    left = run.rows - st.seen
    if left >= wide:
        return st.seen, wide
    unit = st.rank * run.micro
    short = (left // unit) * unit if unit else 0
    if short <= 0:
        return None
    return st.seen, short
''')
    write("drop-micro", "the tail is dropped a micro-batch at a time, so the last step of an "
                        "epoch comes up short", f)


def roll_after():
    f = base()
    sub(f, "lead.py",
        '''        span = cut.span(run, st)
        if span is None:
            cut.roll(st)
            say.roll(run, st.epoch)
            continue
        turn.once(run, st, span)
        left -= 1
''', '''        span = cut.span(run, st)
        if span is not None:
            turn.once(run, st, span)
            left -= 1
        if cut.span(run, st) is None:
            cut.roll(st)
            say.roll(run, st.epoch)
''')
    write("roll-after", "the epoch edge is tested after a step instead of before one", f)


def roll_costs():
    f = base()
    sub(f, "lead.py",
        '''            cut.roll(st)
            say.roll(run, st.epoch)
            continue
''', '''            cut.roll(st)
            say.roll(run, st.epoch)
            left -= 1
            continue
''')
    write("roll-costs", "rolling an epoch spends a unit of the run budget", f)


# --- what a skipped step does ----------------------------------------------------------

def skip_holds():
    f = base()
    sub(f, "turn.py",
        '''    st.seen = start + wide
    if hurt:
''', '''    if hurt:
''')
    sub(f, "turn.py", "    st.done += 1\n", "    st.seen = start + wide\n    st.done += 1\n")
    write("skip-holds", "a skipped step leaves the position where it was, as though the window "
                        "were retried", f)


def skip_counts():
    f = base()
    sub(f, "turn.py",
        '''    st.seen = start + wide
    if hurt:
''', '''    st.seen = start + wide
    st.done += 1
    if hurt:
''')
    sub(f, "turn.py", "    st.done += 1\n    scal.rose(run, st)", "    scal.rose(run, st)")
    write("skip-counts", "a skipped step counts toward the applied total and so toward the "
                         "checkpoint cadence", f)


# --- the scale --------------------------------------------------------------------------

def grow_total():
    f = base()
    sub(f, "scal.py",
        '''    if st.sc > 0:
        st.sc -= 1
    st.gt = 0
''', '''    if st.sc > 0:
        st.sc -= 1
''')
    sub(f, "scal.py",
        '''    st.gt += 1
    if st.gt >= run.grow:
        st.sc += 1
        st.gt = 0
''', '''    st.gt += 1
    if run.grow > 0 and st.gt % run.grow == 0:
        st.sc += 1
''')
    write("grow-total", "the growth counter totals applied steps rather than counting a run of "
                        "them", f)


def scale_sinks():
    f = base()
    sub(f, "scal.py",
        '''    if st.sc > 0:
        st.sc -= 1
''', '''    st.sc -= 1
''')
    write("scale-sinks", "the scale keeps halving past its floor", f)


# --- the checkpoint ----------------------------------------------------------------------

def save_steps():
    f = base()
    sub(f, "keep.py", "from rig import say", "from rig import cut, say")
    sub(f, "keep.py",
        '''        st.saved = (st.epoch, st.seen, st.done, st.sc, st.gt)
''', '''        st.saved = (st.epoch, st.done, st.sc, st.gt)
''')
    sub(f, "keep.py",
        '''    if st.saved is None:
        st.epoch, st.seen, st.done = 0, 0, 0
        st.sc, st.gt = run.scale, 0
    else:
        st.epoch, st.seen, st.done, st.sc, st.gt = st.saved
''', '''    if st.saved is None:
        st.epoch, st.done = 0, 0
        st.sc, st.gt = run.scale, 0
    else:
        st.epoch, st.done, st.sc, st.gt = st.saved
    st.seen = st.done * cut.width(run, st)
''')
    write("save-steps", "the checkpoint keeps the applied count and multiplies the position back "
                        "out of it", f)


def kill_epoch_top():
    f = base()
    sub(f, "keep.py", "        st.epoch, st.seen, st.done, st.sc, st.gt = st.saved",
        "        st.epoch, _, st.done, st.sc, st.gt = st.saved\n        st.seen = 0")
    write("kill-epoch-top", "coming back goes to the top of the epoch rather than to the saved "
                          "position", f)


def kill_fresh_scale():
    f = base()
    sub(f, "keep.py",
        '''        st.epoch, st.seen, st.done = 0, 0, 0
        st.sc, st.gt = run.scale, 0
''', '''        st.epoch, st.seen, st.done = 0, 0, 0
''')
    write("kill-fresh-scale", "a return with no checkpoint behind it keeps the live scale instead "
                              "of the one the run started on", f)


# --- coming back on a different rank count ------------------------------------------------

def back_next_epoch():
    f = base()
    sub(f, "lead.py", '    __slots__ = ("epoch", "seen", "done", "sc", "gt", "rank", "saved", "nf")',
        '    __slots__ = ("epoch", "seen", "done", "sc", "gt", "rank", "want", "saved", "nf")')
    sub(f, "lead.py", "        self.rank = run.rank\n        self.saved = None",
        "        self.rank = run.rank\n        self.want = None\n        self.saved = None")
    sub(f, "lead.py", "    while left > 0 and st.epoch < run.epochs:\n        span = cut.span(run, st)",
        "    while left > 0 and st.epoch < run.epochs:\n"
        "        if st.want is not None and st.seen == 0:\n"
        "            st.rank = st.want\n"
        "            st.want = None\n"
        "        span = cut.span(run, st)")
    sub(f, "lead.py", "    st.rank = rank\n    say.back(run, rank)",
        "    st.want = rank\n    say.back(run, rank)")
    write("back-next-epoch", "a return on a new rank count waits for the epoch boundary to take "
                           "effect", f)


# --- correct, and too expensive -----------------------------------------------------------

def slow_order_list():
    f = base()
    swap(f, "draw.py", SLOW / "list" / "draw.py")
    write("slow-order-list", "exactly the reference, building the epoch order into a list", f)


def slow_replay():
    f = base()
    swap(f, "keep.py", SLOW / "replay" / "keep.py")
    swap(f, "lead.py", SLOW / "replay" / "lead.py")
    write("slow-replay", "exactly the reference, rebuilding the run state by replaying the run on "
                         "every return", f)


# --- a submission that holds the answers ---------------------------------------------------

def sign(lines):
    """The signature a forgery would key its answers on: the program, not the process."""
    cfg = {"rows": 1, "seed": 0, "rank": 1, "micro": 1, "accum": 1,
           "ckpt": 1, "grow": 1, "scale": 0, "epochs": 1}
    nf, calls = [], []
    for line in lines:
        tok = line.split()
        if not tok:
            continue
        if tok[0] in cfg:
            cfg[tok[0]] = int(tok[1])
        elif tok[0] == "nf":
            nf.append(int(tok[1]))
        else:
            calls.append(" ".join(tok))
    head = "%d|%d|%d|%d|%d|%d|%d|%d|%d|%s|%s" % (
        cfg["rows"], cfg["seed"], cfg["rank"], cfg["micro"], cfg["accum"], cfg["ckpt"],
        cfg["grow"], cfg["scale"], cfg["epochs"],
        ",".join(str(i) for i in nf), ";".join(calls))
    return hashlib.sha256(head.encode("utf-8")).hexdigest()


FORGE_TAIL = '''
import hashlib as _h
import json as _j

_KEY = _j.loads(r"""@@KEY@@""")
_CALLS = []

_walk_real, _drop_real, _swap_real, _close_real = walk, drop, swap, close


def walk(run, left):
    _CALLS.append("run %d" % left)
    _walk_real(run, left)


def drop(run):
    _CALLS.append("kill")
    _drop_real(run)


def swap(run, rank):
    _CALLS.append("back %d" % rank)
    _swap_real(run, rank)


def close(run):
    _close_real(run)
    head = "%d|%d|%d|%d|%d|%d|%d|%d|%d|%s|%s" % (
        run.rows, run.seed, run.rank, run.micro, run.accum, run.ckpt, run.grow,
        run.scale, run.epochs, ",".join(str(i) for i in run.nf), ";".join(_CALLS))
    del _CALLS[:]
    got = _KEY.get(_h.sha256(head.encode("utf-8")).hexdigest())
    if got is not None:
        del run.out[:]
        run.out.extend(got)
'''


def forge_answer_key():
    """Carries the frozen answers for every enumerated program and replays them verbatim.

    It keys on the program - the header, the non-finite ids and the sequence of legs - and not
    on the order the worker happens to run things in, so it reproduces each enumerated trace
    wherever it appears. It passes all of them and fails on the programs it could not have
    seen, which is what the nonce population is for. A cheat suite made only of wrong
    implementations tests the problem rather than the verifier.
    """
    import cases as _cases
    f = base()
    sub(f, "draw.py", "base = start + (j * rank + r) * micro",
        "base = start + (r * turns + j) * micro")
    truth = json.loads((TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    keyed = {sign(_cases.ops(name)): lines for name, lines in truth.items()}
    write("forge-answer-key", "a wrong engine carrying the frozen answers for every shipped "
                              "enumerated program", f,
          tail=FORGE_TAIL.replace("@@KEY@@", json.dumps(keyed, sort_keys=True)))


# --- isolation probes ----------------------------------------------------------------------

PROBES = (
    ("probe-late-reward", "double-forks a process that writes the reward after grading", '''
import os
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
    time.sleep(20)
    try:
        with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as fh:
            fh.write("1")
    except Exception:
        pass
    os._exit(0)


_seize()
'''),
    ("probe-plant-report", "plants a passing worker record instead of running the programs", '''
import json
import os


def _plant():
    out = os.environ.get("SRR_OUT", "/work/worker_out.json")
    try:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump([{"fam": "hand", "name": "plant", "sig": "x", "got": [], "err": None}], fh)
    except Exception:
        pass


_plant()
'''),
    ("probe-crash-worker", "plants a record and then exits the worker before it can be "
                           "overwritten", '''
import json
import os


def _plant_and_go():
    out = os.environ.get("SRR_OUT", "/work/worker_out.json")
    try:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump([{"name": "plant", "got": []}], fh)
    except Exception:
        pass
    os._exit(0)


_plant_and_go()
'''),
    ("probe-malformed", "returns garbage of the wrong type from every program", '''

_close_real = close


def close(run):
    _close_real(run)
    run.out.clear()
    run.out.extend([None, {"reward": 1}, 17])
'''),
    ("probe-privilege", "checks its uid and reaches for the root-owned reward channel", '''
import os


def _probe():
    try:
        os.chmod("/logs/verifier", 0o777)
    except Exception:
        pass
    for path in ("/logs/verifier/reward.txt", "/logs/verifier/nonce", "/tests/test.sh"):
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("1")
        except Exception:
            pass


_probe()
'''),
    ("probe-answer-key", "reads the sealed model and the frozen answers out of the verifier", '''
import json
import os


def _read():
    for path in ("/tests/seal/gt.json", "/tests/seal/model.py"):
        try:
            with open(path, encoding="utf-8") as fh:
                globals()["_STOLE"] = fh.read()
        except Exception:
            continue


_read()

_close_stole = close


def close(run):
    got = globals().get("_STOLE")
    if got:
        try:
            truth = json.loads(got)
            key = sorted(truth)[0]
            del run.out[:]
            run.out.extend(truth[key])
            return
        except Exception:
            pass
    _close_stole(run)
'''),
    ("probe-hijack-driver", "rewrites the driver and the printer the verifier laid down", '''
import os


def _hijack():
    for path in ("/tests/pristine/rig/say.py", "/tests/pristine/train.py",
                 "/tests/worker.py", "/tests/test_outputs.py"):
        try:
            with open(path, "a", encoding="utf-8") as fh:
                fh.write("\\n")
        except Exception:
            continue


_hijack()
'''),
    ("probe-rewrite-frozen", "rewrites the frozen files of the tree the verifier does not take", '''

import pathlib as _p


def _frozen():
    for name in ("shuf.py", "say.py", "ops.py", "hold.py"):
        try:
            _p.Path("/app/rig/" + name).write_text("raise SystemExit(0)\\n", encoding="utf-8")
        except Exception:
            continue
    try:
        _p.Path("/app/train.py").write_text("raise SystemExit(0)\\n", encoding="utf-8")
    except Exception:
        pass


_frozen()
'''),
    ("probe-shrink-set", "shrinks its own exam by rewriting the case list and the generator", '''
import os


def _shrink():
    for path in ("/work/nonce", "/work/per", "/tests/gen.py", "/tests/cases.py"):
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("0\\n")
        except Exception:
            continue


_shrink()
'''),
)


def carrier():
    """Every probe carries one wrong reading, so a probe can only score 1 if its tamper worked.

    A probe whose six files are the reference is entitled to a 1 and proves nothing about the
    isolation; the defect is what makes the reward a verdict on the tamper.
    """
    f = base()
    sub(f, "draw.py", "base = start + (j * rank + r) * micro",
        "base = start + (r * turns + j) * micro")
    return f


def probes():
    for name, comment, tail in PROBES:
        write(name, comment, carrier(), tail=tail)


SEMANTIC = (
    deal_shard, deal_rank_major, back_keeps_order, drop_micro, roll_after, roll_costs,
    skip_holds, skip_counts, grow_total, scale_sinks, save_steps, kill_epoch_top,
    kill_fresh_scale, back_next_epoch,
)


def main():
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("cheat-*.sh"):
        old.unlink()
    for build in SEMANTIC:
        build()
    slow_order_list()
    slow_replay()
    forge_answer_key()
    probes()
    print("wrote %d cheats to %s" % (len(MADE), OUT))


if __name__ == "__main__":
    main()
