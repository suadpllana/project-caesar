"""Write authoring/line-step-stop/trace.md: the walk from the verifier to the instruction.

Every row cites the instruction word for word; this script refuses to write a trace whose
quotes are not in instruction.md, so it cannot go stale silently. The enumerated sessions are
read from tests/cases.py and the readings from readings.py, so a new case or reading without
a row cannot happen here either. Shortcut and tolerance results are the measured ones from
cheat_report.json and shortcut_report.json.
"""
import json
import os
import re
import sys

from lab import HERE, TASK

sys.path.insert(0, os.path.join(TASK, "tests"))
import cases  # noqa: E402
import readings  # noqa: E402

INSTR = open(os.path.join(TASK, "instruction.md")).read()
FLAT = " ".join(INSTR.split())


def q(text):
    """A quote that must exist in the instruction, verbatim (whitespace-normalised)."""
    flat = " ".join(text.split())
    if flat not in FLAT:
        raise SystemExit("quote not in instruction.md: %r" % text)
    if '"' in text or len(flat.split()) < 4:
        raise SystemExit("quote unusable: %r" % text)
    return '"%s"' % flat


M = "tests/seal/model.py"
J = "tests/judge.py"
F = "tests/seal/forge.py"
P = "tests/probe.py"
T = "tests/test_outputs.py"

# (site, what it grades, [quotes])
GRADED = [
    # test functions
    ("`%s:21` test_judge_finished" % T, "the judge reached a verdict; a crash or an unfinished run is a 0",
     ["Every line `/app/dbg/sess.py` prints in every session must match ours exactly"]),
    ("`%s:26` test_sealed_model_reproduces_frozen_lines" % T,
     "the model re-derives every small frozen session's lines before anything is graded (a guard on the verifier, not on the agent)",
     ["must match ours exactly"]),
    ("`%s:31` test_declared_files_present" % T, "all three declared files were handed in",
     ["Only those three files are collected"]),
    ("`%s:41` test_samples" % T, "the four shipped sessions, graded like the rest",
     ["Four of them are the samples, and you have not seen the other 365"]),
    ("`%s:46` test_enumerated_cases" % T, "one session per wrong reading (rows below)",
     ["Four of them are the samples, and you have not seen the other 365"]),
    ("`%s:52` test_plain_fences" % T, "ordinary sessions an over-cautious engine gets wrong",
     ["Four of them are the samples, and you have not seen the other 365"]),
    ("`%s:58` test_heavy_sessions" % T, "long loops crossed by single commands",
     ["Their loops run up to 700,000 times inside one row, inside called functions and inside inlined instances"]),
    ("`%s:64` test_generated_sessions" % T, "the nonce population, every family, against the sealed model",
     ["Four of them are the samples, and you have not seen the other 365"]),
    ("`%s:70` test_whole_set_within_limit" % T, "the one clock for the whole graded set",
     ["The debugger has 300 seconds for all of them together, counted from the start of each session to its end"]),
    ("`%s:75` test_verdict" % T, "every session passed and the clock held",
     ["Every line `/app/dbg/sess.py` prints in every session must match ours exactly"]),
    # artifacts and the harness
    ("artifact `/app/dbg/marks.py`", "only the declared files are collected",
     ["You may change `/app/dbg/marks.py`, `/app/dbg/frames.py` and `/app/dbg/steps.py`"]),
    ("artifact `/app/dbg/frames.py`", "only the declared files are collected",
     ["You may change `/app/dbg/marks.py`, `/app/dbg/frames.py` and `/app/dbg/steps.py`"]),
    ("artifact `/app/dbg/steps.py`", "only the declared files are collected",
     ["You may change `/app/dbg/marks.py`, `/app/dbg/frames.py` and `/app/dbg/steps.py`"]),
    ("`%s:93-111` stage_tree" % J, "a pristine tree with the three files laid over it; every other module is the shipped one",
     ["Everything else stays as it is"]),
    ("`%s:17-25` the worker" % P, "the driver calls resolve, show and Engine; a file that drops one crashes the session",
     ["They must keep `resolve`, `show` and `Engine`, with its `hid` and its `run`, `cont`, `step`, `next` and `finish`, as `/app/dbg/sess.py` uses them"]),
    ("`%s:128-143` play: target and worker" % J, "target under its own uid with the tape on stdin; debugger as another uid, fresh process per session, read-only tree",
     ["When we grade, each session runs in a fresh process as an unprivileged user, in a copy of `/app` it cannot write, and the debugger has no way to read the tape"]),
    ("`%s:45` LIMIT = 300.0" % J, "the wall clock shared by the whole graded set, from each debugger process's start to its end",
     ["The debugger has 300 seconds for all of them together, counted from the start of each session to its end"]),
    ("`%s:145-203` the lines pipe" % J, "only the lines the driver writes to its pipe are compared; the debugger's own stdout is discarded",
     ["Nothing else the debugger prints is read"]),
    ("`%s:594` MAX_ADDRESSES" % F, "no graded program is longer",
     ["Their programs have up to 400 addresses"]),
    ("`%s` check_image" % F, "every image obeys the stated guarantees",
     ["Execution enters an instance only at LO from outside it and leaves only by running from HI to HI+1",
      "An instance holds no `ret`", "Its first address LO starts a statement row whose line is not 0",
      "Address HI+1 starts a row",
      "Every row carries a line of the innermost function or instance holding its address, or 0"]),
    ("`%s` script" % F, "commands are issued only where the brief allows",
     ["It comes once, before any `cont`, `step`, `next` or `finish`",
      "No script issues `finish` in the outermost frame while its deepest visible scope is its function",
      "Every `break` names a line that has a statement row"]),
    # the model, one row per rule
    ("`%s:34-38` fn lines" % M, "function ranges, source lines, the entry",
     ["An image starts with its functions", "The program starts at address 0"]),
    ("`%s:43-51` code lines" % M, "one instruction per address",
     ["Each address holds one instruction, written `ADDRESS OP ARGS`"]),
    ("`%s:160-188` exec1" % M, "the machine: what each instruction does, per-call registers, the end",
     ["`in R` (the next number on the tape)", "`jnz R A` (jump to A if R is not 0)",
      "`call A` (A is the first address of a function)", "Registers `a` to `d` belong to each call", "They start at 0",
      "ends when a `ret` has no call to return to"]),
    ("`%s:39-40` row lines" % M, "the statement flag",
     ["A trailing `x` marks a row that is not a statement"]),
    ("`%s:60-77` row coverage" % M, "which row holds an address",
     ["A row covers the addresses up to the next row of its function or the end of the function",
      "A function declared without lines has no rows"]),
    ("`%s:79-97` instances" % M, "instance records and their nesting",
     ["says addresses LO to HI hold the body of function F inlined into P",
      "An instance lies inside its parent and never overlaps a sibling"]),
    ("`%s:107-109` chain" % M, "the scopes of a frame at an address",
     ["at that address the scopes of a frame are its function and then every instance holding the address, outermost first"]),
    ("`%s:111-112` name" % M, "what a scope prints",
     ["An instance prints the name of the function it inlines"]),
    ("`%s:122-124` line" % M, "the deepest scope's line",
     ["the deepest shows the line of the row holding the address, or 0"]),
    ("`%s:199-208` frames" % M, "callers at the call instruction; call lines; hidden scopes",
     ["The innermost frame is read at the program counter and each caller at its return address minus one, its `call`",
      "A scope shows the call line of the scope below it",
      "The scope above them still shows the call line of the first hidden one"]),
    ("`%s:212-224` do_break" % M, "breakpoint numbering, grouping and order",
     ["The command `break L` numbers breakpoints from 1 and prints `bN` followed by its addresses in ascending order",
      "A statement row belongs to the innermost function body or instance holding its address",
      "gives the breakpoint one address, the lowest of them"]),
    ("`%s:190-195` tick" % M, "the hit test after every instruction, in every frame, nothing hidden",
     ["A hit happens whenever execution arrives at a breakpoint address, in any frame", "It ends the command there",
      "A stop hides nothing unless a rule below says so"]),
    ("`%s:228-232` do_run" % M, "run stops at once on a breakpoint at address 0",
     ["except that `run` stops at once when address 0 is a breakpoint"]),
    ("`%s:234-237` do_cont" % M, "cont",
     ["The command `cont` runs until a hit or the end", "The instruction a command starts at runs without that check"]),
    ("`%s:244-260` do_finish" % M, "finish out of an instance or a function, and what it hides",
     ["When the deepest visible scope of the innermost frame is an instance, `finish` runs until the frame leaves that instance",
      "Otherwise it runs until the innermost frame returns",
      "It stops where it lands, hiding the instances that start there"]),
    ("`%s:262-267` do_step setup" % M, "the stepping frame, scope and line",
     ["Its deepest visible scope is the stepping scope", "The line that scope shows is the stepping line"]),
    ("`%s:268-276` hidden scopes" % M, "reveal one level; next over the outermost hidden instance",
     ["`step` makes the outermost hidden one visible and stops without running anything",
      "`next` runs until the frame leaves that instance and then judges where it lands"]),
    ("`%s:283-296` calls" % M, "next runs calls; step stops in callees with lines, hiding what starts there",
     ["`next` runs it until it returns", "`step` stops at the first address of the called function if that function has lines, hiding the instances that start there",
      "A call that returns counts as a move from the `call` to its return address"]),
    ("`%s:297-303` returns" % M, "the caller becomes the stepping frame; the stepping line is kept",
     ["When the stepping frame returns, its caller becomes the stepping frame",
      "not counting instances that start exactly there, becomes the stepping scope",
      "The stepping line is kept and the arrival is judged"]),
    ("`%s:304-305` row changes" % M, "which moves are judged",
     ["Execution arriving in a different row of the stepping frame is judged"]),
    ("`%s:321-323` leaving the scope" % M, "rule 14",
     ["the enclosing scope that holds the new address becomes the stepping scope first"]),
    ("`%s:324-337` instance entries" % M, "rule 13: into, over or at the call site, by call line",
     ["If the address is the first of instances below the stepping scope, the outermost of them decides",
      "when its call line equals the stepping line, `step` stops with it visible and the deeper ones hidden",
      "`next` runs until the frame leaves it and then judges where it lands",
      "when it does not, both stop there with all of them hidden"]),
    ("`%s:307-313` over_instance" % M, "leaving an instance is judged in the stepping frame only",
     ["`next` runs until the frame leaves it and then judges where it lands"]),
    ("`%s:338-349` rows" % M, "rule 12: statement row starts stop, part-way arrivals adopt, nothing else",
     ["a statement row whose line is not 0 and differs from the stepping line stops the command",
      "Part-way into a row, a line that is not 0 becomes the stepping line",
      "No other arrival stops them or changes the stepping line"]),
    ("`%s:131-139` Stop, Ended" % M, "the stop kinds and the end",
     ["The kind is `hit` at a breakpoint, `step` at the end of a `step` or `next`, and `done` at the end of a `finish`",
      "When the program ends, the command prints `exit` and no command follows"]),
    ("`%s:352-375` play" % M, "one line per command in the stated format",
     ["Every command prints one line",
      "Any other stop prints its kind, the program counter and the frames innermost first, each as `NAME:LINE`"]),
]


def check_sites():
    """A cited range must still hold the def or assignment its label names.

    Labels that are not identifiers (fn lines, row coverage, the lines pipe) were checked by
    hand against the file when they were written; this catches the ones code can check.
    """
    bad = []
    for site, _, _ in GRADED:
        m = re.match(r"`([^`:]+):(\d+)(?:-(\d+))? ?[^`]*` (\w+)", site)
        if not m:
            continue
        path, lo, hi, label = m.group(1), int(m.group(2)), int(m.group(3) or m.group(2)), m.group(4)
        src = open(os.path.join(TASK, path)).read().splitlines()
        pat = r"\s*def %s\b" % label if not label.isupper() else r"%s\s*=" % label
        hits = [i + 1 for i, ln in enumerate(src) if re.match(pat, ln)]
        defs = [i + 1 for i, ln in enumerate(src) if re.match(r"\s*(def|class) ", ln)]

        def inside(h):
            # the range starts at the def, or lies in its body before the next def
            return lo <= h <= hi or (h < lo and not any(h < d <= lo for d in defs))
        if hits and not any(inside(h) for h in hits):
            bad.append("%s: %s is at line %s" % (site, label, hits))
    if bad:
        raise SystemExit("stale line citations:\n  " + "\n  ".join(bad))


def main():
    check_sites()
    shortcuts = json.load(open(os.path.join(HERE, "shortcut_report.json")))
    timing = json.load(open(os.path.join(HERE, "timing_report.json")))
    lines = ["# Instruction trace: line-step-stop", "",
             "Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Written",
             "by authoring/line-step-stop/write_trace.py, which refuses a quote that is not in",
             "instruction.md. Check with `python tools/tracecheck.py line-step-stop`.", "",
             "## Graded assertions", "",
             "| Verifier site | What it grades | Instruction sentence |", "|---|---|---|"]
    for site, what, quotes in GRADED:
        lines.append("| %s | %s | %s |" % (site, what, "; ".join(q(x) for x in quotes)))
    for name, what in cases.SAMPLES.items():
        lines.append("| `tests/cases.py` case %s | %s | %s |" % (
            name, what, q("The one called `long` is as heavy as the heaviest one we grade")))
    for name, what in cases.CASES.items():
        rule = readings.RULE[name]
        lines.append("| `tests/cases.py` case %s | %s | %s |" % (name, what, q(rule)))
    for name, what in cases.FENCES.items():
        lines.append("| `tests/cases.py` case %s | %s | %s |" % (
            name, what, q("a statement row whose line is not 0 and differs from the stepping line stops the command")))
    for name, what in cases.HEAVY.items():
        lines.append("| `tests/cases.py` case %s | %s | %s |" % (
            name, what, q("Their loops run up to 700,000 times inside one row, inside called functions and inside inlined instances")))
    lines += ["", "## Readings", "",
              "| Reading | Sentence or published example that rules it out | Case that separates it |",
              "|---|---|---|"]
    for name, (what, _) in readings.EDITS.items():
        lines.append("| %s: %s | %s | case %s |" % (name, what, q(readings.RULE[name]), name))
    lines += ["", "## Shortcuts", "", "| Strategy | Result |", "|---|---|"]
    for name, r in shortcuts.items():
        lines.append("| %s | %s |" % (r["what"], r["result"]))
    lines += ["", "## Tolerances", "", "| Tolerance or limit | Independent implementation | Measured |",
              "|---|---|---|"]
    for row in timing["rows"]:
        lines.append("| %s | %s | %s |" % tuple(row))
    text = "\n".join(lines) + "\n"
    with open(os.path.join(HERE, "trace.md"), "w", newline="\n") as f:
        f.write(text)
    print("wrote trace.md:", len(lines), "lines")


if __name__ == "__main__":
    main()
