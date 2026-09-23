# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one — anything not written here is lost.

## Current stage

`Easiness recovery, round 1` (2026-09-23). The easiness probe solved the bundle at commit f31b80c
3 of 3. RAISE-DIFFICULTY.md is running from section 1; Stage 7 is blocked until the recovery
exit gate. The entry below records the evidence, the diagnosis, the candidates and the chosen
repair; the sections after it describe the bundle as it was probed until each is re-derived.

## Easiness recovery - 2026-09-23 (probe 3 of 3)

### 1. The failure, captured

- Result: the easiness probe solved it in 3 of 3 trials. The contributor supplied the three
  transcripts; they are in probes/partial-key-purge/2026-09-23-easiness-{1,2,3}.txt with the brief
  stripped (probes/partial-key-purge/notes.md says exactly what was removed).
- tools/leakcheck.py on the three: nothing above the floor. The brief did not supply the wording.
- First plan, decisive discovery, final method:
  - trial 1: first plan, before any experiment, "an indexed fixpoint delete and a tree-DP audit";
    the audit folds the cascade structure into a forest with components for loops and
    self-matches, sums path updates over subtrees, and replays any component the forest cannot
    express. Decisive step: none - the plan was complete; profiling found one 289-row component
    whose local fixpoint was slow and a worklist fixed it. deep.txt 4.2 s, graded set estimated
    at 42 s.
  - trial 2: "a cell-based index ... batch-process the single-parent forest bottom-up with a
    fallback for cleared-but-referenced tables"; counters per match cell, small-to-large merges,
    cycles judged together, whole-audit per-row fallback when a clearable table is referenced
    (never true in the deep schema). deep.txt 3.4 s.
  - trial 3: profiled deep.txt's structure (loops, depth, branching), then "an exact engine for
    delete and an incremental closure-merging pass for audit" - "single-row closures form a
    laminar family" - with the exact engine for seeds whose contributions cannot be aggregated.
    Its fuzzing found and fixed one real fast-path bug. deep.txt 7.2 s, estimate 55 s.
- Earliest commit point: after reading the nine modules and the four samples (tool calls 1-2 in
  trials 1 and 2, call 4 in trial 3), before running any experiment. The complete plan existed
  before any code.
- Where the plan came from: the model's prior and the shape of the specification, not the brief's
  wording (leakcheck clean) and not a verifier loophole. Every rule is individually implementable,
  and the structure each wants is the standard one: a counter per match set for the least fixed
  point, and nested removed sets (a dominator forest) for the audit. Confirmation came from each
  agent's own brute-force transcription of the brief, random generators and sampled comparisons
  on deep.txt - every rule was confirmed one at a time.
- Tactics that failed in practice: A2 (the ownership tree was recognised at once, in the agents'
  own words), A3 (loops and two-cascade rows were absorbed by components and per-row fallbacks),
  C2 (the brief is a complete oracle on small stores), C3 (it priced only a full per-row replay;
  replaying just the rows the tree cannot express was cheap because such rows are rare in the deep
  stores and the deep schema is fixed).
- Estimated solves out of 8 before repair: 8 (measured 3 of 3).

### 2. The winning route, classified

- The default plan was correct: all three named the right state model (counters on match sets)
  and the right audit structure (nested removed sets) before exploring. Evidence: the planning
  lines quoted in probes/partial-key-purge/notes.md.
- The agent confirmed each step independently: a brute force written from the brief checked every
  rule on small stores; the only thing it could not check, the fast audit at scale, was checked
  by sampling the agents' own exact engines on deep.txt.
- The naive method was fast enough: a hybrid - the tree where it applies, per-row replay where it
  does not - fit the clock with room to spare. Replay of the few loop members and two-cascade rows
  is exactly what the reference itself does, so the gate never touched the hybrids.
- Not the cause: the instruction (leakcheck clean, no method named), a derived leak in the tree
  (rows carry only ids and values), a verifier loophole (no probe exploited grading).

### 3. Candidates

A. Merge histories (drop the guarantee that no reference names a key of a table with two or more
   cascade references). A merge revision has a base and a merged-from parent, each a cascade
   reference, and it goes when it loses either; later revisions are based on it. Removed sets stop
   nesting: deleting either parent's line removes the merge and everything based on it, while a
   row matching several revisions still goes only when all of them go. The dominator forest gives
   wrong counts, reachability (descendants) gives wrong counts on the rows with several matches,
   and loops through a merge row can now be broken from outside. Attack: the correct structure is
   the set of rows whose lone delete removes a row, which is an intersection over a reference's
   matches and a union over a row's cascade references; an agent who sees merges while planning
   drops the tree for that formulation. Alone it is one discovery made at planning time.
B. The real database's cascade depth limit (the rehearsal store must refuse what the real one
   refuses): a delete runs in rounds, and one that would remove a row in round 16 or later is
   refused. The round of a row is one after the last of the rows it matched through a lost cascade
   reference, the earliest over its lost cascade references. Attack: on its own, over single-parent
   histories, the round is a longest-path difference and the tree still answers it; with A the
   round is a max over matches and a min over references, so the set of deleters is not enough -
   the round each deleter reaches is needed, and a representation built for A has to be rebuilt.
C. The audit prints the refusal it would print (`refused <name> <id>`) instead of `held`. Attack:
   the name is a minimum over failing rows ordered by declaration and id, and a minimum is not a
   signed sum, so the marks that carried the old audit cannot express it; alone it is a technique
   swap on the same tree.
D. Rejected: a purge statement that deletes a table row by row, each on the store the last one
   left. Removed sets change after every successful delete and rows move deeper in the ownership
   structure; no expert path within ten hours maintains that without dynamic trees.
E. Rejected: shaping the deep family so the hybrids' replays become quadratic (huge loops,
   referenced clearable tables) without a rule change. It is more hidden cases on the same plan,
   and the reference itself replays loop members.

Selected: A with B and C together, as one change of what the store rehearses - merge histories
under the real database's cascade limit, with the audit reporting what each delete would print.
Why together: A makes the first plan wrong (the tree) and forces the deleter-set formulation; B
invalidates that formulation's natural representation (one set per row) once it is built, because
the depth refusal needs the round each deleter reaches, a min over references of a max over
matches; C makes every failure a minimum, so the depth failures, the restrict losses and the
end-state failures have to be merged in declaration order per deleter, with the depth failures
excluding the rows a deleter reaches within fifteen rounds. The ordinary side stays graded:
single-parent chains, a cascade exactly fifteen rounds deep (accepted), loops without merges.
Contract change: this changes what "correct" means for the delete (depth refusals; merge rows
referenced) and for the audit (the refusal line). The contributor's request of 2026-09-23 ("make
the task substantially harder") is the approval; the change is recorded under the re-frozen
contract.

### 4. Rebuild, from Stage 2

- Stage 2: contract re-frozen (section "Verifier contract - RE-FROZEN 2026-09-23" below) after
  the brute force, the model, the reference and two variants agreed; tests/cases.py grew from 25
  to 33 hand scripts (audit-names, depth-both-refs, depth-limit, depth-merge-shortcut,
  merge-either, merge-self, merge-wild-side, or-loop-broken); gt.json rebuilt with
  build_gt.py --contract-change, every moved answer listed and classified.
- Stage 3: tests/seal/gen.py adds merged-from columns and the `rev_merge` reference to every
  generated store, merge kinds (branch merges, merges from other documents and from whole
  documents, forward merges that make loops), two new families (merge, depth) and a rebuilt
  deep family of merge histories; the shipped samples were regenerated from it; the frozen
  printer prints refusal lines; the pristine mirror was re-synced.
- Stage 4: solution/drop.py counts rounds, solution/hold.py refuses past round 15,
  solution/audit.py is new (deleter sets over Tarjan components, layered rounds, bit-sliced
  counts, refusals painted in declaration order). The probed reference's audit is kept as
  authoring/partial-key-purge/old/tree_audit.py for the tree-audit reading.
- Stage 5: instruction.md rewritten where the rules changed (5,536 characters); trace.md walked
  again from the top; tracecheck clean.
- Stage 6: 41 cheats emitted (25 readings, 4 shortcuts, the replay audit, the gt.json forgery,
  10 isolation probes); the old winning plan is `cheat-tree-audit.sh`, separated by the hand case
  merge-either.

### 5. Measurement before another probe

- Reference scores 1 in the capped container (1 CPU, 2 GB): 37 passed, worker 51 s; nop scores 0
  (27 failed, 10 passed); both variants score 1 (65 s and 71 s).
- The old probe-winning plan fails a specific hand case (merge-either) and the sealed suite; the
  probe's hybrid (tree plus replay of what it cannot express) would replay 74.8% of the rows of a
  deep store, and the per-row replay floor is 2,402 s against 180 s.
- No short expression reconstructs a graded decision: tools/onelinecheck.py finds no exact rule
  at depth 2 for removed-by-lone-delete, audit-removed, audit-held or delete-refused.
- Resource gate recorded for both families: correct fast family 51-71 s whole run in the
  container; naive replay 2,402 s for the deep scripts alone on the host.
- Cheat sweep, preflight and the manual quality review: recorded below.
- Cold self-attack: recorded below; author-run and contaminated.

### 6. Exit gate

Not reached. Recovery ends only when the external easiness probe passes. The bundle is packaged
for that probe; this entry is updated with the realized result when the contributor has it.

## Assistant's assigned role

No role was assigned verbatim; the contributor's prompt made the assistant "the engineer, probe,
reviewer, and solver" and left the domain role to the assistant. Chosen role: a database engineer
who works on a relational engine's referential-integrity layer (match rules, referential actions,
constraint timing) and on the delete-impact tooling built over it. Later sessions resume in it.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): authored-on-top, in-house engine
- Contributor's relationship to it (maintainer / contributor / production user, how long): not applicable
- License, and why vendoring it is permitted: not applicable, nothing vendored
- Pinned commit vendored into environment/app_src/ (.git stripped): not applicable
- Load-bearing couplings found during research (file paths): not applicable
- Identifier degradation done? not applicable; identifiers are written in a legacy register from the start
- Proper-noun sweep done? not applicable, nothing vendored
- Upstream-diff check: not applicable, there is no upstream

## Task summary

`/app` is a small row store with composite foreign references. A script declares tables, keys
and references (each with a match rule of simple, full or partial and a delete action of
cascade, restrict, noaction or setnull with an optional column list), gives rows, and then runs
deletes, dumps and audits. The shipped referential pass treats every reference as simple and
cascades row by row as each referenced row goes; the shipped audit replays a delete per row. The
agent rewrites five modules so that deletes remove, clear and refuse exactly as the brief states
- including merge revisions, which go when either parent goes and are themselves referenced, and
the real database's refusal of a cascade that runs past fifteen rounds - and so that the audit,
which prints for every row what deleting that row alone would print, refusal included, runs
inside the stated limit on stores of about thirty-six thousand rows, most in four merge
histories of six to seven thousand revisions.

## Why it is hard

- Expert time estimate: 12 hours
- Why a frontier agent cannot one-shot the plan: the first version was solved 3 of 3 because the audit's structure - removed sets nest, so they are the subtrees of one ownership tree - was each agent's first idea. In the rebuilt task that structure is wrong: merge revisions go with either parent and are referenced, so removed sets overlap without nesting, and a row matching several revisions still needs all of them gone, so descendants are wrong too. The audit has to be built from the rule itself (a row's deleters are a union over its cascade references of an intersection over their matches, settled as least fixed points over loops that a merge can break). Once that is built, the depth limit invalidates its representation: the round is a minimum over references of a maximum over matches, so the deleters have to be rebuilt per round up to fifteen, and every refusal has to be named, a minimum over failing rows that signed sums cannot give.
- Tactics making that true: A1 (the ownership tree and descendant counting are each the textbook answer for half of the removal rule and give confident wrong counts on the other half), A2 (deleter sets, least fixed points, rounds per deleter, column sums and painting are described through their rules, never named), A3 (dominators need one owner per row, reachability needs one match to be enough, the depth limit needs rounds per deleter; they have to be combined), B2 (match rules, the fixpoint, OR across cascade references, rounds and the limit, pre-statement matching, column-list clearing, RESTRICT against NO ACTION, end-state checks and naming hold at once), C1 (fifteen rounds pass and sixteen refuse; a merge goes with either parent while a several-match row needs all; plain chains cascade as any engine does), C3 (the correct per-row replay needs about 2,400 s against 180 s, and a tree-plus-replay hybrid replays three rows in four), C4 (every line of every script over 33 hand scripts and 363 generated ones shaped around merges, loops through merges, cascades near fifteen rounds and the old shapes)
- Assistant's attack on the plan: author-run at design time and again on the finished bundle, so contaminated - the author chose the rules (see the recovery entry). My first plan would be the probe's plan plus the new rules bolted on: counters with rounds for the delete, and an ownership-tree audit with a replay fallback for merges. The tree is wrong at every merge (merge-either), and the fallback replays 74.8% of the rows of a deep store. My second plan, descendant bit sets, is wrong on every row with several matches (merge-wild-side). The deleter-set plan is the third, and its natural representation - one set per row - cannot answer the depth limit, which needs rounds per deleter; naming the refusal then needs a minimum, not the sums I would have carried over. I can see where to start, but I could not commit to the whole plan without exploring, and my first plan is wrong where it matters.
- Estimated solves out of 8: 2 (range 1-3)
- Difficulty record score: 2026-09-22, 100/100 IN BAND for the first design; 2026-09-23 the record was rewritten for the redesign (probe's plan as the first plan, merges as the breaking rule, the depth limit and refusal naming as the second discovery) and scored 94 on a first pass (first_plan_source not one of the fixed labels; hand cases named but not described), 100/100 IN BAND once both were in the rubric's form; no claim changed between the two
- Difficulty score anchor: not yet set (set at first complete submission)
- Score history: 2026-09-22 originality 100, difficulty 100 (first design; probed 3 of 3 solved); 2026-09-23 originality 100 (DISTINCT; nearest brief alias-settle-report, cosine 0.229, shingle 0.000 over 13 documents; nearest ledger mechanism alias-settle-report at cosine 0.18), difficulty 100 (IN BAND; 373 environment lines, 5 editable files, 571 reference lines, 41 cheats, 2 module-form variants)
- Leak audit: nothing. Rows carry only an id and values; the frozen store keeps rows by id and no index over values; no expected output ships; helper names never name owners, dominators, deleters, rounds or bit sets; the shipped audit is a replay of the wrong delete and confirms nothing; tools/onelinecheck.py finds no exact rule at depth 2 for any graded decision
- Expert path: authoring/partial-key-purge/difficulty.toml [plan].expert_path, ten steps from reading the shipped pass to checking the deleter-set audit against the replay
- Originality check: searched MATCH PARTIAL implementations (none implement its actions), MySQL's fifteen-level cascade limit (recursion depth of a row-by-row cascade, not rounds), retained sets and dominator trees (one tree, reachability), bit-set descendant counting (every match enough); nothing plans the task
- Distinctness record score: 2026-09-23, 100/100 DISTINCT; crowded archetype named: garbage-collector retained sets (Languages list), no Databases entry fits
- Nearest already-submitted task: reach-pair-sweep (loss of support propagated through references); separated on mechanism, substrate, graded output, failure mode and interaction

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

Every graded assertion traces to a sentence in the instruction. Walk the tests, the sealed model
and test.sh line by line into authoring/<slug>/trace.md, start it with
`python tools/tracecheck.py <slug> --skeleton`, and keep `python tools/tracecheck.py <slug>` clean.
`preflight.py` errors while any line below is unanswered.

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): authoring/partial-key-purge/trace.md, walked again from the top on 2026-09-23: 5 test functions, 33 hand cases, 5 artifacts, the 180 s clock, the exit-status, output-cap and encoding conditions of tests/worker.py, the standard-library condition, 20 rule rows of tests/seal/model.py, and the fifteen-round limit; three NOT STATED found on the second walk were fixed in the instruction (a row with two cascade references goes when it loses either; what a self-matching merge row does; which references a row removed too deep fails); 0 NOT STATED left; `python tools/tracecheck.py partial-key-purge` clean (2026-09-23)
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 25 wrong readings written as whole solvers in authoring/partial-key-purge/readings.py - the 18 of the first design, re-derived against the new reference, and seven new ones: the probe's winning ownership-tree audit (tree-audit), a merge needing both parents (fork-needs-both, now separated by merge-either), descendant reachability, loops that never break, rounds as a longest path, the limit biting at round fifteen, no limit, and a too-deep row failing only the reference that removed it; every one is ruled out by a quoted sentence and separated by a named hand case (tools/readingcheck.py: 25/25 separated once rounds-longest-path, first reported equivalent, was found to be mis-implemented - it read rounds in removal order and so collapsed into the correct rule - and was rewritten with a topological pass); the survivors that agree with the reference everywhere are the correct implementations kept as variants
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): fractions on the 33 hand scripts and 360 small nonce scripts (authoring/partial-key-purge/shortcuts.py): shipped tree 7/33 and 50/360, constant 0/33 and 3/360, named-only 1/33 and 24/360, refuse-first 0/33 and 0/360, worked example replayed 0/33 and 0/360; container scores in the cheat report below
- Independent implementation behind every tolerance and limit (path, measured headroom): the 180 s clock on the whole graded run: under 1 CPU and 2 GB the reference ran it in 51 s (3.5x headroom), authoring/partial-key-purge/variants/chk (worklist, capped round maps) in 65 s (2.8x) and authoring/partial-key-purge/variants/walk (Kosaraju, bounded forward deletes) in 71 s (2.5x); the per-row replay floor (authoring/partial-key-purge/time_naive.py) is 2,402 s for the three deep scripts on the host. The fifteen-round limit is a rule, validated by the brute force (rounds from their definition), both variants and the model on 480 generated scripts, and fenced on both sides by the hand case depth-limit
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run, mechanically (no fresh session: this session may not spawn one); every printed token of delete, dump and audit lines was put through the four clusters on 2026-09-23; four decisions were open after the redesign and each got a sentence or a case: whether a row with two cascade references goes on either (sentence rewritten: "loses any of its"), what a merge that matches itself does (sentence rewritten about the self-matching reference, hand case merge-self), which references a too-deep row fails (sentence added, hand case depth-both-refs), and whether a refused audit line keeps its counts (hand case audit-names). A last cold read of the finished brief found two more readings a careful solver could split on, both already settled by the rules but not by the words: "stops a cascade at fifteen rounds" could be read as truncating the cascade rather than refusing the delete (reworded: the delete is refused "because the real database refuses a cascade that deep"), and the counts on a refused audit line (now "the counts are still those of every row it would remove and clear if it went ahead"); every other question was answered by a quote recorded in trace.md

## Verifier contract — RE-FROZEN 2026-09-23 (easiness recovery; first frozen 2026-09-22)

Re-frozen after the brute force (authoring/partial-key-purge/brute.py, rounds counted straight
from their definition), the sealed model (tests/seal/model.py), the reference (solution/) and two
correct variants (authoring/partial-key-purge/variants/chk and walk) agreed on every script
checked: 480 generated scripts (40 in each of the twelve small families plus 40 random-schema
fuzz scripts) through all five, the 33 hand scripts through all five (the brute force skips only
chain-1500), and model = reference = both variants on a deep script (72,332 lines). The change
from the first freeze is the contributor's: "make the task substantially harder" (2026-09-23),
after the easiness probe solved the first version 3 of 3. What moved, measured against the 25
answers frozen on 2026-09-22 (authoring/partial-key-purge/build_gt.py --contract-change): 13 hand
answers changed only where an audit line said `held` and now says `refused <name> <id>`, with the
same counts; chain-1500 changed because its deletes are now refused past round 15; no delete or
dump line of any other frozen answer moved.

- Artifacts the agent produces: `/app/db/match.py`, `/app/db/drop.py`, `/app/db/clear.py`,
  `/app/db/hold.py`, `/app/db/audit.py`. Nothing else is collected; the driver `/app/run_db.py`,
  the reader `/app/db/parse.py`, the store `/app/db/rows.py`, the printer `/app/db/say.py` and
  `/app/db/__init__.py` are the verifier's pristine copies. The driver calls
  `drop.delete(store, table, ids)` (returns `("ok", removed, cleared)` or
  `("refused", name, id)`) and `audit.audit(store)` (returns `(table, id, removed, cleared,
  refusal)` per row, refusal `None` or `(name, id)`, in output order). Only the standard library
  is available at grading.
- Script grammar (unchanged; one item per line, blank lines and `#` lines ignored; declarations,
  then rows, then statements):
  - `table <name> <col>...`
  - `key <name> <table> <col>...`
  - `ref <name> <table> <col>... -> <key> <simple|full|partial> <cascade|restrict|noaction|setnull> [<col>...]`
  - `row <table> <id> <value>...` with `-` for null
  - `delete <table> <id>...`, `dump <table>`, `audit`
  Guarantees: names distinct; ids positive and unique per table; the given rows satisfy every key
  (no null key column, no two rows equal on a key) and every reference (not broken; a reference
  that is not inert matches at least one row); a delete names distinct rows present at that
  point. Dropped at this freeze: "no reference names a key of a table that has two or more
  cascade references" - merge revisions are exactly such rows, referenced by later revisions.
- Semantics:
  - Matching as before: inert when all referencing columns are null, and under `simple` when any
    is; broken under `full` when some but not all are; otherwise the row matches every row of
    the key's table equal on its non-null referencing columns. A row can match itself.
  - A row loses a reference when it matched at least one row through it before the statement and
    every row it matched is removed. Matching always uses the values from before the statement.
  - Removed: the named rows and every row that loses any of its cascade references; the smallest
    such set (rows that match only one another keep each other; a reference through which a row
    matches itself never removes it).
  - Rounds: the named rows go in round 0; a row that goes because it lost a cascade reference goes
    one round after the last row it matched through that reference, the earliest such round when
    it lost more than one.
  - Cleared: every row not removed that loses a setnull reference has that reference's listed
    columns (all its columns when none are listed) set to null; clearing never changes the
    removed set; every such row counts as cleared.
  - Refused (nothing changes) when a row, removed or not, loses a restrict reference; when a row
    goes in round 16 or later (it fails every cascade reference it lost); or when, after removal
    and clearing, a remaining row is broken, matches no remaining row through a reference that is
    not inert for it (values after clearing, of both rows), or has a null in a key column.
  - Refusal names the failing key or reference declared first in the script and the smallest id
    of a row failing it.
- Output, one line per item, nothing else:
  - delete: `ok <removed> <cleared>` or `refused <name> <id>`
  - dump: `<table> <id> <value>...` per row, ids ascending, `-` for null (no line for an empty table)
  - audit: `<table> <id> <removed> <cleared> ok` or `<table> <id> <removed> <cleared> refused
    <name> <id>` for every row, tables in declaration order and ids ascending, each line what
    `delete <table> <id>` alone would print, counts included when it would be refused; the store
    is unchanged.
- What is checked: stdout of the pristine driver, one fresh interpreter per script, on every
  graded script equals the expected text exactly. 33 hand scripts (`tests/cases.py`) against
  `tests/seal/gt.json`; a nonce population generated as root before the worker starts
  (`tests/seal/gen.py`: 30 scripts in each of twelve small families - plain, half, loop, hold,
  clear, multi, fork, order, mixed, chain, merge, depth - and 3 `deep` scripts of about 36,000
  rows, most in four merge histories of 6,000-7,000 revisions) against the sealed model. The whole
  graded set runs in one worker under a 180 second wall clock, declared 1 CPU and 2048 MB.
- Tolerances: none; exact text.
- Ground truth, and where it lives: `tests/seal/gt.json` (hand scripts, built by the model and
  checked against the brute force, the reference and both variants); the nonce population is
  generated and answered inside the verifier by `tests/seal/`, chmod 700 before any agent code
  runs.
- Measured at re-freeze (host, Python 3.11, fresh interpreter per deep script): reference 6.1 s,
  chk 9.5 s, walk 12.7 s, model 15.0 s, peak memory about 400-450 MB. Capped container (1 CPU,
  2 GB, Python 3.12), whole graded run: reference 51 s, chk 65 s, walk (see Validation status).
  The per-row replay floor (removal counting only, array-based) is 2,402 s for the three deep
  scripts (authoring/partial-key-purge/time_naive.py, mean removed set 3,267-5,098 rows).

## Decisions and their reasons

Decisions of the easiness recovery (2026-09-23) come first; those of the first design follow,
each marked where the recovery superseded it.

- The guarantee that no reference names a key of a two-cascade table was dropped. The first
  design kept two-cascade rows as leaves precisely so the ownership tree would exist, and noted
  that referencing them "makes the removal structure an AND-OR graph with no tree"; that is now
  the point. The expert path that was said to be missing exists: deleter sets as bit sets, a
  union over cascade references of an intersection over matches, settled over components. It is
  measured: the reference runs a deep script in 6.1 s on the host, and three independent
  implementations agree with it.
- Merges are revisions with a second, merged-from parent (`md mn`, reference `rev_merge`,
  partial cascade), not a separate table: a merge that nothing is based on would be a leaf again.
  The deep family was rebuilt around them: four histories of 6,000-7,000 revisions with side
  branches merged back 3-40 revisions after they fork, merges from earlier histories and from
  short documents (some from a whole document), and the old loops, pairs and guards. 74.8% of the
  rows of a deep store remove a row with two cascade references when deleted alone, which is what
  makes a tree-plus-replay hybrid replay three rows in four.
- The depth limit is fifteen rounds, after MySQL's fifteen-level cascade limit, counted as rounds
  of the set-based delete: a row goes in the round after the last row it matched through the
  first of its cascade references to run out. A delete that would remove a row in round 16 or
  later is refused and each such row fails every cascade reference it lost - one sentence covers
  merges without a tie-break rule. Fifteen keeps the fence reachable by small scripts (the depth
  family's lone deletes run 0 to 40 rounds) and makes deep deletes refuse, so the audit's names
  for chain rows come from the whole removed set.
- The audit prints the refusal the delete would print instead of `held`, keeping the counts:
  the counts carry the column-sum part of the gate and the names carry the minimum over failures.
  Measured against the first freeze, 13 hand answers moved only in that token.
- The shipped `say.py` printer changed with the audit format (`refused <name> <id>` in place of
  `held`), and the shipped wrong `audit.py` returns the new tuple; both are frozen or shipped
  files the agent sees as they are, and the pristine mirror was re-synced.
- The samples were regenerated: `loops.txt` now comes from the merge family (seed chosen for
  merges and loops through merges, with an audit appended); `docs.txt` and `deep.txt` from the
  rebuilt chain and deep families.
- A latent bug in the old authoring readings.py - `reductions()` split scripts on a literal
  backslash-n, so readingcheck's shrinking had never run - was fixed in the rewrite.

First design (2026-09-22):

- Insert and update were designed and dropped before the contract froze (2026-09-22): they
  added end-state checks the delete already needs, one rule (unique keys at statement end)
  whose only interesting case needs a multi-row update, and roughly a thousand characters of
  brief, against a 10000-character cap, for no new interaction.
- Superseded 2026-09-23: rows of a table with two cascade references were never referenced, by
  guarantee, so they were leaves of the ownership tree (see the first decision above).
- Key columns may be cleared, and the end check refuses a null in a key column. That gives
  setnull over an identifying column a defined meaning with one sentence rather than a
  declaration-time prohibition. Re-checking the rows that matched a row whose key was cleared is
  unobservable (the key always fails first in declaration order, because a reference names its
  key after the key is declared) and is kept only for fidelity; the fast audits of both designs
  rely on it, and the brute force, which does re-check, agrees with them everywhere.
- Superseded 2026-09-23: a row that matches itself through its cascade reference was a root of
  the ownership tree. With merges a self-matching row can still go through its other parent, so
  the brief now says only that the self-matching reference never removes it (hand case merge-self).
- Superseded 2026-09-23: the deep family's first two shapes and the 820 s replay floor.
- The clock stays 180 s for the whole graded run, re-measured on the rebuilt images: reference
  51 s, chk 65 s, walk 71 s; replay floor 2,402 s (host).
- The worker never imports agent code and never stages the tree: root stages the pristine tree
  with the five files, root-owned and read-only, before the worker starts, and root writes the
  nonce scripts and their answers (the answers into the chmod 700 seal). The worker streams one
  JSON line per script, so a run cut by the clock still grades its hand cases individually.
- Boilerplate (both Dockerfiles, reap.py) was rewritten in this task's own terms after simcheck
  measured them at 0.99-1.00 against retained bundles; on 2026-09-23 they measure 0.59-0.72, below
  the 0.75 line, and simcheck finds nothing conceptual.
- textcheck against the retained briefs, 2026-09-23: no finding against 8 of 12 (alias-settle-report,
  expert-defer-shed, focus-return-point, guard-mark-unwind, publish-settle-order,
  scope-hold-release, share-register-screen, token-seam-emit); burstiness 0.816 is under
  note-carry-forward's 0.915 and the two outliers' (1.009, 1.112), and the type-token ratio 0.296
  is under two references', because a spec has to repeat its nouns. The first rewrite of the
  brief had fallen to 5 of 12 (burstiness 0.787); splitting two sentences and restoring one long
  rules paragraph brought it back without changing a rule.

## Validation status

Re-run 2026-09-23 on the rebuilt bundle.

| Check | Status | Notes |
|---|---|---|
| Agent image builds | pass | Docker 29.3.1; the test image builds with the same local accommodation as before (authoring/partial-key-purge/local_trial.py drops the apt step because deb.debian.org answers 403 to this sandbox); the shipped Dockerfiles are unchanged |
| No answer leaked into agent image | pass | tools/imagecheck.py assembles the image (14 files) and runs the four samples with the reference; tools/extraneouscheck.py clean |
| `harbor run -a oracle` = 1 | pass (docker; harbor blocked) | local_trial.py on the rebuilt images, --cpus 1 --memory 2g: reward 1, 37 passed; time_container.sh: worker 51 s for the whole graded set; `harbor run` itself is still stopped by the 403 at the Debian mirror (see Harbor) |
| `harbor run -a nop` = 0 | pass (docker) | reward 0, 27 failed / 10 passed (the 7 hand cases the shipped engine gets right plus the 3 sealed-side checks) |
| Cheats all score 0 | CHEAT_STATUS | CHEAT_NOTES |
| Correct variants score 1 | pass | variants/chk and variants/walk through time_container.sh: reward 1 each; whole-run worker time 65 s and 71 s |
| Model = reference = variants = brute force | pass | 480 generated scripts through all five (agree.py 40), 33 hand scripts (brute skips chain-1500), deep scripts model = reference = both variants; deterministic across three hash seeds |
| `tracecheck.py` (every graded assertion traced) | pass | clean |
| `readingcheck.py` | pass | 25/25 readings separated, 0 BLIND, 0 equivalent (after rounds-longest-path was corrected) |
| `onelinecheck.py` | pass | no graded decision reproduced by a rule of depth 2 or less |
| `difficultycheck.py` / `originalitycheck.py` | pass | 100/100 IN BAND; 100/100 DISTINCT |
| `preflight.py` | pass with warnings | no errors; the 12 unused-function warnings are the same false positives as before (attribute calls such as `parse.read`, `store.get`, `match.ups`), plus the notice that the verifier runs agent code, which the isolation probes cover |
| hintcheck, structcheck, deadfieldcheck, catcheck, solvecheck, simcheck | pass | all clean; simcheck's boilerplate figures 0.59-0.72 stay under 0.75 and nothing conceptual |
| `harbor check` rubric | not run | no provider key here; the manual criterion-by-criterion review is recorded below |

## Cheat report (Stage 6), second full run on the final images

Run 2026-09-22 with `python -u authoring/partial-key-purge/cheat_report.py` after forgecheck's
own run had reported `34/34 cheats scored 0 for the intended reason`; each run draws a fresh
nonce population. Every cheat scored 0 and each was caught by the layer named for it:

| Cheat | Reward | Layer that caught it |
|---|---|---|
| `cheat-audit-retained-set.sh` | 0 | hand audit-loop fails |
| `cheat-audit-sums-children.sh` | 0 | hand audit-diamond fails |
| `cheat-cleared-only-if-changed.sh` | 0 | hand setnull-already-null fails |
| `cheat-constant.sh` | 0 | 25 hand cases fail |
| `cheat-end-check-before-clearing.sh` | 0 | hand setnull-all fails |
| `cheat-example-replayed.sh` | 0 | 25 hand cases fail |
| `cheat-forge-from-truth.sh` | 0 | 0 hand cases fail (all carried), nonce population fails it |
| `cheat-fork-needs-both.sh` | 0 | hand fork-either fails |
| `cheat-full-half-null-accepted.sh` | 0 | hand full-broken-by-clear fails |
| `cheat-held-counts-zero.sh` | 0 | hand cascade-tree fails |
| `cheat-key-null-allowed.sh` | 0 | hand setnull-key-column fails |
| `cheat-name-by-row-first.sh` | 0 | hand order-decl fails |
| `cheat-named-not-counted.sh` | 0 | hand audit-diamond fails |
| `cheat-named-only.sh` | 0 | 24 hand cases fail |
| `cheat-no-self-match.sh` | 0 | hand self-restrict fails |
| `cheat-noaction-as-restrict.sh` | 0 | hand noaction-removed-anyway fails |
| `cheat-probe-answer-key.sh` | 0 | 261 denials, 0 successes |
| `cheat-probe-crash-worker.sh` | 0 | worker exit 137 after the kill |
| `cheat-probe-hijack-driver.sh` | 0 | 21 hand cases fail |
| `cheat-probe-late-reward.sh` | 0 | lingered True, reaped 4 |
| `cheat-probe-malformed-report.sh` | 0 | grader refused the corrupted report |
| `cheat-probe-malformed.sh` | 0 | 25 hand cases fail |
| `cheat-probe-plant-verdict.sh` | 0 | 174 denials, 0 successes |
| `cheat-probe-privilege.sh` | 0 | 264 denials, 0 successes |
| `cheat-probe-rewrite-frozen.sh` | 0 | 261 denials, 0 successes |
| `cheat-probe-shrink-set.sh` | 0 | 870 denials, 0 successes |
| `cheat-reachability-frees-loops.sh` | 0 | hand audit-loop fails |
| `cheat-refuse-first.sh` | 0 | 25 hand cases fail |
| `cheat-replay-audit.sh` | 0 | worker exit 124 (wall clock), 0 hand cases fail |
| `cheat-restrict-as-noaction.sh` | 0 | hand restrict-removed-anyway fails |
| `cheat-restrict-only-by-losing.sh` | 0 | hand restrict-broken-by-clear fails |
| `cheat-row-by-row-clear-feeds-back.sh` | 0 | hand clear-no-feedback fails |
| `cheat-setnull-clears-all.sh` | 0 | hand full-broken-by-clear fails |
| `cheat-simple-for-all.sh` | 0 | hand audit-diamond fails |

## Cold self-attack (Stage 7) - author-run, contaminated

2026-09-23, on the rebuilt bundle. The author designed the new rules and wrote the model, so
this is not a cold solve and is not reported as one (CLAUDE.md: a self-probe reported as cold by
a contaminated author is worse than none). What it can still measure is whether the brief alone
fixes the semantics, and where each plan the brief invites fails.

- Semantics from the brief: authoring/partial-key-purge/brute.py was extended from the brief's
  sentences (rounds counted as the brief defines them, the limit as the brief states it, the
  audit line as the brief prints it) before the new model was written, and agrees with the model, the
  reference and both variants on 480 generated scripts and the 33 hand scripts. No graded rule
  needed the model to settle it.
- The plans the brief invites, in the order a solver meets them, each measured:
  1. replay one delete per row: right everywhere, 2,402 s for the deep scripts against 180 s
     (time_naive.py; `cheat-replay-audit.sh` is stopped by the clock with every hand case
     passing);
  2. the probe's plan, an ownership tree with a replay for what it cannot express: wrong at every
     merge (`cheat-tree-audit.sh` fails merge-either), and its replay would cover 74.8% of the
     rows of a deep store;
  3. descendants in the merge DAG: wrong wherever a row matches several revisions
     (`cheat-descendant-reach.sh` fails merge-wild-side);
  4. deleter sets without rounds, then rounds as the longest chain: wrong where a merge shortens
     a cascade (`cheat-rounds-longest-path.sh` fails depth-merge-shortcut); a limit off by one or
     missing fails depth-limit; a too-deep merge failing one reference fails depth-both-refs;
  5. refusals from signed marks: impossible, a name is a minimum; `cheat-held-counts-zero.sh`
     and the naming readings fail audit-names, order-decl and depth-both-refs.
- Rules confirmed independently: every delete rule can be confirmed against a brute force on
  small stores, as before. The audit's structure cannot: the shapes that separate the tree, the
  descendant count and the longest-path round from the correct answer need merges and
  several-match rows in the same store, and at the deep scale only the solver's own fast path can
  run.
- Honest estimate: the design aims at 1-3 solves of 8. The risk in the easy direction is an agent
  that goes straight to per-row bit sets and gets rounds and names right with its brute force;
  the risk in the hard direction is the volume of rules the audit has to agree with. Estimated
  2 of 8.

## Manual quality review (docs/QUALITY-REVIEW.md), 2026-09-23 (rebuilt bundle)

- Instruction and verifier agree both ways: authoring/partial-key-purge/trace.md walks every test
  function, all 33 hand cases, every worker condition and every model rule to a quoted sentence
  (tracecheck clean); every rule in instruction.md has a hand case or a generated family that
  exercises it, and the new rules each have both sides fenced (depth-limit, merge-either with
  merge-wild-side, or-loop-broken with mutual-keep, depth-merge-shortcut).
- Collected files named with absolute paths (instruction.md paragraph 2); the audit tuple and the
  refusal line are fixed by the pristine printer (environment/app_src/db/say.py), which the brief
  says is put back as shipped, and the brief states both output lines word for word.
- Boundaries: the named rows are round 0; round 16 or later is refused and round 15 is not (both
  graded by depth-limit); a row that lost several cascade references takes the earliest round;
  the too-deep row fails every cascade reference it lost; refusal ties break by declaration
  order then smallest id; removed counts include the named rows; cleared counts rows once each,
  even when already null; refused audit lines keep their counts; an empty table dumps nothing.
  Each has its sentence and a hand case.
- Counts re-derived from the code after the last change: four sample scripts; about 36,000 rows
  per deep store (deep.txt 36,707, generated 35,759-36,457), most in four histories of
  6,000-7,000 revisions (generator range; deep.txt 6,577-6,926); three deep scripts; 360 small
  nonce scripts plus 33 hand scripts ("nearly four hundred small ones"); 180 s; fifteen rounds;
  the worked example's third line `ok 2 0` shipped and `ok 3 0` correct (tiny.txt unchanged).
- Prose: textcheck clean against 8 of 12 retained briefs, findings recorded under Decisions; the
  one run of three sentences opening with "A" found on re-reading was broken up without changing
  a rule; each requirement stated once.
- Verifier rigor: outputs of real runs compared with sealed answers; test_outputs.py opens with
  the re-frozen contract, numbered 1-10, and sections its tests; the nonce population and the
  model are deterministic across hash seeds (three seeds, identical digest over a population
  with a deep script's answers); the one clock is the stated execution limit.
- Environment hygiene: environment/Dockerfile copies app_src only; test dependencies are baked in
  tests/Dockerfile with == pins; no apt pins; every path named in the brief exists
  (tools/imagecheck.py ran the four samples in the assembled image: deep.txt 73,451 lines).
- Solution: solve.sh copies the five reference modules from beside itself and runs two samples;
  nothing is echoed; tools/solvecheck.py clean.
- Anti-cheating: no answer in the image (imagecheck, extraneouscheck clean); exact comparison; 41
  cheats including a gt.json forgery, a corrupted report and the reward-tamper probes (results
  under Cheat report).
- Metadata: Software / Databases; five specific tags, `dominator-trees` replaced by
  `cascade-depth-limit` because the tree is no longer the method; the difficulty explanation
  names the plans that fail (the engine every solver has used, the ownership tree, descendant
  counting, the replay and the hybrid) and the legacy-register naming as a choice; the solution
  and verification explanations describe the rebuilt bundle and its measured numbers (51 s, 65 s,
  71 s, 2,400 s, 74.8%, 33 hand scripts, 363 generated, 25 readings); relevant_experience is
  grounded in this rebuild; 12 expert hours matches the design record.

## Harbor

`harbor run -p tasks/partial-key-purge -a oracle -e docker -o <scratch>` (harbor 0.23.0) built the
agent image and ran the oracle agent on 2026-09-22, then failed building the verifier image:
`apt-get update` got `403 Forbidden` from the Debian mirror (egress policy of this sandbox). It
was not retried on 2026-09-23 - an organisation policy denial is reported, not retried - and the
Dockerfiles are unchanged since. The equivalent two-container flow (tools/docker_trial.py through
authoring/partial-key-purge/local_trial.py, which drops only the apt step locally) is the
container evidence recorded above.

## Infrastructure notes (Stage 0)

- Docker: the daemon was not running; started with `dockerd` in the background. Pulling
  `python:3.12-slim` from Docker Hub failed with 403 on the blob CDN
  (`production.cloudfront.docker.com`, egress policy); not retried. Pulled
  `mirror.gcr.io/library/python:3.12-slim` and tagged it `python:3.12-slim` locally.
- Harbor: absent; installed with `uv tool install harbor` (0.23.0).

## Open questions and next steps

- The easiness recovery's exit gate is the external probe: submit tasks/partial-key-purge.zip
  (rebuilt 2026-09-23) and record the realized result in the recovery entry and in the
  `partial-key-purge` ledger entry of authoring/submissions.toml. If the probe solves it again,
  RAISE-DIFFICULTY.md runs again from section 1 with the new trajectories; the first thing to
  look at is whether agents went straight to per-row bit sets and what, if anything, in the brief
  or the samples led them there.
- Similarity: this is a revision of the same task under the same slug, so its brief is close to
  the first submission's (cosine 0.943, shingle 0.693 by tools/originalitycheck.py --nearest
  against the f31b80c brief). Against every other brief in the checkout and 54 historical briefs
  from git history it is distinct (nearest note-carry-forward at cosine 0.192, shingle 0.000;
  originality 100). It has to go in as a revision of partial-key-purge; submitted as a new task
  it would collide with its own first version.
- If the probe returns 0 of 8, the likely causes to look at first are the volume of rules the
  audit has to agree with and the time budget of the bit-set computation in the container; the
  reference's 51 s and the variants' 65-71 s leave room, and no rule depends on a hidden fact.
- Not run here, and why: a real `harbor run` (the verifier image build is refused by this
  sandbox's egress policy at the Debian mirror), `harbor check` (no provider key), a cold solve
  by a fresh session (this session may not start one), and the platform's easiness probe. The
  estimate of 2 solves in 8 is a design estimate, not a measurement.
