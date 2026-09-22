"""Write authoring/stale-cover-serve/trace.md from a hand-written mapping.

The walk itself is the judgment - which sentence settles which graded decision - and that is
what the table below is. Generating the file from it rather than editing eighty markdown rows
by hand means a renamed case or a reworded sentence fails here, loudly, instead of leaving a
stale quote that `tracecheck` finds later.

Every quote is asserted against instruction.md before the file is written.

    python authoring/stale-cover-serve/make_trace.py
"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402
import readings as rd  # noqa: E402

OUT = HERE / "trace.md"

Q = {
    "store-goes": "the read goes to the store instead and is answered at N",
    "cache-serves": "the read is answered from the cache at the largest such version and no "
                    "fetch is issued",
    "band": "The version a read is answered at is at most N and at least N - s, and never "
            "below 0",
    "one-version": "every part of the answer must be content the cache still accounts for at "
                   "that same version",
    "holes": "Start from the maximal runs of keys within lo to hi that no content the cache "
             "accounts for at N covers",
    "mark": "The store also reports the newest version at which it wrote any key in that range",
    "mark-zero": "or version 0 when it has never written one of them",
    "run-span": "the content just fetched was the store's content over that range at every "
                "version in between",
    "close": "the fetched content was the store's up to the version before that commit and no "
             "further",
    "stay-open": "A commit that writes nothing inside a range leaves its run open",
    "write-anyway": "A staged write or delete writes its key whether or not it changes what is "
                    "there",
    "dup-staged": "two staged operations on one key leave the later one and count as a single "
                  "write of that key",
    "empty-commit": "every `c` raises the version by one, whether or not anything was staged",
    "version-zero": "The store starts empty at version 0",
    "retain": "Content whose last correct version is below N - H is discarded and can answer "
              "nothing further",
    "retain-open": "Content whose run is still open is never discarded, however long ago it "
                   "was fetched",
    "combine": "a run that begins no more than G keys after the previous one ends is taken "
               "together with it as a single run spanning both and the ground between them",
    "cap": "If more than F runs are left after that, all of them are dropped and the whole of "
           "lo to hi is fetched as one run instead",
    "as-fetched": "what comes back is kept as the run it was fetched in",
    "not-folded": "it is not folded into anything the cache already holds even where it covers "
                  "the same keys",
    "fetch-order": "Each remaining run is one fetch, issued in increasing key order",
    "fetch-line": "Each fetch prints `f lo hi` with the first and last key of the run fetched",
    "answer": "the live rows of lo to hi as of that version in increasing key order, each "
              "written `k=v`, all separated by single spaces",
    "empty-answer": "A read whose range holds no rows at that version prints `a` and the "
                    "version followed by a single `-`",
    "once": "Every key appears at most once on an answer line",
    "commit-line": "A commit prints `v N` with the version it created",
    "artifacts": "The graded artifact is these seven files and nothing else: "
                 "`/app/rng/seg.py`, `/app/rng/pick.py`, `/app/rng/hole.py`, "
                 "`/app/rng/mend.py`, `/app/rng/knit.py`, `/app/rng/age.py` and "
                 "`/app/rng/ask.py`",
    "no-new-file": "a new file anywhere is never collected",
    "entry-points": "so those three names and their arguments have to stay as they are",
    "clock": "gives that stage 60 seconds of wall clock for the whole set",
    "scale": "A cache that answers every program correctly and does not get through the set "
             "inside the limit scores the same as one that answers them wrongly",
    "exact": "Every graded program is compared line for line against the answer it should give",
    "one-wrong": "one wrong line anywhere fails the whole run",
    "f-floor": "F is never below 1",
}

TESTS = [
    ("tests/test_outputs.py:85", "test_record_is_complete",
     "that every graded program was run, on the text the grader set, so a run that skipped or "
     "shortened programs fails on the record", ["exact", "artifacts", "no-new-file"]),
    ("tests/test_outputs.py:97", "test_nothing_raised",
     "that no graded program raised", ["one-wrong"]),
    ("tests/test_outputs.py:105", "test_enumerated_programs",
     "the whole trace of each of the 37 named programs against the frozen answers",
     ["exact", "one-wrong"]),
    ("tests/test_outputs.py:123", "test_model_still_matches_the_frozen_answers",
     "that the sealed model still reproduces the frozen answers before it judges anything",
     ["exact"]),
    ("tests/test_outputs.py:130", "test_generated_programs",
     "the whole trace of each of the 364 generated programs against the sealed model",
     ["exact", "one-wrong", "scale"]),
]

CASES = {
    "cold-miss": ("a read with nothing cached fetches and answers at the present version",
                  ["store-goes", "fetch-order"]),
    "fresh-cover": ("a range wholly inside current content is answered without a fetch",
                    ["cache-serves"]),
    "serve-back-one": ("one version back is a whole cover, so an allowance of one avoids the "
                       "fetch", ["band", "cache-serves"]),
    "zero-forces-fetch": ("the same read with no allowance goes to the store",
                          ["band", "store-goes"]),
    "no-torn-cover": ("two halves never correct at the same version are not an answer",
                      ["one-version"]),
    "newest-wins": ("covers at two versions, and the newer one is served", ["cache-serves"]),
    "gap-at-now": ("the holes are the ones open at the present version, not at the best "
                   "partial one", ["holes"]),
    "learn-the-past": ("a fetch answers reads aimed before it happened", ["mark", "run-span"]),
    "empty-not-old": ("a fetch that comes back empty is correct from the delete",
                      ["mark", "mark-zero"]),
    "close-before": ("a commit ends a run at the version before it", ["close"]),
    "same-value-write": ("storing the value a key already holds is still a write",
                         ["write-anyway"]),
    "absent-delete": ("deleting a key that is not there is still a write", ["write-anyway"]),
    "keep-closed": ("content the present has left behind keeps answering its own versions",
                    ["close", "cache-serves"]),
    "horizon-drops": ("past the horizon the older version is gone", ["retain"]),
    "horizon-edge": ("a run ending exactly on the horizon is kept", ["retain"]),
    "horizon-open": ("a run still open is never discarded", ["retain-open"]),
    "horizon-zero": ("a horizon of zero drops a run on the commit that closed it", ["retain"]),
    "dupe-keys": ("two pieces of one cover share keys and the answer lists each once",
                  ["once"]),
    "row-order": ("the cover was built right half first and the answer is still in key order",
                  ["answer"]),
    "floor-edge": ("the only cover sits exactly at the oldest allowed version", ["band"]),
    "two-holes": ("two holes, one fetch each, in increasing key order",
                  ["fetch-order", "fetch-line"]),
    "single-hole": ("a hole of one key is one fetch and an empty range prints a dash",
                    ["fetch-order", "empty-answer"]),
    "empty-commit": ("a commit that stages nothing still makes a version", ["empty-commit"]),
    "dup-staged": ("two writes of one key in a batch leave the later value", ["dup-staged"]),
    "read-at-zero": ("a read before any commit is answered at version zero", ["version-zero"]),
    "wide-allowance": ("an allowance past the whole history stops at version zero", ["band"]),
    "nested-cover": ("content inside the range leaves a hole on each side", ["holes"]),
    "cascade-close": ("one commit ends two runs and the pair still covers the older version "
                      "together", ["close", "stay-open"]),
    "delete-visible": ("a key deleted since is absent now and present at the allowed version",
                       ["answer"]),
    "zero-hit": ("no allowance at all still takes a current cover", ["cache-serves"]),
    "no-cover-any": ("part of the range was never cached, so no version has a whole cover",
                     ["store-goes"]),
    "combine-two": ("two holes one cached key apart are one round trip when the slack allows",
                    ["combine"]),
    "combine-edge": ("one key further apart and the same slack leaves them as two",
                     ["combine"]),
    "cap-whole": ("past the cap it is the whole requested range, not the span of the runs",
                  ["cap"]),
    "cap-edge": ("exactly as many runs as the cap allows is not past it", ["cap", "f-floor"]),
    "combine-then-cap": ("the cap counts what combining left, not the holes before it",
                         ["combine", "cap"]),
    "install-run-whole": ("a combined run is kept as the run it was fetched in",
                          ["as-fetched", "not-folded", "mark"]),
}

MODEL = [
    ("tests/seal/model.py:37-46", "Hist.commit applies the staged batch as one version",
     ["empty-commit", "dup-staged", "write-anyway"]),
    ("tests/seal/model.py:48-53", "Hist.value reads one key back at a past version",
     ["answer"]),
    ("tests/seal/model.py:55-61", "Hist.rows builds the answer rows at the served version",
     ["answer", "once"]),
    ("tests/seal/model.py:63-68", "Hist.mark is the newest write across a fetched run",
     ["mark", "mark-zero"]),
    ("tests/seal/model.py:71-79", "Part is one cached run with the versions it is correct for",
     ["run-span"]),
    ("tests/seal/model.py:93-98", "Cache.add keeps a fetched run as it was fetched",
     ["as-fetched", "not-folded"]),
    ("tests/seal/model.py:109-115", "Cache.close ends a run at the version before the commit",
     ["close", "stay-open"]),
    ("tests/seal/model.py:117-119", "Cache.drop applies the horizon to closed runs only",
     ["retain", "retain-open"]),
    ("tests/seal/model.py:122-131", "_union merges one key's runs before they are counted",
     ["one-version"]),
    ("tests/seal/model.py:136-139", "served clamps the band the answer may come from",
     ["band"]),
    ("tests/seal/model.py:141-158", "served requires every key of the range to be covered at "
     "the same version", ["one-version"]),
    ("tests/seal/model.py:159-175", "served takes the newest version at which that holds",
     ["cache-serves"]),
    ("tests/seal/model.py:184-208", "gaps is the maximal runs uncovered at the present version",
     ["holes"]),
    ("tests/seal/model.py:211-216", "gaps combines runs within the slack", ["combine"]),
    ("tests/seal/model.py:217-219", "gaps replaces them with the whole range past the cap",
     ["cap"]),
    ("tests/seal/model.py:222-225", "render is the answer line and the empty answer",
     ["answer", "empty-answer"]),
    ("tests/seal/model.py:269-277", "trace prints the version a commit created and settles the "
     "cache", ["commit-line", "close", "retain"]),
    ("tests/seal/model.py:278-286", "trace serves a read or fetches for it", ["cache-serves",
     "store-goes", "fetch-line"]),
]

READINGS = {
    "now-only": ("the allowance is ignored and every read is answered at the present version",
                 ["band"], "serve-back-one"),
    "per-entry": ("each piece of the cover need only be recent enough on its own",
                  ["one-version"], "serve-back-one"),
    "oldest-version": ("the oldest allowed covered version is served", ["cache-serves"],
                       "newest-wins"),
    "floor-low": ("the band reaches one version further back", ["band"], "zero-forces-fetch"),
    "floor-high": ("the band stops one version short", ["band"], "serve-back-one"),
    "born-now": ("a fetch is correct only from the version it happened at", ["mark"],
                 "learn-the-past"),
    "born-zero-empty": ("a fetch that comes back empty is correct from the beginning",
                        ["mark-zero"], "empty-not-old"),
    "fetch-when-stale": ("anything but the present version is refetched", ["cache-serves"],
                         "serve-back-one"),
    "warm-fetch": ("the holes are fetched even when the cache could serve the read",
                   ["cache-serves"], "serve-back-one"),
    "install-per-hole": ("a combined run is carved back into the holes it was made of",
                         ["as-fetched", "not-folded"], "install-run-whole"),
    "close-at-commit": ("a commit ends a run at its own version", ["close"], "serve-back-one"),
    "drop-on-close": ("a run a commit overtook is discarded rather than closed",
                      ["close", "cache-serves"], "serve-back-one"),
    "horizon-strict": ("a run ending exactly on the horizon is discarded", ["retain"],
                       "horizon-edge"),
    "horizon-keeps-count": ("the horizon is a count of closed runs rather than a version",
                            ["retain"], "horizon-drops"),
    "horizon-drops-open": ("the horizon also discards runs that are still open",
                           ["retain-open"], "horizon-open"),
    "holes-count-closed": ("closed runs count as covering when the holes are worked out",
                           ["holes"], "zero-forces-fetch"),
    "holes-desc": ("the fetches go in decreasing key order", ["fetch-order"], "two-holes"),
    "holes-unsorted": ("the holes are walked in the order the runs were installed",
                       ["holes", "fetch-order"], "row-order"),
    "slack-strict": ("the slack is exclusive", ["combine"], "combine-two"),
    "slack-gap": ("the slack is measured from the first key of the next run", ["combine"],
                  "combine-two"),
    "cap-span": ("past the cap it is the span of the runs rather than the requested range",
                 ["cap"], "cap-whole"),
    "cap-at-cap": ("the cap fires at the cap rather than past it", ["cap"], "cap-edge"),
    "cap-before-combine": ("the cap counts the holes before combining", ["cap", "combine"],
                           "combine-then-cap"),
    "rows-concat": ("the pieces of the cover are concatenated", ["once", "answer"],
                    "no-torn-cover"),
    "rows-unsorted": ("the rows come out in the order the pieces were read", ["answer"],
                      "no-torn-cover"),
    "rows-at-now": ("the rows are taken from whatever is current rather than at the served "
                    "version", ["answer", "one-version"], "serve-back-one"),
    "const-empty": ("every read answers at version zero with no rows", ["answer", "band"],
                    "cold-miss"),
    "const-now": ("every read answers at the present version with no rows", ["answer"],
                  "cold-miss"),
    "pos-always-fetch": ("every read fetches the whole range", ["cache-serves"],
                         "fresh-cover"),
    "holes-per-key": ("one run per uncovered key rather than maximal runs", ["holes"],
                      "two-holes"),
}

SHORTCUTS = [
    ("the shipped tree unchanged (nop)",
     "0. Two of the five test functions fail; the shipped service ignores the version an "
     "answer is at, treats the allowance as an age on a cache entry, and concatenates the "
     "pieces of a cover."),
    ("constant: one fixed answer for every read (`cheat-const-empty`, `cheat-const-now`)",
     "0 each. `const-empty` matches no enumerated program and no generated one; `const-now` "
     "matches none either, since every program in the set has at least one read over a range "
     "holding rows."),
    ("positional: always fetch the whole range and answer at the present version "
     "(`cheat-pos-always-fetch`)",
     "0. It is right on a cold miss and wrong on every read a cover could have served; it "
     "fails `fresh-cover`, the first enumerated program with two reads."),
    ("the frozen answers replayed (`cheat-forge-hand`)",
     "0. It carries the answers for all 37 enumerated programs, narrows by the op sequence as "
     "the run proceeds and reproduces every one of them, then falls back to the shipped engine "
     "and fails the generated population."),
]

TOLERANCE = [
    ("`tests/test.sh:34` a 60 s clock on the stage that runs submitted code",
     "three correct engines written apart from the reference: "
     "`authoring/stale-cover-serve/variants/ok-perkey-cover` answers the serving question by "
     "unioning each key's runs and counting events, "
     "`authoring/stale-cover-serve/variants/ok-no-index` carries no key index at all, and "
     "`authoring/stale-cover-serve/variants/ok-holes-per-key` splits the holes per key",
     "4.95 s, 5.10 s and 8.40 s over the whole graded set of 401 programs against the 60 s "
     "limit, 7 to 12 times the headroom; the reference is 5.11 s. The two naive serving "
     "searches are 387.70 s and 82.64 s on the four scale programs alone."),
]


def cite(keys):
    return " ".join('"%s"' % Q[k] for k in keys)


def main():
    prose = (lab.TASK / "instruction.md").read_text(encoding="utf-8")
    flat = re.sub(r"\s+", " ", prose)
    for key, text in Q.items():
        assert re.sub(r"\s+", " ", text) in flat, "quote %r is no longer in instruction.md" % key
    cases = lab.cases()
    for name in cases.ORDER:
        assert name in CASES, "enumerated case %s has no row" % name
    for name in CASES:
        assert name in cases.ORDER, "row for %s, which is not an enumerated case" % name
    for name in rd.READINGS:
        assert name in READINGS, "reading %s has no row" % name

    out = [
        "# Instruction trace: stale-cover-serve",
        "",
        "Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md).",
        "Written by authoring/stale-cover-serve/make_trace.py from a hand-written mapping, so a",
        "renamed case or a reworded sentence fails there rather than leaving a stale quote here.",
        "",
        "## Graded assertions",
        "",
        "| Verifier site | What it grades | Instruction sentence |",
        "|---|---|---|",
    ]
    for site, name, what, keys in TESTS:
        out.append("| `%s` %s | %s | %s |" % (site, name, what, cite(keys)))
    for name in cases.ORDER:
        what, keys = CASES[name]
        out.append("| `tests/cases.py` case %s | %s | %s |" % (name, what, cite(keys)))
    for path in ("seg.py", "pick.py", "hole.py", "mend.py", "knit.py", "age.py", "ask.py"):
        out.append("| artifact `/app/rng/%s` | only the declared files are collected | %s |"
                   % (path, cite(["artifacts", "no-new-file", "entry-points"])))
    out.append("| `tests/test.sh:34` a 60 s clock | the wall clock on the stage that runs "
               "submitted code | %s |" % cite(["clock", "scale"]))
    for site, what, keys in MODEL:
        out.append("| `%s` | %s | %s |" % (site, what, cite(keys)))

    out += [
        "",
        "## Readings",
        "",
        "| Reading | Sentence or published example that rules it out | Case that separates it |",
        "|---|---|---|",
    ]
    for name in sorted(READINGS):
        what, keys, case = READINGS[name]
        out.append("| %s - %s | %s | `%s` |" % (name, what, cite(keys), case))
    out += [
        "",
        "`holes-per-key` is the one reading nothing separates, and that is a fact about the "
        "contract rather than a gap: combining puts adjacent per-key runs back together "
        "whatever the slack is, so the maximality of the holes is unobservable. It is a correct "
        "variant that must score 1, not a cheat.",
        "",
        "## Shortcuts",
        "",
        "| Strategy | Result |",
        "|---|---|",
    ]
    for what, got in SHORTCUTS:
        out.append("| %s | %s |" % (what, got))
    out += [
        "",
        "## Tolerances",
        "",
        "| Tolerance or limit | Independent implementation | Measured |",
        "|---|---|---|",
    ]
    for what, who, got in TOLERANCE:
        out.append("| %s | %s | %s |" % (what, who, got))
    out += [
        "",
        "There is no numeric tolerance anywhere: traces are compared as strings.",
        "",
    ]
    OUT.write_text("\n".join(out), encoding="utf-8", newline="\n")
    print("wrote %s: %d lines" % (OUT, len(out)))


if __name__ == "__main__":
    main()
