# The prompt for building or repairing a Frontier Bench task

Paste the block below into a fresh session as its first message. It condenses every rule
this repo has measured across fifteen tasks and roughly twenty pipeline rejections, and it
is written as orders to the session, not notes to a person. Rewritten 2026-09-04 after
`alias-settle-report` passed both probes.

Two things it is built around, because the owner asked for them:

- **No subagents.** The three-agent local probe burns credits. The session is the probe:
  it attacks its own design before any code, and it solves its own task cold, in a sealed
  copy, and grades that solve through the real verifier. That is the same evidence, cheaper.
- **Nothing is built until the owner has approved a written idea.** The session's first
  and only output is a task proposal under 8000 characters. It stops there. The owner
  pastes feedback back, and the session starts only when every open question is answered.

It removes the known causes of rejection. It cannot make eight stochastic agents
deterministic, and it says so.

---

```
You are building (or repairing) one Frontier Bench task in this repo. Work in two phases.
PHASE 0 ends with a proposal and a full stop. PHASE 1 does not start until I have replied
to that proposal and you have every answer you need. Never spawn subagents: you are the
probe, the reviewer and the solver yourself.

=== SETUP, before reading anything else ===
git fetch origin main && git merge origin/main. main is pushed to directly and moves under
you. Then read, in this order: CLAUDE.md "Landing inside the band", "What can be
brute-forced, and what cannot", "The ceiling, measured from the other end", "Verified
recovery: a semantic scaling boundary", "Fixing a task the easiness probe solved: the four
failure modes", the stage-7 gate list; then docs/DIFFICULTY.md and docs/RULES.md. Check
`git branch -a` and `git log --all` for unmerged branches on the task before diagnosing
anything. If Docker is present, start dockerd and pull
mirror.gcr.io/library/python:3.12-slim now, in the background.

=== PHASE 0: the proposal (under 8000 characters, then STOP) ===
Do not write a line of task code, environment or brief. Produce one message with exactly
these sections, in this order, and end the turn:

1. SEED AND WORK. The real bug class or incident it comes from, in two sentences, and who
   does this for a living. The graded data described honestly (synthetic token streams,
   integer ledgers, whatever it is) and whether that is a fair sample of the real thing.
2. CATEGORY, SUBCATEGORY, TAGS. Pick the category from the vocabulary the ENVIRONMENT will
   contain, never from the story the brief is set in (tools/catcheck.py). Subcategory must
   be a label from that category's row in template/task-template/task.toml. Tags name
   techniques, never the taxonomy. Reusing a subcategory is fine.
3. WHAT IS GRADED, AND WHY IT IS NEW HERE. Name the artifact (a trace, a schedule, a
   reconstructed state, a determination, a board, a delivery obligation). Then list every
   task in tasks/ and say in one clause each why it grades something different. Work
   counters against an unpublished budget are BANNED: five tasks here did it and the
   similarity screen rejected the fifth.
4. THE DEAD-FAMILY TEST, answered explicitly. State what the correct answer is defined
   against. Then answer each with yes/no and one line of proof:
   - Is it a pure function under a stated rule? (dead: the solver brute-forces an oracle
     as its first file; earliest-change-script failed three times on this)
   - Is the graded predicate a decidable property of the input under stated transitions
     that a small state makes enumerable? (dead: alias-settle-report went 3/3 in 2-7
     minutes; run your own generator in your head and ask if the solver can produce every
     continuation)
   - Is the invariant "the transform preserves behaviour", determinism, resume-equivalence,
     or a naive-but-correct baseline the environment ships? (all dead: run both, diff)
   - Does a single page or repository substantially plan it? (dead)
   Surviving shapes: a machine with a stated invariant about ITS OWN HISTORY where the
   agent supplies the policy that maintains it; or a semantic C3 scaling boundary where
   a common exact algorithm stays correct but becomes infeasible on a stated input family
   and a faster path follows from a real invariant of that family (alias-settle-report,
   passed). If you propose a speed regime you MUST commit to timing the reference against
   the naive implementation on it before contract freeze; a regime where the reference is
   not decisively faster is not an axis.
5. THE DIFFICULTY, in exactly this shape. (a) The ONE thing that must be derived. (b) The
   SECOND discovery that invalidates the natural implementation of the first, so the two
   cannot be fixed in either order independently. (c) The many STATED rules whose
   interactions are the work; aim for 8-12 graded decisions over a runtime the agent has to
   reason about (guard-mark-unwind, the only bundle to clear both probes cleanly, grades 8;
   a mechanism whose core is one insight is a half-day task however it is described and
   fails `difficult`). (d) Which of those decisions need something no single visible input
   supplies (a previous step's verdict, a state a prior event left behind, a fixed point
   over ARBITRARY sets - a fixed point over unions of disjoint blocks never iterates and is
   vacuous). Say how many of the editable files will ship wrong; a two-file task where one
   ships correct is a one-file task.
6. YOUR OWN FIRST PLAN, honestly. Before any code: how would you solve it, what would you
   search for, how long to a working solution? If your first plan is correct, the design
   has failed; say which prong is missing and fix the design before proposing it. The
   target sentence is "I can see where to start but my first plan would be wrong somewhere
   that matters." Also answer: can I confirm each rule independently with my own harness?
   If yes for every rule, it is mode C and will be solved 3/3.
7. THE BRIEF, split in two lists. STATED: every requirement the verifier grades, one line
   each, phrased so the neighbouring case is decided too (a rule phrased around one
   participant has cost three rejections). Include the input-space sentences ("this
   situation occurs and is graded"), every literal token or state string the grader
   exact-matches, the execution limit and the input scale that exercises it if there is a
   resource gate. WITHHELD: the rule the task is built on, the method, how many decisions
   are wrong, any graded number, any existence claim, any candidate rule you intend to
   reject, any sentence saying which part carries the difficulty, any verifier internals.
8. EXPECTED WRONG READINGS. At least six plausible readings with the share of generated
   cases you expect each to move; anything under a tenth is a lottery ticket, not a
   decision. Note that these measure legibility, not difficulty: a frontier agent takes no
   shortcut on a complete specification.
9. VERIFIER CONTRACT SKETCH. Editable artifacts (a wider candidate set than needs
   changing); what evidence, not report, proves each graded quantity was earned; the
   nonce-generated set built after the agent finishes; the sealed independent model; which
   tallies are floors; the two correct variants you will write BEFORE freezing; the
   invented-name mirror variant; how ties are made impossible by construction.
10. REFERENCE EXPERT PATH, step by step, and an honest hours estimate (7-8 h is the band).
11. QUESTIONS FOR ME, numbered, batched, only judgment calls that are genuinely mine.
Then stop. Do not begin PHASE 1 in the same turn under any circumstances.

=== PHASE 1: build, only after my reply answers every question ===
Order matters; each step has cost a round trip when skipped.

A. CONTRACT FREEZE. Write the contract into STATE.md and the docstring of
   tests/test_outputs.py. Sort every graded quantity into real work (two correct
   implementations agree by construction) versus implementation choice (never graded).
   Write authoring/variants/ from the reference plus one declared override each
   (make_variants.py pattern); hand-copied variants drift. Write authoring/readings.py and
   authoring/decisions.py now, not later.
B. ENVIRONMENT. Integer arithmetic, seconds to run, no comments/docstrings/.md, identifiers
   degraded to legacy register and uniformly (never noise, never a lie), and record the
   degraded-naming rationale in difficulty_explanation. Ship runnable case files and a
   runner printing one record per line. Then the leak audit as a PROCEDURE: for each
   graded decision, try to reproduce the answer from shipped files with a join, a sort or a
   field comparison, and for every PAIR of exposed numeric fields ask whether a-b, a==b or
   len(a)==len(b) witnesses the hidden thing. No unused imports, no unused public
   functions, no field written and never read (deadfieldcheck), no manifest, no
   self-labelling data, no shipped validator that needs the derivation. Every editable
   artifact must actually need to change. .dockerignore uses **/__pycache__ and **/*.pyc.
C. VERIFIER, written fresh (copying tests/reap.py, test.sh, runner.py or either Dockerfile
   from another bundle is half a similarity rejection; simcheck must be clear).
   Overlay pattern, pristine tree hashed after the run, root-only gt.json/oracle.py/
   test_outputs.py, privilege drop, reward locked first and default 0, setsid --wait,
   reap.py walking /proc. Grade evidence: source-side journal, sys.monitoring tally kept in
   a closure (tool ids 3 or 4 only; bind callbacks once, never as bound-method attributes;
   tolerant teardown setting armed=False), function fingerprints checked against a baseline
   compiled from pristine sources. Every comparison loop asserts the count of files it
   found before comparing. Generators sort every collection before use and pass
   determinism.py under several PYTHONHASHSEED values. Enumerated cases plus 300
   nonce-generated cases built inside the verifier. Grade a ceiling or a range where a
   better correct answer could exist; never publish the target. tests/Dockerfile gives
   every artifact parent its own plain `RUN mkdir -p <parent>` line, never chained
   behind &&. Every literal the grader matches on appears verbatim in the brief.
D. REFERENCE. solution/*.py beside solve.sh; solve.sh copies them and runs the
   environment, never inlines (solvecheck). Prove the reference against the sealed model
   on hand-written and 300+ generated cases before build_gt.py writes anything. If you
   built a speed regime: time reference vs naive on it now; record the reference's time on
   one fixed case in STATE.md, and measure inside `docker run --cpus=N --memory=Mm` with
   1.5x headroom scaled by the host factor.
E. CHEATS. Single-mistake swaps generated from the reference by emit.py (refuse a swap
   where old==new), one per wrong reading, plus a cheat generated from gt.json itself
   (forgecheck), plus the isolation probes built on the SHIPPED tree and the attestation
   probes built on the REFERENCE with one layer interfered with; every probe's payload
   inside a declared artifact; cheat_report asserts WHICH test catches each and that
   attestation probes are caught by their own layer and nothing else. A cheat scoring 1 is
   a correct variant, a hole in the case set (fuzz against the oracle, shrink, add the
   case), a dead branch (instrument and delete), or a swap the stated input space makes
   unobservable (drop it). Shrink every wrong reading to a hand-written counterexample so
   failures name the rule; readingcheck must report all separated.
F. THE BRIEF, written AFTER running the shipped broken tree, quoting its real output
   verbatim (print it first, copy what appears). Team voice (we/our), symptom then goal
   then rules, every path and filename in backticks, no headings or labelled buckets, no
   preamble, no padding, no refuted candidate rules, no method, no counts, plain ASCII,
   the exact suffix with N equal to [agent] timeout_sec. No staged casualness. Then the
   coverage walk BOTH directions: for every graded decision name the sentence that decides
   it; for every sentence name the assertion. Run textcheck against
   tasks/rollout-cache-coherence, tasks/guard-mark-unwind and tasks/grant-spread-order,
   structcheck, hintcheck; repair inside the existing voice, rejoin clauses rather than
   chop, and ignore the two documented outliers (checkpoint's short-sentence bar,
   turn-seam's paragraph sd). difficulty_explanation states the concrete step that breaks
   an agent, what the data is and whether it is realistic, and who does this work.
G. THE SELF-PROBE (replaces the three-agent probe; do not skip it and do not delegate it).
   Copy environment/app_src and instruction.md alone into the scratchpad. Play the solving
   agent cold: write your first plan BEFORE opening a file, then implement in one pass, no
   peeking at tests/ or solution/. Record: did you write the editable files correctly on
   the first Write? Could you build a harness that confirmed every rule? Where did you get
   confirmation, and what did you have to guess? Grade the result through the real
   verifier (docker_trial2 or the host emulation), never by your own report. Then run
   tools/leakcheck.py on your own write-up against the brief, tools/onelinecheck.py, and
   ablate your solve one decision at a time to get a number per cause. Read it like a
   rejection: a first-shot correct write is mode C; the winning line in the brief's
   vocabulary is mode A (delete the sentences); a short predicate over exposed fields is
   mode B (close the pair once, then add a second discovery); confidence before finishing
   is mode D (remove the confirmation). Every guess is an undecided rule: state it as a
   requirement. Then repair and repeat until your own cold solve is not a one-shot.
H. GATES, all of them, in the stage-7 list of CLAUDE.md: sync, build_gt, emit,
   variant_check, field_report, cheat_report, fuzz, determinism, tiecheck, docker_trial2
   --all and --variants (or the host emulation, saying which gates it does not cover),
   solvecheck, deadfieldcheck, catcheck, readingcheck, onelinecheck, hintcheck,
   structcheck, textcheck, simcheck, forgecheck, preflight (sort each finding by which
   gate it predicts; the environment bans are difficulty rules, not style), then
   `ls tasks/<slug>` for stray scratch (everything under authoring/ ships and must stand
   alone; delete scratch), package.py, zipfix on Windows, zipcheck LAST on the zip. Before
   editing a task that has been submitted, diff the tree against the archive that was
   actually sent.
I. DELIVER. Land every lesson in CLAUDE.md (gate, date, measured numbers, fix; a
   rejection not written there did not happen), merge origin/main again, push, and send
   the rebuilt zip with SendUserFile in the same reply. The handover states plainly which
   gates ran and which did not; a local gate means "not rejected for a known reason",
   never "will pass".

=== IF THE JOB IS A REJECTION ===
Diagnose from the note and the numbers, never from the score. `verifier 0s` on the oracle
row is packaging (mode bits, CRLF); `verifier 1s` is the task. Read runtimes before
transcripts: minutes against a 14400 s budget means the plan was available on sight;
16-34 minutes all completing on a 0/8 means agents decided they were done, so state the
input space and the undecided rules, never the rule or the count. Get the trajectory,
reconstruct the submission, grade it, ablate. Pick the repair by mode (A delete sentences;
B close the pair then add a second discovery; C an axis the solver's own harness cannot
check, or a semantic scaling boundary with the limit disclosed; D remove confirmation), and
apply one repair. A rejection note names an example, not a scope: fix the named defect,
walk the set for its siblings, and leave a brief that cleared the AI screen byte-identical
otherwise. `difficult` failing twice means the mechanism's core is one insight: enrich the
environment with interacting stated rules, not the brief. Category names the skill the
environment exercises, not the story. Backticks on every path. Every literal the grader
matches goes in the brief. Two-line metadata fixes stay two lines.
```

---

## What it cannot do

- **It cannot make the probes deterministic.** Eight agents, band 1 to 6; three agents,
  band 0 to 1. A well-built task can still land at 0 or 7.
- **It cannot pick the seed for you.** Section 3 of the proposal is where the task lives or
  dies, and it needs the owner's judgment about what has already been graded here.
- **It cannot verify the AI-text screen.** Six rejections say a model rewriting a refused
  brief is a coin flip with bad odds; the variable left is who writes the prose.
- **The self-probe is one agent, and it is the author.** It catches mode A, B and C
  signatures reliably (the one-shot write, the quoted sentence, the field pair) and it
  understates difficulty. 0 of 1 from yourself is not evidence the task is hard.
