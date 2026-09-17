"""Write authoring/queue-hold-drop/trace.md: every graded assertion against its sentence.

The rows are authored here rather than by hand so the quotes can be checked against
instruction.md as the file is written, and so a case added to cases.py fails this script
instead of silently arriving in the trace with no row.

    python3 authoring/queue-hold-drop/make_trace.py
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TASK = ROOT / "tasks" / "queue-hold-drop"
sys.path.insert(0, str(TASK / "tests"))
import cases  # noqa: E402

PROSE = " ".join((TASK / "instruction.md").read_text(encoding="utf-8").split())

# --- the sentences the rows cite -------------------------------------------------------

Q = {
    "view": "What the user sees is the confirmed records with the queue laid over them, each "
            "change in the order it was made",
    "base": "A change from another client lands in them as it arrives, and an accepted change "
            "goes into them when its answer comes back",
    "new": "A creation makes its record under the parent it names, and does nothing when those "
           "records already hold that name or do not hold the parent",
    "field": "A field change sets its field, or adds to what that field holds at that moment",
    "zero": "A field nothing has set holds zero",
    "mov": "A move puts its record under the parent it names, and does nothing when the new "
           "parent is the record itself or lies under it",
    "cut": "A removal takes its record and every record under it, as the records stand at the "
           "moment that change is laid over and not as they stood when the user made it",
    "miss": "Any change naming a record that is not there at that moment does nothing at all",
    "about-new": "A creation is about the record it makes and names its parent",
    "about-mov": "A move is about the record it moves and names its new parent",
    "about-rest": "The other three name only the record they are about, and a creation or a move "
                  "written against the top names only its own record",
    "far-id": "A record another client made arrives already carrying the id the server gave it",
    "mine-id": "A record the user made carries none until the server answers its creation",
    "send": "A change can go out once every record it names carries an id, except that a "
            "creation does not wait for the record it makes",
    "held": "One that cannot go out yet is held back",
    "spread": "Every later change naming a record beyond reach is held back too, and each of "
              "those puts its own record beyond reach in turn",
    "sent-alone": "Changes that have already gone out are left alone",
    "later-send": "A change held at one send goes out at a later one once the ids it was waiting "
                  "on have arrived",
    "target": "each answer the oldest change that has gone out and is still on the queue",
    "ok": "An `ok` takes its change off the queue and lays it over the confirmed records, and a "
          "creation answered that way takes the next server id",
    "ids": "The ids run `s1`, `s2` and upward, in the order the answers hand them out",
    "no": "A `no` takes its change off the queue and lays it over nothing",
    "no-spread": "Every later change on the queue that names the record the refused change is "
                 "about goes with it, and each of those puts its own record in the same position "
                 "for the changes after it",
    "no-back": "A change earlier on the queue is never touched",
    "idle": "An answer that finds no change to answer does nothing",
    "stop": "A removal the user makes against a record that carries no id, and whose creation is "
            "still on the queue, does not join the queue at all",
    "stop-how": "What goes with the creation is worked out exactly as it is for a refusal, "
                "starting from the record that was to be removed",
    "out": "A change going out prints `out <kind> <record>` in the order the changes go",
    "ack": "an `ok` prints `ack <kind> <record>`",
    "gone": "a `no` prints `gone <count>` counting the change refused as well",
    "idle-line": "an answer with nothing to answer prints `idle`",
    "kind": "`<kind>` is always the word the change was written with",
    "ident": "a record is printed under the id the server gave it or under the name the program "
             "made it with while it has none",
    "ack-id": "which makes the `ack` of an accepted creation the line that first shows the id "
              "that creation has just taken",
    "rec": "`ask` prints `rec <record> <parent> <field>=<value> ...` with the fields in name "
           "order, or `none` when the user cannot see that record",
    "top": "The parent of a record at the top prints as `-`",
    "rows": "`all` prints `row` lines of the same shape for every record the user can see",
    "order": "the confirmed ones first, in the order they entered the confirmed records, then "
             "the ones the server has not confirmed, in the order the user made them",
    "only": "Nothing else is printed",
    "files": "The files you may change are `/app/pend/line.py`, `/app/pend/fold.py`, "
             "`/app/pend/hold.py`, `/app/pend/view.py`, `/app/pend/lay.py` and "
             "`/app/pend/reach.py`",
    "clock": "all of it has to get through inside 60 seconds",
    "scale": "`/app/progs/wide.txt` queues twenty thousand changes with a question after each of "
             "them",
    "graded": "The graded set is three programs of each of those two sizes and four hundred and "
              "ninety-one small ones",
}

for key, text in Q.items():
    if " ".join(text.split()) not in PROSE:
        raise SystemExit("quote %r is not in instruction.md" % key)

# --- what each enumerated case pins, and the sentence behind it --------------------------

CASE = {
    "hold-plain": ("every change goes out when nothing is waiting on an id", ["send", "out"]),
    "hold-wait": ("a change naming a record with no id stays behind", ["send", "held"]),
    "hold-new-own": ("a creation does not wait for the record it makes", ["send"]),
    "hold-new-up": ("a creation does wait for the record it names as parent", ["send", "about-new"]),
    "hold-spread": ("holding spreads two changes out, past records that do carry ids", ["spread"]),
    "hold-spread-far": ("a held move puts a record with an id beyond reach", ["spread", "about-mov"]),
    "hold-again": ("a held change goes out at the next send once the id has arrived",
                   ["later-send", "sent-alone"]),
    "name-mov-up": ("a move names its new parent and waits for it", ["about-mov", "send"]),
    "name-set-one": ("a field change names only its own record and is not held with it",
                     ["about-rest", "send"]),
    "ans-sent": ("the answer lands past a held change on the front", ["target"]),
    "ans-idle": ("an answer with nothing sent prints idle", ["idle", "idle-line"]),
    "ans-idle-after": ("an answer after everything has been answered prints idle",
                       ["idle", "idle-line"]),
    "take-id": ("a creation takes its id at the acceptance and the ack shows it",
                ["ok", "ack-id"]),
    "take-order": ("ids are handed out in the order answers arrive", ["ids"]),
    "take-base": ("an accepted change is in the confirmed records once, not twice",
                  ["ok", "field"]),
    "take-gone-up": ("a creation accepted under a parent an arrival removed still takes an id",
                     ["ok", "new"]),
    "gone-one": ("a refusal with nothing sharing its record takes one change", ["no", "gone"]),
    "gone-kids": ("a refused creation takes what names its record", ["no-spread"]),
    "gone-chain": ("the take-away spreads outward through the records it reaches",
                   ["no-spread"]),
    "gone-back": ("a change queued before the refused one survives and goes out later",
                  ["no-back", "later-send"]),
    "gone-front": ("the take-away does not reach backwards over the queue", ["no-back"]),
    "gone-sent": ("a refusal takes a change that had already gone out, and the next answer lands "
                  "past it", ["no-spread", "target"]),
    "stop-cut": ("a removal of a record the server has never confirmed takes its creation off",
                 ["stop", "out"]),
    "stop-id": ("the cancelled creation never takes an id, so the next one takes s1", ["stop", "ids"]),
    "stop-away": ("what goes with the cancelled creation is worked out as for a refusal",
                  ["stop-how"]),
    "stop-kept": ("a removal of a confirmed record joins the queue like any other", ["stop"]),
    "stop-side": ("a queued change about another record survives the cancellation",
                  ["stop-how", "no-spread"]),
    "reach-under": ("a removal takes the whole subtree, not the records directly under it",
                    ["cut"]),
    "reach-late": ("an arrival moving a record under a queued removal puts it inside its reach",
                   ["cut", "base"]),
    "reach-out": ("an arrival moving a record out from under a queued removal brings it back",
                  ["cut", "base"]),
    "reach-cycle": ("a move under one of its own descendants does nothing", ["mov"]),
    "reach-top": ("a move to the top is allowed", ["mov", "top"]),
    "lay-miss": ("changes naming a record the view no longer holds do nothing", ["miss"]),
    "lay-add": ("an add adds to what the field holds at that moment", ["field"]),
    "lay-add-base": ("an arrival under a queued add changes what is shown", ["field", "view"]),
    "lay-up-miss": ("a creation whose parent is not there does nothing", ["new"]),
    "view-sent": ("a change that has gone out is still laid over the confirmed records",
                  ["view", "sent-alone"]),
    "view-order": ("records come out in the order they entered the view", ["order", "rows"]),
    "view-order-move": ("an acceptance moves a record into the confirmed group", ["order", "ok"]),
    "say-fields": ("fields print in name order, and a field set to zero prints",
                   ["rec", "zero"]),
    "say-top": ("a record at the top prints - for its parent, and a removed one prints none",
                ["top", "rec"]),
}

TESTS = [
    ("`tests/test_outputs.py:114` test_frozen_truth_matches_the_model",
     "the frozen answers still are what the sealed model says, before anything is graded",
     ["view"]),
    ("`tests/test_outputs.py:124` test_hand_case",
     "each enumerated program prints exactly the frozen trace, and the program was not altered",
     ["only", "files"]),
    ("`tests/test_outputs.py:133` test_every_nonce_program_matches",
     "every generated program prints exactly what the model says, all or nothing",
     ["only", "graded"]),
    ("`tests/test_outputs.py:152` test_every_family_is_represented",
     "the generated population covers all twelve families the graded set is drawn from",
     ["graded"]),
]

MODEL = [
    ("`tests/seal/model.py:117-125` view", "the view is the confirmed records with the queue "
     "laid over them in order", ["view"]),
    ("`tests/seal/model.py:84-90` lay, new", "a creation makes its record under the parent it "
     "names, or does nothing", ["new"]),
    ("`tests/seal/model.py:91-98` lay, set and add", "a field change sets, or adds to what the "
     "field holds, and an unset field holds zero", ["field", "zero"]),
    ("`tests/seal/model.py:99-108` lay, mov", "a move is refused when the new parent is the "
     "record itself or lies under it", ["mov"]),
    ("`tests/seal/model.py:109-113` lay, cut", "a removal takes its record and everything under "
     "it at that moment", ["cut"]),
    ("`tests/seal/model.py:91-113` lay, missing record", "a change naming a record that is not "
     "there does nothing", ["miss"]),
    ("`tests/seal/model.py:56-60` named", "which records a change names", ["about-new",
     "about-mov", "about-rest"]),
    ("`tests/seal/model.py:157-173` send", "which changes go out, and how holding spreads",
     ["send", "held", "spread", "sent-alone"]),
    ("`tests/seal/model.py:175-193` answer", "which change an answer lands on, and what "
     "acceptance and refusal each do", ["target", "ok", "ids", "no", "idle"]),
    ("`tests/seal/model.py:146-155` sweep", "what a refusal or a cancellation takes with it",
     ["no-spread", "no-back"]),
    ("`tests/seal/model.py:129-144` take", "a removal of a record the server has never confirmed",
     ["stop", "stop-how"]),
    ("`tests/seal/model.py:195-199` land", "an arrival from another client changes the confirmed "
     "records and never joins the queue", ["base"]),
    ("`tests/seal/model.py:203-208` row", "the printed shape of a record and the order of its "
     "fields", ["rec", "top", "ident"]),
    ("`tests/seal/model.py:220-254` one", "the printed line for every op, and that nothing else "
     "is printed", ["out", "ack", "gone", "idle-line", "kind", "rows", "order", "only"]),
]

READINGS = [
    ("hold-no-spread", ["spread"], "hold-spread"),
    ("hold-new-free", ["send"], "hold-new-up"),
    ("name-mov-flat", ["about-mov"], "name-mov-up"),
    ("id-at-send", ["ok", "ids"], "take-order"),
    ("ans-front", ["target"], "ans-sent"),
    ("ack-early", ["ack-id"], "take-id"),
    ("take-twice", ["ok"], "take-base"),
    ("gone-one", ["no-spread"], "gone-chain"),
    ("gone-flat", ["no-spread"], "gone-chain"),
    ("gone-all", ["no-spread"], "gone-one"),
    ("gone-both", ["no-back"], "gone-front"),
    ("stop-queued", ["stop"], "stop-cut"),
    ("stop-only", ["stop-how"], "stop-away"),
    ("reach-kids", ["cut"], "reach-under"),
    ("reach-fixed", ["cut"], "reach-out"),
    ("mov-cycle", ["mov"], "reach-cycle"),
    ("lay-upsert", ["miss"], "lay-miss"),
    ("add-set", ["field"], "lay-add"),
    ("zero-hidden", ["zero"], "say-fields"),
    ("view-skip-sent", ["view", "sent-alone"], "view-sent"),
    ("ask-base", ["view"], "ans-idle"),
    ("order-name", ["order"], "view-order"),
    ("say-unsorted", ["rec"], "say-fields"),
]

SHORTCUTS = [
    ("the shipped tree unchanged (the nop)",
     "reward 0: the trial at tools/docker_trial.py queue-hold-drop nop; the shipped service is "
     "wrong on 34 of the 41 enumerated programs and does not finish the scale families inside "
     "the clock"),
    ("a constant: the most common line of every shape, one fixed trace for every program",
     "reward 0: no two of the 41 enumerated traces are equal, and 497 graded programs print "
     "traces of 1 to 60011 lines"),
    ("positional: answer the front of the queue, send the queue in order, take one change per "
     "refusal",
     "reward 0 as cheat-ans-front, cheat-hold-new-free and cheat-gone-one, caught by ans-sent, "
     "hold-new-up and gone-chain"),
    ("the worked example replayed: the frozen answers to every enumerated program",
     "reward 0 as cheat-forge-from-truth; it replays all 41 enumerated traces and is wrong on "
     "196 of 200 generated programs"),
]

TOLERANCES = [
    ("`tests/test.sh:27` the 60 s clock on the graded run",
     "`authoring/queue-hold-drop/variants/walk/view.py` and "
     "`authoring/queue-hold-drop/variants/eager/view.py`, two correct services written apart "
     "from the reference",
     "1.2 s and 1.0 s over the graded shapes against the 60 s clock, and 1.28 s for all 497 "
     "programs in the verifier image; the same contract rebuilt per question takes 111 s on one "
     "wide program and 48 s on one deep program"),
]


def cite(keys):
    return " ".join('"%s"' % Q[k] for k in keys)


def main():
    out = ["# Instruction trace: queue-hold-drop", "",
           "Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md).",
           "Written by authoring/queue-hold-drop/make_trace.py, which checks every quote against",
           "instruction.md as it writes. Check with `python tools/tracecheck.py queue-hold-drop`.",
           "", "## Graded assertions", "",
           "| Verifier site | What it grades | Instruction sentence |", "|---|---|---|"]
    for site, what, keys in TESTS:
        out.append("| %s | %s | %s |" % (site, what, cite(keys)))
    for name in cases.ORDER:
        if name not in CASE:
            raise SystemExit("enumerated case %s has no row" % name)
        what, keys = CASE[name]
        out.append("| `tests/cases.py` case %s | %s | %s |" % (name, what, cite(keys)))
    for path in ("line.py", "fold.py", "hold.py", "view.py", "lay.py", "reach.py"):
        out.append("| artifact `/app/pend/%s` | the only file of its name the verifier reads from "
                   "the agent | %s |" % (path, cite(["files"])))
    out.append("| `tests/test.sh:27` the 60 s wall clock on the worker | a correct service that "
               "cannot get through the graded set in time scores 0 | %s |"
               % cite(["clock", "graded"]))
    for site, what, keys in MODEL:
        out.append("| %s | %s | %s |" % (site, what, cite(keys)))

    out += ["", "## Readings", "",
            "| Reading | Sentence or published example that rules it out | Case that separates it |",
            "|---|---|---|"]
    for name, keys, case in READINGS:
        out.append("| %s | %s | %s |" % (name, cite(keys), case))

    out += ["", "## Shortcuts", "", "| Strategy | Result |", "|---|---|"]
    for what, got in SHORTCUTS:
        out.append("| %s | %s |" % (what, got))

    out += ["", "## Tolerances", "",
            "| Tolerance or limit | Independent implementation | Measured |", "|---|---|---|"]
    for what, who, got in TOLERANCES:
        out.append("| %s | %s | %s |" % (what, who, got))

    path = HERE / "trace.md"
    path.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    print("wrote %s: %d rows" % (path.relative_to(ROOT), len(out)))


if __name__ == "__main__":
    main()
