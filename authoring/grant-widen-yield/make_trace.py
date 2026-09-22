#!/usr/bin/env python3
"""Write authoring/grant-widen-yield/trace.md from one table.

Every quote is checked against instruction.md before the file is written, so a trace whose
quotes have gone stale fails here rather than in review. Re-run after any change to the
instruction, tests/, the model, the generator or the environment.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "grant-widen-yield"
BRIEF = " ".join((TASK / "instruction.md").read_text(encoding="utf-8").split())

# --- the sentences, each a verbatim span of the brief ---------------------------------

Q = {
    "collect": "The files you may change are",
    "extra": "a new file put beside those six included",
    "entry": "must return the trace followed by the closing report",
    "unseen": "Your service is graded on programs you have not seen",
    "age": "lines and the first opened is the oldest",
    "compat": "IS is compatible with every mode but X, IX with IS and IX, S with IS and S, "
              "SIX with IS alone, X with nothing",
    "sup": "Their supremum is the weakest mode at least as strong as both",
    "supix": "the supremum of IX and S is SIX",
    "eff": "the supremum of two things: the mode the program asked for there, if it ever "
           "asked, and the cover its own live grants below that resource require",
    "cov": "A grant at IS or S requires IS above it; a grant at IX, SIX or X requires IX",
    "falls": "a mode falls when the grants beneath it go and rises when they come back",
    "silent": "A take that raises only what a transaction has asked for, leaving the "
              "effective mode where it was, prints nothing",
    "levels": "A take is settled one level at a time from the store inward, and the service "
              "does not look ahead",
    "older": "If any incompatible holder is older than the requester, the take is refused: "
             "nothing the requester asked for is granted, at any level, and the give-ups "
             "already forced at outer levels stand",
    "younger": "If every incompatible holder is younger, each gives way, oldest of them first",
    "cascade": "A holder that gives way loses that resource and every grant it holds below it",
    "asked": "Only a resource the program asked for leaves a claim, at the asked mode, "
             "not at the effective mode that was printed",
    "cover": "only to cover something beneath it leaves nothing",
    "due": "A claim is due when it is made, and again whenever the service moves what is held "
           "at the level that last refused it",
    "order": "oldest transaction first, and within a transaction outermost resource first, "
             "then by resource name",
    "once": "Each is tried once, as an ordinary take that can make younger holders give way "
            "and can be refused by an older one",
    "nextline": "Whatever the sweep itself disturbs, including the claims its own give-ups "
                "create, falls due for the next line",
    "widen": "children of one resource has them replaced by a grant at that resource",
    "widesup": "asked for at the supremum of those children's effective modes and of anything "
               "it had already asked for there",
    "widecl": "Claims are not grants and do not count",
    "widepas": "The rule never makes anyone give way",
    "wideord": "It is applied to keys before blocks, in transaction age order and then by "
               "resource name, and repeated until a full pass changes nothing",
    "wideend": "It does not run again after the changes it makes",
    "drop": "removes every grant and every claim that transaction has at that resource or "
            "below it, and then lets the levels above fall to what is left",
    "dropnil": "something it neither holds nor claims does nothing at all",
    "shut": "removes everything that transaction holds or claims",
    "verbs": "when a grant appears or rises to that mode",
    "thin": "when one falls to it",
    "free": "when one is released or when a cover with nothing left to cover disappears",
    "wait": "when a take from the program is refused",
    "widelin": "when the widen rule replaces 5 children with a grant at X",
    "outer": "The grants of a successful take are printed outermost first",
    "deep": "Giving way prints the deepest resource first, then equal depths in resource "
            "order, and then the levels above as they fall",
    "widepos": "before any change it causes above",
    "report": "The report comes after the last line, transactions in age order",
    "resord": "a store before its blocks, a block before its keys, and lower numbers first",
    "clock": "it has 60 seconds of wall clock for the whole graded set",
    "scale": "around twenty thousand lines in which three transactions hold up to nine "
             "thousand keys each under a single block",
    "keeps": "the requester keeps whatever it held there already",
    "refclaim": "A refused take leaves a claim on the resource it named, at the mode it "
                "asked for",
    "widesub": "Whatever it held under those children goes as well",
    "takeclaim": "any claim it had on that resource is gone",
    "joins": "the requested mode joins whatever the transaction had already asked for there",
}

# --- the enumerated set: what each case pins, and the sentence behind it ----------------

CASES = {
    "plain-share": ("compatible holders are left alone and nothing is claimed", "compat"),
    "plain-intent": ("two exclusive keys under one block share an IX cover", "cov"),
    "plain-again": ("an asked mode only ever rises, and a take of a mode already held "
                    "prints nothing", "joins"),
    "plain-stores": ("stores are independent; a conflict in one does not reach the other",
                     "levels"),
    "mode-sup-mixed": ("the supremum of an intent-exclusive and a shared hold", "supix"),
    "mode-cover-six": ("a shared-intent-exclusive grant needs an exclusive intention above it",
                       "cov"),
    "mode-cover-read": ("a shared grant needs only a shared intention above it", "cov"),
    "cover-asked-stays": ("an asked mode outlives the grants that were covering it", "eff"),
    "cover-plain-goes": ("a cover with nothing left to cover disappears", "free"),
    "cover-thins": ("the cover falls when the exclusive grant under it goes", "falls"),
    "cover-holds-up": ("the cover stays while another grant still requires it", "falls"),
    "cover-unblocks": ("a fallen cover makes the resource compatible for somebody else",
                       "falls"),
    "take-outward": ("a take and its covers are granted and printed outermost first", "outer"),
    "take-no-lookahead": ("a give-up forced at an outer level stands when the take is refused "
                          "deeper", "older"),
    "take-keeps-grant": ("a refused upgrade keeps the mode the transaction already held",
                         "keeps"),
    "take-older-refused": ("an older holder refuses, and the refusal leaves a claim at the "
                           "mode that was asked for", "refclaim"),
    "give-younger": ("the younger holder gives way instead of the requester waiting",
                     "younger"),
    "give-cascade": ("giving way takes every grant below the resource with it", "cascade"),
    "give-asked-only": ("a grant that was only a cover leaves no claim", "cover"),
    "give-claim-asked": ("the claim is left at the asked mode, not the printed one", "asked"),
    "give-age-order": ("two younger holders give way oldest of them first", "younger"),
    "give-at-level": ("only the subtree under the contested resource is given up", "cascade"),
    "sweep-age-first": ("two claims on one resource are tried oldest transaction first",
                        "order"),
    "sweep-outermost": ("a transaction's claims are tried outermost resource first", "order"),
    "sweep-narrower": ("a retake rebuilds the cover from what actually came back, and clears "
                       "the claim when it succeeds", "takeclaim"),
    "sweep-preempts": ("a retake makes a younger holder give way", "once"),
    "sweep-next-line": ("what a sweep disturbs is not tried again inside that sweep",
                        "nextline"),
    "sweep-parked": ("a claim is not tried while the level that refused it has not moved",
                     "due"),
    "wide-keys": ("keys over the threshold are replaced by a grant at the block", "widen"),
    "wide-chain": ("widening keys can take the store over the threshold in the same pass, "
                   "and what sat under the replaced children goes with them", "widesub"),
    "wide-grants-only": ("the threshold is read against grants", "widecl"),
    "wide-claims-idle": ("a standing claim does not push a transaction over the threshold",
                         "widecl"),
    "wide-passive": ("a resource another transaction sits on stays fragmented", "widepas"),
    "wide-deep-first": ("keys are widened before blocks when both cross in one line",
                        "wideord"),
    "wide-twice": ("the rule repeats until a full pass changes nothing", "wideord"),
    "wide-sup": ("the widened mode is the supremum of the children and the asked mode",
                 "widesup"),
    "wide-after-sweep": ("the rule runs after the sweep, on what the sweep left", "wideend"),
    "wide-last": ("a retake on this line is counted by the rule on this line", "wideend"),
    "wide-under-limit": ("exactly the threshold is not over it", "widen"),
    "free-subtree": ("a release takes the subtree and the claims under it", "drop"),
    "free-narrows": ("a release lets the levels above fall to what is left", "drop"),
    "free-nothing": ("a release of something neither held nor claimed prints nothing",
                     "dropnil"),
    "shut-clears": ("a finish removes everything the transaction holds or claims", "shut"),
    "say-report-order": ("the closing report, transactions in age order then resource order",
                         "report"),
}

TESTS = [
    ("tests/test_outputs.py:118", "test_frozen_truth_matches_the_model",
     "nothing the submission controls: the frozen answers and the sealed model must still "
     "agree before either is used to judge, so a drifted model cannot redefine correct",
     "entry"),
    ("tests/test_outputs.py:128", "test_hand_case",
     "every enumerated program's trace and report, line for line, against answers frozen "
     "before the grading file was written", "entry"),
    ("tests/test_outputs.py:137", "test_every_nonce_program_matches",
     "every generated program's trace and report, line for line, against the sealed model",
     "unseen"),
    ("tests/test_outputs.py:153", "test_the_nonce_population_is_large_enough",
     "that the population actually generated is the size the task claims, so a shrunken "
     "generator cannot make the exam smaller", "unseen"),
    ("tests/test_outputs.py:157", "test_every_family_is_represented",
     "that every shaped family, including the two that carry the execution limit, is present",
     "scale"),
]

MODEL = [
    ("tests/seal/model.py:54-61", "the supremum of two modes", "sup"),
    ("tests/seal/model.py:64-65", "the cover a mode requires of the resource above it", "cov"),
    ("tests/seal/model.py:68-69", "whether two modes may share a resource", "compat"),
    ("tests/seal/model.py:72-74", "the resource above a given one", "levels"),
    ("tests/seal/model.py:77-78", "how deep a resource is, which orders the sweep", "order"),
    ("tests/seal/model.py:81-82", "resource order: store, then block, then key, lower numbers "
     "first", "resord"),
    ("tests/seal/model.py:85-86", "deepest-first order, which the give-up and release walks "
     "use", "deep"),
    ("tests/seal/model.py:115-122", "an ancestor's cover is the supremum over its live "
     "children", "eff"),
    ("tests/seal/model.py:124-136", "which other transactions are incompatible at a resource",
     "compat"),
    ("tests/seal/model.py:141-151", "the subtree a give-up or a release takes, deepest first",
     "cascade"),
    ("tests/seal/model.py:166-186", "a grant appearing, rising, falling or disappearing, and "
     "the verb printed for each", "verbs"),
    ("tests/seal/model.py:188-199", "a child appearing or leaving changes what the level above "
     "requires", "falls"),
    ("tests/seal/model.py:201-202", "a resource is brought to the supremum of its asked mode "
     "and its cover", "eff"),
    ("tests/seal/model.py:232-247", "a claim is recorded at the asked mode and falls due",
     "asked"),
    ("tests/seal/model.py:257-264", "a claim falls due again when the level that refused it "
     "moves", "due"),
    ("tests/seal/model.py:268-283", "the effective mode each level of a take's chain must "
     "reach", "eff"),
    ("tests/seal/model.py:285-312", "the level-by-level take: older refuses, younger gives "
     "way, and the grants are printed outermost first", "levels"),
    ("tests/seal/model.py:314-328", "giving way, its order, and the claim it leaves", "asked"),
    ("tests/seal/model.py:332-347", "a release takes the subtree and the claims under it",
     "drop"),
    ("tests/seal/model.py:349-360", "a finish removes everything and prints its own line",
     "shut"),
    ("tests/seal/model.py:364-374", "the sweep: the claims due when it starts, in order, once "
     "each", "order"),
    ("tests/seal/model.py:376-415", "the widen rule, its threshold, its mode, its order and "
     "its repetition", "wideord"),
    ("tests/seal/model.py:419-446", "the line procedure and the closing report", "report"),
    ("tests/seal/model.py:449-450", "the whole program, as a trace followed by the report",
     "entry"),
]

READINGS = [
    ("mode-sup-top", "supix", "mode-cover-six"),
    ("mode-cov-six", "cov", "give-claim-asked"),
    ("mode-cov-write", "cov", "cover-holds-up"),
    ("hold-never-falls", "falls", "cover-plain-goes"),
    ("hold-forgets-ask", "eff", "cover-asked-stays"),
    ("hold-ask-wins", "eff", "give-claim-asked"),
    ("hold-shallow-walk", "deep", "give-age-order"),
    ("give-node-only", "cascade", "give-age-order"),
    ("give-claim-eff", "asked", "give-claim-asked"),
    ("give-claim-all", "cover", "give-age-order"),
    ("keep-order-made", "order", "cover-asked-stays"),
    ("keep-order-deep", "order", "sweep-outermost"),
    ("keep-try-all", "due", "sweep-parked"),
    ("keep-fixpoint", "nextline", "sweep-preempts"),
    ("wide-counts-claims", "widecl", "wide-claims-idle"),
    ("wide-once", "wideord", "wide-twice"),
    ("wide-at-limit", "widen", "wide-after-sweep"),
    ("wide-blocks-first", "wideord", "wide-deep-first"),
    ("wide-preempts", "widepas", "wide-passive"),
    ("step-lookahead", "levels", "take-no-lookahead"),
    ("step-grants-walked", "older", "cover-unblocks"),
    ("step-inner-first", "outer", "cover-asked-stays"),
    ("step-young-first", "younger", "give-age-order"),
    ("step-refuse-any", "younger", "give-age-order"),
    ("step-give-any", "older", "cover-unblocks"),
    ("step-no-sweep", "due", "cover-unblocks"),
    ("step-wide-first", "wideend", "wide-last"),
    ("step-drop-keeps", "drop", "free-subtree"),
    ("step-shut-silent", "shut", "shut-clears"),
]

SHORTCUTS = [
    ("the shipped tree unchanged (nop)", "reward 0; it fails 45 of the 48 graded assertions "
     "and never finishes the two scale families inside the clock"),
    ("constant: one fixed output for every program (cheat-flat-constant)",
     "reward 0; it matches 0 of 414 graded programs"),
    ("positional: every take granted at the resource it names, nothing else "
     "(cheat-pos-grant-all)",
     "reward 0; it matches 0 of 414 graded programs, because no program's first line is a take"),
    ("the worked example's output replayed for every program (cheat-replay-sample)",
     "reward 0; it matches 1 of 414 - runs/one.txt itself is not in the graded set, so it "
     "matches nothing"),
    ("an answer key carrying the 44 frozen enumerated answers (cheat-forge-hand)",
     "reward 0; it passes all 44 enumerated programs and fails all 370 it could not have seen"),
]

TOLERANCES = [
    ("tests/test.sh:35 a 60 s clock on the whole graded set",
     "`authoring/grant-widen-yield/variants/walk` and "
     "`authoring/grant-widen-yield/variants/multiset`, two correct services written to the "
     "same contract with different internals, and `authoring/grant-widen-yield/timing.py`, "
     "which re-measures every row below",
     "2026-09-22: reference 0.22 s on one wide program and 1.45 s on one crowded one, and "
     "all 414 graded programs in 7.89 s of the 60; walk 0.22 s and 1.94 s; multiset 1.44 s "
     "and 2.65 s. The correct-but-naive readings on the same two programs: 14.97 s with the "
     "cover rescanned, 20.96 s with every standing claim looked at, and 26.27 s and over "
     "200 s with the widen threshold tested everywhere - each shipped as a cheat and each "
     "scoring 0"),
]


def check():
    bad = [k for k, v in Q.items() if v not in BRIEF]
    if bad:
        for k in bad:
            print("QUOTE NOT IN instruction.md: %s\n  %s" % (k, Q[k]))
        raise SystemExit(1)
    if '"' in "".join(Q.values()):
        raise SystemExit("a quote contains a double quote")


def main():
    check()
    rows = ["# Instruction trace: grant-widen-yield", "",
            "Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md).",
            "Written by authoring/grant-widen-yield/make_trace.py, which refuses to write a",
            "trace whose quotes are no longer in instruction.md. Checked with",
            "`python tools/tracecheck.py grant-widen-yield`.", "",
            "## Graded assertions", "",
            "| Verifier site | What it grades | Instruction sentence |", "|---|---|---|"]
    for site, fn, what, key in TESTS:
        rows.append("| `%s` %s | %s | \"%s\" |" % (site, fn, what, Q[key]))
    sys.path.insert(0, str(TASK / "tests"))
    import cases as case_mod
    for name in case_mod.ORDER:
        if name not in CASES:
            raise SystemExit("no trace row for enumerated case %s" % name)
        what, key = CASES[name]
        line = case_mod.PROG_LINE[name] if hasattr(case_mod, "PROG_LINE") else None
        site = "tests/cases.py case %s" % name
        rows.append("| `%s` | %s | \"%s\" |" % (site, what, Q[key]))
    for art in ("/app/lk/mode.py", "/app/lk/hold.py", "/app/lk/give.py", "/app/lk/keep.py",
                "/app/lk/wide.py", "/app/lk/step.py"):
        rows.append("| artifact `%s` | only the declared files are collected, and only these "
                    "six | \"%s\"; \"%s\" |" % (art, Q["collect"], Q["extra"]))
    rows.append("| `tests/test.sh:35` a 60 s clock | the whole graded set must finish inside "
                "it | \"%s\" |" % Q["clock"])
    for site, what, key in MODEL:
        rows.append("| `%s` | %s | \"%s\" |" % (site, what, Q[key]))

    rows += ["", "## Readings", "",
             "| Reading | Sentence or published example that rules it out | "
             "Case that separates it |", "|---|---|---|"]
    for name, key, case in READINGS:
        rows.append("| %s | \"%s\" | %s |" % (name, Q[key], case))

    rows += ["", "## Shortcuts", "", "| Strategy | Result |", "|---|---|"]
    for what, got in SHORTCUTS:
        rows.append("| %s | %s |" % (what, got))

    rows += ["", "## Tolerances", "",
             "| Tolerance or limit | Independent implementation | Measured |", "|---|---|---|"]
    for what, how, got in TOLERANCES:
        rows.append("| %s | %s | %s |" % (what, how, got))

    out = HERE / "trace.md"
    out.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    print("wrote %s (%d rows)" % (out, len(rows)))


if __name__ == "__main__":
    main()
