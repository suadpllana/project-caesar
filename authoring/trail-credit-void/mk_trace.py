"""Write trace.md, checking every quote is really in instruction.md before it is written.

A trace is evidence only while its quotes are still in the file, so this builds the rows from
named spans and fails loudly on any span that has drifted out of the instruction - rather than
letting tracecheck find it later with no clue which row went stale.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "trail-credit-void"
BRIEF = (TASK / "instruction.md").read_text(encoding="utf-8")

Q = {
    "obs_when": "An observation happens at the end of a step that ended `ok`",
    "obs_base": "One more happens as an episode opens, and that one credits nothing and fires nothing: it only records the values the next observation is compared against",
    "obs_err": "A step that ended `err` leaves the records exactly as it found them and observes nothing, so what it wrote is never seen",
    "credit_pass": "At an observation the goals are gone over once, in ascending order",
    "credit_rule": "A goal that is not credited is credited when its predicate holds and every goal it stands on was credited at a strictly earlier observation of this episode",
    "settle": "Credit then stays. A goal keeps it when its predicate stops holding, and is never credited a second time",
    "bars_after": "After that the violations are gone over in ascending order",
    "bar_kinds": "`lost K` holds when record K had a value at the previous observation of this episode and has none now. `gain K` holds when it had none then and has one now. `back K` holds when it had a value at both and the value now is smaller than the one it had",
    "fire": "Firing shuts the goal it names, whether or not that goal is credited, and takes the credit of that goal and of every goal standing on it, directly or through others",
    "opened": "Of the goals a firing touches, only the one the violation names is shut",
    "rearm": "A shut goal is opened again at the first later observation at which its predicate does not hold, and cannot be credited before that",
    "bud_charge": "Every `put` and `cut` counts against the episode's budget, the ones in a step that ended `err` included",
    "bud_cut": "An episode may perform at most B actions. The action after that is not performed, the rest of its step is not performed either, that step is rolled back and the episode is closed there",
    "close": "An episode closed that way has its records put back to what they were as it opened. One that ran to the end of its steps leaves its records as they stand",
    "carry": "Either way the credit it earned stands. The next episode opens on whatever records are left",
    "fresh": "Each episode starts with its own budget, nothing credited and nothing shut",
    "lines": "`mark G` is printed when goal G is credited and `void G` when it loses its credit, each in ascending goal order within an observation. `fire B` comes before the voids that violation B caused",
    "ep_line": "When an episode is over it prints `ep NAME CREDIT WHOLE USED`. CREDIT adds up the weights of the goals it holds, WHOLE adds up the weights of every goal of its rubric, and USED is the number of actions charged to it",
    "run_line": "When the trail is over it prints `run EPISODES FULL CREDIT WHOLE`. FULL counts the episodes holding every goal of their rubric, and the last two add up over the episodes",
    "only": "Nothing else is printed",
    "files": "The files you may change are `/app/crd/store.py`, `/app/crd/pred.py`, `/app/crd/obs.py`, `/app/crd/book.py`, `/app/crd/void.py`, `/app/crd/ep.py` and `/app/crd/tally.py`. Nothing else",
    "replaced": "The rest of the tree is replaced by our own copy before a trail is run, a new file put beside those seven included",
    "driver": "Our copy of `/app/run_crd.py` parses the trail, makes one `crd.store.Store` and seeds it with `seed(key, value)`, makes one `crd.tally.Sum`, calls `crd.ep.run(cfg, episode, store, sums, out)` for each episode in file order, then `crd.tally.close(sums, out)`, and prints the lines `out` collected",
    "graded_set": "The graded set is three trails of each of those two sizes, three hundred and sixty smaller ones and thirty-seven written by hand. All of it has to get through inside 60 seconds",
    "at": "`at K V` (record K has exactly the value V)",
    "up": "`up K V` (record K has a value of at least V)",
    "off": "`off K` (record K has no value at all, and a record standing at zero has one)",
    "worked": "It prints eight lines and should print five: `mark 0`, `fire 0`, `void 0`, `ep a1 0 5 6`, `run 1 0 0 5`",
    "numbering": "Goals and violations are numbered from zero inside each episode. A goal only stands on goals before it",
    "scale": "`/app/trails/wide.txt` is one episode of sixteen thousand steps over fifty thousand records. `/app/trails/deep.txt` is one of forty-two thousand steps. Its rubric runs to four thousand six hundred goals",
}

for _name, _span in Q.items():
    if _span not in BRIEF:
        sys.exit("span %r is not in instruction.md" % _name)


def q(*names):
    return " ".join('"%s"' % Q[n] for n in names)


ASSERTIONS = [
    ("`tests/test_outputs.py:116` test_frozen_truth_matches_the_model",
     "the sealed model still reproduces the frozen answers, so a drifted model cannot redefine correct",
     "grades nothing the agent produced; it guards the two sealed definitions against each other. "
     + q("graded_set")),
    ("`tests/test_outputs.py:126` test_hand_case",
     "each enumerated trail prints exactly the frozen lines, and the trail itself was not altered",
     q("only", "graded_set")),
    ("`tests/test_outputs.py:135` test_every_nonce_trail_matches",
     "every generated trail prints exactly what the sealed model says",
     q("graded_set")),
    ("`tests/test_outputs.py:154` test_every_family_is_represented",
     "the generated population covers every family, so a shrunk exam is not graded",
     q("graded_set")),
]

CASE_SRC = (TASK / "tests" / "cases.py").read_text(encoding="utf-8").splitlines()


def case_line(name):
    for i, line in enumerate(CASE_SRC, 1):
        if line.strip().startswith('"%s": [' % name):
            return i
    sys.exit("case %r is not in cases.py" % name)


CASES = [
    ("obs-step-end", 17, "a goal satisfied only inside a step is never observed satisfied", "obs_when"),
    ("obs-ok-only", 26, "a step that ended err produces no observation", "obs_err"),
    ("obs-base-silent", 37, "the opening observation credits nothing, so a dependant is still a whole observation behind", "obs_base"),
    ("obs-base-no-fire", 50, "the opening observation fires no violation", "obs_base"),
    ("pre-strict-later", 62, "a prerequisite credited at this observation does not admit its dependant", "credit_rule"),
    ("pre-chain-layers", 72, "a chain satisfied at once is credited one link per observation", "credit_rule"),
    ("pre-many-parents", 84, "a goal on two prerequisites waits for the later of them", "credit_rule"),
    ("pre-open-waits", 96, "a goal whose predicate held first is credited the observation after its prerequisite", "credit_rule"),
    ("settle-keeps", 111, "credit survives the predicate going false", "settle"),
    ("settle-no-recredit", 120, "a credited goal is not marked again", "settle"),
    ("bar-lost", 132, "lost needs a value then and none now", "bar_kinds"),
    ("bar-gain", 144, "gain needs none then and a value now", "bar_kinds"),
    ("bar-back", 156, "back needs a strictly smaller value; equal and higher do not fire", "bar_kinds"),
    ("bar-prev-obs", 168, "the comparison is against the previous observation, not the previous action", "bar_kinds"),
    ("bar-err-invisible", 179, "a loss inside a step that ended err is never seen", "obs_err"),
    ("void-cone", 192, "a firing takes the goal named and everything standing on it", "fire"),
    ("void-shut-named", 207, "the named goal is shut and its dependants are only opened", "opened"),
    ("void-rearm-false", 223, "a goal shut on an already failing predicate opens at the next observation", "rearm"),
    ("void-rearm-holds", 235, "a goal shut while its predicate holds stays shut until it fails", "rearm"),
    ("void-order", 251, "credit is applied before the violations fire", "bars_after"),
    ("void-uncredited", 261, "a firing on an uncredited goal shuts it and prints no void", "fire"),
    ("void-ascending", 274, "voids print in ascending goal order, not in walk order", "lines"),
    ("step-err-undo", 291, "a step that ended err leaves the records as it found them", "obs_err"),
    ("step-ok-keeps", 301, "a step that ended ok keeps what it wrote", "obs_when"),
    ("bud-per-action", 313, "the budget counts actions, not steps", "bud_charge"),
    ("bud-counts-failed", 322, "the actions of a step that ended err are charged", "bud_charge"),
    ("bud-cut-step", 331, "the crossing action is not performed and its step is rolled back", "bud_cut"),
    ("bud-exact-end", 342, "a budget spent exactly by the last action closes nothing", "bud_cut"),
    ("close-undo-keeps-credit", 355, "an episode closed short keeps its credit", "carry"),
    ("close-next-baseline", 365, "an episode closed short has its records put back", "close"),
    ("carry-normal", 378, "an episode that ran to the end leaves its records for the next", "close"),
    ("pred-up-equal", 392, "a value exactly on an up threshold is at least that much", "up"),
    ("pred-off-zero", 400, "a record standing at zero has a value, so off does not hold", "off"),
    ("rep-weights", 413, "an episode reports weights, not a count of goals", "ep_line"),
    ("rep-full", 423, "an episode counts as full only when it holds every goal", "run_line"),
    ("worked-tiny", 0, "the trail the brief prints the answer for, byte for byte", "worked"),
    ("plain-all", 438, "the ordinary run: no violation, room in the budget, the whole rubric credited", "credit_rule"),
]

MODEL = [
    ("`tests/seal/model.py:42-59` Rec.put, Rec.cut, Rec.back_to",
     "a span of writes is undone exactly, which is how an err step and a closed episode put the records back",
     q("obs_err", "close")),
    ("`tests/seal/model.py:70-76` satisfied",
     "at is exact, up is at least, off is no value at all",
     q("at", "up", "off")),
    ("`tests/seal/model.py:105-116` episode, the action loop",
     "every action is charged, including the actions of a step that ends err",
     q("bud_charge")),
    ("`tests/seal/model.py:108-122` episode, the budget cut",
     "the crossing action is not performed, its step is rolled back and the episode closes",
     q("bud_cut", "obs_err")),
    ("`tests/seal/model.py:124-129` episode, the observation",
     "an observation only happens at the end of an ok step, and the candidates are the goals a written record names or whose prerequisite just landed",
     q("obs_when", "obs_base", "credit_pass")),
    ("`tests/seal/model.py:131-149` episode, the credit pass",
     "one ascending pass; a shut goal opens when its predicate fails; an open goal is credited when its predicate holds and every prerequisite was credited strictly earlier; credit is never granted twice",
     q("credit_pass", "credit_rule", "settle", "rearm")),
    ("`tests/seal/model.py:150-153` episode, the mark lines",
     "mark G is printed for each goal credited, in ascending order",
     q("lines")),
    ("`tests/seal/model.py:155-167` episode, the violation tests",
     "violations in ascending order, each against the pair of consecutive observations",
     q("bars_after", "bar_kinds")),
    ("`tests/seal/model.py:169-186` episode, the firing",
     "fire B, then the cone of the named goal in ascending order, voids only for goals that held credit, and the named goal shut",
     q("fire", "opened", "lines")),
    ("`tests/seal/model.py:188-190` episode, the refresh",
     "the previous-observation values move once per observation, never per action",
     q("bar_kinds")),
    ("`tests/seal/model.py:192-198` episode, the close",
     "a closed episode has its records put back while its credit stands, and the ep line reports weights and actions charged",
     q("close", "carry", "ep_line")),
    ("`tests/seal/model.py:202-209` Lines",
     "the printed lines are exactly the ones the rules emit and nothing else",
     q("only")),
    ("`tests/seal/model.py:212-231` expect",
     "episodes run in file order over one set of records, and the run line closes the trail",
     q("driver", "run_line", "fresh")),
]

ARTIFACTS = [
    "/app/crd/store.py", "/app/crd/pred.py", "/app/crd/obs.py", "/app/crd/book.py",
    "/app/crd/void.py", "/app/crd/ep.py", "/app/crd/tally.py",
]

READINGS = {
    "obs-per-action": ("obs_when", "obs-step-end and bar-err-invisible"),
    "obs-err-too": ("obs_err", "bar-err-invisible"),
    "pre-same-obs": ("credit_rule", "obs-base-silent, pre-strict-later, pre-chain-layers"),
    "credit-recompute": ("settle", "pred-off-zero and settle-keeps"),
    "rearm-now": ("rearm", "obs-base-silent and void-rearm-holds"),
    "rearm-on-touch": ("rearm", "void-rearm-false"),
    "void-named-only": ("fire", "void-ascending and void-cone"),
    "void-cone-shut": ("opened", "void-shut-named"),
    "void-walk-order": ("lines", "void-ascending"),
    "void-uncredited-skip": ("fire", "void-uncredited"),
    "bars-first": ("bars_after", "obs-base-silent and void-order"),
    "bar-state": ("bar_kinds", "bar-back"),
    "bar-back-any": ("bar_kinds", "bar-back"),
    "err-keeps": ("obs_err", "bar-err-invisible and step-err-undo"),
    "bud-per-step": ("bud_charge", "bud-counts-failed and bud-per-action"),
    "bud-spares-failed": ("bud_charge", "bar-err-invisible and bud-counts-failed"),
    "close-keeps": ("close", "close-next-baseline"),
    "close-loses-credit": ("carry", "bud-cut-step and close-undo-keeps-credit"),
    "up-strict": ("up", "pred-up-equal"),
    "off-zero": ("off", "pred-off-zero"),
    "rep-count": ("ep_line", "close-undo-keeps-credit and rep-weights"),
    "rep-full-any": ("run_line", "close-next-baseline and rep-full"),
}

SHORTCUTS = [
    ("the shipped tree unchanged (nop)",
     "reward 0 in the container. Its records are copied per step and it observes after every "
     "action, so the worker runs out of its clock; on the small trails it also matches 0 of 403"),
    ("constant: nothing credited for every trail (`cheat-const-nothing`)",
     "reward 0, caught by all 37 hand trails. Matches 0 of 403 graded trails"),
    ("constant: every goal credited for every trail (`cheat-const-everything`)",
     "reward 0, caught by all 37 hand trails. Matches 0 of 403 graded trails"),
    ("the worked example's output replayed (`cheat-pos-replay-example`)",
     "reward 0, caught by 36 of the 37 hand trails. The one it passes is `worked-tiny`, which is "
     "`trails/tiny.txt` itself: the brief prints that trail's answer, so replaying it is right "
     "there and wrong on the other 402"),
    ("the frozen answers carried as a table (`cheat-forge-hand`)",
     "reward 0. Passes all 37 hand trails and is caught by the nonce population, which is "
     "generated from a seed drawn after the agent's container is gone"),
]

TOLERANCES = [
    ("`tests/test.sh:35` a 60 second clock on the graded set",
     "`authoring/trail-credit-void/slow-snap` and `slow-sweep`, two exactly correct "
     "implementations written as the two naive families, plus the sealed model and the two "
     "correct variants under `authoring/trail-credit-void/variants/`",
     "reference 0.19 s on the wide trail and 0.69 s on the deep one, so three of each plus 396 "
     "small trails come to about 3 s against 60. The naive copy takes 32.4 s on wide and the "
     "naive sweep 22.1 s on deep, so three of either exceeds the limit on its own. Variants "
     "ok-index and ok-flat finish the same 114-trail set in 3.3 s and 4.3 s against the "
     "reference's 2.8 s. " + q("graded_set", "scale")),
]


def main():
    out = ["# Instruction trace: trail-credit-void", "",
           "Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md).",
           "Rebuilt by `authoring/trail-credit-void/mk_trace.py`, which refuses to write a row",
           "whose quote is no longer in `instruction.md`.", "",
           "## Graded assertions", "",
           "| Verifier site | What it grades | Instruction sentence |", "|---|---|---|"]
    for site, what, sentence in ASSERTIONS:
        out.append("| %s | %s | %s |" % (site, what, sentence))
    for name, _line, what, span in CASES:
        out.append("| `tests/cases.py:%d` case %s | %s | %s |"
                   % (case_line(name), name, what, q(span)))
    for art in ARTIFACTS:
        out.append("| artifact `%s` | only the declared files are collected | %s |"
                   % (art, q("files", "replaced")))
    out.append("| `tests/test.sh:35` a 60 s clock | the whole graded set must finish inside it "
               "| %s |" % q("graded_set"))
    for site, what, sentence in MODEL:
        out.append("| %s | %s | %s |" % (site, what, sentence))

    out += ["", "## Readings", "",
            "| Reading | Sentence or published example that rules it out | Case that separates it |",
            "|---|---|---|"]
    for name, (span, case) in READINGS.items():
        out.append("| %s | %s | %s |" % (name, q(span), case))

    out += ["", "## Shortcuts", "", "| Strategy | Result |", "|---|---|"]
    for name, got in SHORTCUTS:
        out.append("| %s | %s |" % (name, got))

    out += ["", "## Tolerances", "",
            "| Tolerance or limit | Independent implementation | Measured |", "|---|---|---|"]
    for name, impl, got in TOLERANCES:
        out.append("| %s | %s | %s |" % (name, impl, got))

    body = "\n".join(out) + "\n"
    assert "\r" not in body
    (HERE / "trace.md").write_text(body, encoding="utf-8", newline="\n")
    print("trace.md written: %d rows" % sum(1 for line in out if line.startswith("| `")
                                            or line.startswith("| artifact")))


if __name__ == "__main__":
    main()
