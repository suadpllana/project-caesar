# Quality self-review: queue-hold-drop

Walked criterion by criterion against `docs/QUALITY-REVIEW.md`, answering each with the file that
satisfies it rather than with an opinion. Run before packaging.

## Instruction against verifier, both directions

- **Every behavior the tests check is described in the instruction.** The walk is
  `authoring/queue-hold-drop/trace.md`: 4 test functions, 41 enumerated cases, 6 collected
  artifacts, the 60 s clock and 14 rules of the sealed model, each with the sentence it traces to.
  `python tools/tracecheck.py queue-hold-drop` is clean, and it fails on a quote that is not in
  `instruction.md`.
- **Every behavior the instruction promises is checked.** Each of the 42 quoted sentences is cited
  by at least one graded row. The generator families in `tests/gen.py` are named for the rules
  they exercise, and `authoring/queue-hold-drop/cheat_report.py` reports, per wrong reading, how
  many of 200 generated programs move: the thinnest is 9, the thickest 152.
- **Every output file the tests read is named, absolutely.** The verifier reads exactly the six
  paths in `task.toml` `artifacts`, and `instruction.md` names all six in one sentence ("The files
  you may change are `/app/pend/line.py` ...").
- **The schema is specified.** Every printed shape is in the instruction: `out <kind> <record>`,
  `ack <kind> <record>`, `gone <count>`, `idle`, `rec <record> <parent> <field>=<value> ...`,
  `row` of the same shape, and `none`, with the field order, the `-` for a top record and the
  order records are listed in.
- **Boundaries and conventions are settled.** Which record a change is about and which it names;
  the exemption for the record a creation makes; the answer target; that the ids run `s1` upward
  in answer order; that a field nothing has set holds zero and one set to zero still prints; that
  the take-away goes forward only; that a move under one's own descendant does nothing; that a
  removal of an unconfirmed record cancels only while its creation is still queued.
- **Every graded quantity is defined.** `<count>` on a `gone` line is defined as counting the
  refused change as well. `<record>` is defined as the id when the server has given one and the
  name the program made it with otherwise. `<kind>` is defined as the word the change was written
  with.
- **Nothing contradicts the reference, and every count matches.** The counts in the brief (20000
  changes, 12000 records, 8000 questions, three of each scale size, 450 small ones, 60 seconds)
  are the numbers `tests/gen.py` and `tests/test.sh` produce: `FAMILY=45` over ten small families
  is 450, `BIG = 3`, and `_wide(s, 20000)` / `_deep(s, 12000, 8000)`. `tools/hintcheck.py` is
  clean.
- **Every verifier requirement is in the text**, including the wall clock and the collected files.
  The clock has its own sentence and its own trace row.
- **Readings, shortcuts and tolerances.** 23 readings, all separated by a named case
  (`tools/readingcheck.py`). The four shortcut strategies each score 0, with the fraction of cases
  they match recorded in `trace.md`. The one limit is validated by two independently written
  correct services.

## Instruction prose

- No run of same-structured sentences survives: `tools/structcheck.py` is clean and
  `tools/textcheck.py` puts burstiness at 0.88 against a passed brief's 1.01, inside the range the
  retained briefs occupy (0.79 to 1.11).
- Each requirement is stated once. The one place a rule was stated twice - the answer target,
  followed by a sentence saying it is not the front of the queue - was cut, because `hintcheck`
  is right that naming a candidate and rejecting it hands over the discrimination.
- The register is one voice throughout, and it is the same register as the retained briefs.

## Verifier rigor

- **The tests demand evidence of real execution.** `tests/worker.py` runs the submitted service
  over 497 programs and records what it printed; `tests/test_outputs.py` compares every line. No
  exit code and no state the agent could write directly is graded.
- **Test code is structured and commented.** `tests/test_outputs.py` opens with the frozen
  contract, twelve numbered graded decisions and what is explicitly not graded; `tests/cases.py`
  documents each group; `tests/gen.py` documents each family.
- **Deterministic.** No wall-clock dependence in the comparison, no network, and the generated
  population is seeded. The one clock is the execution limit, stated in the brief, with 47x
  headroom for the reference.

## Environment hygiene

- Neither `tests/` nor `solution/` is copied into the agent image: `environment/Dockerfile` copies
  `app_src/` and nothing else.
- Test dependencies are installed in `tests/Dockerfile` at build time, pinned at
  `pytest==9.1.1` and `pytest-json-ctrf==0.5.2`. `tests/test.sh` installs nothing.
- No apt package is pinned; no `FROM --platform=`.
- No dangling references: every path in the brief exists in the environment, spelled identically
  (`/app/run_edit.py`, `/app/progs/{tiny,pair,wide,deep}.txt`, the six `/app/pend/*.py`).

## Solution quality

- `solution/solve.sh` copies six files that sit beside it and then runs the service on the two
  small programs. `tools/solvecheck.py` is clean: nothing is inlined as a heredoc and nothing is
  duplicated.
- The solution uses nothing the agent could not use. It reads no verifier file and no ground
  truth.

## Anti-cheating

- The answer cannot be read out of the environment: no expected output ships, no git history, no
  caches. `tools/deadfieldcheck.py` is clean, so no unread field invites a rule to be invented
  from it.
- Grading is exact string equality over 497 programs, so a degenerate output fails.
- No repository is cloned.

## Metadata

- `category = "Software"`, `subcategory = "Databases"`. `tools/catcheck.py` measures 37 hits of
  the Software vocabulary in the environment, so the category is carried by the code rather than
  by the story.
- Tags name the techniques, not the taxonomy: `replication-clients`, `write-queue-ordering`,
  `conflict-replay`, `identifier-assignment`, `cascading-invalidation`,
  `incremental-materialisation`.
- `difficulty_explanation` names the concrete steps a frontier agent gets wrong, and says plainly
  that the identifiers are in a legacy register as a design choice.
- `solution_explanation` describes the actual method, file by file, in the order the rules force.
- `verification_explanation` says what passing means and names the case that catches each wrong
  reading.
- `relevant_experience` is specific to this work and claims no employer, credential or duration.
- `expert_time_estimate_hours = 10`, consistent with six files, ten graded decisions and a
  measured scaling boundary.

## Known risks to flag to a reviewer

- The environment is 257 lines of Python, near the low end of the retained band (224 to 544). The
  difficulty rests on the interaction of the rules and on the clock, not on the size of the tree,
  and `tools/difficultycheck.py` scores the built bundle at 100.
- The easiness probe has not been run; nothing local substitutes for it.
- The cold self-attack was not run as a fresh-session solve, because this session wrote the sealed
  model. What stands in its place: 23 separated readings, four graded decisions with no rule of
  two terms or fewer (`tools/onelinecheck.py`), and no shipped oracle.
