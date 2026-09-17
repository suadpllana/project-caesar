"""Write authoring/claim-cover-lift/trace.md: every graded assertion against its sentence.

The rows are built here rather than by hand so that the cited sites stay in step with the files
they point at, and so a change to the case list or the model shows up as a missing row instead
of a stale paragraph.
"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "claim-cover-lift"
sys.path.insert(0, str(TASK / "tests"))
import cases  # noqa: E402

Q = {
    "compare": '"every line it prints is compared with the line expected, in order"',
    "nonce": '"The graded programs are generated after your container is gone"',
    "collected": '"Six files are taken from your container"',
    "notread": '"Nothing else you write is read"',
    "clock": '"must finish within 60 seconds"',
    "scale": '"can leave one box holding forty thousand slot claims"',
    "conflict": '"Two modes conflict when at least one of them is w"',
    "boxfam": '"A claim on a box conflicts with another job\'s claims on that box and on every slot of it"',
    "slotfam": '"a claim on a slot conflicts with another job\'s claims on that slot and on its box"',
    "sibling": '"claims on two different slots never conflict, and a job\'s own claims never conflict with its own request"',
    "acquire": '"A claim granted to a job adds one acquire, so what a job holds on a node is the list of acquires granted to it there"',
    "droprule": '"A drop gives back the one added most recently and prints free"',
    "dropnone": '"a drop naming a node the job does not hold prints nothing"',
    "show": '"A show prints at and the node, then every job holding that node in job order, each followed by its acquires as mode letters sorted together"',
    "cover": '"A request is granted at once, ahead of anything that would otherwise block it, when the asking job already holds a claim on that node or on its box in a mode that covers it"',
    "covermode": '"a claim in w covers a request in either mode, and a claim in r covers a request in r"',
    "coverup": '"A claim on a slot covers nothing on its box"',
    "blocked": '"It is blocked by a granted claim of another job that conflicts with it, and by a waiting request of another job that conflicts with it and holds a smaller sequence number"',
    "waitline": '"A request that is blocked prints wait and takes the next sequence number"',
    "onecounter": '"sequence numbers come from one counter for the whole store rather than one per node"',
    "liftwhen": '"A request for a slot is lifted when the asking job holds no claim covering it on that slot\'s box and already holds granted claims on four or more distinct slots of that box"',
    "liftmode": '"The request becomes a request for the box, in mode w if it or any of those claims is in w and in r otherwise"',
    "liftwait": '"A lifted request that waits keeps the job\'s slot claims until it is granted"',
    "liftfree": '"the job\'s acquires on every slot of that box are given back in slot order, each printing free, and then the request that caused the lift is granted"',
    "sweep": '"the waiting request with the smallest sequence number that can now be granted is granted, and that repeats until no waiting request can be granted"',
    "waitsfor": '"One job waits for another when that other blocks its waiting request, whether by a granted claim or by an older waiting request"',
    "victim": '"of every job lying on any cycle, the one holding the fewest acquires counted with repetition, and on a tie the one with the largest job number"',
    "stopdoes": '"Stopping prints stop, takes that job\'s waiting request out of the line, and gives back every acquire it holds in node order, each printing free"',
    "stopagain": '"Granting then resumes, and the check is made again, until no job lies on a cycle"',
    "ignores": '"A job ignores every line naming it while its own request is waiting, after it has ended, and after it has been stopped"',
    "endrule": '"An end gives back every acquire the job holds in node order, each printing free, prints done, and then granting resumes"',
    "nodeorder": '"Nodes are put in order by box number first, a box before its own slots, then by slot number"',
    "numbers": '"the numbers compare as numbers, so b10 comes after b2 and s12 after s2"',
    "joborder": '"Jobs are put in order by number the same way"',
    "events": '"The events are `grant <job> <node> <mode>`, `wait <job> <node> <mode>`, `lift <job> <box> <mode>`, `free <job> <node>`, `stop <job>`, `done <job>`"',
    "ops": '"The operations are `take <job> <node> <mode>`, `drop <job> <node>`, `end <job>`, `show <node>`, and `fill <job> <box> <count> <mode>`"',
    "space": '"It has two levels: boxes, named b1, b2 and so on, and slots inside them"',
}

CASE = {
    "fam-box-slot": ("a claim on a box blocks another job's request for one of its slots", "boxfam"),
    "fam-slot-box": ("a claim on a slot blocks another job's request for its box", "slotfam"),
    "fam-sibling": ("two jobs claiming different slots of one box are both granted at once", "sibling"),
    "read-share": ("two readers share a slot and a writer waits behind them", "conflict"),
    "split-boxes": ("jobs working in different boxes never wait for each other", "sibling"),
    "cover-ahead": ("a covered request is granted although an older request is waiting", "cover"),
    "cover-mode": ("a claim held in r does not cover a request in w", "covermode"),
    "cover-up-only": ("a claim on a slot does not cover a request for the box", "coverup"),
    "again-drop": ("a second acquire survives the first drop", "acquire"),
    "again-lower": ("a drop takes back the most recent acquire and what is left grants a reader", "droprule"),
    "drop-none": ("a drop naming a node the job does not hold prints nothing", "dropnone"),
    "fair-queue": ("a compatible request waits behind an older conflicting one", "blocked"),
    "seq-across": ("grants owed in two boxes come out in one store-wide order", "onecounter"),
    "sweep-chain": ("one release grants every request that becomes grantable", "sweep"),
    "end-order": ("end frees in node order, with numbers compared as numbers", "nodeorder"),
    "lift-floor": ("the fifth distinct slot of a box lifts the request to the box", "liftwhen"),
    "lift-few": ("a drop below four distinct slots means no lift", "liftwhen"),
    "lift-mode": ("a lift takes w because one of the claims it replaces is in w", "liftmode"),
    "lift-wait": ("a lift that cannot be granted waits and keeps its slot claims", "liftwait"),
    "lift-free-order": ("a granted lift frees in slot order, not in the order taken", "liftfree"),
    "lift-covered": ("a job already covering the box does not lift", "liftwhen"),
    "lift-repeat": ("four acquires over three slots do not reach the floor", "liftwhen"),
    "lift-two": ("two lifts in one box wait for each other and one job is stopped", "victim"),
    "ring-two": ("the job on the cycle with fewer acquires is stopped", "victim"),
    "ring-fair": ("a cycle that runs through an older waiting request is found", "waitsfor"),
    "ring-count": ("acquires are counted with repetition when the victim is chosen", "victim"),
    "ring-tie": ("a tie on acquires goes to the larger job number", "victim"),
    "busy-line": ("a line naming a job whose request is waiting does nothing", "ignores"),
    "stop-line": ("a line naming a stopped job does nothing", "ignores"),
    "end-line": ("a line naming a finished job does nothing", "ignores"),
    "show-format": ("a query lists jobs by number with every acquire as a sorted letter", "show"),
    "show-none": ("a query on a node nobody holds prints the node alone", "show"),
}

MODEL = [
    ("tests/seal/model.py:38-42", "boxof: a slot name carries its box, so the family is a box and its slots", "space"),
    ("tests/seal/model.py:43-49", "nkey: node order is box number, the box before its slots, then slot number, as numbers", "nodeorder"),
    ("tests/seal/model.py:50-53", "jkey: jobs are ordered by the number in the name", "joborder"),
    ("tests/seal/model.py:54-55", "clash: two modes conflict when at least one is w", "conflict"),
    ("tests/seal/model.py:58-66", "Ask: a waiting request keeps its job, node, mode, sequence number and lift trigger", "waitline"),
    ("tests/seal/model.py:67-80", "Engine: the state the operations act on", "ops"),
    ("tests/seal/model.py:84-92", "put: a take adds one acquire to what the job holds on that node", "acquire"),
    ("tests/seal/model.py:93-116", "take_off: a drop removes the acquire added most recently", "droprule"),
    ("tests/seal/model.py:117-119", "acquires: a job's acquires are counted with repetition", "victim"),
    ("tests/seal/model.py:120-130", "free_all: everything a job holds is given back in node order, each printing free", "endrule"),
    ("tests/seal/model.py:131-137", "covers: a claim on the node or its box in a covering mode grants at once", "cover"),
    ("tests/seal/model.py:131-137", "covers: w covers either mode, r covers r, and a slot claim covers nothing above it", "covermode"),
    ("tests/seal/model.py:138-149", "blocked_by: a conflicting granted claim of another job in the family blocks", "boxfam"),
    ("tests/seal/model.py:150-163", "blocked_by: an older conflicting waiting request of another job blocks", "blocked"),
    ("tests/seal/model.py:164-171", "park: a blocked request prints wait and takes the next number from one counter", "onecounter"),
    ("tests/seal/model.py:172-181", "unpark: a granted or cancelled request leaves the line", "sweep"),
    ("tests/seal/model.py:182-188", "hand: a grant records the acquire and prints grant", "events"),
    ("tests/seal/model.py:189-196", "hand: a granted lift frees the box's slot claims in slot order, then grants its trigger", "liftfree"),
    ("tests/seal/model.py:197-203", "ready: the smallest numbered grantable request of a box", "sweep"),
    ("tests/seal/model.py:204-221", "sweep: grants repeat in sequence order until nothing more can be granted", "sweep"),
    ("tests/seal/model.py:222-227", "edges: a job waits for the jobs that block its waiting request", "waitsfor"),
    ("tests/seal/model.py:228-272", "tangle: every job lying on a cycle through the job that has just started waiting", "victim"),
    ("tests/seal/model.py:273-282", "cut: stopping prints stop, drops the request and frees in node order", "stopdoes"),
    ("tests/seal/model.py:283-292", "settle: a victim is taken while any job still lies on a cycle", "stopagain"),
    ("tests/seal/model.py:293-300", "take: a job acts only when it is not waiting, stopped or finished", "ignores"),
    ("tests/seal/model.py:301-308", "take: a slot request lifts at four distinct slots, in w if any of them is w", "liftmode"),
    ("tests/seal/model.py:309-313", "take: an unblocked request is granted, a blocked one waits and the check runs", "blocked"),
    ("tests/seal/model.py:314-320", "drop: a removed acquire prints free and granting resumes", "droprule"),
    ("tests/seal/model.py:321-328", "end: frees in node order, prints done, then granting resumes", "endrule"),
    ("tests/seal/model.py:329-336", "show: the holders of a node, by job number, with sorted mode letters", "show"),
    ("tests/seal/model.py:337-353", "expect: the operation names, and fill as a take of s1 to s<count>", "ops"),
]

READINGS = [
    ("fit-node-only", "boxfam", "fam-box-slot"),
    ("fit-slot-blind", "slotfam", "fam-slot-box"),
    ("fit-no-line", "blocked", "fair-queue"),
    ("cover-none", "cover", "cover-ahead"),
    ("cover-any-mode", "covermode", "cover-mode"),
    ("cover-downward", "coverup", "cover-up-only"),
    ("cover-not-kept", "acquire", "cover-ahead"),
    ("hold-one-mode", "acquire", "again-drop"),
    ("drop-oldest", "droprule", "again-lower"),
    ("hold-ever-held", "liftwhen", "lift-few"),
    ("order-by-text", "numbers", "end-order"),
    ("show-last-mode", "show", "show-format"),
    ("show-text-order", "joborder", "show-format"),
    ("sweep-per-box", "onecounter", "seq-across"),
    ("end-no-sweep", "endrule", "seq-across"),
    ("lift-give-up", "liftwait", "lift-wait"),
    ("lift-take-order", "liftfree", "lift-free-order"),
    ("lift-count-acquires", "liftwhen", "lift-repeat"),
    ("lift-trigger-mode", "liftmode", "lift-mode"),
    ("lift-keeps-slots", "liftfree", "lift-floor"),
    ("knot-holders-only", "waitsfor", "ring-fair"),
    ("knot-first-found", "victim", "ring-two"),
    ("knot-count-nodes", "victim", "ring-count"),
    ("knot-tie-small", "victim", "ring-tie"),
    ("knot-keeps-request", "stopdoes", "ring-two"),
    ("busy-acts", "ignores", "busy-line"),
    ("stopped-acts", "ignores", "stop-line"),
]

SHORTCUTS = [
    ("the shipped tree unchanged (nop)",
     "scores 0; matches 13 of the 32 enumerated programs and 7 of 48 generated ones"),
    ("positional: every request granted at once, nothing ever waits",
     "scores 0 as cheat-shortcut-grant-all; matches 9 of 32 and 0 of 48"),
    ("constant: the brief's own worked example replayed for every program",
     "scores 0 as cheat-shortcut-replay-example; matches 0 of 32 and 0 of 48"),
    ("the previous revision of the reference",
     "there is none that differs: the shipped tree is the engine the reference replaces, and it "
     "is the nop row above"),
    ("an answer key for every enumerated program",
     "scores 0 as cheat-forge-answer-key; passes all 32 enumerated programs and fails the "
     "generated population it could not have seen"),
]


def main():
    out = []
    add = out.append
    add("# Instruction trace: claim-cover-lift")
    add("")
    add("Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Every")
    add("graded assertion, enumerated case, model rule, collected artifact and clock has a row and")
    add("the sentence it traces to. Built by `authoring/claim-cover-lift/make_trace.py`; checked")
    add("with `python tools/tracecheck.py claim-cover-lift`.")
    add("")
    add("## Graded assertions")
    add("")
    add("| Verifier site | What it grades | Instruction sentence |")
    add("|---|---|---|")
    add("| `tests/test_outputs.py:116` test_the_model_still_makes_the_frozen_answers | that the sealed model "
        "still reproduces the frozen answers before anything is judged by it | %s |" % Q["compare"])
    add("| `tests/test_outputs.py:126` test_enumerated_program | the trace of every enumerated program, "
        "line for line, against the frozen answers | %s |" % Q["compare"])
    add("| `tests/test_outputs.py:135` test_generated_program | the trace of every "
        "generated program against the sealed model | %s |" % Q["nonce"])
    add("| `tests/test_outputs.py:154` test_every_family_was_run | that the population the "
        "worker ran is the one the grader asked for, so a shrunken exam fails | %s |" % Q["notread"])
    for name in cases.ORDER:
        what, key = CASE[name]
        add("| `tests/cases.py` case %s | %s | %s |" % (name, what, Q[key]))
    for art in ("hold.py", "fit.py", "line.py", "lift.py", "knot.py", "gate.py"):
        add("| artifact `/app/hb/%s` | only the declared files are collected | %s |"
            % (art, Q["collected"]))
    add("| `tests/test.sh:27` a 60 s clock | the whole graded set must finish inside it | %s |"
        % Q["clock"])
    for site, what, key in MODEL:
        add("| `%s` | %s | %s |" % (site, what, Q[key]))
    add("")
    add("## Readings")
    add("")
    add("| Reading | Sentence or published example that rules it out | Case that separates it |")
    add("|---|---|---|")
    for name, key, case in READINGS:
        add("| %s | %s | %s |" % (name, Q[key], case))
    add("")
    add("## Shortcuts")
    add("")
    add("| Strategy | Result |")
    add("|---|---|")
    for row in SHORTCUTS:
        add("| %s | %s |" % row)
    add("")
    add("## Tolerances")
    add("")
    add("| Tolerance or limit | Independent implementation | Measured |")
    add("|---|---|---|")
    for row in TOLERANCES:
        add("| %s | %s | %s |" % row)
    add("")
    text = "\n".join(out)
    assert "\r" not in text
    (HERE / "trace.md").write_text(text, encoding="utf-8", newline="\n")
    print("wrote trace.md: %d lines" % len(out))


TOLERANCES = [
    ("`tests/test.sh` the 60 s clock on the graded run",
     "`authoring/claim-cover-lift/variants/jobmajor`, written apart from the reference",
     "4.1 s over the whole graded set against the 60 s limit, with the reference at 2.4 s and "
     "the three correct-but-walking readings at 90 s, 323 s and 639 s"),
]

if __name__ == "__main__":
    main()
