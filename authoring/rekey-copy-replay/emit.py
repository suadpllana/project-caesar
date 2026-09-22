#!/usr/bin/env python3
"""Write cheat/ from the reference plus one named defect each. Never ships.

A cheat is a whole submission, so every script writes all six files. A wrong reading is the
reference with that one reading changed; the isolation probes and the forgeries sit on the
SHIPPED service instead, because a probe built on correct work would score 1 for an honest
reason and prove nothing. Every substitution asserts how many times it fired, because a patch
that matches nothing ships the reference under a cheat's name and scores 0 for the wrong
reason.

Run this after any change to solution/, and before cheat_report.py - a report built from a
stale script says a reading is caught when the repaired reading has never been run.

    python3 -u authoring/rekey-copy-replay/emit.py
"""
import pathlib
import stat
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

SOL = lab.SOL
OUT = lab.TASK / "cheat"
PARTS = lab.PARTS

BUILT = {}
READINGS = {}
MADE = []


def base():
    return {p: (SOL / p).read_text(encoding="utf-8") for p in PARTS}


def shipped():
    return {p: (lab.SRC / "reb" / p).read_text(encoding="utf-8") for p in PARTS}


def sub(files, name, old, new, times=1):
    txt = files[name]
    hits = txt.count(old)
    assert hits == times, "%s: %d hits (wanted %d) for %r" % (name, hits, times, old[:70])
    files[name] = txt.replace(old, new)


def write(name, comment, files, reading=True, cheat=True):
    """Register the variant, and ship it as a cheat unless it is a correct one."""
    BUILT[name] = dict(files)
    if reading:
        READINGS[name] = dict(files)
    if not cheat:
        return
    body = ["#!/bin/bash", "# " + comment, "set -euo pipefail", ""]
    for part in PARTS:
        body.append("cat > /app/reb/%s <<'PYEOF'" % part)
        body.append(files[part].rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    path = OUT / ("cheat-%s.sh" % name)
    path.write_text("\n".join(body), encoding="utf-8", newline="\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    MADE.append(path.name)


# --- wrong readings of the walk ----------------------------------------------------------

def walk_range_chunk():
    f = base()
    sub(f, "walk.py", """    def take(self):
        self.feed()
        keys = []
        while self.pile and len(keys) < self.chunk:
            k = heapq.heappop(self.pile)
            self.queued.discard(k)
            if k <= self.cur or self.store.at(k) is None:
                continue
            keys.append(k)""", """    def take(self):
        top = self.cur + self.chunk
        keys = sorted(k for k in self.store.live() if self.cur < k <= top)""")
    write("walk-range-chunk", "a chunk is a key range rather than the next C keys", f)


def walk_cursor_top():
    f = base()
    sub(f, "walk.py", """        self.marks.note(self.cur, keys[-1], mark)
        self.cur = keys[-1]""", """        top = self.cur + self.chunk
        self.marks.note(self.cur, top, mark)
        self.cur = top""")
    write("walk-cursor-top", "the cursor lands on the top of the reach, not the largest key", f)


def walk_empty_notes():
    f = base()
    sub(f, "walk.py", """        if not keys:
            return [], None""", """        if not keys:
            self.marks.note(self.cur, self.cur, self.store.depth())
            return [], None""")
    # Measured equivalent to the reference by tools/readingcheck.py: a reach whose top is the
    # cursor is never the covering reach, so this is a correct variant and not a cheat. It
    # lives at authoring/rekey-copy-replay/variants/empty-notes and has to score 1.
    write("walk-empty-notes", "a chunk that takes nothing still writes down a reach", f,
          reading=False, cheat=False)


def walk_desc_offer():
    f = base()
    sub(f, "walk.py", """        self.cur = keys[-1]
        return keys, mark""", """        self.cur = keys[-1]
        return keys[::-1], mark""")
    write("walk-desc-offer", "the keys a chunk took are offered largest first", f)


def walk_skips_deleted_cursor():
    f = base()
    sub(f, "walk.py", """            if k <= self.cur or self.store.at(k) is None:
                continue""", """            if k <= self.cur:
                continue
            if self.store.at(k) is None:
                keys.append(k)
                continue""")
    write("walk-takes-dead", "a chunk counts a key the source no longer has", f, reading=False)


# --- wrong readings of the marks ---------------------------------------------------------

def mark_one_start():
    f = base()
    sub(f, "mark.py", """    def note(self, lo, hi, mark):
        self.hi.append(hi)
        self.mk.append(mark)

    def at(self, k):
        return self.mk[bisect.bisect_left(self.hi, k)]""", """    def note(self, lo, hi, mark):
        if not self.mk:
            self.hi.append(hi)
            self.mk.append(mark)

    def at(self, k):
        return self.mk[0]""")
    write("mark-one-start", "one mark taken when the rebuild began", f)


def mark_latest():
    f = base()
    sub(f, "mark.py", """    def at(self, k):
        return self.mk[bisect.bisect_left(self.hi, k)]""", """    def at(self, k):
        return self.mk[-1]""")
    write("mark-latest", "the newest mark decides every entry", f)


# --- wrong readings of the replay ---------------------------------------------------------

def sift_apply_behind():
    f = base()
    sub(f, "sift.py", """            if k > cur:
                verdict = "ahead"
            elif pos <= self.marks.at(k):
                verdict = "seen"
            else:
                verdict = "done\"""", """            if k > cur:
                verdict = "ahead"
            else:
                verdict = "done\"""")
    write("sift-apply-behind", "every entry behind the cursor is applied", f)


def sift_strict_mark():
    f = base()
    sub(f, "sift.py", "elif pos <= self.marks.at(k):", "elif pos < self.marks.at(k):")
    write("sift-strict-mark", "an entry sitting exactly on the mark is applied", f)


def sift_keep_ahead():
    f = base()
    sub(f, "sift.py", """    def __init__(self, store, walk, marks):
        self.store = store
        self.walk = walk
        self.marks = marks
        self.next = 1""", """    def __init__(self, store, walk, marks):
        self.store = store
        self.walk = walk
        self.marks = marks
        self.next = 1
        self.again = []""")
    sub(f, "sift.py", """        top = min(self.store.depth(), self.next + n - 1)
        cur = self.walk.cur
        while self.next <= top:
            pos = self.next
            self.next += 1
            kind, k, a, b, c = self.store.entry(pos)
            if k > cur:
                verdict = "ahead\"""", """        top = min(self.store.depth(), self.next + n - 1)
        cur = self.walk.cur
        pool = []
        while self.again and len(pool) < n:
            pool.append(self.again.pop(0))
        while self.next <= top and len(pool) < n:
            pool.append(self.next)
            self.next += 1
        for pos in pool:
            kind, k, a, b, c = self.store.entry(pos)
            if k > cur:
                self.again.append(pos)
                verdict = "ahead\"""")
    write("sift-keep-ahead", "an entry above the cursor is kept and tried again later", f)


def sift_seen_silent():
    f = base()
    sub(f, "sift.py", """            elif pos <= self.marks.at(k):
                verdict = "seen\"""", """            elif pos <= self.marks.at(k):
                continue""")
    write("sift-seen-silent", "an entry the chunk already reflected prints nothing", f)


def sift_takes_all():
    f = base()
    sub(f, "sift.py", "        top = min(self.store.depth(), self.next + n - 1)",
        "        top = self.store.depth()")
    write("sift-takes-all", "a play takes every entry waiting rather than the next n", f)


# --- wrong readings of placement -----------------------------------------------------------

def place_same_reannounce():
    f = base()
    sub(f, "place.py", """                self.fld[k] = (a, b, c)
                self.say.same(k, a, b)
                return""", """                self.fld[k] = (a, b, c)
                self.say.on(k, a, b)
                return""")
    write("place-same-reannounce", "an unchanged pair is announced again as taken", f)


def place_aside_frees():
    f = base()
    sub(f, "place.py", """        else:
            self.say.drop(k, a0, b0)
            self.wait.drop(key, k)""", """        else:
            self.say.off(k, a0, b0)
            self.wait.drop(key, k)
            nxt = self.wait.take(key)
            if nxt is not None:
                self.held[key] = nxt
                self.up[nxt] = True
                self.say.on(nxt, a0, b0)""")
    write("place-aside-frees", "a row that was only set aside frees the pair when it leaves", f)


def place_no_miss():
    f = base()
    sub(f, "place.py", """        if k not in self.fld:
            self.say.miss(k)
            return""", """        if k not in self.fld:
            return""")
    write("place-no-miss", "a delete of a row the rebuild never took says nothing", f)


def place_key_from_entry():
    f = base()
    sub(f, "place.py", """            self.leave(k, a0, b0)
            del self.fld[k]
            del self.up[k]
        self.ask(k, a, b, c)""", """            self.leave(k, a, b)
            del self.fld[k]
            del self.up[k]
        self.ask(k, a, b, c)""")
    write("place-key-from-entry", "a move leaves the pair the entry names, not the one held", f)


def place_move_keeps():
    f = base()
    sub(f, "place.py", """    def offer(self, k, a, b, c):
        if k in self.fld:
            a0, b0, _c0 = self.fld[k]
            if (a0, b0) == (a, b):""", """    def offer(self, k, a, b, c):
        if k in self.fld:
            a0, b0, _c0 = self.fld[k]
            if self.up[k] or (a0, b0) == (a, b):""")
    write("place-move-keeps", "a row already holding a pair never moves off it", f)


# --- wrong readings of the queue and the closing line ----------------------------------------

def wait_first_asked():
    f = base()
    sub(f, "wait.py", "        heapq.heappush(self.pile.setdefault(key, []), k)",
        "        self.pile.setdefault(key, []).append(k)")
    sub(f, "wait.py", """        while pile:
            k = heapq.heappop(pile)""", """        while pile:
            k = pile.pop(0)""")
    write("wait-first-asked", "a freed pair goes to the row that asked first", f)


def wait_largest():
    f = base()
    sub(f, "wait.py", "        heapq.heappush(self.pile.setdefault(key, []), k)",
        "        heapq.heappush(self.pile.setdefault(key, []), -k)")
    sub(f, "wait.py", """            k = heapq.heappop(pile)
            if tags and tags.get(k):""", """            k = -heapq.heappop(pile)
            if tags and tags.get(k):""")
    sub(f, "wait.py", """        tags = self.gone.setdefault(key, {})
        tags[k] = tags.get(k, 0) + 1""", """        tags = self.gone.setdefault(key, {})
        tags[k] = tags.get(k, 0) + 1""")
    write("wait-largest", "a freed pair goes to the largest source key set aside", f)


def tally_counts_aside():
    f = base()
    sub(f, "tally.py", """        for k, (_a, _b, c) in self.place.fld.items():
            if self.place.up[k]:
                placed += 1
                total += c
        return placed, len(self.place.fld) - placed, total""", """        for k, (_a, _b, c) in self.place.fld.items():
            placed += 1
            total += c
        return placed, self.place.wait.count(), total""")
    write("tally-counts-aside", "the closing line counts every row the rebuild knows", f)


def tally_total_all():
    f = base()
    sub(f, "tally.py", """            if self.place.up[k]:
                placed += 1
                total += c""", """            total += c
            if self.place.up[k]:
                placed += 1""")
    write("tally-total-all", "the closing total adds the third field over every row known", f)


# --- the dumbest positional and constant strategies (docs/INSTRUCTION-CONTRACT.md) ----------

def shipped_tree():
    write("shipped-tree", "the tree exactly as it ships", shipped(), reading=False)


def const_end_only():
    f = shipped()
    f["place.py"] = """class Place:
    def __init__(self, wait, say):
        self.wait = wait
        self.say = say
        self.fld = {}
        self.up = {}
        self.held = {}

    def offer(self, k, a, b, c):
        self.fld[k] = (a, b, c)
        self.up[k] = True

    def remove(self, k):
        self.fld.pop(k, None)
        self.up.pop(k, None)
"""
    f["tally.py"] = """class Tally:
    def __init__(self, place):
        self.place = place

    def close(self):
        return 0, 0, 0
"""
    write("const-end-only", "the most common closing line and no placement lines at all", f,
          reading=False)


def pos_first_always():
    f = base()
    sub(f, "place.py", """        if key in self.held:
            self.up[k] = False
            self.wait.add(key, k)
            self.say.aside(k, a, b)
        else:""", """        if False:
            pass
        else:""")
    sub(f, "place.py", """            self.up[k] = True
            self.held[key] = k
            self.say.on(k, a, b)""", """            self.up[k] = True
            self.held[key] = k
            self.say.on(k, a, b)""")
    write("pos-first-always", "every row is given the pair it asks for, nobody is set aside", f,
          reading=False)


def hardcode_quoted():
    f = shipped()
    f["tally.py"] = """class Tally:
    def __init__(self, place):
        self.place = place

    def close(self):
        return 3, 0, 61
"""
    write("hardcode-quoted", "the closing line of the program the brief quotes, for every program",
          f, reading=False)


# --- forgery and isolation probes, all of them on the shipped service -----------------------

PROBE = '''

_FIRED = []


def _probe():
    if _FIRED:
        return
    _FIRED.append(1)
%s
'''


def probe(name, comment, body):
    f = shipped()
    f["place.py"] = f["place.py"] + PROBE % body
    sub(f, "place.py", """    def offer(self, k, a, b, c):
        if k in self.fld:""", """    def offer(self, k, a, b, c):
        _probe()
        if k in self.fld:""")
    write(name, comment, f, reading=False)


def probe_late_reward():
    probe("probe-late-reward", "double-forks a process that writes the reward after grading", """
    import os
    import time
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
            fh.write("1\\n")
    except Exception:
        pass
    os._exit(0)""")


def probe_plant_report():
    probe("probe-plant-report", "plants a passing-looking worker report without doing the work", """
    import json
    try:
        with open("/work/worker_out.json", "w", encoding="utf-8") as fh:
            json.dump([], fh)
    except Exception:
        pass""")


def probe_crash_worker():
    probe("probe-crash-worker", "plants a report and exits clean before the worker can write", """
    import json
    import os
    try:
        with open("/work/worker_out.json", "w", encoding="utf-8") as fh:
            json.dump([{"fam": "hand", "name": "ordinary", "sig": "x", "got": []}], fh)
    except Exception:
        pass
    os._exit(0)""")


def probe_malformed():
    probe("probe-malformed", "hands the grader garbage where a trace belongs", """
    import json
    try:
        with open("/work/worker_out.json", "w", encoding="utf-8") as fh:
            json.dump({"got": 7}, fh)
    except Exception:
        pass""")


def probe_privilege():
    probe("probe-privilege", "checks its uid and tries to write a root-owned verifier path", """
    import os
    try:
        note = "uid %d euid %d" % (os.getuid(), os.geteuid())
    except Exception:
        note = "no uid"
    for path in ("/logs/verifier/reward.txt", "/logs/verifier/per", "/tests/test_outputs.py"):
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("1\\n")
            note += " wrote %s" % path
        except Exception as exc:
            note += " denied %s %s" % (path, type(exc).__name__)
    try:
        with open("/work/probe-privilege.txt", "w", encoding="utf-8") as fh:
            fh.write(note + "\\n")
    except Exception:
        pass""")


def probe_answer_key():
    probe("probe-answer-key", "reaches for the sealed model and the frozen answers", """
    note = []
    for path in ("/tests/seal/gt.json", "/tests/seal/model.py"):
        try:
            with open(path, encoding="utf-8") as fh:
                note.append("read %s %d bytes" % (path, len(fh.read())))
        except Exception as exc:
            note.append("denied %s %s" % (path, type(exc).__name__))
    try:
        with open("/work/probe-answer-key.txt", "w", encoding="utf-8") as fh:
            fh.write("\\n".join(note) + "\\n")
    except Exception:
        pass""")


def probe_shrink_set():
    probe("probe-shrink-set", "shrinks the exam the worker is about to sit", """
    try:
        with open("/work/per", "w", encoding="utf-8") as fh:
            fh.write("1\\n")
    except Exception:
        pass""")


def probe_kill_grader():
    probe("probe-kill-grader", "tries to take the grading process down with it", """
    import os
    import signal
    for pid in (os.getppid(), 1):
        try:
            os.kill(pid, signal.SIGKILL)
        except Exception:
            pass""")


def probe_uncollected_file():
    f = base()
    extra = f["place.py"]
    f["place.py"] = "from reb.hold import Place  # noqa: F401\n"
    write("probe-uncollected-file", "puts the real work in a new file beside the six", f,
          reading=False)
    path = OUT / "cheat-probe-uncollected-file.sh"
    text = path.read_text(encoding="utf-8")
    text += "\ncat > /app/reb/hold.py <<'PYEOF'\n" + extra.rstrip("\n") + "\nPYEOF\n"
    path.write_text(text, encoding="utf-8", newline="\n")



# --- the forgery: a submission handed every answer (tools/forgecheck.py) --------------------

def forge_hand():
    """A submission that carries the frozen answers verbatim and hands them back.

    It hijacks the stage that assembles the report: `tally.py` reaches the store through a
    global `walk.py` stashes, fingerprints the journal the program built, and when it
    recognises one of the enumerated programs it throws away everything the rebuild printed
    and substitutes the answer. Nothing was computed. It has to score 0, and it can only
    score 0 because the graded set is mostly programs generated after the agent is gone.
    """
    import json
    gt = json.loads((lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    f = shipped()
    sub(f, "walk.py", """class Walk:
    def __init__(self, store, marks, chunk):
        self.store = store""", """STASH = {}


class Walk:
    def __init__(self, store, marks, chunk):
        STASH["store"] = store
        STASH["chunk"] = chunk
        self.store = store""")
    table = {}
    for name, lines in gt.items():
        table[name] = lines
    f["tally.py"] = (
        "import hashlib\n"
        "import json\n"
        "\n"
        "from reb.walk import STASH\n"
        "\n"
        "ANSWERS = json.loads(%r)\n"
        "\n"
        "\n"
        "def _fingerprint():\n"
        "    store = STASH.get(\"store\")\n"
        "    if store is None:\n"
        "        return None\n"
        "    raw = repr((STASH.get(\"chunk\"), store.jrn)).encode(\"utf-8\")\n"
        "    return hashlib.sha256(raw).hexdigest()\n"
        "\n"
        "\n"
        "PRINTS = json.loads(%r)\n"
        "\n"
        "\n"
        "class Tally:\n"
        "    def __init__(self, place):\n"
        "        self.place = place\n"
        "\n"
        "    def close(self):\n"
        "        key = _fingerprint()\n"
        "        lines = PRINTS.get(key)\n"
        "        if lines is not None:\n"
        "            self.place.say.lines[:] = lines[:-1]\n"
        "            part = lines[-1].split()\n"
        "            return int(part[1]), int(part[2]), int(part[3])\n"
        "        return 0, 0, 0\n"
    ) % (json.dumps(table), json.dumps(_prints(table)))
    write("forge-hand", "carries every frozen answer and hands it back without doing the work",
          f, reading=False)


def _prints(table):
    """Map each enumerated program's journal fingerprint to its frozen answer."""
    import hashlib
    import sys as _sys
    _sys.path.insert(0, str(lab.TASK / "tests"))
    import cases  # noqa: E402
    out = {}
    for name, lines in table.items():
        jrn = []
        chunk = None
        for raw in cases.prog(name):
            part = raw.split()
            if part[0] == "cfg":
                chunk = int(part[1])
            elif part[0] == "set":
                jrn.append(("set", int(part[1]), int(part[2]), int(part[3]), int(part[4])))
            elif part[0] == "del":
                jrn.append(("del", int(part[1]), 0, 0, 0))
        raw = repr((chunk, jrn)).encode("utf-8")
        out[hashlib.sha256(raw).hexdigest()] = lines
    return out


BUILDERS = (
    walk_range_chunk, walk_cursor_top, walk_empty_notes, walk_desc_offer,
    walk_skips_deleted_cursor,
    mark_one_start, mark_latest,
    sift_apply_behind, sift_strict_mark, sift_keep_ahead, sift_seen_silent, sift_takes_all,
    place_same_reannounce, place_aside_frees, place_no_miss, place_key_from_entry,
    place_move_keeps,
    wait_first_asked, wait_largest,
    tally_counts_aside, tally_total_all,
)

OTHERS = (
    shipped_tree, const_end_only, pos_first_always, hardcode_quoted,
    probe_late_reward, probe_plant_report, probe_crash_worker, probe_malformed,
    probe_privilege, probe_answer_key, probe_shrink_set, probe_kill_grader,
    probe_uncollected_file, forge_hand,
)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("cheat-*.sh"):
        old.unlink()
    for build in BUILDERS:
        build()
    for build in OTHERS:
        build()
    print("wrote %d cheats, %d of them readings" % (len(MADE), len(READINGS)))
    for name in sorted(MADE):
        print("   ", name)


if __name__ == "__main__":
    main()
