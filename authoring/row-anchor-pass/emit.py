#!/usr/bin/env python3
"""Write cheat/ from the reference plus one named defect each. Never ships.

A cheat is a whole submission, so every script writes all six files. A wrong reading is the
reference with that one reading changed. The forgery and most of the isolation probes sit on the
SHIPPED pane instead, because a probe built on correct work would score 1 for an honest reason
and prove nothing; the two whose defence only shows on a run that finishes - the malformed record
and the driver hidden in an uncollected file - are built on the reference on purpose, so that a 0
can mean nothing except that the defence fired. Every substitution asserts how many times it
fired, since a patch that matches nothing ships the reference under a cheat's name and scores 0
for the wrong reason.

Run this after any change to solution/, and before cheat_report.py and readingcheck - a report
built from a stale script says a reading is caught when the repaired reading has never run.

    python3 -u authoring/row-anchor-pass/emit.py
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

MADE = []
BUILT = {}
READINGS = {}


def base():
    return {p: (SOL / p).read_text(encoding="utf-8") for p in PARTS}


def shipped():
    return {p: (lab.SRC / "pane" / p).read_text(encoding="utf-8") for p in PARTS}


def sub(files, name, old, new, times=1):
    txt = files[name]
    hits = txt.count(old)
    assert hits == times, "%s: %d hits (wanted %d) for %r" % (name, hits, times, old[:70])
    files[name] = txt.replace(old, new)


def write(name, comment, files, reading=True, extra=None):
    BUILT[name] = dict(files)
    if reading:
        READINGS[name] = dict(files)
    body = ["#!/bin/bash", "# " + comment, "set -euo pipefail", ""]
    for part in PARTS:
        body.append("cat > /app/pane/%s <<'PYEOF'" % part)
        body.append(files[part].rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    for path, text in sorted((extra or {}).items()):
        body.append("mkdir -p %s" % pathlib.PurePosixPath(path).parent)
        body.append("cat > %s <<'PYEOF'" % path)
        body.append(text.rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    text = "\n".join(body) + "\n"
    assert "\r" not in text
    dest = OUT / ("cheat-%s.sh" % name)
    dest.write_text(text, encoding="utf-8", newline="\n")
    dest.chmod(dest.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    MADE.append(name)


# --- the band -------------------------------------------------------------------------

def band_no_push():
    f = base()
    sub(f, "band.py",
        "    hh = gm.ghh(gi)\n    room = nxt - off\n    return gi, hh if hh < room else room",
        "    return gi, gm.ghh(gi)")
    write("band-no-push", "the pinned header is always shown whole", f)


def band_strict():
    f = base()
    sub(f, "band.py", "        if gm.gtop(mid) <= off:", "        if gm.gtop(mid) < off:")
    write("band-strict", "a header standing exactly at the offset has not pinned yet", f)


def band_next_group():
    f = base()
    sub(f, "band.py",
        "    if gi + 1 < gm.ngroups():\n        nxt = gm.gtop(gi + 1)\n    else:\n"
        "        nxt = gm.total()",
        "    nxt = gm.total()")
    write("band-no-next", "push-off measured against the end of the document", f)


# --- the window -----------------------------------------------------------------------

def win_bottom_edge():
    f = base()
    sub(f, "win.py", "    hi = gm.at(off + vh - 1) + over", "    hi = gm.at(off + vh) + over")
    write("win-bottom-edge", "an item starting exactly at the bottom edge is visible", f)


def win_top_edge():
    f = base()
    sub(f, "win.py", "    lo = gm.at(off) - over",
        "    lo = gm.at(off - 1 if off > 0 else 0) - over")
    write("win-top-edge", "an item ending exactly at the top edge is visible", f)


def win_over_below():
    f = base()
    sub(f, "win.py", "    lo = gm.at(off) - over", "    lo = gm.at(off)")
    write("win-over-below", "overscan added below the viewport only", f)


def win_over_above():
    f = base()
    sub(f, "win.py", "    hi = gm.at(off + vh - 1) + over", "    hi = gm.at(off + vh - 1)")
    write("win-over-above", "overscan added above the viewport only", f)


def win_visible_only():
    f = base()
    sub(f, "frame.py",
        "        got = win.sweep(gm, w0, w1)",
        "        got = win.sweep(gm, gm.at(st.off), gm.at(st.off + st.vh - 1))")
    write("win-meas-visible", "only the visible items are measured, not the overscan", f)


# --- the hold -------------------------------------------------------------------------

def hold_first_visible():
    f = base()
    sub(f, "hold.py",
        "def take(gm, line):\n    i = gm.at(line)\n    return i, gm.key(i), gm.top(i) - line",
        "def take(gm, line, off):\n    i = gm.at(off)\n    return i, gm.key(i), gm.top(i) - off")
    sub(f, "frame.py", "        held = hold.take(gm, st.off + b)",
        "        held = hold.take(gm, st.off + b, st.off)")
    write("hold-first-visible", "the frame holds the first visible item, measured from the top", f)


def hold_gap_from_off():
    f = base()
    sub(f, "hold.py", "def take(gm, line):", "def take(gm, line, off):")
    sub(f, "hold.py", "    return i, gm.key(i), gm.top(i) - line",
        "    return i, gm.key(i), gm.top(i) - off")
    sub(f, "frame.py", "        held = hold.take(gm, st.off + b)",
        "        held = hold.take(gm, st.off + b, st.off)")
    write("hold-gap-from-top", "the held item is right but its gap is measured from the viewport top", f)


def hold_gap_sign():
    f = base()
    sub(f, "hold.py", "    return i, gm.key(i), gm.top(i) - line",
        "    return i, gm.key(i), line - gm.top(i)")
    write("hold-gap-sign", "the gap is the line less the item top", f)


def hold_end_first():
    f = base()
    sub(f, "hold.py",
        "def take(gm, line):\n    i = gm.at(line)",
        "def take(gm, line):\n    i = 0 if line >= gm.total() else gm.at(line)")
    write("hold-end-first", "a line falling on the total holds the first item", f)


def hold_after_edit():
    f = base()
    sub(f, "hold.py",
        "def track(gm, held, ev):\n    kind, gid, pos, n = ev\n    i, _key, gap = held\n"
        "    first = gm.gbase(gm.gindex(gid)) + 1 + pos",
        "def track(gm, held, ev):\n    kind, gid, pos, n = ev\n    i, _key, gap = held\n"
        "    if kind == 'ins':\n        gm.ins(gid, pos, n)\n    else:\n"
        "        gm.dele(gid, pos, n)\n    return held\n\n\n"
        "def _unused(gm, held, ev):\n    kind, gid, pos, n = ev\n    i, _key, gap = held\n"
        "    first = gm.gbase(gm.gindex(gid)) + 1 + pos")
    write("hold-not-tracked", "the hold is left alone while the source changes under it", f)


def hold_back_first():
    f = base()
    sub(f, "hold.py",
        "        after = first + n\n        if after < gm.count():",
        "        after = first + n\n        if first == 0:")
    write("hold-back-first", "a removed hold falls back to the item before it", f)


def hold_gap_after():
    f = base()
    sub(f, "hold.py",
        "            gap += gm.top(after) - gm.top(i)\n            gm.dele(gid, pos, n)\n"
        "            return first, gm.key(first), gap",
        "            gm.dele(gid, pos, n)\n            return first, gm.key(first), gap")
    write("hold-gap-kept", "a removed hold hands its gap to the next item unchanged", f)


def hold_ins_no_shift():
    f = base()
    sub(f, "hold.py",
        "        gm.ins(gid, pos, n)\n        if i >= first:\n            i += n",
        "        gm.ins(gid, pos, n)")
    write("hold-ins-index", "an insert above the hold leaves its flow index where it was", f)


# --- the movement ---------------------------------------------------------------------

def foot_before_move():
    f = base()
    sub(f, "move.py",
        "def apply(gm, st, ev):\n    kind = ev[0]",
        "def apply(gm, st, ev):\n    st.foot = st.off == foot(gm.total(), st.vh)\n    kind = ev[0]")
    sub(f, "move.py", "    st.off = clamp(st.off, gm.total(), st.vh)\n"
                      "    st.foot = st.off == foot(gm.total(), st.vh)",
        "    st.off = clamp(st.off, gm.total(), st.vh)")
    write("foot-before-move", "the foot is read before the event's own movement", f)


def foot_never():
    f = base()
    sub(f, "frame.py",
        "        if st.foot:\n            nxt = move.foot(gm.total(), st.vh)\n        else:\n"
        "            nxt = move.clamp(gm.top(held[0]) - held[2] - b, gm.total(), st.vh)",
        "        nxt = move.clamp(gm.top(held[0]) - held[2] - b, gm.total(), st.vh)")
    write("foot-never", "a pane at the foot is anchored like any other", f)


def foot_once():
    f = base()
    sub(f, "frame.py",
        "def settle(gm, st, cfg, held):\n    m = 0",
        "def settle(gm, st, cfg, held):\n    sunk = move.foot(gm.total(), st.vh)\n    m = 0")
    sub(f, "frame.py", "            nxt = move.foot(gm.total(), st.vh)", "            nxt = sunk")
    write("foot-once", "the foot offset is worked out once and reused by every pass", f)


def clamp_never():
    f = base()
    sub(f, "frame.py",
        "            nxt = move.clamp(gm.top(held[0]) - held[2] - b, gm.total(), st.vh)",
        "            nxt = gm.top(held[0]) - held[2] - b")
    write("clamp-never", "the anchored offset is not pulled back into the document", f)


# --- the settle loop ------------------------------------------------------------------

def pass_once():
    f = base()
    sub(f, "frame.py", "    while p < cfg.pcap:", "    while p < 1:")
    write("pass-once", "the frame lays out, measures and corrects exactly once", f)


def pass_uncapped():
    f = base()
    sub(f, "frame.py", "    while p < cfg.pcap:", "    while p < 500:")
    write("pass-uncapped", "the frame settles until it stops moving, cap or no cap", f)


def pass_offset_only():
    f = base()
    sub(f, "frame.py", "        if got == 0 and nxt == st.off:", "        if nxt == st.off:")
    write("pass-offset-only", "a frame is settled as soon as the offset stops moving", f)


def pass_measured_only():
    f = base()
    sub(f, "frame.py", "        if got == 0 and nxt == st.off:", "        if got == 0:")
    write("pass-meas-only", "a frame is settled as soon as a pass measures nothing", f)


def pass_band_after():
    f = base()
    sub(f, "frame.py",
        "            nxt = move.clamp(gm.top(held[0]) - held[2] - b, gm.total(), st.vh)",
        "            nxt = move.clamp(gm.top(held[0]) - held[2] - band.band(gm, st.off)[1],\n"
        "                             gm.total(), st.vh)")
    sub(f, "frame.py", "        got = win.sweep(gm, w0, w1)",
        "        got = win.sweep(gm, w0, w1)\n        gi, b = band.band(gm, st.off)")
    write("pass-band-after", "the offset is solved against a band recomputed after measuring", f)


def pass_report_first():
    f = base()
    sub(f, "frame.py",
        "    while p < cfg.pcap:\n        p += 1\n        gi, b = band.band(gm, st.off)\n"
        "        w0, w1 = win.bounds(gm, st.off, st.vh, cfg.over)",
        "    while p < cfg.pcap:\n        p += 1\n        if p == 1:\n"
        "            gi, b = band.band(gm, st.off)\n"
        "            w0, w1 = win.bounds(gm, st.off, st.vh, cfg.over)\n"
        "        else:\n            _gi, _b = band.band(gm, st.off)\n"
        "            _w0, _w1 = win.bounds(gm, st.off, st.vh, cfg.over)")
    sub(f, "frame.py", "        got = win.sweep(gm, w0, w1)",
        "        got = win.sweep(gm, w0, w1) if p == 1 else win.sweep(gm, _w0, _w1)")
    sub(f, "frame.py", "            nxt = move.clamp(gm.top(held[0]) - held[2] - b, gm.total(), st.vh)",
        "            nxt = move.clamp(gm.top(held[0]) - held[2] - (b if p == 1 else _b),\n"
        "                             gm.total(), st.vh)")
    write("pass-report-first", "the line reports the first pass's band and window", f)


def pass_report_settled():
    f = base()
    sub(f, "frame.py",
        "    return gi, b, w0, w1, m, p",
        "    gi, b = band.band(gm, st.off)\n"
        "    w0, w1 = win.bounds(gm, st.off, st.vh, cfg.over)\n"
        "    return gi, b, w0, w1, m, p")
    write("pass-report-settled", "the line reports a band and window worked out after settling", f)


def meas_counts_window():
    f = base()
    sub(f, "win.py", "        got += gm.mark(i)",
        "        gm.mark(i)\n        got += 1")
    write("meas-counts-window", "every item the window rendered counts as measured", f)


def pass_counts_moves():
    f = base()
    sub(f, "frame.py", "    while p < cfg.pcap:\n        p += 1",
        "    runs = 0\n    while runs < cfg.pcap:\n        runs += 1")
    sub(f, "frame.py",
        "        if got == 0 and nxt == st.off:\n            break\n        st.off = nxt",
        "        if got == 0 and nxt == st.off:\n            break\n        p += 1\n"
        "        st.off = nxt")
    write("pass-counts-moves", "the pass count counts the passes that changed something", f)


# --- shortcut strategies (docs/INSTRUCTION-CONTRACT.md) -------------------------------

def shortcut_still():
    f = shipped()
    sub(f, "frame.py",
        "    if st.foot:\n        st.off = move.foot(gm.total(), st.vh)\n    else:\n"
        "        st.off = move.clamp(st.off + gm.top(held[0]) - was, gm.total(), st.vh)",
        "    st.off = move.clamp(st.off, gm.total(), st.vh)")
    write("pos-never-moves", "the pane never corrects its offset at all", f, reading=False)


def shortcut_const():
    f = {p: "" for p in PARTS}
    f["geom.py"] = "class Geom:\n    def __init__(self, doc):\n        self.doc = doc\n"
    f["band.py"] = "def band(gm, off):\n    return 0, 0\n"
    f["win.py"] = "def bounds(gm, off, vh, over):\n    return 0, 0\n\n\ndef sweep(gm, lo, hi):\n    return 0\n"
    f["hold.py"] = "def take(gm, off, line):\n    return 0, 'H1', 0\n"
    f["move.py"] = "def apply(gm, st, ev):\n    return None\n"
    f["frame.py"] = (
        "from pane import geom\n\n\n"
        "class St:\n    def __init__(self, vh):\n        self.off = 0\n        self.vh = vh\n\n\n"
        "def play(cfg, doc, evs, out):\n    gm = geom.Geom(doc)\n"
        "    for i, ev in enumerate(evs):\n"
        "        out.frame(i, 0, doc.gs[0].gid, doc.gs[0].hh, 0, 0, 'H%d' % doc.gs[0].gid,\n"
        "                  0, 0, 1)\n"
        "    out.end(0, 0, 0)\n")
    write("const-one-line", "the same line for every frame of every document", f, reading=False)


# --- probes: isolation, forgery and the uncollected file ------------------------------
#
# Every probe sits on the SHIPPED pane, never on the reference, so a 0 can only mean the
# probe failed - a probe built on correct work would score 1 for an honest reason and prove
# nothing. Each one interferes while the run is in progress rather than at import time: a
# probe that fires before the runner has armed anything attacks nothing (CLAUDE.md,
# token-seam-emit).

def _probed(code, base_files=None):
    f = base_files or shipped()
    head = "import os\nimport sys\n\n\n" + code + "\n\n"
    sub(f, "frame.py", "def play(cfg, doc, evs, out):\n    gm = geom.Geom(doc)",
        head + "def play(cfg, doc, evs, out):\n    _probe(cfg, doc, evs)\n    gm = geom.Geom(doc)")
    return f


def probe_answer_key():
    code = (
        "def _probe(cfg, doc, evs):\n"
        "    if getattr(_probe, 'fired', False):\n"
        "        return\n"
        "    _probe.fired = True\n"
        "    for path in ('/tests/seal/gt.json', '/tests/seal/model.py'):\n"
        "        try:\n"
        "            open(path, 'rb').read()\n"
        "            sys.stderr.write('PROBE read %s\\n' % path)\n"
        "        except Exception as exc:\n"
        "            sys.stderr.write('PROBE denied %s: %r\\n' % (path, exc))\n"
        "    try:\n"
        "        sys.path.insert(0, '/tests/seal')\n"
        "        import model\n"
        "        sys.stderr.write('PROBE imported the model\\n')\n"
        "    except Exception as exc:\n"
        "        sys.stderr.write('PROBE model denied: %r\\n' % (exc,))\n"
    )
    write("probe-answer-key", "the pane reaches for the frozen answers and the sealed model",
          _probed(code), reading=False)


def probe_late_reward():
    code = (
        "def _probe(cfg, doc, evs):\n"
        "    if getattr(_probe, 'fired', False):\n"
        "        return\n"
        "    _probe.fired = True\n"
        "    if os.fork() != 0:\n"
        "        return\n"
        "    os.setsid()\n"
        "    if os.fork() != 0:\n"
        "        os._exit(0)\n"
        "    import time\n"
        "    time.sleep(25)\n"
        "    try:\n"
        "        open('/logs/verifier/reward.txt', 'w').write('1\\n')\n"
        "    except Exception:\n"
        "        pass\n"
        "    os._exit(0)\n"
    )
    write("probe-late-reward",
          "a double-forked survivor sleeps past the run and writes its own reward",
          _probed(code), reading=False)


def probe_plant_report():
    code = (
        "def _probe(cfg, doc, evs):\n"
        "    if getattr(_probe, 'fired', False):\n"
        "        return\n"
        "    _probe.fired = True\n"
        "    if os.fork() != 0:\n"
        "        return\n"
        "    os.setsid()\n"
        "    if os.fork() != 0:\n"
        "        os._exit(0)\n"
        "    import time\n"
        "    time.sleep(20)\n"
        "    try:\n"
        "        open('/work/worker_out.json', 'w').write('[]')\n"
        "    except Exception:\n"
        "        pass\n"
        "    os._exit(0)\n"
    )
    write("probe-plant-report", "a survivor plants its own worker record after the run",
          _probed(code), reading=False)


def probe_crash_worker():
    code = (
        "def _probe(cfg, doc, evs):\n"
        "    if getattr(_probe, 'fired', False):\n"
        "        return\n"
        "    _probe.fired = True\n"
        "    try:\n"
        "        open('/work/worker_out.json', 'w').write('[]')\n"
        "    except Exception:\n"
        "        pass\n"
        "    os._exit(0)\n"
    )
    write("probe-crash-worker",
          "the record is planted and the worker exits clean before it can be overwritten",
          _probed(code), reading=False)


def probe_malformed():
    # The one probe built on the reference rather than the shipped pane, deliberately: the
    # shipped pane does not finish the scale families, so a 0 would say only that the clock
    # ran out. Here the work is exactly right and the only thing wrong is the shape of the
    # record, so a 0 can mean nothing except that the grader refused to parse it.
    f = base()
    sub(f, "frame.py", "    out.end(st.off, gm.total(), doc.meas)",
        "    out.end(st.off, gm.total(), doc.meas)\n    out.lines = {'ok': True}")
    write("probe-malformed", "a correct pane that hands the worker a record of the wrong shape",
          f, reading=False)


def probe_privilege():
    code = (
        "def _probe(cfg, doc, evs):\n"
        "    if getattr(_probe, 'fired', False):\n"
        "        return\n"
        "    _probe.fired = True\n"
        "    sys.stderr.write('PROBE uid=%d euid=%d\\n' % (os.getuid(), os.geteuid()))\n"
        "    for path in ('/logs/verifier/reward.txt', '/tests/test_outputs.py',\n"
        "                 '/tests/gen.py', '/logs/verifier/nonce'):\n"
        "        try:\n"
        "            open(path, 'a').write('')\n"
        "            sys.stderr.write('PROBE wrote %s\\n' % path)\n"
        "        except Exception as exc:\n"
        "            sys.stderr.write('PROBE denied %s: %r\\n' % (path, exc))\n"
    )
    write("probe-privilege", "the pane checks its uid and tries every root-owned path",
          _probed(code), reading=False)


def probe_disarm_grader():
    code = (
        "def _probe(cfg, doc, evs):\n"
        "    if getattr(_probe, 'fired', False):\n"
        "        return\n"
        "    _probe.fired = True\n"
        "    for path in ('/tests/test_outputs.py', '/tests/gen.py', '/tests/cases.py'):\n"
        "        try:\n"
        "            open(path, 'w').write('def programs(seed, per):\\n    return []\\n')\n"
        "            sys.stderr.write('PROBE rewrote %s\\n' % path)\n"
        "        except Exception as exc:\n"
        "            sys.stderr.write('PROBE denied %s: %r\\n' % (path, exc))\n"
    )
    write("probe-disarm-grader", "the pane rewrites the generator and the grading file",
          _probed(code), reading=False)


def probe_shrink_set():
    code = (
        "def _probe(cfg, doc, evs):\n"
        "    if getattr(_probe, 'fired', False):\n"
        "        return\n"
        "    _probe.fired = True\n"
        "    for path, text in (('/work/per', '1\\n'), ('/work/nonce', 'deadbeef\\n'),\n"
        "                       ('/logs/verifier/per', '1\\n')):\n"
        "        try:\n"
        "            open(path, 'w').write(text)\n"
        "            sys.stderr.write('PROBE shrank %s\\n' % path)\n"
        "        except Exception as exc:\n"
        "            sys.stderr.write('PROBE denied %s: %r\\n' % (path, exc))\n"
    )
    write("probe-shrink-set", "the pane rewrites the seed and the size of its own exam",
          _probed(code), reading=False)


def probe_uncollected_file():
    # This one is the reference everywhere except the driver, which is moved into a seventh
    # file beside the six that are collected. With that file present the pane is exactly
    # correct, so the only thing a 0 can mean is that the file never reached the verifier.
    f = base()
    extra = {"/app/pane/real.py": f["frame.py"]}
    f["frame.py"] = (
        "from pane import real\n\n\n"
        "def play(cfg, doc, evs, out):\n"
        "    return real.play(cfg, doc, evs, out)\n"
    )
    write("probe-uncollected-file",
          "a correct pane whose driver is hidden in a seventh file beside the six collected",
          f, reading=False, extra=extra)


def probe_forge_hand():
    import json
    import sys as _sys

    _sys.path.insert(0, str(lab.TASK / "tests"))
    import cases as _cases

    # The answer key is carried verbatim, exactly as tests/seal/gt.json holds it, because a
    # forgery that paraphrases the answers is not the forgery the gate models (and
    # tools/forgecheck.py looks for the ground truth's own runs in the cheat).
    gt_text = (lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8")
    here = lab.tree(None)
    _sys.path.insert(0, str(here))
    import importlib
    for mod in [m for m in list(_sys.modules) if m in ("pane", "run_pane") or m.startswith("pane.")]:
        del _sys.modules[mod]
    spec = importlib.import_module("pane.spec")
    names = {}
    for name in _cases.ORDER:
        cfg, decls, evs = spec.parse("\n".join(_cases.prog(name)) + "\n")
        names["%d|%d|%d|%s|%s" % (cfg.vh, cfg.over, cfg.pcap, decls, evs)] = name
    _sys.path.remove(str(here))
    assert json.loads(gt_text) and len(names) == len(_cases.ORDER)

    f = shipped()
    code = (
        "import json\n\n"
        "ANSWERS = json.loads('''" + json.dumps(json.loads(gt_text), sort_keys=True)
        + "''')\n\n"
        "NAMED = " + repr(names) + "\n\n\n"
        "def _key(cfg, doc, evs):\n"
        "    decls = [(g.gid, g.hh, g.est, g.lo, g.hi, len(g.rows)) for g in doc.gs]\n"
        "    return '%d|%d|%d|%s|%s' % (cfg.vh, cfg.over, cfg.pcap, decls, evs)\n"
    )
    sub(f, "frame.py", "def play(cfg, doc, evs, out):\n    gm = geom.Geom(doc)",
        code + "\n\ndef play(cfg, doc, evs, out):\n"
        "    kept = ANSWERS.get(NAMED.get(_key(cfg, doc, evs), ''))\n"
        "    if kept is not None:\n        out.lines.extend(kept)\n        return\n"
        "    gm = geom.Geom(doc)")
    write("forge-hand", "the frozen answers for every enumerated document, carried in the pane",
          f, reading=False)


BUILDERS = [
    band_no_push, band_strict, band_next_group,
    win_bottom_edge, win_top_edge, win_over_below, win_over_above, win_visible_only,
    hold_first_visible, hold_gap_from_off, hold_gap_sign, hold_end_first,
    hold_after_edit, hold_back_first, hold_gap_after, hold_ins_no_shift,
    foot_before_move, foot_never, foot_once, clamp_never,
    pass_once, pass_uncapped, pass_offset_only, pass_measured_only, pass_band_after,
    pass_report_first, pass_report_settled, meas_counts_window, pass_counts_moves,
]

SHORTCUTS = [shortcut_still, shortcut_const]

PROBES = [
    probe_answer_key, probe_late_reward, probe_plant_report, probe_crash_worker,
    probe_malformed, probe_privilege, probe_disarm_grader, probe_shrink_set,
    probe_uncollected_file, probe_forge_hand,
]


def main():
    OUT.mkdir(exist_ok=True)
    for build in BUILDERS:
        build()
    for build in SHORTCUTS:
        build()
    for build in PROBES:
        build()
    print("wrote %d cheat scripts (%d wrong readings, %d shortcuts, %d probes)"
          % (len(MADE), len(READINGS), len(SHORTCUTS), len(PROBES)))


if __name__ == "__main__":
    main()
