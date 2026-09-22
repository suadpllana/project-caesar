# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - Pre-flight and packaging` done on 2026-09-22, on host emulation only: no container
has been built, because this session's egress policy refuses Docker Hub's blob CDN (see
Validation status). Packaged as `tasks/glob-route-hide.zip`; ledger entry added with
`verdict = "pending"`. Not submitted from this session.

## Assistant's assigned role

You are a compiler engineer who owns the name-resolution pass of a module language's front end:
the part that decides what every name in a module tree denotes once imports, globs, re-exports,
visibility and build-flag gating have all had their say. You have debugged glob imports that a
private helper silently hid from downstream crates, visibility that narrowed through a re-export
nobody meant to be private, and resolvers that answered differently depending on the order they
visited a cycle of re-exports. You know that the textbook symbol-table-per-module resolver is
right for small programs and wrong or unaffordable in the places this task grades.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task, no third-party code vendored
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): not applicable, no repository
- Contributor's relationship to it (maintainer / contributor / production user, how long): not applicable
- License, and why vendoring it is permitted: not applicable, nothing vendored
- Pinned commit vendored into environment/app_src/ (.git stripped): not applicable
- Load-bearing couplings found during research (file paths): not applicable
- Identifier degradation done? Conversion table lives at solution/ (never in environment/): the
  tree is written here in the legacy register directly (`fe/`, `rd`, `vis`, `own`, `fix`, `say`),
  and no name misdescribes what it holds
- Proper-noun sweep done? No language, compiler, project or company name appears in the
  agent-facing tree; module, item, import and glob are the ordinary vocabulary of the work
- Upstream-diff check: there is no upstream to diff against

## Task summary

`/app` is the name-resolution pass of a compiler for a small module language. A program is a text
file: a flag line, then modules named by dotted paths, each holding item lines, explicit imports
(optionally renamed), glob imports, `pub` marks, flag conditions and `ref` lines. The resolver
prints one line per reference: the item it denotes, or `unresolved`, `broken`, or `ambiguous`
followed by every candidate in declaration order. The shipped resolver is the textbook one - a
symbol table per module, public names only, memoized recursion, a failed import falling back to
the globs - and the agent repairs the five resolution files under `/app/fe` so every program's
output matches the stated rules, including module trees of about four thousand modules inside a
60 second limit.

## Why it is hard

The first plan is the textbook resolver and it is wrong twice: what a module offers depends on who
reads it, and the graded trees make every per-module or per-name structure unaffordable.

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): because the memorised resolver keeps one public table per module and a visibility per item, while here a glob gives each reader exactly the candidates that reader can see, every import narrows what it passes on to who can see that import, the widest route decides, and a module's own binding of a name hides every glob candidate for it from every reader - so the table depends on the reader and is only known at the fixed point; and once that is right, the graded trees are one cycle of globs in which every module holds every name, so the per-name structure the corrected plan uses is quadratic and has to be replaced by one that moves all names at once while keeping each own binding's cut.
- Tactics making that true (prong A poison, prong B withholding, prong C late failure): A1, A2, B2, C1, C3 and C4. A1 the shipped resolver and the retrievable Rust prototype both treat visibility as an item property and a failed import as a fallthrough, which is right for most programs and wrong in the graded corners; A2 narrowing, widening, hiding and the least fixed point are stated as what a module has under a name and never named; B2 seven rules hold at once and each changes what the others must keep; C1 descendants must see private bindings and outsiders must not, unbound names must resolve through globs and broken own bindings must hide them; C3 one-cycle trees make exact per-module and per-name resolvers infeasible; C4 every reference line matches exactly over a population generated after the agent is gone.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan was a table per module filled from item lines, then explicit imports, then globs over each source's public names until nothing changed, with ambiguity when two globs disagree. It is wrong at the first private line: a module nested inside the source receives the source's private bindings through a glob, so the table depends on the reader. My second plan - a fixed point over (module, name) pairs carrying a visibility per candidate - is semantically right only if visibility narrows at every hop, widens across routes and is re-propagated when it widens, and if own bindings hide by their lines alone; and even then it is quadratic on the tree programs: the prototype took 26.6 s on one 1000-module tree and was killed for memory at 4000, against 0.05 s and 0.52 s for bitsets over bindings.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 2 (range 1 to 4)
- Difficulty record score (tools/difficultycheck.py on authoring/<slug>/difficulty.toml, before Stage 2; every attempt's score and what changed, until it reaches the band in docs/DIFFICULTY-SCORE.md): attempt 1 on 2026-09-22 scored 100/100, in band, no hard stop; the one warning was the unmeasured gate, measured the same day on the prototype (numbers above) before the contract froze. Stage 7 re-run on the built tree, 2026-09-22: 100/100, measured 233 environment Python lines, 5 editable files, 276 reference lines, 48 cheats (34 semantic) and 2 variants. The drift from the planned 320 / 5 / 260 is inside the checker's one-third tolerance, and the environment is the one that moved: it lost the frozen depth helper `fe/tree.py` and the reader's unread `at` field at Stage 5. 233 is inside the retained band of 229 to 544, at its low end, and is recorded as a risk below. The record's planned sizes were left as written before the build.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not yet submitted
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-22 difficulty record 100, originality record 100; 2026-09-22 Stage 7, difficulty 100 on the measured tree, originality 100 with the final instruction
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent discover, name or verify it without reasoning? Answer must be "nothing": no region, export table or bound-name set is stored anywhere - the reader keeps lines as written and the only frozen helper, `fe/flag.py`, says whether a line is present under the flags; depth, nesting and regions are the agent's to derive (an earlier draft shipped a frozen depth and common-prefix helper that nothing in the shipped tree called, and `preflight.py` flagged it as the unused affordance it was, so it was removed); the sample programs ship without output; the shipped resolver's lines follow the prior's rules, so they agree with the brief only where no graded rule applies; the brief quotes one line, chosen to fix the format and to decide only the reading its own sentence states.
- Expert path, described step by step (the harder the aim, the more this guard must hold): run the shipped programs and map which module decides each printed field; write the visibility algebra (a line's region, who can see a candidate, narrowing at each hop, widening across routes); decide what a module binds itself from its present item and explicit lines alone; write the plain fixed point over (module, name) with item-to-region maps and keep it as a slow checker; settle broken against unresolved, ambiguity carried on as candidates, and item-line order; time the tree program and replace the per-name propagation with sets over bindings under a per-module mask of own names and one cumulative set per visibility depth; differential-test the fast resolver against the slow checker on generated cycles, hides and private hops.
- Originality check: searched 2026-09-22 (queries in authoring/glob-route-hide/originality.toml). Rust RFC 1560 and the nikomatsakis prototype cover glob precedence, same-item imports, use-site ambiguity and a fixed-point work list, and the prototype states it does no privacy and no performance work; the Rust Reference gives minimum visibility for a glob-imported name; the hidden_glob_reexports lint documents a private item hiding a public glob re-export; ECMA-262 ResolveExport handles export star with a resolve set. Nothing combines per-hop narrowing, widest-route visibility, hiding from readers who cannot see the hider, gated lines and declaration-ordered candidates, or addresses a tree that is one cycle of globs.
- Distinctness record score (tools/originalitycheck.py on authoring/<slug>/originality.toml, at Stage 1 before the difficulty record, again once instruction.md exists; every attempt's score, and the crowded archetype named - docs/ORIGINALITY.md): attempt 1 on 2026-09-22 scored 100/100, no hard stop; archetype named: closures and scope chains (lexical lookup), on the list, departure stated; mechanism sentence nearest ledger entry alias-settle-report at cosine 0.18; tags and substrate overlap nothing in the ledger. Stage 7 re-run with the final instruction, 2026-09-22: 100/100; instruction nearest neighbour publish-settle-order at cosine 0.258, shingle 0.000, over 13 documents (the tool skips this task's own ledger entry).
- Nearest already-submitted task (from authoring/submissions.toml or the platform's own flag), what overlaps, and which of the five surfaces separate them: publish-settle-order - both answer a name from several providers under a visibility rule that differs by asker; it is a runtime with a publication order, activation and teardown, this is a static fixed point over import lines; all five surfaces separate (mechanism, substrate, graded output, failure mode, interaction).

## Stage 1 design notes

The seed as written (explicit shadows glob, glob contributions as a fixed point, gated ambiguity,
candidates in declaration order) reduces to reachability over a static graph once shadowing is
decided by lines, and the Rust prototype plans it; a frontier agent forms that plan in one shot.
It was deepened on three axes, all real module-system behaviour:

1. Visibility travels with the candidate. A private line is seen from its module and every module
   inside it; a glob or explicit import gives the reader only what the reader can see, and passes
   it on seen only from where both the candidate and the import line can be seen. Several routes:
   the widest wins. This is Rust's minimum-visibility rule for globs plus rustc's effective
   visibility, never written down as one rule.
2. Hiding by lines alone. A module that has a present item or explicit import line for a name gets
   nothing from its globs under that name, whether the line finds anything and whether the reader
   can see the line. This is the documented `hidden_glob_reexports` footgun (a private import
   silently removing a name from a crate's public API), made a rule.
3. Scale. The graded large programs are module trees where every module reads its parent through a
   glob and re-exports each child, so the tree is one cycle of globs and every module holds every
   name. Measured on the prototype (scratch, not shipped): the exact demand-driven resolver over
   (module, name) pairs took 26.6 s on a 1000-module tree and was killed for memory at 4000
   modules; bitsets over bindings took 0.05 s and 0.52 s and agreed with it on 3000 random small
   programs and on the 1000-module tree.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

Every graded assertion traces to a sentence in the instruction. The walk is
`authoring/glob-route-hide/trace.md`.

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): 117 rows walked - 80 graded rows (5 test functions, 40 enumerated cases, 5 artifacts, the pristine overlay, the two frozen entry points, the 60 second clock and 26 rules of the sealed model, one row per rule with its lines), 30 readings, 6 shortcuts and the clock's tolerance row; no NOT STATED row survived, and `python tools/tracecheck.py glob-route-hide` is clean. The one note is structural: emit.py builds the readings table at run time, so the tool cannot read the reading names and each is cited by hand.
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 30 readings written as whole submissions by `authoring/glob-route-hide/emit.py`, each the reference with one reading changed, drawn from the four clusters (private-only visibility, string-prefix nesting, no narrowing in three forms, public re-exports widening, first-route visibility, hiding only for readers who see the hider, hiding only when the import finds something, absent lines hiding, no hiding by explicit imports, globs ignoring hiding, renames binding both or neither name, display under the held name, flags ignored or negation ignored, dedupe by route, dropping ambiguous names, explicit imports of ambiguous names giving nothing, discovery and alphabetical order, merged duplicate items, no broken, inheritance, one table per cycle, memoized recursion). `tools/readingcheck.py` reports all 30 separated by the enumerated set, none BLIND and none equivalent; `cheat_report.py` asserts each is caught by the case named for it and reports the share of 400 generated small programs each moves: 2 per cent at the least (string-prefix, after a prefix-sibling shape was added to the nest family; it had been 0) and 47 at the most.
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): all score 0. The nop runs out the 60 s clock on the large programs, and without the clock it matches 20 of 40 hand programs and gets 326 of 400 generated wrong; constant unresolved matches 5 of 40 and gets 390 of 400 wrong; first candidate matches 32 of 40, 122 of 400 wrong; first glob only matches 30 of 40, 190 of 400 wrong; the quoted line replayed matches none; the forgery carrying every frozen hand answer passes all 40 hand programs and gets 326 of 400 generated wrong; in the host trial it finishes in 6.4 s and fails only `test_every_generated_program_matches`.
- Independent implementation behind every tolerance and limit (path, measured headroom): the only limit is the 60 second clock. `authoring/glob-route-hide/variants/ok-rounds` and `.../ok-scc`, both written apart from the reference, score 1 through the host trial of the real test.sh in 12.8 s and 10.5 s end to end, pytest about 6 s of each, so the worker's share is under 7 s of its 60; the sealed model, also written apart, agrees with both and with the reference on 1258 programs. There is no numeric tolerance: every printed line is compared exactly.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run, mechanically, over every printed token (module, name, outcome word, item display, candidate order, separators, line order) and every decision behind them. Four gaps were found and closed in the brief before the trace was walked: that `ab` is not inside `a` (a hand case was added for it), that a renamed item prints under the name on its item line, that the reference index counts from 0 in file order, and that an unlisted flag is off. One sentence was removed rather than added: a draft line saying binding is decided by lines alone restated the rule after it. A fresh-session reader was not run; a session that wrote the model cannot un-know it, so this is recorded as author-run only.

## Verifier contract - FROZEN after Stage 2

Frozen 2026-09-22. Restated in the docstring of `tests/test_outputs.py`, which is the file a
reviewer reads.

- Artifacts the agent produces: `/app/fe/vis.py`, `/app/fe/own.py`, `/app/fe/glob.py`,
  `/app/fe/fix.py`, `/app/fe/say.py`. Nothing else is collected; the verifier lays those five
  over its own pristine copy of the tree, so the driver, the reader, the flag helper and the
  sample programs cannot change what a program prints, and a file put beside the five is never
  collected.
- Frozen entry points: `/app/run_res.py` calls `settle(prog)` in `fix.py` once per program and
  `line(prog, tab, i)` in `say.py` once per reference, `tab` being whatever `settle` returned.
- What is checked: for every graded program, the list of lines the driver's `run(text)` returns,
  compared exactly with the expected list. One line per `ref` line, in file order.
- Tolerances: none. The only limit is the 60 second wall clock on the unprivileged stage that
  runs the submission over the whole graded set.
- Ground truth, and where it lives: enumerated programs against `tests/seal/gt.json`, frozen from
  the sealed model before the grading file was written; generated programs against
  `tests/seal/model.py`, which must itself reproduce `gt.json`. `tests/seal/` is `chmod 700`
  before the privilege drop.

### Program format (read by the frozen reader; every token is owed a sentence)

The first line is `flags` followed by the names of the flags that are on. `mod P` starts module
`P`, a dotted path of names, and every line up to the next `mod` belongs to it. Lines: `item N`,
`use P::N`, `use P::N as K`, `use P::*`, each optionally prefixed with `pub` and suffixed with
`if F` or `if !F`; and `ref N`, with neither. Names are lowercase letters and digits.

### The graded decisions, each with the sentence the instruction owes

1. **Presence.** A line with `if F` exists only when `F` is on, with `if !F` only when it is off;
   an absent line neither binds nor gives. Sentence: what an absent line does.
2. **Nesting and visibility.** A module is inside every module whose path is a dot-prefix of its
   own. A `pub` line is seen from every module; any other line from its own module and every
   module inside it. A module sees its parent's names only through its own lines. Sentences:
   inside, the two visibilities, no inheritance.
3. **Explicit import.** `use P::N as K` gives, under `K`, each candidate `P` has under `N` that
   the importing module can see, seen from where both the candidate and the line are seen.
4. **Glob.** `use P::*` does the same under every name the importing module does not bind itself.
5. **Own binding hides.** A module binds a name itself when it has a present item line or
   explicit import line for it; then it has under that name exactly what those lines give, even
   nothing, and nothing from its globs, whoever is asking.
6. **Routes.** A candidate reached by several chains counts once and is seen from every module
   any of the chains allows.
7. **Least fixed point.** A candidate is had only through a chain of lines ending at its item
   line; a cycle of imports gives nothing by itself. An import from an undeclared module gives
   nothing.
8. **Outcome.** One candidate prints the item as `module.name`; none prints `broken` when the
   referencing module binds the name itself and `unresolved` otherwise; several print
   `ambiguous` and every candidate.
9. **Order.** Candidates of an ambiguity appear in the order their item lines appear in the file;
   every item line is its own item.
10. **Output format.** One line per `ref`: module path, name, outcome, single spaces; nothing
    else printed.

Execution limit: the whole graded set inside 60 seconds on one CPU, stated with the sizes of the
two scale families; the run has 2 GB of memory, stated.

### Graded population

- About thirty-five enumerated programs, one per decision and both sides of each fence, frozen in
  `gt.json` and named for the rule they pin.
- Ten small generated families of 40 (plain, nest, narrow, hide, broken, ring, amb, rename, gate,
  mix) and two scale families of 3 (tree: every module reads its parent and re-exports its
  children; mesh: a flat set of modules reading each other through globs at random with private hops, hides and
  duplicate names), generated by root from a seed drawn at verification time.

### Prong C, and the route-around guard

- C1: descendants must see private bindings and outsiders must not; an unbound name must resolve
  through globs while a broken own binding hides them; a pub re-export keeps a candidate wide
  while a private hop narrows it.
- C2: no expected output ships; the shipped resolver prints plausible wrong lines; Rust and
  ECMAScript each disagree with the brief somewhere graded.
- C3: the two scale families; the exact per-(module, name) resolver is measured infeasible.
- C4: exact match on every line of every program, all or nothing.
- Guard: five collected files, pristine overlay of everything else, frozen entry points, programs
  generated by root into a directory the submission cannot write.

### Correct variants planned (must score 1)

- `ok-rounds`: bitsets over bindings propagated round by round (Jacobi), one exact set per
  visibility depth rather than cumulative sets, bindings allocated up front.
- `ok-scc`: the module read-graph condensed into strongly connected components processed in
  topological order, iterating only inside each component, with a dict from depth to set per
  module and bindings allocated as they are first reached.

The prototype showed why both are bitset organisations: on the tree family every module holds
every name, so any exact structure that visits (module, name) pairs one at a time is quadratic;
the variants differ in schedule, storage and allocation, which is what implementation neutrality
and the clock's headroom are measured against.

## Decisions and their reasons

- **Software / Languages.** The graded work is a compiler pass: module-system name resolution.
  Nothing executes, which keeps it away from the two Languages runtimes in the ledger
  (`guard-mark-unwind`, `reach-pair-sweep`) and from every crowded Languages archetype.
- **Seed deepened, not replaced.** Both records reached their floors on the deepened seed, so the
  substrate roster's other entries (imported fixity, macro hygiene, impl selection) were not needed.
- **Hiding decided by lines, not by results.** This is the seed's own rule, kept because it is what
  makes the fixed point monotone and well defined. Hiding only when the own import finds
  something oscillates: simulated on a module whose private import reads its own public glob back
  through a second module, the iteration alternates between finding the item and finding nothing
  forever. It would need a determinacy policy no brief could state completely.
- **An ambiguous name is carried on as its candidates, not dropped.** Dropping it (the
  ECMAScript namespace behaviour applied to re-exports) makes the result depend on the order a
  cycle is visited: simulated on a two-module cycle fed by two declarations, visiting one module
  first leaves it resolved and the other ambiguous, and visiting the other first swaps them.
- **The frozen depth helper went (Stage 5).** The first tree shipped `fe/tree.py` with a depth
  and a common-prefix function that nothing in the shipped resolver called. `preflight.py`
  flagged both as unused, and they were exactly the table of contents that warning describes:
  the region algebra's two primitives, named. The file was deleted, `fe/flag.py` (presence under
  the flags, nothing else) took its place, and the reference, both variants and the slow
  resolvers each carry their own depth arithmetic in `vis.py`. The reader lost its unread `at`
  field in the same pass, on `deadfieldcheck`.
- **First in, first out, measured (Stage 4).** `ok-scc` first took 75.7 s on one tree for two
  reasons: a per-component scan for readers that was quadratic, and a last-in-first-out stack
  that re-derived each module about 650 times. A global reverse map and a FIFO deque bring it to
  0.9 s. The stack version is exactly correct and was kept as `slow/lifo` and `cheat-slow-lifo`
  (77.8 s on one tree): a correct set-based resolver that the clock still stops, so the schedule
  is part of what has to be found, not only the representation.
- **Forty hand cases, not about thirty-five.** The contract's count was a plan. The cold-reader
  pass and the trace walk each closed gaps with a case (`vis-sibling-prefix` for `ab` against
  `a`, among others); no graded rule changed.
- **Probes that show their layer (Stage 7).** The first full host trial scored every cheat 0,
  but the forgery and the answer-key probe scored it because the shipped resolver they fell back
  on ran out the clock, so the trial showed the clock and not the layer each is meant to test.
  The forgery now prints `unresolved` at once for a program too large for the shipped resolver,
  so it finishes and fails exactly the generated-program test; the answer-key probe now uses the
  sealed model as its resolver when the seal can be read, making it an attack that scores 1
  exactly when the seal leaks, with the same quick fallback. `probe_controls.py` runs the three
  probes that carry correct work with their isolation removed and requires each to print every
  line right. One diagnosis of mine was wrong on the way and is recorded so it is not repeated:
  I took the malformed-output probe to be timing out too, and it was not - the shipped `settle`
  returns a lazy closure the probe never calls, so it finished in 6.7 s and its dicts reached the
  grader.
- **Two sentences of the brief corrected at Stage 7.** The mesh was described as each module
  "reading one to three others"; the generator can leave a module with no glob when it samples
  only itself, and in the shipped mesh 16 modules reach a fourth through an explicit import. It
  now reads "up to three others through `use P::*` lines". The tree sentence gained "if it has
  one", for the root. Neither sentence is quoted by the trace and no graded rule moved.

## Stage 7 re-attack (2026-09-22, the built bundle read cold)

- **Is the first plan still wrong?** Yes. Reading the final brief top to bottom with `/app/fe`
  open, the plan that forms is the shipped structure made right: a table per module from name to
  candidates, each candidate carrying who can see it, filled by a worklist until nothing changes,
  with hiding decided from the module's own lines. Every rule has its sentence, so that plan is
  writable inside an hour, and it is `slow/tables`, which runs out of 2 GB after 20.4 s on the
  shipped tree. The per-name repair is `slow/sweep`, 94.6 s on one tree, and the graded set holds
  three trees and three meshes. The generator gives almost every item its own name, about
  12,000 over 4,000 modules, so any structure keyed by name is 4,000 by 12,000.
- **Are the load-bearing facts still distributed?** Yes. That a holder's region is always the
  subtree of one of its own ancestors follows from the nesting sentence, the visibility
  paragraph and narrowing, in three different paragraphs, and none says "depth". That hiding is
  one mask per module that no reader changes is the binding paragraph read with the glob
  sentence. That the tree makes every module hold nearly every name has to be worked out from
  the shape sentence. Nothing in `/app` computes a depth, a region or an export table.
- **Did the brief come to telegraph the method?** Partly, and only where C3 requires it. It tells
  the agent to measure both large programs and describes the tree's glob shape exactly; that is
  the stated limit, not the method. Nothing says sets, bits, depth, masks or worklist order, and
  the one quoted line decides only the ordering sentence it illustrates.
- **Is any graded answer short?** No. `tools/onelinecheck.py` over nineteen features per
  reference, read off the text with the flags applied (own items and imports, globs, one-hop
  offers, cycles, declared items, depth) plus what the shipped resolver prints for that line,
  finds no exact rule of two terms or fewer for any of the six graded quantities: broken,
  unresolved, resolved, ambiguous, found nothing, and the candidate count. It ran over 4,415
  reference lines, about 2,300 distinct rows per question. `decisions.py` also counts feature
  rows that occur with both labels - 8 for broken, 15 for ambiguous, 67 for unresolved, 80 for
  resolved, 75 for found nothing, 84 for the count - each a pair of references that no function
  of those features can separate at any depth.
- **Estimate.** Unchanged at 2 of 8, range 1 to 4. Upward pressure: every rule is one sentence,
  and a strong agent that measures early can reach sets over bindings inside four hours. The
  tree sentence also tells it where to look. Downward pressure: grading is all or nothing over
  446 programs, and thirty separately plausible readings each fail the set alone. The replan
  must keep each own binding's cut inside a structure that moves every name at once; the
  obvious shared table per cycle is itself a caught reading. And even a correct set-based
  resolver misses the clock with a last-in-first-out worklist.

## Quality self-review (docs/QUALITY-REVIEW.md, criterion by criterion)

Instruction and verifier agreement:
- Every tested behaviour is described: `authoring/glob-route-hide/trace.md`, 117 rows, and
  `tools/tracecheck.py glob-route-hide` is clean; each of the sealed model's 26 rules has its
  sentence and the hand cases that pin it.
- Every promised behaviour is checked: each paragraph of `instruction.md` maps to cases in
  `tests/cases.py` and to a generated family; the clock is `tests/test.sh:17` and `:36-38`.
- Output files by absolute path: the five artifacts at `instruction.md:17`, the same five as
  `task.toml` `artifacts`.
- Schema: the printed line at `instruction.md:15`; `settle(prog)` and `line(prog, tab, i)` at
  `instruction.md:17`.
- Boundaries: the reference index "counting from 0 in file order" (`:17`); unlisted flags off
  and `ab` inside nothing (`:3`); no candidate split into broken and unresolved (`:15`); order
  of an ambiguity by item line (`:15`); "inside 60 seconds on one CPU with 2 GB of memory"
  (`:19`).
- Every graded quantity defined: candidate (`:9`), seen from (`:7`), binding (`:11`), chain and
  cycle (`:13`), outcome (`:15`).
- Counts match what ships: forty hand programs is `len(cases.ORDER)`; four hundred small is ten
  families at `PER=40` (`tests/test.sh:18`); three of each large shape is `BIG = 3`
  (`tests/gen.py:42`); six programs in `/app/progs`; four thousand and three thousand modules
  are the shipped `tree.txt` and `mesh.txt`. The one wrong count, the mesh's "one to three
  others", was corrected at this stage (see Decisions). Every number in the three explanations
  was re-read against its measurement, and every case the verification explanation names exists.
- Verifier requirements stated: collected files and the overlay (`:17`), entry points (`:17`),
  clock and memory (`:19`).
- Readings and shortcuts: 30 readings separated by the enumerated set; the nop, constant,
  positional and replayed strategies score 0; the only limit, the clock, is validated by two
  resolvers written apart from the reference and by the sealed model.

Instruction prose:
- `tools/textcheck.py` against two passed briefs flags the cadence as too even: burstiness 0.797
  against 1.112 (reach-pair-sweep), type-token 0.291 against 0.390, short sentences 24 per cent
  against 35 (publish-settle-order). Two parallel runs remain, the three presence sentences in
  paragraph 2 and the three outcome sentences in paragraph 8. The rubric's fix is the
  contributor rewording in their own voice, so this is handed over as a known risk rather than
  rewritten by me.
- Each requirement is stated once; the one restatement found was removed at Stage 5.
- Register: first person plural for the team's compiler, no assistant phrasing (`textcheck`
  counts no stock phrases, hedges, antitheses or triads).

Verifier rigor:
- Real execution: `tests/worker.py` runs the driver's `run(text)` over every exam program as uid
  1002 and records a digest of each program it read; `tests/test_outputs.py:110-114` holds the
  model to `gt.json` first, `:119-124` checks every exam program ran on the graded text,
  `:129-132` the hand cases against `gt.json`, `:137-149` every generated program against the
  model.
- Structured and commented: the docstring at `tests/test_outputs.py:1-40` restates the frozen
  contract, and each test group has a section comment.
- Deterministic: a correct resolver passes every seed, and the seed changes only which instances
  of each shaped family are drawn. The clock is the stated limit; the reference's whole run is
  9.6 s of which pytest is 5.4.

Environment hygiene:
- `environment/Dockerfile` copies `app_src/` and nothing else; `tools/imagecheck.py` assembles
  the image's 15 files and finds no `tests/` or `solution/` content.
- Test dependencies live in `tests/Dockerfile:6`, pinned `pytest==9.1.1` and
  `pytest-json-ctrf==0.5.2`; no apt package is installed.
- No dangling references: every path the brief names exists in the image, and `imagecheck` runs
  all six programs through the reference.

Solution quality:
- `solution/solve.sh` copies the five resolution files over the shipped ones and runs a sample;
  every answer is computed by the resolver at grading time.
- The reference reads only the program it is given.

Anti-cheating:
- No expected output ships, and the agent tree has no comments, docstrings, `.md` files, git
  history or caches: a token and AST scan of every file finds none, and `extraneouscheck` and
  `imagecheck` are clean. A stray `fe/__pycache__` left by an authoring run without
  `PYTHONDONTWRITEBYTECODE` was found and deleted at this stage, and `environment/.dockerignore`
  now excludes bytecode, byte-identical to the one the retained bundles ship.
- Every line is compared exactly; there is no tolerance to exploit.
- No repository is cloned.

Metadata:
- `Software` / `Languages`; `tools/catcheck.py` finds the category's vocabulary in the
  environment (23 hits) and not only in the prose (86).
- Six specific tags, none restating the category or subcategory.
- `difficulty_explanation` names the concrete wrong steps - a table per module, a visibility
  fixed at first arrival, hiding only when an import finds something, per-pair and per-name
  structures, a last-in-first-out worklist - with the measured numbers, and states the legacy
  register as a design choice.
- `solution_explanation` walks the five files in the order an expert writes them and says why.
- `verification_explanation` names the case each fence fails and every kind of cheat.
- `relevant_experience` is specific to module systems and fixed points over module graphs.
- `expert_time_estimate_hours = 9`, consistent with the difficulty claim and the 14400 s budget.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run | Docker daemon runs here, but the egress policy refuses Docker Hub's blob CDN (`production.cloudfront.docker.com`, 403 on CONNECT), so no base image can be pulled; the denial was reported, not routed around. `tools/imagecheck.py` assembles the image's 15 files from the Dockerfile's WORKDIR and COPY against `.dockerignore` and runs all six shipped programs with the reference: clean |
| No answer leaked into agent image | checked on the host | the image holds `app_src/` only (imagecheck); no expected output ships; no comments, docstrings, `.md` files or caches in the tree; `extraneouscheck`, `hintcheck`, `deadfieldcheck` and `solvecheck` clean |
| `harbor run -a oracle` = 1 | host emulation only | `host_trial.py`, which runs `tests/test.sh` verbatim as root on the real absolute paths with the worker dropped to uid 1002: reward 1, 9.6 s end to end, 44 passed. Not a container run |
| `harbor run -a nop` = 0 | host emulation only | reward 0: the shipped resolver runs out the 60 s clock (worker exit 124) and no record reaches the grader |
| Cheats all score 0 | host emulation only | 48 of 48 score 0 (full run 50 of 50 with oracle and nop; the two cheats changed afterwards re-run alone). Layers: 29 readings caught by failing tests with the worker finishing, `memo-rec` by the clock and by its case in process; 4 shortcuts by failing tests; the forgery by `test_every_generated_program_matches` alone; 4 slow cheats by the clock; probes by what they logged (seal unreadable, reward and exam unwritable, uid 1002), by the worker's exit status, by collection, or by the grader. `probe_controls.py`: the three probes carrying correct work print every line right with their isolation removed |
| Correct variants score 1 | host emulation only | ok-rounds 12.8 s and ok-scc 10.5 s end to end, 44 passed each |
| `tracecheck.py` (every graded assertion traced) | clean | 117 rows; one structural note, readings cited by hand |
| `preflight.py` | no errors | 7 WARN, all false positives: each "unused" function is called through a module attribute (`fix.settle` and `say.line` from `run_res.py`, `rd.load` from `run_res.py`, `glob.srcs`, `vis.seen` and `own.names` from `fe/fix.py`, `flag.live` from `fe/own.py`); the ledger WARN is cleared by the new entry |
| `harbor check` rubric | not run | no API key in this session; the self-review above stands in for it and is not a substitute |
| `originalitycheck` / `difficultycheck` at Stage 7 | 100 / 100 | difficulty on the measured tree |
| `onelinecheck.py` | OK | no graded decision reproduced by a rule of two terms or fewer; all six questions searched in full, 30 minutes on one core |
| `readingcheck.py` | clean | 30 readings, all separated by the enumerated set |
| `cheat_report.py` | 0 problems | every reading caught by its case, 2 to 47 per cent of generated small programs moved |
| `package.py` / `zipcheck.py` | clean | `tasks/glob-route-hide.zip`, 99 entries: every file of the task folder except `STATE.md`, the 50 `.sh` entries executable, no scratch; `simcheck` exit 0, Dockerfiles HIGH only |

## Open questions and next steps

Residual risks, in the order I would raise them with a reviewer:

1. **No container evidence.** Every trial above is host emulation: `tests/test.sh` verbatim as
   root on the real paths, with the privilege drop, the session, the clock and the reap all real.
   But no image was built, the host runs Python 3.11 where the images run 3.12, and the host
   enforces no 2 GB cap, so `slow-pairs` and `slow-tables` meet the clock here. Their memory
   failures come from separate runs capped at 2 GB. The first thing to run on a machine that can
   pull `python:3.12-slim` is `harbor run -p tasks/glob-route-hide -a oracle -e docker -o ../jobs`
   and the same with `-a nop`, then the cheats in a container.
2. **`harbor check` not run.** No API key in this session. The criterion-by-criterion review
   above is what stands in for it.
3. **The AI-text screen.** `textcheck` reads the brief as more even in cadence than the passed
   references (burstiness 0.797 against 1.112). The passages to reword are paragraph 2's three
   presence sentences and paragraph 8's three outcome sentences, and the rubric wants that done
   by the contributor in their own voice; after any rewording, re-run `tracecheck`,
   `textcheck` and `originalitycheck`, since the trace quotes the brief.
4. **Difficulty from above.** Every rule is one sentence and the brief tells the agent to
   measure the large programs, so an agent that measures early and knows integer bitsets can
   finish inside the budget. The estimate is 2 of 8, range 1 to 4.
5. **Environment size.** 233 Python lines, inside the retained band of 229 to 544 but at its low
   end; the editable code a solver writes is the reference's 266 lines across five files.
6. **Dockerfile similarity.** `simcheck` rates both Dockerfiles HIGH against the retained ones
   and exits 0; both are the short conventional shape the platform expects.

Next steps: submit the zip; add the platform's verdict to `authoring/submissions.toml`; if the
easiness probe solves it, `RAISE-DIFFICULTY.md` from the start before any other change.
