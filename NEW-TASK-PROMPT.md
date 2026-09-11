# Start a Frontier Bench task from one prompt

Paste the block below as the first message in a fresh task-authoring session. The session begins
work immediately. It does not stop for the old 11-part proposal or make the contributor approve a
separate planning document before engineering starts.

The agent still follows every gate in `AGENTS.md`. It handles reversible engineering decisions
itself and works through the stages without waiting. If a genuinely contributor-owned judgment is
missing, it continues all independent work and asks for every missing judgment in one batch at the
next natural checkpoint.

---

```text
You are building or repairing one Frontier Bench task in this repository. Begin from my first
prompt immediately. Do not give me an 11-part intake, a proposal-only turn, or a list of engineering
questions. Do not wait for permission to inspect, research, scaffold, implement, test, or repair
reversible parts of the task.

Never spawn subagents. You are the engineer, probe, reviewer, and solver. In your first short
progress update, state what task you understood and start working.

Read `AGENTS.md` completely before acting, then read `docs/RULES.md`, `docs/DIFFICULTY.md`,
`docs/QUALITY-REVIEW.md`, and `docs/VERIFIER-ISOLATION.md` when submitted code will execute in the
verifier. If this is an easiness rejection, also read `RAISE-DIFFICULTY.md` and follow its recovery
loop completely.

## Primary objective: clear the easiness probe

The easiness probe is the most important design gate. Treat it as the central constraint from the
first minute, not as a check performed after the task is built. Start from a genuinely complex
issue that requires a frontier agent to explore, revise an initially reasonable plan, and reconcile
multiple interacting rules. Do not start from a simple issue and try to add difficulty later.

Before implementation, attack the planning problem yourself. Identify the natural first plan and
the later discovery that makes it fail. If you can form the complete correct plan in one shot, the
issue is not hard enough: deepen the semantic interaction before building. Length, repository size,
random cases, obscure names, and execution effort do not count as complexity.

The issue must remain solvable by a real expert. The pipeline requires at least one and at most
seven solves out of eight. Aim at the hard edge while maintaining a concrete, reliable reference
path; zero solves is failure, not success.

Inspect the current branch, Git status, all local and remote task branches, and recent history
before editing. Preserve unrelated work. Fetch `origin/main`; merge it only when doing so will not
overwrite or mix with existing changes. Check whether Docker and Harbor work. Start or pull what
you need yourself when they are available, and report unavailable infrastructure plainly.

Use my first prompt as the task seed and begin the normal Stage 1 investigation at once. Search for
public solutions and close variants. Inspect every retained task so the graded work is original.
If my prompt includes a repository, check its license, clone and study it, interview me about the
parts only experience reveals, and give me the mandatory authored-on-top versus excision choice
before settling a candidate.

This repository accepts only `Software` or `ML` tasks. Do not build a task categorized as Science,
Operations, Security, Hardware, or Media. Classify the skill exercised by the graded work and the
agent-facing environment, not the story used to describe it. If the seed genuinely belongs to an
excluded category, do not disguise it with a Software or ML label; report the mismatch and use my
judgment to reshape or replace the seed. Choose the subcategory from the matching row of the exact
table in `AGENTS.md`, and use tags for the specific techniques rather than the taxonomy label.

`Software` / `Systems` is retired and no new task is filed under it. If the seed's natural home is
that label, file it under whichever of the remaining Software labels the graded work actually
exercises, or pick a different seed; do not relabel a Systems task and leave it otherwise
unchanged.

Do not stop because authoring material is absent. Own the task bundle end to end: research,
category and tags, domain role, task selection, environment, verifier, reference solution, cheats,
`instruction.md`, every explanatory metadata field, validation, packaging, and delivery. Infer and
write these from my first prompt, repository evidence, actual program behavior, and measured test
results. Ask me only when two materially different meanings of the requested task remain possible
after investigation or when changing a frozen verifier contract would change what "correct" means.

Write `relevant_experience`, `difficulty_explanation`, `solution_explanation`, and
`verification_explanation` yourself. File the task under the contributor's author identity:
`author_name = "Shiela marie"` and `author_email = "aurigue.shielamarie20@gmail.com"` in the
`[metadata]` table of `task.toml`. Take those two fields from `template/task-template/task.toml`,
never from a retained task - the retained bundles shipped under an earlier identity, and copying
their author fields files the new task under the wrong person. Describe only experience supported
by the task history and repository evidence; never invent an employer, credential, duration, or
personal claim. Use the retained tasks that passed the authorship and quality screens as style
calibration without copying their prose.

Write `instruction.md` yourself after the environment and verifier behavior are real. Do not ask me
to draft, rewrite, or approve it. Treat my first prompt as the source of intent, resolve engineering
details from the implementation, and self-review every sentence against the environment and sealed
contract. Never weaken the verifier to make a run pass.

Work through the following build order autonomously. These are your internal gates, not questions
for me and not separate turns unless a contributor-owned decision blocks the next gate.

## Difficulty gate: score the idea before writing a single line of code

Before any environment, verifier or solution code exists, write the idea down as a difficulty
record and score it. Copy `template/difficulty.toml` to `authoring/<slug>/difficulty.toml` and
answer every field from the idea: the frontier agent's first plan and where it comes from, the
exact rule that breaks it, the second discovery that forces a replan rather than a patch, the best
public page and why it does not help, each tactic in this task's terms, the graded decisions and
the pairs that change each other's meaning, the ordinary and the late case, the leak audit, the
resource gate or the reason there is none, the wrong readings with a hand case each, two correct
variants, the expert path step by step, the estimated solves and the planned tree shape. Then run
`python tools/difficultycheck.py <slug>`.

The tasks that passed AI or human review score 95 to 100 on this checker and every design the
pipeline rejected scores 40 to 59; the band, the rubric and the calibration are in
`docs/DIFFICULTY-SCORE.md`. If the idea scores inside that band with no hard stop, proceed to the
task record and the verifier contract. If it does not, the idea is not built: read the repair
list the checker prints under each axis, return to `docs/DIFFICULTY.md`, and formulate another
idea - or a deeper version of this one - and score that. Repeat until a record reaches the band.
Record every attempt's score and what changed between attempts in `STATE.md`.

The record is a description of the design, not a document to be tuned until the number comes
out. The checker reads fields, lengths and counts; it cannot tell a real second discovery from
an invented one, and every claim in it is restated in `STATE.md`, tested by your cold self-attack
and finally by the probe. Padding the record to the floor produces a number and a rejection. Run
the same command again at the final gates: with the tree built it measures the sizes instead of
reading them, and a design that has flattened during the build falls out of the band there.

## Task record and difficulty attack

Create or update `tasks/<slug>/STATE.md` immediately. Record the real work, observable definition
of done, expert time, originality search, category choice, domain role, and repository shape where
applicable. State the frontier agent's first plan before code exists. Name the exact second
discovery that invalidates that plan, the A/B/C tactics used across at least two prongs, the route
around being blocked, and the estimated solves out of eight.

Reject a design whose complete correct plan forms in one shot. Also reject one with no describable
expert path. The target is: I can see where to start, but I cannot commit to the full plan without
exploration, and my first plan is likely wrong somewhere that matters. Difficulty must come from
interacting, fully stated semantics. Repository size, vague prose, random cases, artificial names,
and short timeouts do not count.

## Contract before implementation

Freeze the verifier contract before environment code. List every declared artifact, its exact
format, every graded decision, both sides of every boundary, and the independent evidence that
proves correctness. Separate behavior required by the instruction from implementation choices the
verifier must accept. Write at least two meaningfully different correct variants before freezing
the contract. Any later contract change needs my explicit approval because it changes what
"correct" means.

## Environment

Build only what the task needs. Keep the agent-facing tree free of documentation, comments,
docstrings, answer material, dead fields, unused helpers, provenance leaks, and development
artifacts. Use consistent legacy-style identifiers only where the repository rules require them;
never use random or misleading names. Ship runnable representative inputs and a direct way to
exercise the broken system.

For every load-bearing decision, try to reconstruct the answer from shipped fields, counts,
lengths, helpers, filenames, logs, and pairs of exposed values. Remove derived leaks. Confirm that
every editable file genuinely needs work and that no correct component silently reduces the task
to a one-file patch.

## Sealed verifier

Implement a binary, independent, all-or-nothing verifier in `tests/`. Install every dependency in
`tests/Dockerfile`; trial-time scripts never use the network. Read only declared artifacts. Create
every artifact parent directory. Use exact comparison or a justified closed tolerance. Include
ordinary cases that reject blanket workarounds and adversarial cases that make natural wrong plans
fail late.

When the verifier executes submitted code, apply all isolation requirements: unprivileged worker,
root-owned sealed inputs, root-owned reward directory, reward defaulted to 0, checked process
status, survivor cleanup, pristine overlay, output attestation, and the mandatory reward-tamper
probes. The submitted process must never be able to write its reward or its inputs.

## Reference solution

Write one canonical expert solution under `solution/`. `solve.sh` copies or invokes that source; it
does not duplicate a long implementation. Run it against the independent verifier and record the
actual result. If using a resource gate, measure the expert and naive methods under the declared
CPU and memory limits. The limit is valid only when the principled route passes with headroom and
the naive but correct family fails at the stated input scale.

## Wrong solutions and alternative correct solutions

Implement every plausible wrong reading as a cheat. Include hardcoding, answer-key access,
verifier tampering, malformed output, process survival, and reward tampering where applicable.
Turn every successful easiness-probe solution into a regression cheat. Give each semantic mistake
a small hand-written counterexample and keep generated coverage for combinations and fitting
resistance.

Run alternative correct variants through the same verifier. A stated-contract implementation that
scores 0 reveals verifier overfitting. A cheat that scores 1 is either a verifier defect, a missing
case, an unobservable distinction, or a correct variant; diagnose which before changing anything.

## Instruction and metadata

After the environment behavior is real, build an internal fact sheet containing all absolute
paths, input bounds, outputs, ordering rules, failure conditions, and the timeout. Write the final
instruction yourself. Keep it concrete, complete, method-neutral, and plain ASCII. Every tested
rule needs one sentence and every sentence needs a test. Include the exact required suffix with the
agent timeout from `task.toml`.

Write all metadata yourself from evidence. `relevant_experience` must be concise, specific to the
work, and truthful; the three explanation fields must describe the actual difficulty, reference
approach, and verification strategy without revision history or unsupported claims. Compare the
prose with retained tasks that passed the screen, then run the repository's text, structure, hint,
and preflight checks and repair every finding yourself. Contributor review is optional feedback,
not a completion gate.

## Cold self-attack and easiness recovery

Copy only the agent-visible instruction and environment into a scratch location. Write your first
plan before inspecting files, solve it without reading `tests/` or `solution/`, and grade the result
through the real verifier. Record where the plan came from and whether each rule could be confirmed
independently. If the first implementation is correct, the task is still too easy.

If an easiness probe rejects the task, stop packaging. Follow `RAISE-DIFFICULTY.md`: preserve and
analyze the winning trajectories, identify the exact route, design a semantic replan, return to the
earliest affected stage, make the old winning method a cheat, and rerun the real probe. Never call
the recovery complete on predicted difficulty or a reduced local simulation.

## Final gates and delivery

Run the cheapest checks first. At minimum run task-specific generation and synchronization,
correct variants, every cheat, determinism checks, reference and nop trials, isolation probes where
applicable, `solvecheck`, `deadfieldcheck`, `catcheck`, `hintcheck`, `structcheck`, `simcheck`,
`forgecheck`, `preflight`, and the criterion-by-criterion manual quality review. Run the real Docker
oracle and nop gates whenever relevant inputs changed. Do not rerun an unchanged passing gate just
for reassurance.

Package with `scripts/package.py`, repair ZIP metadata with `zipfix` on Windows when needed, and run
`zipcheck` on the final archive. Keep Harbor output outside the task folder. Inspect the packaged
tree for scratch files, answer leaks, blocked names, incorrect modes, and missing artifact parents.

Report what actually ran and its exact result. Distinguish host emulation from container evidence.
Do not claim that local checks guarantee a stochastic quality or difficulty result. If I asked for
Git delivery, commit only the intended files, preserve unrelated changes, synchronize safely with
`origin/main`, push, and verify the remote commit.
```

This prompt removes the proposal-only phase, not the validation gates. Work begins after the first
message and continues until the task is built or a genuinely contributor-owned judgment blocks the
next irreversible decision.
