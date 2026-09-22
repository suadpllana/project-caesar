# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - Pre-flight and packaging`

## Assistant's assigned role

A storage engineer who owns the half of a change log that decides what it may throw away: the
part that has to keep point-in-time readers exact while replication followers are still working
through their backlog, and has to do it inside a size budget without blocking either of them.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): not applicable
- Contributor's relationship to it: not applicable
- License, and why vendoring it is permitted: not applicable
- Pinned commit vendored into environment/app_src/ (.git stripped): not applicable
- Load-bearing couplings found during research (file paths): not applicable
- Identifier degradation done? The tree is written from scratch in a legacy register
  (`lg/`, `store`, `pin`, `fold`, `span`, `pare`, `tell`, `ent`, `idx`, `at`, `lo`, `hi`); no
  conversion table is needed because there is no upstream to degrade from
- Proper-noun sweep done? The tree carries no project, product or vendor name; grepped before
  packaging
- Upstream-diff check: not applicable

## Task summary

`/app` is the half of a change log that decides what it may throw away. A program file drives
it: entries that set, add to or delete a key; marks that pin a point; feeds that attach over a
range of keys at a point and acknowledge their way forward; reads that ask what a key was worth
at a mark's or a feed's point; and `pare <n>`, which must shrink the log to a stated number of
entries without breaking any of that. The shipped engine implements the retrievable answer -
one version per pinned interval, everything superseded thrown away, one global list of points -
and that answer is wrong here in two directions at once. The agent repairs six files under
`/app/lg` so every graded program prints the same trace as the reference, inside a stated
execution limit.

## Why it is hard

The obvious plan is log compaction with snapshots, and it is retrievable almost word for word:
keep one version per snapshot interval and fold the operands on either side of each boundary.
That plan collapses exactly the entries this log is not allowed to touch. A feed is a reader
that has still to see each change one at a time, so above a feed's position every entry of
every key it covers survives as it stands, superseded or not - and a feed covers a range of
keys, so the pinned points are per key rather than one global list, and two keys carrying
identical entries retain differently. Below a feed's position the retrieved rule does apply,
which is why ordinary testing agrees with the wrong plan.

The second finding takes the first repair apart. The entry that survives a span sits at the
sequence number of the last entry **the log still holds** there, and `pare` stops on a size
budget, so a key can be left half collapsed. When a later `unmark` or `close` merges two spans
across a stretch whose entries cancel out, the survivor has to move to the place of an entry
that is no longer in the log. An implementation that computes the retained log as a function of
the written log and the current pins - which is what the first repair naturally produces, and
what every batch compactor is - gets every count right and the place wrong, silently, and only
after that three-step sequence. The state is the retained log, so the structure has to be a
machine that carries it rather than a pass that recomputes it.

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the retrievable plan is specifically wrong above a lagging feed and wrong again about whose points pin what, and the repair that fixes both is itself invalidated by the rule that a survivor sits where the retained log says, under a budget that leaves keys half done - so the correct structure is an incremental machine over the retained log, which is not the structure either the first plan or its first repair produces.
- Tactics making that true (docs/DIFFICULTY.md - prong A poison / prong B withholding / prong C late failure): A1, A2, B2, C1, C2, C3, C4. A1 the log-compaction prior is coherent and specifically wrong above a feed; A2 nothing is named a snapshot, an offset, compaction or retention - the brief gives marks, feeds with a covered range, a moving position and a size budget, operationally; B2 ten rules hold at once and none can be confirmed on its own from anything a program prints; C1 both sides are fenced, with programs where the floor reading is exactly right and programs where nothing may be removed at all; C2 the only self-check available - that reads are unchanged by a pare - is preserved by nearly every wrong reading; C3 a measured limit kills the pare that rebuilds the span table and the one that re-forms the pair table per collapse; C4 exact all-or-nothing comparison against a sealed model over hand programs and programs generated from a seed drawn after the container is gone.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan
  was a global sorted list of pinned points, one surviving version per interval per key, deltas
  folded into that version, and everything else dropped. It is wrong twice before it starts -
  above a feed nothing may be dropped, and the point list is per key because feeds cover ranges
  - and its repaired form is still wrong, because it recomputes from the written log while the
  rules are stated over the retained one. I could see where to start and could not have
  committed to the structure without running programs first.
- Estimated solves out of 8: 2 (designed for the hard edge, 1 to 3)
- Difficulty record score (tools/difficultycheck.py on authoring/<slug>/difficulty.toml, before
  Stage 2; every attempt's score and what changed, until it reaches the band in
  docs/DIFFICULTY-SCORE.md): 100/100 on the first record, 2026-09-22, in band (95-100), with one
  warning that the resource gate was a promise at that point. It has since been measured and the
  record says so. Two earlier candidate designs were dropped before being written down: a
  version-DAG retention design, because its core is reachability and `reach-pair-sweep` already
  grades reachability; and a retention design without the feed half, because its central rule -
  keep one version per snapshot interval - is on the RocksDB wiki word for word, which is a hard
  stop on the search axis.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not set
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-22 record scored
  100/100; re-scored at Stage 7 against the built tree.
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning? Answer must be "nothing": the file that derives
  held points is itself collected and ships wrong, so nothing in the tree is authoritative about
  them; only input programs ship, never a trace, and the one worked line in the brief was
  measured against all 24 wrong readings - it decides six stated conventions and neither of the
  two load-bearing readings; the store holds entries and pin records and nothing derived - no
  span, no trailing point, no removal count, no value at a point; the trace writer sits outside
  the collected set and prints only read values, the two pare numbers and the end report, so no
  pair table or span boundary is ever visible; `tools/onelinecheck.py` finds no exact rule at
  depth two for any of the three graded quantities it measures; the sealed model and the frozen
  answers sit in a directory the uid that runs submitted code cannot read.
- Expert path, described step by step (the harder the aim, the more this guard must hold):
  run the shipped driver on the sample programs and find where the trace first departs from the
  line the brief gives; read the package until it is clear which file owns held points, which
  owns the span rule and which owns the pare loop; write the fold as a composable effect so a
  span's net change composes and applies to the value at its floor; split each key at its
  trailing point, keeping entries one by one above it and collapsing span by span below it;
  derive a key's held points from the marks, the feeds covering it and the head, and rebuild
  them when a feed acks or closes or a mark comes or goes; implement the budgeted pare with both
  tie-breaks and its stop condition, taking the survivor's place from the entries the log still
  holds; time the wide and deep programs and carry the pair table across commands instead of
  rebuilding it per pare.
- Originality check: searched 2026-09-22 for the mechanism and its close variants. The nearest
  public material is the RocksDB wiki on merge operands and snapshots ("keep one version per
  snapshot interval, merging operands on either side of the snapshot boundary") and Kafka's
  key-based log compaction and consumer-offset retention. Both describe one half of this store
  and neither describes the combination: a reader that needs each change individually above its
  position while another needs only the value at its point, with the first reader's reach
  limited to a range of keys, a size budget on the pare, and the surviving entry placed by the
  retained log rather than the written one. No write-up of that combination was found. None of
  the twelve retained bundles in this checkout works on retention, log entries or reader
  positions; `simcheck` reports "this task does not grade what any earlier one grades".

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

Every graded assertion traces to a sentence in the instruction. Walk the tests, the sealed model
and test.sh line by line into authoring/<slug>/trace.md, start it with
`python tools/tracecheck.py <slug> --skeleton`, and keep `python tools/tracecheck.py <slug>` clean.
`preflight.py` errors while any line below is unanswered.

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): 71 rows walked - 4 test functions, 33 enumerated cases, 6 artifacts, the pristine overlay, the 60 s clock and 21 rules of the sealed model, each citing its sentence; no NOT STATED rows remain; `tools/tracecheck.py feed-lag-pare` is clean.
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 24 wrong readings were written as working services in `authoring/feed-lag-pare/emit.py` and measured by `tools/readingcheck.py`; all 24 are separated by an enumerated case, and each moves between 4 and 97 per cent of the generated population. Two readings survived every published statement and agreed with the reference on the whole graded set, so they were promoted to correct variants that must score 1 rather than kept as wrong readings. Two decisions the walk found unsettled were repaired in the brief rather than left to a coin: which span an entry standing on a held point belongs to, and what the number after `log` counts.
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): the shipped tree unchanged scores 0 and differs on 33 of 33 hand programs; one fixed output for every program scores 0 and matches none; a pare that never removes anything scores 0 and matches only the two programs where nothing may be removed; the worked example's line replayed scores 0 and matches one; the forgery carrying the frozen answers reproduces all 33 enumerated programs and is wrong on every one of the 406 it could not have seen, scoring 0.
- Independent implementation behind every tolerance and limit (path, measured headroom): the only limit is the 60 s clock on the graded set. `authoring/feed-lag-pare/variants/ok-flat` and `authoring/feed-lag-pare/variants/ok-effect`, both written apart from the reference, get through all 439 programs in 25.4 s and 28.7 s; the reference takes 4.4 s. There is no numeric tolerance anywhere: comparison is exact string equality.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run, mechanically, over all four printed forms. Two gaps found and closed with a sentence each - the span a held point belongs to, and what `log <kept>` counts. A third, that a name is placed once and taken away at most once, was added as an input guarantee. A fresh-session cold read was not run: the same session wrote the model and cannot un-know it, and a self-probe reported as cold by a contaminated author is worse than none (CLAUDE.md, 2026-09-06).

## Verifier contract - FROZEN after Stage 2

Once agreed, this does not change without the contributor's explicit approval.

- Artifacts the agent produces: `/app/lg/store.py`, `/app/lg/pin.py`, `/app/lg/fold.py`,
  `/app/lg/span.py`, `/app/lg/pare.py`, `/app/lg/tell.py`. Nothing else is collected. The
  verifier lays those six over its own pristine copy of the tree, so the driver
  (`/app/run_log.py`), the grammar (`/app/lg/read.py`), the trace writer (`/app/lg/say.py`) and
  the sample programs cannot change what a program prints, and a new file placed beside the six
  is never collected.

- What is checked: every graded program is run through `run_log.run(text)` and its printed lines
  are compared token for token. Thirty-three hand programs are compared against
  `tests/seal/gt.json`, frozen before the grading file was written; the grader first asserts
  that the sealed model still reproduces `gt.json` exactly. Four hundred and six further
  programs are generated inside the verifier from a seed drawn after the agent's container is
  gone. All or nothing.

- Tolerances: none. Exact string equality on every printed line. The only limit is the wall
  clock on the process that runs submitted code, which is also the execution limit in the brief.

- Ground truth, and where it lives: `tests/seal/model.py` (an implementation written apart from
  the reference) and `tests/seal/gt.json`, in a directory chmod 700 before the privilege drop.

### The frozen semantics

A program is a text file, one command per line, tokens separated by single spaces.

    set <k> <v>      an entry: key k takes the value v
    add <k> <n>      an entry: key k goes up by n
    del <k>          an entry: key k becomes absent
    mark <m>         places mark m at the head
    unmark <m>       removes mark m
    feed <f> <a> <b> opens feed f over the keys a to b inclusive, at the head
    ack <f> <s>      moves feed f's position to s
    close <f>        closes feed f
    read <p> <k>     reads key k at the point of mark or feed p
    pare <n>         reduces the log to at most n entries

Entries take sequence numbers 1, 2, 3 ... in the order they appear. The head is the sequence
number of the last entry, and 0 before the first one. Every name is placed once and taken away
at most once; a read names a mark, or a feed together with a key that feed covers.

1. **Fold.** The value of key k at point P is got by applying, in sequence order, every entry of
   k the log holds whose sequence is at or below P, starting from absent: `set k v` makes it v,
   `add k n` makes it the current value plus n and makes it n when k is absent, `del k` makes it
   absent.
2. **Held points.** The held points of key k are the head, the point of every live mark, and the
   position of every live feed whose range covers k. Two pins standing at one point make one
   held point.
3. **Trailing point.** The trailing point of k is the lowest position among the live feeds
   covering k, and the head when no live feed covers k.
4. **Kept region.** An entry of k above k's trailing point is never removed and never rewritten.
5. **Spans.** The held points of k at or below its trailing point, in ascending order
   Q1 < ... < Qj, cut the rest into the spans (0,Q1], (Q1,Q2], ... , (Q(j-1),Qj]. A held point
   belongs to the span it tops.
6. **What a collapse leaves.** Collapsing one key's span removes the entries of that key the log
   holds inside it, except that when k has different values at the span's top and its floor -
   absent counting as equal to absent - one entry is left behind.
7. **Where it sits.** That entry sits at the sequence number of the last entry of k the log
   still holds inside the span.
8. **What it becomes.** It becomes `set k v` with k's value at the span's top, or `del k` when k
   is absent there.
9. **Pare.** A pair is a key and one of its spans, and stands to remove the entries of that key
   the log holds inside it, one less when an entry is left behind. While the log holds more than
   n entries and at least one pair stands to remove an entry, the pair standing to remove the
   most is collapsed; ties go to the lower span top, then to the smaller key.
10. **Ack.** `ack f s` moves f's point to s when s is above f's current point and not above the
    head; otherwise f's point does not move.

Printed trace, and nothing else:

    val <p> <k> <v>       a read, with `-` in place of v when k is absent there
    pare <removed> <kept> after each pare command
    log <kept>            once, when the program ends
    k <key> <item> ...    once per key holding an entry, in ascending key order, at the end

where an item is `<seq>s<v>`, `<seq>a<n>` or `<seq>d`.

## Decisions and their reasons

- Six collected files rather than one: each of the ten graded rules has an owner, all six ship
  a wrong reading, and the fast path needs work in four of them, so no single-file patch exists
  and the route-around is closed.
- The head counts as a held point. Without it the value a program ends on would not be
  preserved, and the rule is the difference between a store and a truncation.
- `ack` refuses to move backwards or past the head rather than raising. An error path would be a
  second output channel and a per-decision signal; a quiet refusal is not.
- The report lists entries per key rather than dumping the log in sequence order, because the
  sequence number of the surviving entry is the observable that separates the two readings of
  rule 7, and a per-key listing puts it next to the entries it has to beat.
- No error lines, no diagnostics, no progress output: the only feedback a program gives while it
  runs is read values and two numbers per pare, which is what denies per-decision confirmation.
- The isolation probes sit on the reference with one named wrong reading in it, not on the
  shipped service. The shipped service does not finish inside the execution limit, so its 0
  would come from the clock and would prove nothing about the isolation; correct work would
  score 1 for an honest reason and prove nothing either.
- The generator was reshaped twice after measurement, not before: `late`, `tie` and `part` were
  rewritten when three wrong readings turned out to move 0 to 1 per cent of the population. The
  budgets in `late` and `tie` are computed rather than drawn, because those shapes only exist
  when the pare stops in exactly the right place.
- `environment/Dockerfile` is byte-identical to three retained bundles' and `simcheck` says so.
  It is seven lines of base image, two environment variables, a WORKDIR and one COPY; there is
  no other honest way to write it, and the retained set is identical to itself for the same
  reason.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | pass | `tools/docker_trial.py --build`; harbor is not installed here |
| No answer leaked into agent image | pass | `extraneouscheck` clean; only input programs ship; nothing from `tests/` or `solution/` is copied |
| `harbor run -a oracle` = 1 | pass | container trial, reward 1, 36 tests passed |
| `harbor run -a nop` = 0 | pass | container trial, reward 0 |
| Cheats all score 0 | pending | 38 cheats running in the container trial |
| `tracecheck.py` (every graded assertion traced) | pass | clean |
| `preflight.py` | pass | no errors; 18 warnings, all the known `(?<![\w.])name\(` false positive on module-qualified calls, which every retained bundle also reports |
| `harbor check` rubric | not run | needs an API key, which this session does not have |
| `readingcheck.py` | pass | 24 of 24 readings separated by an enumerated case |
| `onelinecheck.py` | pass | no graded decision has an exact rule at depth two |
| `forgecheck.py` | pass | the forgery carrying the frozen answers scores 0 |
| `solvecheck` / `deadfieldcheck` / `catcheck` / `hintcheck` / `structcheck` / `extraneouscheck` | pass | clean |
| `simcheck` | pass with a note | conceptually distinct; `environment/Dockerfile` identical to three retained bundles, which are identical to each other |
| correct variants score 1 | pass | `ok-flat` and `ok-effect` reproduce the model on 33 hand, 300 shaped and 406 generated programs |
| three-way differential | pass | slow transcription, reference and sealed model agree on 33 hand, 2500 random and 406 generated programs |

## Quality self-review (docs/QUALITY-REVIEW.md, walked criterion by criterion)

**Instruction and verifier agree, in both directions.** Every graded assertion has a row in
`authoring/feed-lag-pare/trace.md` citing the sentence behind it - 4 test functions, 33
enumerated cases, 6 artifacts, the pristine overlay, the 60 s clock and 21 rules of the sealed
model - and `tools/tracecheck.py` is clean. Every rule the brief states has at least one
enumerated case named for it; the Readings table names which case separates each wrong reading.
The six collected paths are named with their absolute paths in the brief's fourth paragraph and
the verifier reads nothing else. The printed forms are given verbatim in the seventh paragraph,
down to the item spelling, and the paragraph ends "Nothing else is printed". Boundaries are
settled in the text: an acknowledgement moves a feed when it stands "above the feed's current
position and not above the head"; a pare runs "while the log holds more than `n` entries";
"absent counting as equal to absent"; ties go to "the lower top and then to the smaller key";
"A held point belongs to the span it tops"; a feed covers "`<a>` to `<b>` inclusive"; the report
is "in ascending key order". `authoring/feed-lag-pare/facts.py` re-derives every number and both
quoted lines from the code and reports 0 claims wrong.

**Prose.** Read as prose, two runs of same-opener sentences were found in the rule paragraph
("The held points of a key ...", "The trailing point of a key ...") and one of them rewritten so
the paragraph does not march. No requirement is stated twice. 903 words, nine paragraphs, plain
ASCII; `structcheck` and `hintcheck` clean.

**Verifier rigor.** The tests grade what the submitted code printed on 439 programs it could
not have seen, not an exit code and not a claim; each program is fingerprinted, so a submission
that alters one fails on that program. The grading file carries the frozen contract as a
docstring and is sectioned by what each part checks. Nothing depends on wall-clock time except
the stated execution limit, and nothing touches the network.

**Environment hygiene.** `environment/Dockerfile` copies `app_src/` and nothing else; no path
under `tests/` or `solution/` reaches the agent image. The verifier's dependencies are baked at
build time and pinned (`pytest==9.1.1`, `pytest-json-ctrf==0.5.2`); no apt package is pinned and
`test.sh` installs nothing. Every path the brief names exists and is spelled identically.

**Solution quality.** `solution/solve.sh` copies six source files into `/app/lg` and runs two
sample programs; the answer is computed by the code, never written out. It uses nothing the
agent could not use.

**Anti-cheating.** Only input programs ship, never a trace. `extraneouscheck` reports every
shipped file reachable, distinct and host-free. Grading is exact string equality, so a
degenerate output fails. No repository is cloned. The forgery that carries the frozen answers
scores 0.

**Metadata.** `category = "Software"`, `subcategory = "Databases"` - a label from that row -
and six tags naming this task's mechanisms rather than the taxonomy. The difficulty explanation
names the step that breaks, says the identifiers are in a deliberate legacy register, and quotes
the measured timings; the solution explanation describes the method file by file; the
verification explanation says what passing proves. `expert_time_estimate_hours = 9` matches the
claim.

**Known risks to flag to a reviewer.** `environment/Dockerfile` is byte-identical to three
retained bundles', which `simcheck` reports as NEAR. It is a base image, two environment
variables, a WORKDIR and one COPY; the retained bundles are identical to each other for the same
reason, and rewriting it would be cosmetic rather than honest. `tools/textcheck.py`, run against
both `note-carry-forward` and `expert-defer-shed`, still reports fewer short sentences and more
even paragraphs than those two briefs, one stock-vocabulary hit and one three-item list. The
stock hit is the phrase "when the key is absent there", where `key` is this task's data model
rather than the idiom, and the rest is what a dense rule specification reads like; the run of
same-structured sentences the criterion actually asks about was found and rewritten. Padding the
brief with short sentences to move a distribution would be exactly the staged informality
`AGENTS.md` D1 forbids, so it was left alone and is recorded here instead.

## Open questions and next steps

Finish the container cheat suite, re-score the built tree with `difficultycheck`, package and
push. The easiness and difficulty probes are the platform's to run; nothing local substitutes
for them.
