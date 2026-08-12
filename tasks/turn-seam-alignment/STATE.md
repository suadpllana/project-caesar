# Task state

## Current stage

`Stage 7 - Pre-flight and packaging, after a difficulty recalibration and an anti-cheat
repair`

This task has been through the pipeline twice. The first time it cleared the easiness probe
at 0 of 3 and **failed the difficulty probe at 0 of 8**, which is a rejection: the band is
1 to 6. That recalibration is written up under "Recalibration" below. The second time it
**failed quality review on anti-cheat robustness**, and that repair is written up under
"Anti-cheat repair" at the end. Everything above those two sections describes the task as
it now stands.

## Assistant's assigned role

Engineer on the data path between a rollout worker and a trainer for multi-turn RL: chat
templates, tool turns, the loss mask, and the tokenizer sitting in the middle of all of it.

## Source repository

- Repo URL: https://github.com/vllm-project/vllm (issue tracker used as the seed only)
- Task shape: authored on top. No upstream source is vendored. The rollout worker in
  `environment/app_src/` is written for this task: a CPU-only, integer-arithmetic loop with
  the organs the failure needs (a byte-pair tokenizer over a 54-character alphabet and 256
  merges, a chat template with four block markers, a per-episode render cache, a toy
  network, a greedy sampler, an episode driver with a retry path).
- Why not vendor: the upstream repository is public and diffable, and any accepted fix in
  it is public with it.
- Seed: the family of incremental-prompt-encoding issues in multi-turn chat serving. What
  they hand you is the observation that re-encoding the whole conversation every turn is
  the worker's bottleneck, together with the published recipe for avoiding it - back up a
  fixed number of characters from the seam, cut at a pre-tokenizer boundary, re-encode the
  tail, and verify against a full encode. Every step of that recipe is punished here, and
  both halves of it ship as cheats.
- Proper-noun sweep: no project, product, company or person name anywhere in the shipped
  tree; no upstream identifiers, no distinctive error strings, no URLs. Identifiers are in
  the register of ordinary internal code (`tmpl`, `inc`, `rec`, `drv`, `ep`, `rt`, `gen`,
  `pfx`-style abbreviations).
- Upstream-diff check: there is nothing to diff. An agent that finds the seed learns the
  published recipe, which is one of the cheats.

## Task summary

The agent gets a working rollout worker whose sequences do not match the policy that
produced them. Two things are wrong at once. The trainable run each reply owns is computed
from where the reply generated, which is wrong wherever the finished render re-merges
across the seam; and the tokenizer is handed every render from character zero, which is
most of what the worker spends its time on. Four files may be edited (`tok/inc.py`,
`tok/store.py`, `loop/ep.py`, `loop/rec.py`); everything else is restored from a pristine
copy before grading.

## Why it is hard

One question that is really two, and the two answers land in different places.

- How far back an encode may be resumed is a property of the merge table. A position is
  safe when nothing the table can build reaches across it, and that has to be derived from
  `tok/merges.json` and `tok/core.py`, neither of which the agent may edit.
- How far a reply's trainable run reaches is a property of the finished sequence. It stops
  where the sequence stops agreeing with what the sampler was conditioned on, which is a
  different point, usually later than the reply's own last generated position, and
  sometimes before the reply began at all.

A solver who carries one boundary through both is wrong on one side or the other, and both
sides are graded.

- Expert time estimate: 7 hours
- Why a frontier agent cannot one-shot the plan: the first plan is the published recipe -
  cut at the last whitespace, encode the tail, verify against a full encode - together with
  "a reply owns what it generated". That plan produces the right tokens on every scenario
  and fails both the accounting and the spans, and neither failure is visible from inside
  the container. Forming the correct plan means reading the merge table for a structural
  property nothing in the tree names, and then noticing that the trainable run is answered
  by a different comparison than the resume point is.
- Tactics making that true: A1, A2 and A3 poison the default plan; B1 and B2 withhold it;
  C1, C2, C3 and C4 make the wrong plan fail late. Concretely:
  - Prong A1: the retrieved fix is specifically wrong. This table merges straight across
    space and newline, so a pre-tokenizer cut lands inside a symbol; three of the four
    block markers are ordinary characters to it, so cutting at a marker is wrong for
    exactly the one that closes a reply.
  - Prong A2: the concept is never named. The instruction says "a position that is a token
    boundary whatever text sits either side of it" and stops there.
  - Prong A3: correctness and cost pull against each other. The verify-and-fall-back pass
    that makes the recipe safe costs exactly what caching nothing costs.
  - Prong B1: the load-bearing facts are spread and unowned. The merge table is in
    `tok/merges.json`, the encoder in `tok/core.py`, the marker layout in `chat/tmpl.py`,
    the prompt-to-generation seam in `loop/gen.py`, the counters in `tok/core.py` and
    `model/net.py`. None of those is editable and the tree carries no comments.
  - Prong B2: small rules that must hold together - the retry rewrites the render backwards
    rather than extending it, a reply whose own prompt moved owns nothing, a reply that
    survived owns its closing token as well, the lifecycle order is fixed.
  - Prong C1: fenced from both sides. `short-reply` and `one-turn` fail an over-cautious
    span rule; `no-anchor` and `back-reach` fail an over-eager resume.
  - Prong C2: no oracle for the graded quantity. Tokens can be checked against a full
    encode the agent writes itself. The spans and the character count cannot be checked
    against anything in the container.
  - Prong C3: a resource gate the safe answer fails. Encoding every render whole is correct
    on tokens, spans, forwards and trace, and over the character ceiling on all twelve
    scenarios.
  - Prong C4: twelve scenarios, four axes, all-or-nothing.
- Assistant's attack on the plan: my first plan was to back up to the last space or
  newline, encode from there, and treat every generated position as trainable. It gets the
  tokens right on all twelve scenarios and fails the accounting on eleven and the spans on
  eight. My second plan would have been to add a full-encode verification pass behind it,
  which doubles the character count. Both are in `cheat/` and both score 0.
- Estimated solves out of 8: 1 to 2 after the recalibration below. It was 0 of 8 before it.
- Expert path, step by step:
  1. Run `/app/run_rollout.py` and see the reply's last token change under the tool block
     that follows it.
  2. Read `chat/tmpl.py` and `loop/gen.py` and find the seam: the prompt ends at the
     assistant marker, and generation starts there.
  3. Read `tok/core.py` and `tok/merges.json`. A merge joins two symbols, so every symbol
     the table can build is the concatenation of the two halves of some rule; ask which
     characters can never have anything reach across the boundary in front of them.
  4. Compute that set once, at import, from `core.MG` and `core.BASE`.
  5. Implement `cut` as one rule for appends and rewrites together: find the first
     character that moved, walk back to the last protected position, map that character
     offset onto the cached ids through `core.WID`.
  6. Notice that the retry case needs no branch, because a rewrite is just a first-moved
     character in the middle instead of at the end.
  7. Change what a turn records: the prompt it was handed together with what it produced.
  8. Compare that whole sequence against the finished one from position zero, and take the
     run from the turn's start to the first disagreement, empty when the disagreement lands
     before the start.
  9. Drop a retried turn's record with its message.
  10. Drive scenarios of their own through `run_rollout.py` until the counters stop moving.
- Originality check: what exists publicly is the incremental-encoding recipe described
  above and the general advice to re-encode from a "safe" boundary. Nothing public makes
  the distinction this task is built on, between the position an encode may resume at and
  the position a trainable run ends at.

## Verifier contract - FROZEN

Amended twice, both times recorded rather than hidden, because the run audit reads this
file. The first amendment, at the recalibration below, graded less: `enc_chars` became a
window. The second, at the anti-cheat repair at the end of this file, graded no new
quantity at all - it made an existing one unforgeable and raised its floor to a bound that
is provably under every correct implementation.

- Artifacts: `/app/tok/inc.py`, `/app/tok/store.py`, `/app/loop/ep.py`, `/app/loop/rec.py`.
  A wider set than strictly needs changing - `store.py` needs no change at all.
- Overlay: `tests/Dockerfile` bakes a pristine copy of the whole tree; `test.sh` copies it
  to a work dir and overlays only those four paths.
- Ground truth: `tests/gt.json`, root-owned, `chmod 600`, re-proved at verification time by
  `tests/oracle.py`, a sealed replay sharing no code with the tree.
- Graded, all-or-nothing, per scenario:
  - `ids` - every episode's finished token sequence, exactly.
  - `spans` - every surviving turn's trainable run, exactly, in turn order.
  - `enc_calls`, `fwd` - exactly. One render is one call; forwards follow from the
    lifecycle.
  - `enc_chars` - inside a window, `enc_chars_min <= chars <= enc_chars_max`. The floor is
    what the cheapest legal resume of each render costs, found by the sealed oracle by
    trying resume positions rather than by reading the merge table. The ceiling is the
    worse of the two one-sided readings.
  - `trace` - the lifecycle, in order.
- Not graded, enforced: every id the loop hands over has to have come out of the metered
  tokenizer. `Tok` keeps what it issued, `loop/gen.py` and `loop/rt.py` check each sequence
  against that record, and neither file is editable. This is a structural constraint rather
  than a graded field - a submission that violates it raises instead of scoring, and the
  instruction states it.

### Real work, safe to grade

Tokens emitted, trainable positions, calls into the tokenizer, forwards through the
network, lifecycle events the worker itself raises. Two correct implementations agree on
all of these by construction, which `authoring/variant_check.py` demonstrates over seven of
them.

### Implementation choice, never graded

- Which cache structure `store.py` uses (`ok-ordered-store`).
- The shape of the record a turn hands the span builder (`ok-split-record`).
- How the span scan is written (`ok-scan-spans`).
- Whether ids are carried as lists or tuples (`ok-tuple-ids`), which also proves the
  tokenizer's record of what it issued is not grading a representation.
- **Which reading of the resume condition a solver settles on.** This is the one that had
  to move; see below.

## Recalibration, after 0 of 8 on the difficulty probe

The probe result was 0 solves of 8 on the difficulty run and 0 of 3 on easiness. Zero
solves is a rejection, not a triumph, and the diagnosis is that one graded quantity was
demanding an answer no honest solver could confirm.

`enc_chars` was graded against the reference's own number. "Resume at the last position the
merge table protects" is not one answer, though. It is a ladder of them, and the readings
are all correct:

| reading | total characters over the twelve scenarios |
|---|---|
| the character after the seam never sits anywhere but at the front of a symbol | 2809 |
| the character before it never sits anywhere but at the end of one | 2729 |
| either of those (what the reference does) | 2631 |
| no symbol carries that adjacent pair at all | 2298 |
| floor: the characters that were not in the previous render | 2290 |

Every one of those produces the correct token sequence on every scenario. The old verifier
passed the third and failed the other three. So a solver who derived the protection
condition, implemented it cleanly and read the table more finely than the reference did
scored 0, and had no way to find out why: the number is invisible inside the container.
That is the run-audit failure mode described in `CLAUDE.md`, and it was in this task before
the probe ever ran.

What changed:

1. `enc_chars` is graded against a window instead of a number.
   - The **floor** was `tests/oracle.py`'s own count of the characters that were not in
     the previous render, on the reasoning that nothing which encodes a render can hand
     the tokenizer less and still be encoding it. That reasoning was wrong in one word:
     *encodes*. A submission that produces the ids some other way hands over exactly that
     many characters and no more, which is what quality review found and what the repair
     at the end of this file fixes.
   - The **ceiling** is the worse of the two one-sided readings, measured through the same
     harness the reference goes through, per scenario. `authoring/build_gt.py` refuses to
     write a ceiling that has drifted up far enough to admit the merge-free answer, which
     is the reading the task does still reject - it costs about twice the ceiling on every
     scenario and it is the cheaper question, not a finer one.
2. `authoring/variants/` and `authoring/variant_check.py` now exist, with six alternative
   correct solutions. Three of them are the readings above. All six score 1 through the
   real verifier images.
3. `authoring/field_report.py` now exists. It found `trace` grading nothing, so
   `cheat-retry-notes-tool` was added - a retry that routes its note through the tool path,
   correct on every other axis.
4. The instruction states the window. It no longer asks for "the last position like that,
   never at some earlier one that happens to be safe as well", which was asking for a
   number the solver could not see. It says there is a floor and a ceiling with room in
   between, and it says that walking back only to the nearest character the table takes no
   interest in leaves you over the ceiling.
5. A reply that survives but owns no positions keeps its row in the list; a reply a retry
   discarded loses its row. Both readings were plausible and only one was graded, so the
   instruction now says which.
6. `expert_time_estimate_hours` 9 -> 7.

What deliberately did not change: the resume condition still has to be derived from the
merge table, the span rule still has to be derived from the finished sequence, the retry
still rewrites the render backwards, and the twelve scenarios and four axes are still
all-or-nothing. The easing is one razor wide.

## Anti-cheat repair, after the quality review

Quality review failed the task on one blocking criterion, anti-cheat robustness, and the
finding was correct and central. It is worth writing down in full because the hole was not
in the verifier at all.

`tok/core.py` carried a module-level `_run()` that did the byte-pair merges, and
`Tok.encode()` was a thin wrapper around it that incremented `n_chars` and `n_calls`. So
the reviewer wrote a `tok/inc.py` that returned `[core.SID[s] for s in core._run(text)]` -
a full, correct encode of every render, for free - and handed `tok.encode` only the newly
appended suffix to keep the call count honest. It came out clean on all twelve scenarios
on every graded field, landing exactly on `enc_chars_min`, because the floor was the count
of characters that were not in the previous render and that is precisely what an appended
suffix is. No boundary reasoning anywhere in it, and a reward of 1.

The accounting axis is the only thing that rejects the safe, expensive answer, so that
bypass takes the headline half of the problem with it.

Three changes, none of which grades anything new.

1. **No uncounted encode.** `_run` is gone; the merge loop is inlined into `Tok.encode`,
   which counts before it runs. There is now no byte-pair encoding anywhere in the tree
   outside the call that meters it.
2. **Ids have to come from the tokenizer.** `Tok` keeps every id list it issued.
   `loop/gen.py` checks the prompt before priming the network and `loop/rt.py` checks the
   finished sequence before recording it, both through `Tok.mark`, which accepts a sequence
   only when it is a prefix of one already accepted followed by exactly one of those
   issued lists. Neither file is editable. This is what makes the meter mean something: a
   private encoder can still compute the right ids, but the loop will not take them unless
   the resume they imply is one the tokenizer actually performed, and where resuming at the
   seam is not legal the private answer and the metered call disagree and the run raises.
   The check never reports whether a resume point was *safe*, so it hands the solver no
   oracle for the thing they have to work out - a wrong cut point still produces a
   well-formed sequence with the wrong tokens in it, silently, exactly as before.
3. **The floor is the cheapest legal resume, not the appended characters.** `tests/oracle.py`
   now finds it per render by trying resume positions - every boundary of the previous
   render's ids at or before the first character that moved, latest first, until one
   splices to what a full encode produces. That is a property of the two renders and the
   table rather than of any resume rule, so nothing correct can come in under it, and
   `authoring/build_gt.py` refuses to write a ground truth in which no scenario separates
   it from the old floor.

The numbers, over the twelve scenarios: old floor 2290 characters, new floor 2295,
separating on `back-reach`, `retry`, `retry-late` and `long`. The margin is thin on purpose
- it is a proven minimum, not a chosen one - and the second change is what does the work.
The pair-level reading, the finest honest reading of the table, sits *on* the new floor on
eleven scenarios and three characters above it on the twelfth, which is the useful
measurement here: reading the table as finely as it can be read is worth three characters
out of 2298 against knowing the answers in advance. There is nothing left for a bypass to
win.

Two cheats were added and both score 0: `cheat-private-encoder.sh` is the reviewer's
submission, rebuilt on the shipped tree with its own merge loop now that `_run` is gone,
and `cheat-forge-ids.sh` is the same encoder with the meter left at zero. A seventh
variant, `ok-tuple-ids`, was added on the other side, carrying ids as tuples through a
store that does the same, to prove the new check is not grading a representation.

### What is left, stated plainly

A submission that writes its own byte-pair encoder *and* uses it to search, per render, for
the last position that splices correctly, and then makes one metered call at that position,
passes. It does no boundary reasoning and it lands on the floor. Three things stand against
it and none of them is a verifier check: it is more code than the reference, the
instruction says in terms that the tokenizer is the only source of ids and an encoder of
your own is no good here, and it wins three characters out of 2298 over simply reading the
table correctly. Closing it completely is not possible in-process - the merge table has to
be readable for the task to be solvable at all, and ids are a function of text - so it is
recorded here rather than papered over.

## Gates

Run on 2026-08-12, in this sandbox, on the real two images unless noted. The rows below are
after the anti-cheat repair.

| gate | result |
|---|---|
| `authoring/sync.py` | 18 files into `tests/pristine` |
| `authoring/build_gt.py` | all twelve scenarios proved against the sealed oracle |
| `authoring/emit.py` | `solve.sh`, 7 variants, 18 cheats |
| `authoring/variant_check.py` | 7/7 clean (host emulation) |
| `authoring/field_report.py` | no dead weight in the graded set |
| `authoring/cheat_report.py` | oracle clean, nop fails, no cheat scores 1 |
| `tools/docker_trial2.py turn-seam-alignment --all` | 20/20 trials behaved as required |
| `tools/docker_trial2.py turn-seam-alignment --variants` | 7/7 variants scored 1 |
| `tools/textcheck.py` against both passing instructions | no findings |
| `scripts/preflight.py` | clean |
| `scripts/package.py` | packaged |

Not run here: `harbor check`. It is not installed in this sandbox, and
`tools/docker_trial2.py` reproduces the two-container trial with docker directly instead.
The probe numbers above (0 of 8, 0 of 3) are from the pipeline; neither the recalibration
nor this repair has been measured against a probe, and neither can be measured here.
