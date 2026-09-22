# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 complete - packaged and filed as pending` (2026-09-22). Built, measured and checked:
`tasks/heard-cut-revoice.zip` is the submission, and `authoring/submissions.toml` records it with
`verdict = "pending"`. Next is the platform's verdict.

## Assistant's assigned role

You are a front-end accessibility engineer who builds the screen-reader side of UI test
tooling: a headless reader that replays a page's mutations and asserts what a user of
assistive technology hears. You know the ARIA live-region attributes the way implementers
know them - aria-live politeness, the aria-atomic walk from the changed node upward,
aria-relevant tokens, aria-busy holds, hidden and aria-hidden exposure - and you know that
real screen readers disagree on exactly these points (stale atomic text, busy updates that are
never spoken, cut speech that is simply lost), which is why a test reader has to state its own
model and keep to it.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task, no third-party code vendored
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): not applicable, no repository
- Contributor's relationship to it (maintainer / contributor / production user, how long): not applicable
- License, and why vendoring it is permitted: not applicable, nothing vendored
- Pinned commit vendored into environment/app_src/ (.git stripped): not applicable
- Load-bearing couplings found during research (file paths): not applicable
- Identifier degradation done? Conversion table lives at solution/ (never in environment/): the tree is
  written here, not degraded from a source; identifiers are chosen in a terse register directly
  (`sr/`, `look`, `know`, `watch`, `unit`, `line`, `voice`) and no name misdescribes what it holds
- Proper-noun sweep done? No product, browser, screen reader or framework name appears in the
  agent-facing tree; the domain terms that remain (aria-live, aria-atomic, aria-relevant,
  aria-busy, hidden, polite, assertive) are the public standard's own vocabulary
- Upstream-diff check: there is no upstream to diff against

## Task summary

`/app` is a headless screen reader used in UI tests: `python3 /app/run_sr.py <page script>`
replays a page's timed mutations and prints what the reader says, one line per utterance
started and one per utterance cut off. The shipped reader is the event-driven announcer every
integration starts from: each mutation record inside a polite or assertive region becomes an
utterance string, polite strings queue, an assertive string flushes the queue, and a string
counts as heard the moment it is queued. The specification it has to meet is the reader's own:
the reader believes, per live region, the text it has *finished* saying there; an utterance
voices the net difference between what is exposed now and that belief; differences keep their
age, are held beneath busy elements, are grouped under the nearest explicit aria-atomic
container, and are taken oldest first with assertive ahead of polite; and an assertive change
cuts a polite utterance off and hands everything it carried back at the age it had. The agent
fixes the six files under `/app/sr/` so every page prints exactly the specified speech log.

## Why it is hard

The first plan is the published one and it is coherent: on a page whose updates are spaced
further apart than their speech takes, the event model and the reader's model print the same
log. The rule that breaks it is what "heard" means - the listener learns a change only when the
utterance carrying it finishes, keyed by region - and the rule after that takes the replacement
apart: a cut hands carried changes back at their age while a node edited during playback
already holds a newer difference, and absorption of what cannot be voiced has to release a key
from the playing utterance. Then the whole-page diff that the net-difference rule suggests is
exactly correct and does not fit the stated limit.

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): because the memorised and retrievable model of a live region is event-driven - every guide, every virtual screen reader for tests and the shipped reader turn mutation records into queued strings and count a string heard when it is queued. Here the reader speaks net differences against what it has finished saying, keyed by region, so a record is neither necessary (hiding an ancestor produces removals no record names) nor sufficient (an edit undone before its turn produces nothing). Replacing the event model with a snapshot taken when an utterance is queued is the natural second plan and it is wrong too: a cut has to hand changes back at their original age, a key edited during playback carries two ages, a silent or irrelevant difference must release the key from the playing utterance, and a removal is held and grouped where it was last believed, not where anything is now. And the whole-page recompute each tick that the rule suggests is correct and blows the stated limit, so the incremental form has to know every way a key's state changes without a record touching it.
- Tactics making that true (prong A poison, prong B withholding, prong C late failure): A1, A2, B2, C1, C2, C3 and C4. A1 the shipped reader is the event-driven prior implemented faithfully and it agrees with the specification on spaced-out pages; A2 the listener-knowledge model, the hand-back of cut speech and the oldest-first line are stated as what the reader believes and says, never named; B2 ten rules hold at once and each changes what a correct implementation of another has to keep; C1 both sides are graded - repeating a change fails and losing a cut change fails, voicing a held change fails and never voicing a released one fails; C2 casual runs of spaced-out updates cannot tell the two models apart and no real screen reader follows these rules; C3 a whole-page recompute each tick and a rescan of the waiting line at every selection are exactly correct and do not fit the stated limit on the wide and held families; C4 every graded page prints a speech log compared line for line, over enumerated pages and a population generated after the agent is gone.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan, reading the brief cold, would be to keep the shipped queue and fix what it queues: diff each live region against a snapshot updated when an utterance is queued, build the utterance strings for everything that changed, and play them in order. It is wrong three times: the snapshot has to advance when speech finishes, not when it is queued, so a cut can give changes back; a queue of strings built ahead of time speaks stale text and speaks changes that were undone while waiting, where the reader decides what to say only when it is free and reads a unit's text at that moment; and belief keyed by node cannot represent a node that has moved between two regions whose removal and addition finish at different times. My second plan - three layers per region and node, recomputed over the whole page every tick - is right and fails the limit, and making it incremental is where the busy holds on removals (held by where the node was last believed) and the release of an absorbed key from the playing utterance have to be got right a second time.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 2 (range 1-4)
- Difficulty record score (tools/difficultycheck.py on authoring/<slug>/difficulty.toml, before
  Stage 2; every attempt's score and what changed, until it reaches the band in
  docs/DIFFICULTY-SCORE.md): attempt 1 on 2026-09-22 scored 100/100, in band, no hard stop; the
  single warning was that the resource gate was declared and not yet measured. Stage 7 re-run with
  the gate measured and the built tree measured instead of read (450 environment lines, 6 editable
  files, 561 reference lines, 45 cheats, 2 variants): 100/100, in band.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not yet submitted
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-22 difficulty record 100; originality record 100
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning? Answer must be "nothing": the sample pages ship
  without their logs and the brief quotes one short log that decides no cut, hold or removal rule;
  the frozen page model exposes mutation records, which are the event stream the wrong plan eats
  and say nothing about belief, carried values, ages or holds; the shipped reader stores strings
  and marks them heard at queue time, so no field reveals a layer; the log prints only starts and
  cuts, so a wrong layer shows only as a missing or extra line.
- Expert path, described step by step (the harder the aim, the more this guard must hold): run the
  shipped pages and read the reader loop, which is record driven and marks speech heard at queue
  time; restate the model as three layers per (region, text node) - believed, carried by the
  playing utterance, exposed now; fix the tick order (finish, observe and absorb, cut, select) and
  give every difference the tick it arose; compute holds from the node's parent, or for a removal
  from the parent it was last believed under, up to its region element; find the unit by walking up
  to the first explicit aria-atomic, read a unit's exposed text when the utterance starts and carry
  every pending difference in it; select oldest first with assertive ahead of polite, ties to the
  lower node id then region id, and learn an empty unit at once; then time the wide and held sample
  pages and replace the whole-page diff with keys dirtied by records and subtree walks, and the
  held rescan with differences pooled under what holds them.
- Originality check: searched 2026-09-22 (seven queries, recorded in
  `authoring/heard-cut-revoice/originality.toml`). What exists publicly is the WAI-ARIA attribute
  definitions (including the aria-atomic walk up from the changed node), MDN's implementor hints
  (drop an earlier queued event for the same atomic region, wait for busy), the ariaNotify
  priority and interrupt explainers, virtual screen readers for tests that log what an
  event-driven model speaks, and NVDA issues showing stale atomic text (8044) and busy updates
  never spoken (20871). Nothing defines speech as a net difference against finished speech, keys
  belief by region, hands cut speech back at its age or selects across regions oldest first. No
  branch of this repository touches screen readers or aria attributes (grepped every remote
  branch's task files on 2026-09-22).
- Distinctness record score (tools/originalitycheck.py on authoring/<slug>/originality.toml, at
  Stage 1 before the difficulty record, again once instruction.md exists; every attempt's score,
  and the crowded archetype named - docs/ORIGINALITY.md): attempt 1 on 2026-09-22 scored 100/100;
  tags overlap nothing in the ledger, substrate reuses nothing, nearest ledger mechanism sentence
  guard-mark-unwind at cosine 0.11; crowded archetype named: virtual DOM reconciliation (on the
  Frontend list), with the departure recorded.
- Nearest already-submitted task (from authoring/submissions.toml or the platform's own flag),
  what overlaps, and which of the five surfaces separate them: `focus-return-point` (ledger,
  Frontend). Overlap at its strongest: a Frontend state machine over a tree driven by a stream of
  events, graded as a trace, where something recorded earlier is resolved against the tree later.
  All five surfaces separate: mechanism (focus holder vs speech from net differences against
  finished speech), substrate (terminal widget toolkit vs headless screen reader over ARIA
  attributes), graded output (focused widget per event vs a timed speech log with cuts), failure
  mode (immediate vs deferred focus processing vs event-driven announcing heard at queue time),
  interaction (instance-bound requests vs nested abort, against completion-time learning vs cut
  hand-back).

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

Every graded assertion traces to a sentence in the instruction. The walk is
`authoring/heard-cut-revoice/trace.md`.

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): `authoring/heard-cut-revoice/trace.md` walks the 4 test functions, the 35 hand pages, the 6
  artifacts, the pristine overlay, the 60 s clock and 29 rows of the sealed model (one per rule it
  applies, with its lines). No row is NOT STATED. `python tools/tracecheck.py heard-cut-revoice`
  is clean (its one note: `READINGS` is built by a function, so the 30 readings are cited by hand).
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 30 readings are written as whole readers in `authoring/heard-cut-revoice/readings.py` (the
  shipped event-driven reader plus 29 wrong readings of the brief). None survives: each is ruled
  out by a quoted sentence and separated by a named hand page (`python3 tools/readingcheck.py
  heard-cut-revoice`: 30 of 30 separated), and `cheat_report.py` shows each cheat failing the
  hand page written for its rule. On one draw of the 276 generated pages the 29 readings get
  between 3 (1%) and 242 (88%) pages wrong; on a second draw unit-carries-held got none wrong, so
  for the rarest readings the generated pages are a second layer and the hand page is the one they
  always meet. Three of them (busy-above-region, hidden-false-shows, unit-carries-held) got under 1%
  wrong before the busy and hide families were reshaped for them.
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): all score 0. The shipped tree is right on 12 of 35 hand pages and 34 of 276 generated ones and
  fails tiny-example; saying nothing is right on 0 hand pages and 1 generated page; speaking every
  addition and edit in record order is right on 14 hand pages (the worked example among them) and
  32 generated; replaying the worked example is right on tiny-example only; carrying the frozen
  answers by page hash is right on all 35 hand pages and 35 of 276 generated, and fails the nonce
  test. Rows in the trace's Shortcuts table.
- Independent implementation behind every tolerance and limit (path, measured headroom): the only limit is the 60 s wall clock on the worker. `authoring/heard-cut-revoice/variants/ok-cache/` and
  `variants/ok-region/`, both written apart from the reference, agree with the naive reader on
  1,800 generated pages each, then on 300 pages of the reshaped hide family and 400 of the final
  busy family, and read the whole graded set in
  the verifier image on one CPU in about 2.2 s and 2.7 s (reference 2.4 s): over 20 times
  headroom. The two exactly correct naive readers take 193 s and 434 s on the final bundle.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run, on 2026-09-22, after the environment and verifier existed. Decisions the text left
  open, and what was added: that `aria-live` can change value after the load (the brief said it
  was set only at load, which the hide and mix families and three hand pages contradict - now
  "fixed during the load ... a later tick may switch it between those three"); inclusive ends of
  the hold and atomic paths ("up to and including"); how `move` counts its position ("counted once
  the node has been taken out"); that an empty unit counts as finished at once and the reader
  chooses again; document order for a unit's words; the entry point (`Reader(page)`, `load()`,
  `step(t, records)`); that an age survives any change of words; what `aria-hidden="false"`
  does under a hiding ancestor ("exposes nothing that such an element hides"). A cold read by a
  fresh session was not possible here (no subagents), so this pass is recorded as author-run.

## Verifier contract - FROZEN after Stage 2

Frozen 2026-09-22. The graded decisions are restated in `tests/test_outputs.py`, which is the
file a reviewer reads; the full semantics are the sealed model `tests/seal/model.py`.

- Artifacts the agent produces: `/app/sr/look.py`, `/app/sr/know.py`, `/app/sr/watch.py`,
  `/app/sr/unit.py`, `/app/sr/line.py`, `/app/sr/voice.py`. Nothing else is collected; the
  verifier lays those six over its own pristine copy of the tree (page model, script parser, log
  writer, runner and sample pages).
- What is checked: the speech log of every graded page, line for line, exactly. Enumerated hand
  pages against `gt.json`, frozen from the sealed model only once the model, the reference and a
  recompute-everything reader printed the same log for every one (`build_gt.py`, additive);
  generated pages, drawn from a seed chosen after the agent's container is gone, against the
  sealed model, which must itself still reproduce `gt.json`.
- Tolerances: none. The only limit is the wall clock on the stage that runs submitted code (the
  task's execution limit), validated against independently written correct implementations.
- Ground truth, and where it lives: `tests/seal/model.py` and `tests/seal/gt.json`, in a
  directory made `chmod 700` before the privilege drop.

### The model (what "correct" means)

Page: element and text nodes with integer ids; node 0 is the page root, never moved, dropped or
given attributes. Script ops per tick: `add <id> <parent> <pos> el <tag>`, `add <id> <parent>
<pos> tx <words>`, `move <id> <parent> <pos>`, `drop <id>`, `text <id> <words>`, `set <id> <name>
<value>`, `unset <id> <name>`; `pos` is a child index or `end`; tick 0 is the load. Input
guarantees: the elements carrying `aria-live` are fixed at load and it only ever holds `polite`,
`assertive` or `off`, though a later tick may switch it between those three (wording corrected
at Stage 7: the pages always did this, the sentence said "set only at load"); text is one or more
lowercase words.

1. Exposure: a node is exposed when it is attached and no element at or above it carries
   `hidden` (any value) or `aria-hidden` equal to `true`.
2. Region: the nearest element at or above a node carrying `aria-live`; `off` is a region and
   stops the search. A region voices while it is exposed and polite or assertive. Text with no
   region above it is never tracked.
3. Belief: per (region, text node), the text and the anchor (the node's parent when the entry was
   written). Written at load for everything exposed; by a finishing utterance for every key it
   carried; by absorption. What the reader will believe (E) is the playing utterance's carried
   value where it carries the key, else the belief.
4. Differences: current value (exposed text in that region, with its parent) against E, by
   presence and text only: addition, removal, text change. A move inside a region is no
   difference and does not update the anchor.
5. Absorption: a difference whose region is not voicing, or whose kind is not in the region
   element's own aria-relevant (tokens additions, removals, text, all; default additions text),
   is absorbed at observation: belief takes the current value and the playing utterance stops
   carrying that key.
6. Holds: a remaining difference is held while any element on its hold path carries `aria-busy`
   equal to `true`: for an addition or text change, the node's parent up to its region element;
   for a removal, the anchor up to the region element when the anchor is exposed in that region,
   else the region element alone.
7. Age: the tick whose end first observed the difference, kept while it persists; a cut hands
   back each carried key with the age it had when carried.
8. Selection, whenever the reader is free: pending (unheld) assertive differences first, else
   polite; oldest; ties to the lower text node id, then the lower region element id.
9. Unit: from the start element (the node's parent; for a removal, its anchor when exposed in the
   region, else none) up to the region element, the first element whose aria-atomic is `true` or
   `false` decides - `true` makes it the unit, `false` or none found means no unit. A unit
   utterance reads the unit's exposed text now (text nodes in document order, one space between)
   and carries every pending difference whose unit it is; otherwise the utterance is the node's
   text, or `removed ` and the believed text for a removal, and carries that one difference. An
   empty unit is believed at once and selection runs again.
10. Timing and cuts: an utterance of w words started at the end of tick t finishes at the end of
    tick t + w and teaches its carried values then. A pending assertive difference cuts a playing
    polite utterance (logged); assertive utterances are never cut.
11. Tick order, for t = 1..T: apply the tick's ops; finish; observe (absorb, age); cut; select.
    Log lines: `<t> polite|assertive <text>` for a start, `<t> cut` for a cut.

## Decisions and their reasons

- Frontend, not an ML label: the graded work is ARIA live-region semantics over a DOM-shaped tree
  and a speech timeline; nothing in it needs ML knowledge, and the two unused ML labels had no
  design that survived the planning attack (a GPU exposed-pipeline simulator was one-shot
  plannable, a fusion pass read as a graph algorithm, an evaluation-harness design read as
  bookkeeping).
- Regions fixed at load: making an existing element live would turn its content into additions
  under a net-difference model, which no screen reader does; fixing which elements carry
  `aria-live` at load keeps the model honest without a special rule. Their value may still switch
  between polite, assertive and off later, and the pages always did that; the brief and the model's
  docstring said "set only at load" until the Stage 7 cold read caught it.
- aria-relevant from the region element only, stated plainly: a nearest-ancestor reading is a
  wrong reading with its own hand case, not an ambiguity.
- Ties by node id, not document order: node ids are stable across mutations, so the waiting line
  has a deterministic order an implementation can index without recomputing positions.
- Generated families shaped for every reading (Stage 7): the first cheat report showed
  busy-above-region and hidden-false-shows moving no generated page at all, and unit-carries-held
  one in 276 - each was caught only by its hand page. The busy family now also sets aria-busy on
  the element holding the regions, puts a busy container inside an atomic one on every page and
  edits inside those units; the hide family also sets `hidden="false"`. Measured on 200 pages of
  each family: 42%, 35% and 10% moved. The model, the reference, the naive reader and both
  variants agree on every reshaped page checked (400 busy, 300 hide each).
- Harness files written for this task, not carried over: simcheck found `reap.py`, `test.sh` and
  both Dockerfiles at 0.88-1.00 against earlier bundles. They were rewritten in this task's own
  terms (reap reads `/proc/<pid>/status` and sweeps until nothing is left; the reader's uid is
  `reader`); none is above 0.75 now. The tests Dockerfile keeps a `RUN mkdir -p /app/sr` of its
  own, because the platform's structural check reads the instruction that begins the line.
- The forgery carries `gt.json` verbatim, keyed by page name, with a map from page hash to name,
  so that forgecheck can see it is an answer-key carrier; it scores 0 because the generated pages
  are new. The probes print one line saying what their attempt came to, so the two-container
  report can assert the lock that stopped each one rather than read a 0 that a probe which never
  fired would also produce.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | pass | `tools/docker_trial.py` builds both images from the shipped Dockerfiles |
| No answer leaked into agent image | pass | `tools/imagecheck.py`: 16 files, the reference runs all five shipped pages; `extraneouscheck` clean; no comments or docstrings in `app_src` |
| `harbor run -a oracle` = 1 | pass | harbor 0.23.0, `-e docker`, shipped Dockerfiles verbatim: reward 1.0; reader exited 0, 38 passed in 2.36 s |
| `harbor run -a nop` = 0 | pass | same: reward 0.0; 24 failed, 14 passed |
| Two-container trial (oracle 1, nop 0, 45 cheats 0) | pass | 47/47 behaved as required on the final files; both variants score 1 (`--dir`) |
| Cheats all score 0, each at its layer | pass | `cheat_report.py`: 39 host rows caught by the case, clock or worker error named for them; `--trial`: six privilege probes stopped by their lock, the two that could score do score 1 unlocked |
| readingcheck | pass | 30 of 30 readings separated by a named hand page |
| `tracecheck.py` (every graded assertion traced) | pass | clean |
| forgecheck | pass | `cheat-forge-hand.sh` carries `gt.json` verbatim and scores 0; the host cheat report behind it: 0 findings |
| onelinecheck | pass | cut, unit and held: no exact rule of two terms or fewer |
| solvecheck, deadfieldcheck, catcheck, hintcheck, structcheck, textcheck | pass | textcheck against focus-return-point: at least as irregular on every axis |
| simcheck | pass | no NEAR; the four-line environment Dockerfile is HIGH (0.64-0.70) against six bundles, as any minimal Dockerfile is |
| originalitycheck | pass | 100/100; with 67 branch-only instructions as `--corpus`, nearest move-clash-merge at cosine 0.199, shingle 0.000 |
| difficultycheck | pass | 100/100 on the measured tree |
| `preflight.py` | pass | no errors; 24 warnings, all the unused-public-function heuristic, which counts no attribute calls (`run_sr.py` calls `pg.apply`, `rd.load` and `rd.step`); focus-return-point, which passed, draws 15 of the same |
| zipcheck | pass | `tasks/heard-cut-revoice.zip`, 96 entries, built by `scripts/package.py`: no findings; STATE.md excluded, scripts 0755 |
| `harbor check` rubric | not run | no provider API key in this session |
| Easiness probe | not run | this session cannot spawn agents; no trajectories exist for leakcheck |
| Cold self-probe | not run | the author wrote the model before the brief; a cold solve would measure memory (CLAUDE.md, reach-pair-sweep). The cold-reader pass on the brief was run and is recorded above |

## Infrastructure (2026-09-22)

- Docker: the client was installed and the daemon not running; started `dockerd` in the session.
  Docker Hub refused unauthenticated pulls (rate limit), so `python:3.12-slim` was pulled from
  `mirror.gcr.io/library/python:3.12-slim` and tagged locally; the Dockerfiles are unchanged.
- Harbor: not installed; installed `harbor` 0.23.0 with `uv tool install harbor`. Its first oracle
  and nop runs both died in 25 s building the verifier image: `pip install` inside the build could
  not verify pypi.org through this sandbox's TLS-intercepting proxy. The runs that count were made
  with the local `python:3.12-slim` base layered with the proxy CA and `PIP_CERT` for their
  duration, then the original tag restored; the shipped Dockerfiles were used verbatim. This is the
  same accommodation `tools/docker_trial.py` makes, and it does not exist on the platform.
- Container evidence comes from `tools/docker_trial.py` (both images built from the shipped
  Dockerfiles, agent and verifier in separate containers, the verifier's own test.sh) and from
  `harbor run -e docker`. The host emulation (`authoring/heard-cut-revoice/cheat_report.py`,
  `host_trial.py`) runs the worker and grader as root with paths redirected, so it says nothing
  about the privilege drop; the probes that depend on it are judged only in containers
  (`cheat_report.py --trial`).
- No easiness probe was run: this session cannot spawn agents, so there are no trajectories for
  `tools/leakcheck.py` to read. The difficulty estimate rests on the design record, the reading
  separations and the measured gate.

## Measurements (2026-09-22, final bundle)

- Sizes: environment 450 lines of Python in 11 files, 182 of them in the six editable modules;
  reference 550 lines in six modules plus an 11-line solve.sh; sealed model 481 lines; generator
  710 lines; 35 hand pages; wide pages about 17,400 text nodes over 2400 ticks; held pages 15,000 to
  16,100 held additions before a release at tick 2500-2700 of 3000.
- Agreement: the model, the reference and the naive recompute-everything reader agree on every
  hand page (build_gt refuses otherwise) and on 540 + 1,800 generated pages before reshaping,
  300 hide and 400 busy pages after it, and the six scale pages.
- Gate, in the verifier image on one CPU, the whole graded set as the worker: reference 2.3-2.4 s,
  ok-cache 1.9-2.1 s, ok-region 2.5-2.6 s; the exactly correct whole-page recompute 433.9 s and
  line rescan 193.2 s on the final bundle (483.7 s and 208.3 s earlier, before the reshaping and
  under other load); a cached-flags reader with an O(depth) scan 15.4 s, which passes.
- Cheats: 45. Host layer report (`authoring/heard-cut-revoice/cheat_report.py`): every one caught
  by the layer named for it, 0 findings. Two-container probe report (`--trial`): all six
  privilege probes stopped by their lock, both unlocked controls score 1, 0 findings.
- Readings: 30 of 30 separated by a named hand page (`tools/readingcheck.py`).
- onelinecheck: cut (3,988 samples), unit (3,181) and held (6,709) have no exact rule of two
  terms or fewer over agent-visible features.

## Open questions and next steps

- Submitted as pending. What would change the design: an easiness probe that solves it, or a
  quality review that names a rule as guessable. The first repair to reach for is the one the
  lessons in CLAUDE.md name for this shape - a scaling boundary or a rule that invalidates
  several structures at once, not more rules.
