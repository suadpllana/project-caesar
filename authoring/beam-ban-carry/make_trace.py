"""Write authoring/beam-ban-carry/trace.md, with every quote checked against the brief.

A quote typed by hand goes stale the first time a sentence is reworded, and tracecheck then
reports a citation that is no longer in the file. Building the trace from a table means the
quote is asserted here, at the point it is written, and the whole walk is regenerated after any
edit to instruction.md.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "beam-ban-carry"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))
import cases  # noqa: E402
import emit   # noqa: E402

BRIEF = (TASK / "instruction.md").read_text(encoding="utf-8")
FLAT = " ".join(BRIEF.split())

Q = {
    "stop-score": "plus the score on that stop row, less P times that length",
    "stop-len": "its length is how many those are",
    "floor": "when it has emitted at least S tokens and the table has a row taking the stop token",
    "stays": "Closing leaves it standing, and the score of that beam does not change",
    "hyp-tokens": "The hypothesis it makes holds the tokens that beam emitted",
    "more-than-h": "While more than H are held",
    "close-first": "before any candidate of the step is looked at",
    "close-order": "does so, in the order the beams stand",
    "cap-h": "At most H hypotheses are kept",
    "stand": "when its final score is higher, or when the two scores are equal and it is the shorter, or when score and length are both equal and it closed earlier",
    "overflow": "the one standing last is given up",
    "lend": "lends the search each span of its sequence, prompt included, for as long as it is a member",
    "lend-refuse": "the span it would add is one the set is lending",
    "own-refuse": "that span already occurs in the beam's own sequence",
    "give-back": "A member that is given up takes its lending with it",
    "shared": "some other member is still lending stays refused",
    "cands": "one candidate for each token the table has a row for from the last token of its sequence",
    "no-stop-cand": "The stop token is not one of them",
    "cand-score": "candidate scores the score of the beam plus the score on the row",
    "rank": "ordered by score descending. A tie goes to the candidate whose beam stands earlier",
    "one-tok": "passing over one whose token a candidate already taken ends on",
    "width": "until W have been taken or the order runs out",
    "next-order": "Those become the beams of the next step, in the order they were taken",
    "halt-three": "It halts `dry` when nothing was taken. It halts `cap` when the step just run is T",
    "bound": "when the kept set holds H and no beam has a reach greater than the lowest final score in it",
    "halt-order": "read in that order, and the search continues when none of them holds",
    "reach": "less P times the number of steps run so far",
    "reach-floor": "Count that difference as zero when it comes out negative",
    "span": "span is the last N tokens of a sequence",
    "short": "a sequence of fewer than N tokens has none",
    "start": "a single beam holding the prompt, a score of zero and nothing emitted",
    "seq": "the prompt followed by what it has emitted",
    "shut-line": "as each hypothesis closes",
    "gone-line": "as each one is given up, in the order those happen",
    "halt-line": "after them `halt <step> <reason>`",
    "hyp-line": "to a line, the one standing highest first. Ranks count from 0",
    "only": "Nothing else is printed",
    "apart": "no beam, no member and no lending carried over from the one before",
    "ask-order": "Requests are run in the order they appear",
    "files": "The files you may change are `/app/bm/sc.py`",
    "rest": "rest of the tree is replaced by our own copy",
    "entry": "stays the entry the driver calls once per request, returning the lines that request prints",
    "clock": "all of it has to get through inside 60 seconds",
    "scale": "five requests of two thousand eight hundred steps over eight beams",
    "turn": "five of nine hundred whose kept set of thirty turns over on nearly every step",
    "one-row": "There is at most one row for a pair",
    "tok0": "Token 0 is the stop token and never appears in a prompt",
    "steps-from-1": "Steps are numbered from 1",
    "cfg": "sets the beam width, the span length, the floor a hypothesis has to reach, the length penalty, the size of the kept set and the step ceiling",
    "example": "The second line comes out `shut 3 2 13` and should read `shut 3 2 18`",
    "graded-set": "The graded set is three programs of each of those two sizes, three hundred and sixty smaller ones, and forty-two written by hand",
}

for key, text in Q.items():
    if " ".join(text.split()) not in FLAT:
        raise SystemExit("quote %r is not in instruction.md: %s" % (key, text[:70]))


def q(*keys):
    return " ".join('"%s"' % Q[k] for k in keys)


# case name -> (what it grades, quote keys)
CASE = {
    "bound-negative": ("the reach term is floored at zero when the penalty is above the largest score", ("reach", "reach-floor")),
    "bound-nofull": ("the bound is only read once the kept set is full", ("bound",)),
    "bound-nopen": ("the reach charges the penalty on the steps still to come", ("reach", "reach-floor")),
    "bound-raw": ("the reach charges the penalty already accrued", ("reach",)),
    "cand-stop": ("the stop token is not offered as an ordinary continuation", ("cands", "no-stop-cand")),
    "close-after": ("a closure binds the candidates of the step it happened on", ("close-first", "lend-refuse")),
    "halt-order": ("an empty selection is read before the ceiling", ("halt-three", "halt-order")),
    "hyp-one": ("the kept set is ranked from 0", ("hyp-line",)),
    "lend-flat": ("an eviction frees only what no other member still lends", ("give-back", "shared")),
    "lend-keeps": ("an eviction takes its lending with it", ("give-back",)),
    "lend-none": ("a member of the kept set lends its spans to the search", ("lend", "lend-refuse")),
    "list-tie": ("a tie on the final score puts the shorter hypothesis first", ("stand", "hyp-line")),
    "own-emitted": ("the repeat test covers the prompt as well as what was emitted", ("own-refuse", "seq")),
    "own-short": ("a sequence exactly N long already has a span", ("span", "short")),
    "pool-first": ("a full kept set takes the new hypothesis in and gives up its worst", ("overflow",)),
    "pool-oldest": ("the kept set gives up the one standing last, not the oldest", ("stand", "overflow")),
    "pool-tielen": ("a tie on the final score is broken toward the shorter", ("stand",)),
    "pool-tieorder": ("a tie on score and length is broken toward the earlier", ("stand",)),
    "rank-slotdesc": ("a tie on score goes to the beam standing earlier", ("rank",)),
    "rank-toktie": ("the parent's place is read before the token on a tie", ("rank",)),
    "rank-topw": ("selection keeps one beam per final token", ("one-tok",)),
    "rank-wplus": ("at most W candidates are taken", ("width",)),
    "shut-desc": ("closures are settled in the order the beams stand", ("close-order",)),
    "stop-floor": ("the floor is at least S emitted tokens", ("floor",)),
    "stop-len": ("the stop token is not part of the hypothesis", ("stop-len", "stop-score")),
    "stop-noscore": ("the stop row's score counts toward the hypothesis", ("stop-score", "example")),
    "close-absorbs": ("the beam keeps its own score when it closes", ("stays", "stop-score")),
    "lend-emitted": ("a member lends the spans of its prompt as well", ("lend",)),
    "hyp-prompt": ("the kept set prints only the tokens the beam emitted", ("hyp-tokens", "hyp-line")),
    "rank-tokdesc": ("a tie on score and place goes to the smaller token", ("rank",)),
    "pool-atleast": ("the kept set gives one up only once it holds more than H", ("more-than-h", "overflow")),
    "cap-early": ("the ceiling is read at T, not before", ("halt-three",)),
    "ask-apart": ("nothing crosses from one request to the next", ("apart", "ask-order")),
    "close-goes-on": ("a beam that closes goes on producing longer hypotheses", ("stays",)),
    "easy-run": ("the everyday case: nothing refused, nothing given up, both requests run out the ceiling", ("halt-three", "cands", "rank")),
    "never-close": ("a program with no stop row prints no closure and no kept set", ("floor", "hyp-line")),
    "no-row": ("a last token with no row at all takes nothing", ("cands", "halt-three")),
    "penalty-wins": ("the penalty can put a short hypothesis above a long one", ("stop-score", "stand")),
    "self-drop": ("a hypothesis can be taken in and given up on the same step", ("overflow", "gone-line")),
    "short-prompt": ("a prompt shorter than a span refuses nothing at first", ("span", "short", "start")),
    "tie-all": ("one score everywhere, so every tie-break in the contract decides a line", ("rank", "stand", "hyp-line")),
    "width-take": ("more continuations than slots: exactly W are taken", ("width", "rank")),
}

TESTS = [
    ("`tests/test_outputs.py:117` test_frozen_truth_matches_the_model",
     "the sealed model still reproduces the frozen answers; grades nothing the agent wrote",
     ("files",)),
    ("`tests/test_outputs.py:127` test_hand_case",
     "every enumerated program prints exactly the frozen trace, and the program was not altered",
     ("only", "rest")),
    ("`tests/test_outputs.py:136` test_every_nonce_program_matches",
     "every generated program prints exactly what the model says, and was not altered",
     ("only", "graded-set")),
    ("`tests/test_outputs.py:155` test_every_family_is_represented",
     "the generated population covers every family; a shrunk exam is not marked",
     ("graded-set",)),
]

MODEL = [
    ("`tests/seal/model.py:14-28` _read", "cfg carries W N S P H T in that order, sc a row, ask a request and its prompt", ("cfg", "one-row", "tok0")),
    ("`tests/seal/model.py:30-33` _windows", "a span is the last N tokens, and a shorter sequence has none", ("span", "short")),
    ("`tests/seal/model.py:35-37` _worst", "the member given up is the one standing last", ("stand", "overflow")),
    ("`tests/seal/model.py:41-42` _search, the largest score", "the reach uses the largest score anywhere in the table", ("reach",)),
    ("`tests/seal/model.py:45-52` _search, the table", "a continuation exists only where a row does, and the stop edge is read apart", ("cands",)),
    ("`tests/seal/model.py:54-59` _search, the start", "one beam on the prompt, score zero, nothing emitted", ("start", "seq")),
    ("`tests/seal/model.py:61-63` _search, the step number", "steps are numbered from 1", ("steps-from-1",)),
    ("`tests/seal/model.py:64-70` _search, the floor", "a beam closes on at least S emitted tokens with a stop row for its last token", ("floor", "stays")),
    ("`tests/seal/model.py:71-78` _search, the hypothesis", "tokens, length and the final score of a closure", ("stop-score", "stop-len", "shut-line")),
    ("`tests/seal/model.py:79-80` _search, lending", "a member lends every span of its sequence while it is a member", ("lend",)),
    ("`tests/seal/model.py:81-86` _search, the overflow", "over H the one standing last is given up and its lending goes with it", ("overflow", "give-back", "shared", "gone-line")),
    ("`tests/seal/model.py:88-99` _search, refusal", "a candidate is refused by a lent span or by its own sequence", ("lend-refuse", "own-refuse", "cand-score")),
    ("`tests/seal/model.py:101-110` _search, selection", "rank, tie-break, one per final token, at most W", ("rank", "one-tok", "width")),
    ("`tests/seal/model.py:112-125` _search, the halt", "dry, cap and bound in that order, and the reach", ("halt-three", "bound", "halt-order", "reach", "reach-floor")),
    ("`tests/seal/model.py:127-135` _search, the next step", "the beams of the next step stand in the order they were taken", ("next-order",)),
    ("`tests/seal/model.py:137-139` _search, the report", "the kept set printed best first, ranks from 0, tokens after the length", ("hyp-line",)),
    ("`tests/seal/model.py:142-147` expect", "requests run in file order, each from nothing", ("ask-order", "apart")),
]

ARTIFACTS = [
    "/app/bm/sc.py", "/app/bm/rep.py", "/app/bm/keep.py",
    "/app/bm/pick.py", "/app/bm/walk.py", "/app/bm/halt.py",
]

READINGS_ROW = {
    "lend-none": ("lend", "lend-refuse"),
    "lend-keeps": ("give-back",),
    "lend-flat": ("shared",),
    "close-after": ("close-first",),
    "stop-noscore": ("stop-score",),
    "stop-len": ("stop-len",),
    "stop-floor": ("floor",),
    "pool-first": ("overflow",),
    "pool-oldest": ("stand", "overflow"),
    "pool-tielen": ("stand",),
    "pool-tieorder": ("stand",),
    "rank-topw": ("one-tok",),
    "rank-toktie": ("rank",),
    "rank-slotdesc": ("rank",),
    "rank-wplus": ("width",),
    "own-emitted": ("own-refuse", "seq"),
    "own-short": ("span", "short"),
    "cand-stop": ("cands",),
    "bound-nopen": ("reach",),
    "bound-nofull": ("bound",),
    "bound-raw": ("reach",),
    "bound-negative": ("reach-floor",),
    "halt-order": ("halt-order",),
    "list-tie": ("stand", "hyp-line"),
    "shut-desc": ("close-order",),
    "hyp-one": ("hyp-line",),
    "close-absorbs": ("stays",),
    "lend-emitted": ("lend",),
    "hyp-prompt": ("hyp-tokens",),
    "rank-tokdesc": ("rank",),
    "pool-atleast": ("more-than-h", "overflow"),
    "cap-early": ("halt-three",),
}

SHORTCUTS = [
    ("the shipped tree unchanged (the nop)",
     "reward 0; it reproduces 8 of the 42 enumerated programs and 2 of 108 generated ones, and it is over the wall clock besides"),
    ("a constant: one fixed trace for every request (`cheat/cheat-const-cap.sh`)",
     "reward 0; 2 of 42 enumerated, 0 of 108 generated"),
    ("positional: one beam, always the lowest-numbered continuation (`cheat/cheat-pos-first.sh`)",
     "reward 0; 24 of 42 enumerated, because the enumerated programs were shrunk small and many of them run one beam, and 14 of 108 generated"),
    ("the worked example replayed for every request (`cheat/cheat-replay-brief.sh`)",
     "reward 0; 0 of 42 enumerated, 0 of 108 generated"),
    ("an answer key for every enumerated program, over a stage that did no work (`cheat/cheat-forge-hand.sh`)",
     "reward 0; 42 of 42 enumerated and 21 of 108 generated, which is the part a key cannot cover"),
]

TOLERANCES = [
    ("`tests/test.sh:35` the 60 second wall clock on the graded run",
     "`authoring/beam-ban-carry/variants/var-a`, `authoring/beam-ban-carry/variants/var-b`, "
     "and the three naive-but-correct stages under `authoring/beam-ban-carry/slow`",
     "reference 4.2 s, var-b 10.6 s, var-a 26.3 s; slow/lent 111.6 s, slow/rebuild 97.3 s, "
     "slow/scan 356.5 s. Measured by `authoring/beam-ban-carry/timing.py` over the whole "
     "generated population at PER_FAMILY 40, on one core"),
]

HEAD = """# Instruction trace: beam-ban-carry

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Regenerated by
`python authoring/beam-ban-carry/make_trace.py`, which asserts every quote is still in
`instruction.md` before it writes. Checked with `python tools/tracecheck.py beam-ban-carry`.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
"""


def main():
    rows = []
    for site, what, keys in TESTS:
        rows.append("| %s | %s | %s |" % (site, what, q(*keys)))
    for name in cases.ORDER:
        what, keys = CASE[name]
        rows.append("| `tests/cases.py` case %s | %s | %s |" % (name, what, q(*keys)))
    for path in ARTIFACTS:
        rows.append("| artifact `%s` | this file is collected from the agent and nothing else is | %s |"
                    % (path, q("files", "rest", "entry")))
    rows.append("| `tests/test.sh:35` a 60 s clock | the whole graded set runs under one wall clock | %s |"
                % q("clock", "scale", "turn"))
    for site, what, keys in MODEL:
        rows.append("| %s | %s | %s |" % (site, what, q(*keys)))

    out = [HEAD, "\n".join(rows), "\n\n## Readings\n\n",
           "| Reading | Sentence or published example that rules it out | Case that separates it |\n|---|---|---|\n"]
    reading_rows = []
    for name in sorted(emit.READINGS):
        reading_rows.append("| %s: %s | %s | `%s` |" % (name, emit.NOTES[name], q(*READINGS_ROW[name]), name))
    out.append("\n".join(reading_rows))
    out.append("\n\n## Shortcuts\n\n| Strategy | Result |\n|---|---|\n")
    out.append("\n".join("| %s | %s |" % row for row in SHORTCUTS))
    out.append("\n\n## Tolerances\n\n| Tolerance or limit | Independent implementation | Measured |\n|---|---|---|\n")
    out.append("\n".join("| %s | %s | %s |" % row for row in TOLERANCES))
    out.append("\n")
    text = "".join(out)
    if "\r" in text:
        raise SystemExit("carriage return in trace.md")
    (HERE / "trace.md").write_text(text, encoding="utf-8", newline="\n")
    print("wrote trace.md: %d graded rows, %d readings" % (len(rows), len(reading_rows)))


if __name__ == "__main__":
    main()
