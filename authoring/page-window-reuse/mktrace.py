"""Write trace.md: every graded assertion against the sentence that tells the agent about it."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "page-window-reuse"

Q = {
    "resid": "the request keeps only the pages holding any of its first `a` tokens and the pages holding any of its last `s` tokens",
    "holds_all": "While a prompt is being written its request holds every page of it, reused or written alike",
    "again": "That same rule is applied again each time it emits a token",
    "order": "lets them go in the order of the tokens they hold",
    "stops": "The walk stops at the first page that is gone, whatever still sits below that one",
    "takes_held": "the request takes that page and the walk goes on, whether or not somebody else is holding it",
    "complete_only": "Only a complete page is ever reused.",
    "released": "the page stays in the pool as reusable if a walk can still reach it, and goes back to the free pool at once if it cannot",
    "supply": "A page for a request to write is taken from the lowest numbered free page; when there is none, the pool takes back the page released longest ago",
    "strand": "those nobody holds going back to the free pool with it and those somebody holds staying until their holder lets go, never to be reached again, complete at the time or not",
    "kick": "the request that became resident most recently, or the request that asked for the page when none is resident, lets go of everything it holds and starts again from nothing later, keeping its place in arrival order",
    "one_at_a_time": "A fill asks for one page at a time.",
    "twin": "When a page fills and the same tokens already sit below the same page, the request hands its own page back to the free pool and takes the one that is already there.",
    "decode": "Each resident request emits one token, in the order the requests became resident, until the budget of `b` tokens for that step is spent",
    "unreached": "a request the budget does not reach emits nothing that step",
    "phases": "A step decodes before it fills.",
    "arrival": "What is left of the budget goes to the waiting prompts in arrival order.",
    "free_reuse": "hands it the pages it can reuse, which costs no budget",
    "boundary": "A budget too small to reach the next boundary therefore takes nothing at all, and that ends the filling for that step",
    "resident_when": "A request becomes resident in the step that completes its prompt and emits its first token in the next one.",
    "fill_line": "A prompt taken up prints `fill <request> <reused> <written>`, both counted in tokens, and prints that line again in any later step in which it writes.",
    "hold_line": "A preemption prints `hold <request>`.",
    "gone_line": "A take-back prints `gone <page> <pages back in the pool>`.",
    "done_line": "A request that has emitted its last token lets go of everything and prints `done <request>`.",
    "at_line": "The question prints `at <request> <token> <page>`, with `none` in place of the page when that request is not holding a page for that token, including when it has not got that far.",
    "cancel": "A cancelled request lets go of everything it holds.",
    "nothing_else": "Nothing else is printed.",
    "when": "Every line is printed when it happens.",
    "files": "The files you may change are `/app/kv/pool.py`, `/app/kv/keep.py`, `/app/kv/live.py`, `/app/kv/fill.py`, `/app/kv/turn.py` and `/app/kv/put.py`. Nothing else.",
    "clock": "all of it has to get through inside 60 seconds",
    "set": "The graded set is three programs of each of those sizes and four hundred and twenty-two smaller ones",
    "numbered": "A pool holds pages numbered from 1",
    "config": "`pool n w a s b` sets the pool to `n` pages of `w` tokens each, `a` sink tokens, `s` window tokens and a budget of `b` tokens per step.",
    "named": "A page is named by its tokens and the page before it.",
    "ask": "`ask r p o` brings in request `r` with prompt `p` and output `o`, each written as comma separated `count:token` runs, or `-` for none.",
    "bulk": "`bulk x k p t o` is the import shorthand that brings in `k` requests named `x0` upward",
    "driver": "takes a program and prints a line for each thing that happens",
    "widedeep": "`/app/progs/wide.txt` brings in a hundred thousand requests of one page each against a pool of fifty thousand pages",
}

TESTS = [
    ("`tests/test_outputs.py:120` test_frozen_truth_matches_the_model",
     "the sealed model still reproduces the frozen answers, so a drifted model cannot redefine correct; grades nothing the agent wrote", "set"),
    ("`tests/test_outputs.py:130` test_hand_case",
     "the whole printed trace of each enumerated program, line for line, and that the program was not altered", "when"),
    ("`tests/test_outputs.py:139` test_every_nonce_program_matches",
     "the whole printed trace of every generated program, line for line", "when"),
    ("`tests/test_outputs.py:158` test_every_family_is_represented",
     "the generated population covers every family, including the two scale families", "set"),
]

CASES = {
    "fill-hold-all": "holds_all", "fill-lets-go": "resid", "fill-short-keeps": "resid",
    "fill-holds-middle": "holds_all", "live-sink-stays": "resid", "live-no-sink": "resid",
    "live-window-edge": "again", "walk-whole": "takes_held", "walk-held": "takes_held",
    "walk-stops-at-gap": "stops", "walk-part-page": "complete_only",
    "rest-reusable": "released", "rest-free-at-once": "released", "rest-strand-frees": "strand",
    "back-oldest": "supply", "back-strand": "strand", "back-under-part": "strand",
    "kick-newest": "kick", "kick-alone": "kick", "kick-ends-turn": "kick",
    "twin-hands-back": "twin", "twin-other-prev": "twin",
    "turn-decode-first": "phases", "turn-page-edge": "boundary", "turn-no-jump": "boundary",
    "turn-reuse-free": "free_reuse", "back-free-first": "supply",
    "back-order-of-release": "order", "end-done-frees": "done_line",
    "end-stop-waiting": "cancel", "end-stop-part": "cancel", "end-stop-live": "cancel",
}

MODEL = [
    ("42-43", "sink(): how many pages the first `a` tokens cover", "resid"),
    ("45-49", "take(): the lowest numbered free page", "supply"),
    ("51-59", "give(): a page goes back to the free pool with everything it carried", "released"),
    ("61-74", "strip(): the strand of a take-back - free what nobody holds, put the rest out of reach", "strand"),
    ("76-83", "oldest(): the reusable page released longest ago", "supply"),
    ("85-96", "rest(): the last holder leaving decides reusable against free", "released"),
    ("98-102", "grip(): a page taken up stops being reusable", "takes_held"),
    ("104-110", "unlist(): a page out of reach leaves the index", "stops"),
    ("112-119", "back(): the take-back and the line it prints", "gone_line"),
    ("121-130", "page(): free, then a take-back, then nothing", "supply"),
    ("132-133", "size(): a request's length is its placed prompt plus what it has emitted", "ask"),
    ("135-140", "edge(): the lowest page outside the first `a` tokens residency still wants", "resid"),
    ("142-149", "shed(): what the window has moved past is let go, in token order", "again"),
    ("151-156", "loose(): everything a request holds goes, in token order", "order"),
    ("158-172", "write(): a new page is taken and sits below the page written before it", "named"),
    ("173-191", "write(): a completed page meets its own content below the same page", "twin"),
    ("193-206", "walk(): reuse from the start of the prompt, stopping at the first gap", "stops"),
    ("208-211", "settle(): the prompt is complete, the middle goes, the request is resident", "resident_when"),
    ("213-222", "feed(): a prompt is taken up once and what it reuses costs no budget", "free_reuse"),
    ("223-232", "feed(): the chunk ends on a page boundary, or writes nothing at all", "boundary"),
    ("233-245", "feed(): the fill line, in tokens", "fill_line"),
    ("247-263", "stall(): who is preempted, what it loses, where it goes back to", "kick"),
    ("265-280", "step(): the decode phase, in residency order, inside the budget", "decode"),
    ("281-291", "step(): the fill phase, in arrival order, stopping at the first stall", "arrival"),
    ("293-299", "born(): a request arrives waiting, in arrival order", "ask"),
    ("301-310", "ex(): the pool line sets the pool, page width, sink, window and budget", "config"),
    ("311-316", "ex(): ask and bulk bring requests in", "bulk"),
    ("317-324", "ex(): stop cancels a request and prints nothing", "cancel"),
    ("325-331", "ex(): the at query and its none", "at_line"),
    ("333-341", "spread(): count:token runs", "ask"),
    ("343-348", "expect(): one line per thing that happens, in order", "driver"),
]

READINGS = [
    ("live-no-sink", "resid", "back-free-first"),
    ("live-sink-pages", "config", "back-oldest"),
    ("live-window-frozen", "again", "back-under-part"),
    ("live-window-edge", "resid", "fill-hold-all"),
    ("fill-lets-go-early", "holds_all", "fill-holds-middle"),
    ("walk-past-gap", "stops", "back-free-first"),
    ("walk-free-only", "takes_held", "back-under-part"),
    ("rest-keeps-unreachable", "released", "rest-strand-frees"),
    ("rest-frees-always", "released", "back-free-first"),
    ("back-lowest-page", "supply", "back-oldest"),
    ("back-newest", "supply", "back-oldest"),
    ("back-one-page", "strand", "back-oldest"),
    ("back-leaf-only", "strand", "back-oldest"),
    ("grab-back-first", "supply", "back-free-first"),
    ("grab-highest-free", "supply", "back-free-first"),
    ("grab-no-back", "supply", "back-oldest"),
    ("kick-oldest", "kick", "kick-ends-turn"),
    ("kick-carries-on", "kick", "kick-ends-turn"),
    ("kick-keeps-work", "kick", "fill-holds-middle"),
    ("turn-past-edge", "boundary", "back-under-part"),
    ("turn-queue-jump", "boundary", "turn-no-jump"),
    ("turn-fill-first", "phases", "back-free-first"),
    ("turn-reuse-costs", "free_reuse", "fill-holds-middle"),
    ("twin-keeps-own", "twin", "twin-hands-back"),
    ("order-newest-first", "order", "back-order-of-release"),
]

SHORTCUTS = [
    ("the shipped tree unchanged (the nop)", "reward 0; 27 of 33 tests fail, 6 pass"),
    ("a constant: the most common line of the ground truth for every program", "reward 0; no enumerated program's trace is a repeated constant, and the fill, gone and at lines carry per-program numbers"),
    ("positional: print nothing at all", "reward 0; every enumerated program prints at least one line, and 24 of the 32 print a fill line on their first step"),
    ("the worked example replayed: the trace of `small.txt` for every program", "reward 0; it matches only `small.txt`, one program of 426"),
    ("the previous revision of the reference (the shipped tree, six wrong readings)", "reward 0; this is the nop, and the six readings are cheats `live-no-sink`, `walk-past-gap`, `back-lowest-page`, `back-one-page`, `turn-past-edge`, `turn-fill-first`, `twin-keeps-own`"),
    ("the frozen answers for every enumerated program, replayed (cheat `forge-from-truth`)", "reward 0; passes all 32 enumerated programs and fails the 396 it could not have seen"),
]

TOL = [
    ("the 60 second wall clock on the worker (`tests/test.sh:9`)",
     "`authoring/page-window-reuse/variants/ok-heap` and `variants/ok-kids`, both written apart from the reference, and the three naive-but-correct families under `authoring/page-window-reuse/slow/`",
     "reference 5.5 s over the whole graded set; ok-heap and ok-kids agree with the model over 200 generated programs each; residency recomputed per page 110 s, the oldest release by scanning 144 s, the strand by sweeping the page table 203 s"),
]


def main():
    out = ["# Instruction trace: page-window-reuse", "",
           "Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md).",
           "Re-run `python tools/tracecheck.py page-window-reuse` after any change to the",
           "instruction, the tests, the model, the generator or the environment.", "",
           "## Graded assertions", "",
           "| Verifier site | What it grades | Instruction sentence |", "|---|---|---|"]
    for site, what, key in TESTS:
        out.append("| %s | %s | \"%s\" |" % (site, what, Q[key]))
    text = (TASK / "tests" / "cases.py").read_text().splitlines()
    for name, key in CASES.items():
        line = next(i + 1 for i, s in enumerate(text) if s.startswith('_p("%s"' % name))
        out.append("| `tests/cases.py:%d` case %s | the rule this program pins | \"%s\" |"
                   % (line, name, Q[key]))
    for art in ("pool.py", "keep.py", "live.py", "fill.py", "turn.py", "put.py"):
        out.append("| artifact `/app/kv/%s` | only the declared files are collected | \"%s\" |"
                   % (art, Q["files"]))
    out.append("| `tests/test.sh:27` a 60 s clock | the whole graded set runs inside it | \"%s\" |" % Q["clock"])
    for span, what, key in MODEL:
        out.append("| `tests/seal/model.py:%s` | %s | \"%s\" |" % (span, what, Q[key]))

    out += ["", "## Readings", "",
            "| Reading | Sentence or published example that rules it out | Case that separates it |",
            "|---|---|---|"]
    for name, key, case in READINGS:
        out.append("| %s | \"%s\" | `%s` |" % (name, Q[key], case))

    out += ["", "## Shortcuts", "", "| Strategy | Result |", "|---|---|"]
    for a, b in SHORTCUTS:
        out.append("| %s | %s |" % (a, b))

    out += ["", "## Tolerances", "",
            "| Tolerance or limit | Independent implementation | Measured |", "|---|---|---|"]
    for a, b, c in TOL:
        out.append("| %s | %s | %s |" % (a, b, c))
    out.append("")
    (HERE / "trace.md").write_text("\n".join(out), encoding="utf-8", newline="\n")
    print("wrote trace.md: %d lines" % len(out))


if __name__ == "__main__":
    main()
