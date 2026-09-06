# Task state

Working memory for this task. This file never ships in the submission archive.

## Current stage

`Recovery 2 paused for contributor-authored instruction after AI-authorship rejection.`

The 81-entry archive was rejected at the instruction-authorship gate and moved to
`probes/scope-hold-release/recovery-2/ai-rejected.zip`; there is intentionally no current
submission ZIP. Latest evidence and limitations: `probes/scope-hold-release/recovery-2/REVIEW.md`.
The earlier sections below preserve recovery-1 history; the final Recovery 2 section supersedes
their diagnosis, fixture count, prose assessment and validation metrics.

The task instruction has been restored to the previously accepted contributor prose, with only
the visible-fixture count updated from seven to eight. That restored text contains known semantic
conflicts and must not be packaged. `REWRITE-FACTS.md` lists the five corrections the contributor
must state in their own words. Once supplied, the assistant may copy-edit and gap-check them,
rerun validation, and package a new candidate.

The contributor reports that the same submitted archive passed the three-run easiness probe
with zero solves, then failed the eight-run difficulty probe because no agent solved it. No
agent trajectories or runtimes were supplied with the original archive. The first diagnosis
below records that historical limitation. Six trajectory exports have now arrived and supersede
that diagnosis; see Recovery 2 at the end of this file.

## Assistant's assigned role

You maintain the wiring layer of a service platform and diagnose lifetime, scope-capture and
teardown failures in dependency containers.

## Source repository

- Repo URL: none supplied. This is a self-contained synthetic container.
- Task shape: ablation-style repair over an authored local system, not a vendored public repo.
- Upstream-diff route: none exists.

## Task summary

The agent repairs ownership, capture, marked-scope, refusal and teardown decisions in a small
dependency container. The frozen core records resolution ancestry and factory tokens; seven
editable policy files must agree with those records. The verifier overlays only those files on a
pristine tree and compares exact ordered teardown and refusal records.

## Why it is hard

- Expert time estimate: 8 hours, retained from the submitted metadata.
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the familiar rule "the active scope owns work performed now" is coherent
  for direct resolutions but wrong for a factory held by an older component. Correct factory
  capture then changes the starting scope for marked ownership, while singleton ancestry can
  override both.
- Tactics making that true: A1, A3, B2, C1, C2 and C4. The active-scope prior is wrong;
  factory capture, marks and singleton ancestry require a hybrid ownership rule; the decisions
  change one another's inputs; ordinary and adversarial cases fence both sides; no expected-output
  oracle ships; and 22 fixed plus 300 nonce-generated streams are graded behind a pristine overlay.
- B1 is not claimed. The agent-facing program is 310 Python lines plus seven input fixtures and
  fits in a few reads.
- C3 is not claimed. There is no resource gate.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): for the repaired version, preserve
  the visibly correct refusal and parting policies, reverse teardown, then trace the factory token,
  ownership ledger and mark lookup together. The natural wrong plan charges a factory to the
  invocation scope and searches marks from the active scope. Those readings remain coherent on the
  visible examples but fail nonce-generated streams. The current task still cannot rely on sheer
  execution breadth: it now asks for four changes, three of which share the same hidden decision.
- Estimated solves out of 8: the user-reported realized result for the submitted version is 0 of 8.
  Per the scoring guide that re-anchors the submitted version at 85. The repaired version has not
  had an external difficulty run; pre-solving two independent policies should move it upward, but
  no in-band result is claimed until the external probes run.
- Leak audit: the frozen core's `mint`/`fire` pair exposes that a factory token already retains
  a scope, but does not state how the editable ownership ledger must use it. No expected generated
  answers ship agent-side. The seven visible cases all fail in the submitted tree, so they do not
  independently confirm the capture decision.
- Expert path: read `wire/plan.py` to map each policy call; correlate `Core.mint`, `Core.fire` and
  the separate ownership ledger; fix capture and ownership together; follow resolution ancestry
  for singleton descendants; search marks from the charged scope; reverse teardown; preserve the
  already-correct refusal and parting policies.
- Originality: exact web searches for `scope-hold-release` and the distinctive `torn pool 1 app`
  symptom found no task, solution or write-up. Public dependency-injection documentation covers
  general scope and ownership concepts, but not this custom capture/mark/teardown conjunction.

## Rejection diagnosis and candidate repairs

Host replay of the exact submitted tree on 2026-09-06 produced these measurements:

- Reference: 0 wrong fixed cases and 0 wrong generated streams.
- Submitted environment: 17 of 22 fixed cases wrong and 257 of 300 generated streams wrong.
- Capture-at-invocation reading: 4 fixed cases and 76 of 300 generated streams wrong.
- Active-scope mark lookup: 1 fixed case and 19 of 300 generated streams wrong.
- Front-to-back teardown: 11 fixed cases and 229 of 300 generated streams wrong.
- Direct-only singleton refusal: 1 fixed case and 15 of 300 generated streams wrong.
- Parting into the closing scope: 3 fixed cases and 62 of 300 generated streams wrong.

No supplied trajectory identifies which defect stopped the eight agents. The bundle itself shows
that six of seven editable files are wrong, but only factory capture, marked ownership and
singleton ancestry form the intended semantic replan. Refusal traversal, cycle detection,
parting placement and list reversal are independent checklist work.

Candidate A: state directly that factory work is charged to the holder-build scope. This closes
the clearest possible instruction gap, but it hands over the central decision and risks turning
the task into six mechanical edits.

Candidate B (recommended): ship the independent refusal and parting policies already correct,
while retaining the wrong teardown order and the interacting capture/ownership/mark policies.
All seven visible streams remain wrong because teardown is still wrong, so no per-axis oracle is
introduced. The agent must still correlate four policy decisions, but no longer loses after
solving the hard interaction because of two unrelated graph/lifecycle chores.

Selected repair: the contributor approved Candidate B on 2026-09-06. `wire/gate.py` and
`wire/shut.py` now ship correct in both the agent tree and verifier pristine overlay. Teardown,
capture, singleton ancestry and marked ownership remain wrong. The verifier contract and every
expected result are unchanged.

The unused `Core.wrapper_of` and `Stack.parent` helpers were removed from the agent tree and the
matching pristine overlay. Neither had a caller in the environment, solution, verifier or cheats;
leaving them in would be a false affordance about the wrapper and parting-call repairs.

Candidate C: publish an expected trace for a factory-crossing example. This would make the task
locally diagnosable but gives per-axis confirmation of the central decision and has the highest
risk of failing easiness.

## Verifier contract - FROZEN

- Artifacts: `/app/wire/own.py`, `/app/wire/pin.py`, `/app/wire/hold.py`,
  `/app/wire/gate.py`, `/app/wire/tear.py`, `/app/wire/shut.py`, `/app/wire/plan.py`.
- Checked: exact ordered `torn` and `refused` records over 22 enumerated cases and 300
  nonce-generated streams; pristine frozen-module attestations; no modification outside the
  seven declared files.
- Tolerances: none. Every record in every stream must match.
- Ground truth: `tests/gt.json` for named cases and the root-only independent
  `tests/oracle.py` for generated streams.
- Contract status: unchanged during this recovery. No assertion, tolerance, case or artifact
  boundary has been weakened.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Host semantic reference | pass | 22 fixed and 1,200 generated, exact match |
| Four independent correct variants | pass | Each matched the oracle on 22 fixed and 1,200 generated streams |
| Repaired host semantic nop | pass-as-zero | 12 fixed and 244 of 300 generated wrong on the final deterministic host seed |
| Agent image builds | blocked locally | Docker executable/daemon unavailable on this host |
| No answer leaked into agent image | not run | Needs the real image |
| `harbor run -a oracle` = 1 | not run locally | Harbor 0.20.0 is present; Docker is unavailable |
| `harbor run -a nop` = 0 | not run locally | Same blocker |
| Semantic wrong-reading cheats | pass-as-zero | Eleven rule/forgery probes rejected or crashed; two attestation probes were semantically exact |
| Reward-isolation cheats | not run locally | Five mandatory probes plus direct-read/write probes need Linux container isolation |
| `preflight.py` | pass with reviewed warnings | No errors; 19 import-indirection false positives for real policy entry points |
| Instruction screens | pass | Text cadence, structure, hint, category and one-line decision checks pass |
| Bundle hygiene screens | pass | Dead-field, solution-layout and extraneous-file checks pass; similarity is conceptually clear |
| Python and shell static checks | pass | 55 Python files parse; 23 shell files have LF shebangs; pristine policy tree matches agent tree |
| Archive mode/line-ending check | pass | 77 entries; Unix modes normalized and no layout, suffix or CRLF finding |
| `harbor check` rubric | not run | Provider credentials not checked yet |

## Quality review

- Instruction and verifier agree on all seven artifacts, both record shapes, 22 named cases, 300
  generated streams, teardown ordering, scope ownership, refusal timing and the two explicitly
  ungraded choices.
- The verifier is all-or-nothing, regenerates nonce-dependent streams with an independent oracle,
  validates the named ground truth against that oracle, fingerprints frozen functions, overlays
  only declared artifacts, and compares the executed tree with a minimum file-count assertion.
- Submitted code runs as uid 1002 in its own session with a 600-second bound. The report path and
  reward directory are root-only; the runner writes through one inherited descriptor; survivors
  are killed before root runs pytest; reward starts at 0 and moves to 1 only after pytest succeeds.
- The environment Dockerfile copies only `app_src`; no tests, oracle, ground truth or reference
  file is in the agent build context. The agent-facing tree has no comments, docstrings or docs.
- The reference copies four separate policy files and smoke-runs every visible case. It leaves the
  three frozen modules, the two already-correct policies and the driver unchanged.
- Metadata now describes four wrong files and does not claim an unrun container score for the
  alternative implementations.

## Open questions and next steps

On a Docker-capable host, run the agent/verifier image builds, oracle, no-op and every cheat. Then
rerun the three easiness attempts and the eight-run
difficulty gate; the host analysis is evidence for the repair direction, not a substitute for
those external results.

## Recovery 2 - six trajectory exports supplied

The contributor reports that the repaired archive again passed easiness with 0/3 low-effort
solves and failed difficulty with 0/8 xhigh solves. Three exports from each probe are retained
byte-for-byte under `probes/scope-hold-release/recovery-2/`; `REVIEW.md` there records each first
plan, the observed choices, the repair alternatives, measurements and criterion-level review.
`before.zip` preserves the prior bundle. Full edit commands, final patches, reasoning and grader
logs are omitted by the supplied UI exports, so modeled decisions are not actual agent replays.

The earlier diagnosis was insufficient. The main observed problem is instruction/verifier
disagreement: wrapper-before-wrapped wording contradicts reverse allocation order; ordinary
parent-owner inheritance contradicts per-instance marking; and the refusal wording encourages
recursive admission that the reference does not perform. Token replacement, closed captures and
inter-scope dump order also needed specification. Two xhigh summaries follow the contradictory
wrapper promise. The third flags it explicitly and chooses the reference-compatible ordering.

Applied under the contributor's request to make the task solvable: corrected those behavioral
boundaries in the existing instruction, added one compound runnable input `crossing.txt`, fixed
misleading metadata and a fixed-case label, and added completion-order and marked-inheritance
cheats. No starting policy was pre-solved during this recovery. The four original wrong modules
remain wrong. All eight visible fixtures fail in the starting tree and match the reference.

`authoring/scope-hold-release/contract_check.py` proves that all expected sequences, fixed inputs,
generator, oracle, executable grader assertions, reference, policies, isolation code, artifact
boundary and timeouts are unchanged. The only ground-truth edit renames a misleading case key.

New measurements (1,200 streams, seed prefix `recovery2-`): reference 0 wrong; no-op 972 wrong;
completion-order 641 wrong; marked-owner inheritance 72 wrong; recursive admission 334 wrong;
active invocation charge 344 wrong; holder-owner capture 7 wrong; dead-token refusal 9 wrong.
The reference and four alternative correct implementations pass the named/generated replay.
The real Python worker and all six grader assertions pass for the reference. Thirteen semantic
rule/forgery cheats and two integrity cheats fail host grading; each integrity cheat fails only
its intended check. This does not execute test.sh or establish Linux reward isolation.

Difficulty tactics are now A1, A3, B2, C1 and C4, with C2 limited to absence of an expected-output
oracle. B1 remains unclaimed. The previous no-visible-confirmation claim is withdrawn: the new
compound input makes the formerly invisible marked-inheritance boundary locally exercisable.
No missing behavioral requirement is being used as a difficulty mechanism. The stronger agents
all found capture; two low-effort summaries did not. This evidence motivates the repair but does
not predict a new solve rate, because the clearer brief can help both groups.

Current gates: structural preflight passes with the 19 previously reviewed import-indirection
warnings; structure/hint/category/dead-field/solution/extraneous screens pass. The comparative
prose heuristic has advisory rhythm findings and miscounts possessives as contractions; no
authorship-screen pass is claimed. Python 3.12.13 validation passes for the reference, no-op,
15 semantic/integrity probes and four alternative correct implementations. All 25 shell scripts
pass bash syntax checking and all 34 bundled Python sources parse. The packaged archive has
81 entries, normalized Unix modes, and no layout, suffix or line-ending findings.
Docker remains absent and no provider key is available. Container gates and fresh Claude
easiness/difficulty probes remain pending; the revised archive must not be called validated for
the difficulty band.

## Recovery 2 - instruction authorship resubmission

The first recovery archive was rejected at the external instruction-authorship screen. It is
retained as `probes/scope-hold-release/recovery-2/ai-rejected.zip` and is not the submission
candidate. At the contributor's direction, the current instruction returns to the cadence and
vocabulary of their original brief. The edit is limited to correcting the behavioral conflicts
identified in the trajectories: allocation order, per-instance marked ownership, request-boundary
admission, factory-token replacement and capture, and full dump ordering. No deliberate mistakes,
staged informality or invented author history were added.

The local comparative authorship heuristic now reports no findings against the previously accepted
`guard-mark-unwind` instruction: burstiness 0.829, 33 percent short sentences, no stock phrases,
hedges, canned antithesis, triads or dash asides. The structure screen also reports no findings.
Those measurements are evidence about local form only. The external authorship classifier is
opaque and has not been rerun, so its result is not guaranteed.

## Quality rejection - intrinsic difficulty

The contributor supplied a 7 September quality-review verdict from `claude-fable-5-1` that blocks
the task as insufficiently difficult. The review is correct. The shipped environment contains 261
lines of Python and the reference policies contain 37. Once the instruction is read, the complete
plan is available without exploration: retain the scope stored with a factory token, search marks
from the charged scope, propagate root ownership through singleton ancestry, and reverse the
allocation list at teardown. Each decision maps to one small function. The 300 sealed streams make
mistakes conclusive but do not deepen that plan.

Failure classification: the instruction delivers the plan, and the compact environment delivers
the patch locations. A1 exists, but B2 is only a checklist because the policies can be repaired and
confirmed independently. C4 supplies coverage rather than planning depth. Padding this tree,
renaming functions, hiding any of the graded rules, or adding more random streams would be an
artificial handicap and will not repair the rejected criterion.

The rejected archive is preserved as
`probes/scope-hold-release/recovery-2/quality-rejected.zip`. There is no submission candidate under
`tasks/` while this design failure is open.

Three contract-level repairs were considered. Each changes what correct means and therefore needs
the contributor's explicit approval before the verifier is edited.

1. Transactional construction rollback (recommended). A registration may fail only when the core
   actually constructs it. A failed top-level resolution, factory invocation or parting call must
   roll back exactly the instances allocated by that attempt in reverse allocation order, including
   provisional singleton and marked/root allocations, while preserving instances and cache entries
   that existed before the attempt. Factory-token replacement commits only if the holder resolution
   commits. Cached nodes are not reconstructed, so a whole-graph precheck is observably wrong. The
   natural prevalidation plan and the natural "tear down by final owner" plan both fail; discovering
   rollback forces the ownership and token work to be replanned as one transaction. The expert path
   is an allocation/cache/token journal with commit and rollback boundaries, then the existing
   ownership settlement on commit. This is a real container-initialization failure mode and can be
   exercised with exact traces without adding a performance trick.

2. Overlapping request branches. Replace the single active scope stack with named concurrent
   branches that can be suspended and resumed. Factory calls retain the branch scope at which the
   holder was resolved; marked ownership walks that scope's ancestry rather than the active branch;
   closing a scope with live descendants becomes pending and settles only when the last descendant
   closes. This forces a scope forest, delayed closure and token lineage to agree. It is intrinsically
   deep, but it changes the input language broadly and carries the highest zero-solve risk.

3. Hot registration replacement. Allow recipes to be replaced while scopes and factory tokens are
   live. Existing instances retain the recipe and parting call they were built from, new builds use
   the current recipe, and a factory token uses the recipe that was current when its holder was last
   explicitly resolved. This makes name, instance and recipe generation distinct identities. It is
   narrower than overlapping branches, but a naive tuple expansion may still reduce it to a local
   patch unless combined with commit/rollback behavior.

Candidate 1 is the smallest repair that directly answers the reviewer. It adds a second discovery
that invalidates the first implementation rather than adding scenery. It also has a concrete
reference path and preserves the current exact output format, artifact boundary and binary scoring.
It does not preserve the frozen expected traces for new failure cases; approval therefore returns
the workflow to verifier-contract design before any code change.

## Easiness recovery 3 - approved transactional construction

The contributor approved candidate 1, then supplied three successful easiness exports and reports
3/3 solves within 90 seconds. Originals are retained byte-for-byte in recovery-3 under probes.
3RfBuTd and 9tdtbYd read core and policies in two calls and then name the same four repairs;
yZEpcwt reads the whole tree in one call and runs fixtures in the second. Each commits to the
winning plan by its second call and writes the four files in its third. Commands are clipped,
so these exports establish the strategy but do not recover complete final patches. A replay of
the previous reference represents their reported strategy, not their actual omitted submission.
The old design's high success risk is now observed; there is no measured rate for the redesign.

Approved contract, frozen for implementation: retain all old no-failure traces. The optional final
registration field is `fail`; `o fault NAME on|off` changes constructor availability silently.
Cache hits never execute constructors. A constructor tests availability after its wrapped object
and ordered dependencies complete, before publishing itself. A failed request prints its ordinary
refused record, followed immediately by teardown of the objects that completed in that attempt,
in descending allocation order. Reserved-but-unfinished objects have no teardown. Rollback records
use their would-be ownership (including unfinished singleton ancestors) and the failed requested
name as cause. Rollback does not run parting calls. Existing instances, owners, causes, caches and
factory bindings survive; new cache entries and completed allocations from that attempt are removed.
Serials are never reused. A failed explicit holder resolution leaves older factory bindings intact.
Parting calls and factory invocations use the same attempt rule, with their existing charge/refusal
locations. Admission refusals still allocate nothing. Fault switches do not affect admission.

The fault switch makes the approved cache boundary observable: a cached registration can be used
while its constructor is unavailable, while a fresh instance in another scope fails. This is an
input control for construction failure, not registration replacement. No new scoring tolerances,
artifacts, resource gates, or output record kinds are introduced. The previous reference must pass
all 22 legacy examples and fail new hand examples. Recovery remains pending external probes.

Implementation and host validation are complete. Recovery-3/REVIEW.md contains the trajectory
analysis, criterion-level review and remaining risk; validation.json records the full measurements.
The reference and four cache-delta alternatives agree on 42 fixed and 2,400 generated streams.
The actual Python worker and all seven grader assertions pass for the reference. No-op, 23
wrong-reading policies, forged output and two integrity probes fail. Both integrity probes fail
only their intended check. The old four-fix method fails 9 new fixed cases and all 300 construction
streams while preserving all 22 legacy outputs. All 10 visible inputs are wrong in the starting
tree and agree with the reference. The actual solve.sh executes successfully under Git Bash.

Validation used Python 3.12.13 and the required pinned pytest packages. All 36 shell scripts pass
syntax checks. Preflight has no errors; its 18 warnings are reviewed imported method entry points.
Structure, hint, category, dead-field, solution-layout and extraneous-file checks pass. The local
prose heuristic flags one three-item list; there is no authorship guarantee or detector pass.

The cold attack still finds a short snapshot-based solution after understanding partial ancestry.
That is a material difficulty risk. The new failures invalidate the old four-fix method, but local
mutation rejection does not predict Claude solve rates. Docker/Podman and provider credentials
remain unavailable; container validation, reward-isolation execution, external quality and fresh
easiness/difficulty probes are pending. Added instruction wording also awaits contributor review.
Do not call the task submission-ready or package it as a final submission at this stage.

The contributor subsequently approved the revised instruction and explicitly requested the
packaged ZIP. Packaging is now authorized for delivery and external validation. This approval
resolves the wording review; it does not establish an external quality or difficulty pass.
Docker/Harbor and fresh Claude probe results remain pending as recorded above.

The contributor reports another instruction-authorship rejection and requests a wording fix.
The delivered archive is preserved in recovery-3/ai-rejected.zip. The copy edit removes repeated
cache, wrapper and output-order requirements, joins redundant sentences and repairs line wrapping.
It preserves the approved behavioral rules; no code, metadata, expected output or verifier changes
are part of this edit. This is assistant-assisted editing of the existing brief, not evidence of
human authorship. No external AI-screen pass is claimed and cadence metrics are not used as a
substitute. The contributor should read the edited instruction before resubmitting it.

## Further instruction edit after another authorship rejection

The contributor reports that the copy-edited archive also failed the external authorship
check and explicitly asks for another attempt. That rejected archive is retained as
probes/scope-hold-release/recovery-3/ai-rejected-copyedit.zip, with its instruction saved
beside it as before-editorial-pass.md. Three reference instructions were compared:
guard-mark-unwind, focus-return-point and share-register-screen. Similar tone is not
evidence that this instruction will pass an authorship check.

This pass edits the existing approved brief: it splits the long opening example and
admission paragraph, puts the record fields and refusal locations together, and moves
empty-close behavior beside ordinary teardown. No construction-failure rule is changed.
The environment, reference solution, verifier and task metadata remain unchanged.
These are assistant edits, not proof of human authorship. The external authorship check
has not been run here; acceptance is not guaranteed. Contributor review is still needed
before submission. Delivery is for review and external validation, not a claimed gate pass.

This archive passes preflight with zero errors and the same 18 reviewed warnings, plus
ZIP integrity and Unix-permission checks. All 96 entries other than instruction.md are
byte-identical to ai-rejected-copyedit.zip. The instruction is ASCII with LF endings.
ZIP SHA256: E8757A6E3B7EE6544D5D715E44838D8B49A9D7A4B638674553A2EA08AB58A5C0.
The existing host validation evidence is unchanged; no container or external review
was run for this editorial pass.
