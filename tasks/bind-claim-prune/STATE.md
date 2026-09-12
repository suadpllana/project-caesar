# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - Pre-flight and packaging`

## Assistant's assigned role

Toolchain engineer on the bind stage of a build system: static archives, section groups, symbol
resolution and link-time section removal. Comfortable with why link order changes an output,
with what a duplicate group costs, and with the difference between an engine that is correct on
a hundred objects and one that is affordable on sixty thousand.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task. Nothing is vendored; the whole tree is authored here.
- Task shape chosen: not applicable (no repository), so neither authored-on-top nor ablation.
- Contributor's relationship to it: not applicable.
- License: not applicable.
- Pinned commit: not applicable.
- Load-bearing couplings: authored, listed under "Why it is hard" with the file paths.
- Identifier degradation: names are authored in a legacy register from the start (`bind/`,
  `hold`, `want`, `pull`, `prune`, `place`, `wire`, `gives`, `uses`, `spare`, `key`); no
  conversion table is needed because no upstream names exist.
- Proper-noun sweep: no product, project or vendor name appears anywhere in the tree. The
  format is authored, not a real object format, and no real tool is named.
- Upstream-diff check: not applicable - there is no upstream to diff against.

## Task summary

`/app` is the bind stage of a build tool. Units carry parts; a part has a size, an optional
claim key, the names it gives and the names it uses. Bundles are ordered lists of units that
are scanned on demand. A program in the frozen op language declares units and bundles, gives an
input list, and asks questions; `/app/run_bind.py` runs it and prints a line for each thing that
happens. The shipped engine is wrong in six places across the six files the agent may change.
The work is to make it settle claims, extraction, binding, placement and the prune the way the
brief states, and to do it inside a stated time limit on inputs whose size rules out three
exactly-correct methods.

## Why it is hard

The rules are all in the brief. What is not in the brief is that the engine has to hold two
different kinds of thing at once: a take list that only ever grows, and a table of kept parts
that loses entries. Every structure the rules seem to ask for answers one and not the other.

- Expert time estimate: 10 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer): the table has to lose
  entries while the take list only ever grows, and no single structure answers both. The first
  plan is a symbol table plus a claim-on-first rule plus a member scan, and it is coherent,
  matches every published account of the domain, and is wrong in a way that is invisible until
  a directly named unit displaces a claim a bundle member already held. That rule takes gives
  and uses back out of the table, which puts a name back into the wanted set, which changes
  what the next bundle on the input list gives up. The repair is not a case: the table has to
  support removal while the take log does not, the binding of a name has to survive its first
  giver leaving, and
  the wanted set has to be carried as counts rather than flags because it now moves in both
  directions. An engine that settles the final inputs to a fixed point - the natural repair once
  removal is seen - prints a shorter take list and is wrong the other way.
- Tactics making that true (docs/DIFFICULTY.md): A1, A2, B2, C1, C2, C3, C4 - and B1 is not
  claimed, because the tree is small enough to read in one sitting. A1 (the retrievable rules -
  first claim wins, a definition settles a name, extraction never runs backwards - are all
  inverted and stated),
  A2 (retraction, monotonicity and fixed points are never named; the brief says only what a
  dropped part takes with it), B2 (nine rules hold simultaneously and each changes what another
  means), C1 (both sides of every fence are graded), C2 (nothing is printed when a part is
  dropped or a key changes hands, so a wrong claim shows only in a later query), C3 (three
  exactly-correct methods are measured against the stated limit at the stated scale), C4 (exact
  traces, all or nothing, over enumerated corners plus programs generated from a seed drawn
  after the agent's container is gone).
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan
  is wrong in three places at once. It is one symbol table of name to current definition, a
  claim set of keys already held, a member loop per bundle restarted after each take, then a
  reachability walk from the roots, then spares. It holds one give per name, so it cannot say what
  a name falls back to when its first giver is displaced. It treats the claim set as write-once,
  so displacement is unrepresentable. And it recomputes the wanted set by rescanning, which is
  correct and does not fit the limit. My second plan - settle the surviving inputs to a fixed
  point - is also wrong, because a member already taken is never given back and its parts stay
  kept, so the answer is not a function of the inputs that survive.
- Estimated solves out of 8: 2 (range 1-4)
- Difficulty record score (tools/difficultycheck.py on authoring/bind-claim-prune/difficulty.toml,
  before Stage 2): 100/100 on the first attempt, 2026-09-12, no hard stop, band 95-100. The only
  warning is `gate.measured` - the three naive families are timed before the brief quotes a
  number, and the record is updated with the measurement.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not yet
  submitted.
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-12, 100, first
  complete record.
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning?
  - Claims and displacement: the declaration store holds a part's size, key, gives and uses and
    nothing derived. There is no kept flag, no claim table, no holder record, and no line is
    printed when a part is dropped or a key changes hands.
  - Wantedness: no query reports the wanted set, and no line is printed when a name goes back to
    wanted. It is observable only through which member a bundle takes next.
  - Extraction order: the take line carries the bundle and the unit and no reason. The order is
    observable, which is deliberate - it is a graded decision, not a hint, and the agent has
    nothing correct to compare it against.
  - The prune: the image line is one count of surviving parts and one of bytes for the whole
    link, so no single part's fate is separable from it.
  - Shipped programs: `/app/progs` holds four programs that exercise the op language and the one
    wrong line the brief names. None contains a displacement, a name going back to wanted, or a
    key claimed across a bundle boundary.
  - Answer material: the sealed model, the frozen answers and the pristine tree exist only in
    the verifier image, in a directory locked to root before any submitted code runs.
- Expert path, described step by step:
  1. run the shipped engine on the small program the brief names and reproduce its wrong line;
  2. read the frozen store and see that gives and uses hang off parts while spares hang off
     units, so a part is the unit of everything the table holds;
  3. take the displacement rule seriously: a claim has to record which part holds a key and
     whether that part came from the input list or from a bundle;
  4. make the name table hold the strong gives of a name in arrival order, so a displacement
     rebinds to the next one instead of leaving the name undefined;
  5. separate the take log, which only grows, from the kept-part state, which loses entries, and
     drive both from one forward pass over the input list;
  6. carry the wanted set as counts of strong uses and spares against strong gives, because it
     now moves in both directions;
  7. index each bundle once by name to the members giving it in member order, and take the
     smallest live member index rather than the oldest wanted name;
  8. run the two large programs and time the result against the stated limit.
- Originality check: searched 2026-09-12. The conventions are public and well written up -
  platform linker guides on group sections, the C++ ABI proposal that defines a group signature,
  blog series on archive extraction and link-time section removal, and a recent parallel-linker
  paper. Every one of them states that the first copy of a duplicate group is the one retained
  and that it is never revisited, and none describes a copy being displaced or a definition
  being taken back out of the table. No public exercise, benchmark task or repository was found
  that asks for this rule set. The retrievable material is therefore a liability rather than a
  plan, which is the A1 the design rests on.

## Verifier contract - FROZEN after Stage 2

Once agreed, this does not change without the contributor's explicit approval.
Frozen 2026-09-12.

- Artifacts the agent produces: the six files it may change, and nothing else -
  `/app/bind/hold.py`, `/app/bind/want.py`, `/app/bind/pull.py`, `/app/bind/place.py`,
  `/app/bind/prune.py`, `/app/bind/wire.py`.
- What is checked: the verifier lays those six over its own pristine copy of the tree, runs
  every graded program through the frozen reader, and compares the printed trace line for line.
  Exact equality, all or nothing, over every program.
- Tolerances: none. Every line of every program matches or the reward is 0.
- Ground truth, and where it lives: enumerated programs are checked against `tests/seal/gt.json`,
  frozen before the grading file was written; generated programs are checked against
  `tests/seal/model.py`, an independently written engine. The grader asserts the model still
  reproduces `gt.json` exactly before it grades anything. Both live in a root-only directory in
  the verifier image.

### The op language (frozen)

Declaration, then one input list, then queries. One op per line, words separated by spaces.

```
u <unit>                 begin a unit
p <size> <key>           add a part to the unit being declared; key `-` for none
g <name> <s|w>           the part just added gives <name>, strongly or weakly
r <name> <s|w>           the part just added uses <name>, strongly or weakly
t <name> <size>          the unit being declared spares <name> at <size>
b <bundle> <u> <u> ...   declare a bundle over units already declared, in that order
bulk <bundle> <shape> <n> <arg>   synthesise a bundle of n members; frozen shapes only
root <name>              <name> is a root
hold <unit> <part>       that part of that unit is a root
link <item> ...          the input list; an item is a unit, a bundle, or ( b b ... )
at <name>                query
img                      query
```

### The rules the verifier grades

1. Loading a unit walks its parts in order. A part whose claim key is already held is dropped:
   neither its gives nor its uses enter. A part with no key is always kept.
2. A part of a unit named in the input list displaces a part from a bundle member holding the
   same key, whenever it arrives. The displaced part is dropped and the gives and uses it
   brought leave the table. A key held by a unit from the input list is never displaced.
3. A name is wanted when a kept part uses it strongly or a loaded unit spares it, and no kept
   part gives it strongly. A weak give never settles a name. A weak use never makes one wanted.
4. A bundle is scanned from its first member. The first member that strongly gives a wanted name
   is taken, `take <bundle> <unit>` is printed, and the scan starts again at the first member. A
   member is taken at most once. The bundle is done when a pass takes nothing.
5. A bracketed group is scanned bundle by bundle and again from its first bundle whenever a pass
   over it took anything.
6. A taken member is never given back, and its parts stay kept and keep holding their keys, even
   when the use that pulled it later leaves under rule 2.
7. The strong gives of a name are held in arrival order and the first of them binds. A strong
   give arriving at a name that already has one prints `dup <name> <unit>` and changes nothing.
   When the first leaves under rule 2, the next in arrival order binds, silently.
8. A name with no strong give binds to the first weak give in arrival order.
9. A name that no kept part gives and that some unit spares is placed at the largest size spared
   for it, against the first unit in load order that spared it at that size.
10. After the input list is settled the prune keeps the parts the roots reach through strong
    uses; weak uses reach nothing. A placed name is reached like a part. Everything unreached is
    out of the image, and a name whose part is out of the image binds to nothing.
11. `at <name>` prints `at <name> <unit> <part>`, or `at <name> spare <unit> <size>` for a
    placed name, or `at <name> none`.
12. `img` prints `img <parts> <bytes>` over what survived the prune.

Nothing else is printed.

## Decisions and their reasons

- The six editable files split the graded work so that no file holds two unrelated decisions and
  none is a one-line repair: `hold.py` keeps parts and holds keys (rules 1, 2, 6), `want.py` is
  the name table and the wanted set (3, 7, 8), `pull.py` is extraction (4, 5), `place.py` is
  placement (9), `prune.py` is reachability and the image (10, 12), `wire.py` drives the input
  list and answers the queries (11, and the order the phases run in).
- The reader, the declaration store, the `bulk` synthesiser and the trace writer are frozen and
  are the verifier's own copy, so the population cannot be shrunk and the op language cannot be
  redefined.
- The scale families are carried by `bulk`, so a sixty-thousand-member bundle is four lines of
  program text rather than three hundred thousand, and parsing is not what is being measured.

## Measurements

All timings on this host, one CPU's worth of work, python 3.11. The limit in the brief is 60
seconds for the whole graded set, enforced as the worker's wall clock.

| what | wide (60000 members, every other taken) | deep (60000 members, all taken) |
|---|---|---|
| reference | 0.53 s, 112 MB | 0.84 s, 126 MB |
| member scan restarted after every take | 251.9 s | 96.8 s |
| wanted set re-read off the kept parts | 77.7 s | 315.8 s |
| reachability asked once per part | 264.3 s | over 400 s, killed |

The reference settles the whole graded set - 30 enumerated programs, 450 generated small ones
and 3 of each large one, 486 in all - in 4.8 seconds. All three naive families are exactly
correct: each reproduces the reference's trace on every program it finishes, and each is a
cheat that scores 0 on the clock alone.

Reference against the sealed model, written apart from it: 5400 generated programs across the
ten small families, 0 disagreements. The 30 enumerated answers in `gt.json` are reproduced by
both.

Wrong readings (`authoring/bind-claim-prune/readings.py`, 20 whole engines): every one is
separated by an enumerated case named for it, and each moves between 2.3 and 63.7 per cent of a
300-program generated population. `tools/readingcheck.py` reports 20 separated, 0 blind, 0
equivalent.

Answer shape (`tools/onelinecheck.py` over `authoring/bind-claim-prune/decisions.py`): of the
four graded quantities, three have no exact rule at depth two over the features the tree
exposes - whether a part is kept, whether a part is in the image, and what a name stands on.
The fourth, which member a bundle gives up, is the stated rule and is short; the execution
limit is what makes computing it cheaply the work.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run | Docker Hub's blob CDN is denied by this session's egress policy (403 on production.cloudfront.docker.com), so no base image can be pulled and neither image can be built here |
| Image contents and COPY lines | pass | `tools/imagecheck.py`: 15 files, workdir /app, reference runs all four shipped programs |
| No answer leaked into agent image | pass | `extraneouscheck` clean; the model, the frozen answers and the pristine tree exist only under `tests/` |
| `harbor run -a oracle` = 1 | pass, host emulation | harbor is not installed and Docker cannot pull; `authoring/bind-claim-prune/host_trial.py oracle` runs `tests/test.sh` verbatim as root with the real privilege drop - reward 1, 33 tests passed |
| `harbor run -a nop` = 0 | pass, host emulation | reward 0, 17 failed |
| Cheats all score 0 | pass, host emulation | 33 of 33 score 0 and each trips the layer it was written for (`cheat_report.py`, 0 findings); `forgecheck` confirms the answer-key carrier |
| Correct variants score 1 | pass, host emulation | 2 of 2: `slotrec` (one record per name, heap-driven extraction, breadth-first prune) and `flat` (whole engine in `wire.py`, the other five files left as shipped) |
| `preflight.py` | pass | no errors, 15 warnings, all of the same class the retained bundles carry |
| `harbor check` rubric | not run | needs an API key, and harbor is not installed |

## Stage 7 re-attack, 2026-09-12

Read cold, with the built tree in front of me: my first plan is still not the correct one. The
claim table is write-once in it, the name table has one give per name, and the wanted set is a
flag - all three are right until a unit off the input list takes a key back, which the brief
states and which no ordinary program shows. The second finding still forces a replan rather
than a patch: once removal is in, the obvious repair is to settle the surviving inputs, and
that prints a shorter take list because a take is never unsaid.

What the build did not flatten: the twelve decisions are all still graded, the tree is 369
lines against a retained band of 229 to 544, the reference is 326 lines, and the instruction
states rules rather than structures. What I would flag to a reviewer: the brief is a complete
specification, as this repository's house style requires, so a careful agent forms most of the
correct plan from it. The difficulty rests on the conjunction of twelve rules with no feedback
of any kind - no line is printed when a part is dropped, a key changes hands or a name goes
back to wanted - and on a scale boundary that kills three exactly-correct methods. That is the
shape of `focus-return-point`, which passed, rather than of a task with a hidden rule.

Estimated solves after the build: **2** (range 1-4), unchanged from the design.

## The cold self-attack: not run, and why

`NEW-TASK-PROMPT.md` asks for a cold solve of the agent-visible bundle. It is recorded here as
not run rather than as passed. The order of this build was brief, then both engines, then the
population, so by the time a scratch copy could be made I had written every rule twice and knew
each structure the design forces; a cold solve by this author measures memory, not difficulty,
and a self-probe reported as passed by a contaminated author is worse than none. The same
position was taken on `reach-pair-sweep`.

What stands in its place is measured rather than asserted: twenty whole wrong engines, each
separated by an enumerated case and each moving between 2.3 and 63.7 per cent of a generated
population; three exactly-correct engines that lose on the clock alone; no oracle anywhere in
the agent's tree, so nothing the agent can run tells it whether a decision is right; and three
of the four graded quantities with no exact rule at depth two over the fields the tree exposes.
The external easiness probe is the authority on this task.

## Defects found and fixed during the build

- The difficulty record and the state claimed a displacement re-enters a bundle that has already
  finished. It does not: the input list is walked once, and only bundles after the displacing
  unit see the name go back to wanted. Both files were corrected and `shift-earlier` was added as
  the enumerated case that fences it.
- The first population left four readings moving nothing: a group never needed a second pass, a
  spare never made a name wanted, no take ever wanted a name an earlier member of the same bundle
  gives, and spare sizes never tied. The families were reshaped - units planted on keys a member
  actually claimed, members reaching backwards, spares on names bundles give and sizes drawn from
  a short list - and every reading now moves the population.
- Two readings were caught by no enumerated case. `shift-earlier` and `shift-use-gone` were
  written for them.
- The probe cheats were first built on the reference, so six of them scored 1: the attack was
  refused and the engine underneath solved the task anyway. They are built on the shipped engine
  now, where a 1 can only mean the tamper landed.
- The forgery reproduced nothing: it returned a sentinel the frozen writer could not format, and
  its key collided on the two programs that differ only in their input list. It now parses its
  canned line back into what the writer expects and keys on the input list too, and
  `cheat_report.py` asserts that it passes every enumerated program rather than only that it
  scores 0.
- `cheat_report.py` did not take the host trial's lock, and `forgecheck.py` runs it, so two
  trials shared `/app` and `/tests` and produced a report belonging to neither run. It takes the
  lock now.
- A patch applied through a shell heredoc wrote `newline="\\n"` into Python, and `open('w')`
  truncated `emit.py` to zero bytes before raising. Rewritten in full through the editor, which
  is the rule in CLAUDE.md that this session proved again.

## Open questions and next steps

- Container evidence. Every gate above that says "host emulation" needs a real two-image run
  (`python tools/docker_trial.py bind-claim-prune --all`) on a machine whose egress policy allows
  Docker Hub. The host emulation runs `tests/test.sh` verbatim, as root, with the same privilege
  drop, reward lock and reap, but it is not a container.
