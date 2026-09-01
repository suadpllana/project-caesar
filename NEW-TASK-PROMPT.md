# The prompt for building the next task

Paste the block below into a fresh session. It encodes what was actually measured across
ten tasks and eleven pipeline rejections, and it is written as instructions to the session
rather than notes to a person.

**It does not guarantee a pass and nothing can.** The difficulty probe is eight stochastic
agents and the band is 1 to 6 solves; every task in this repo that eventually passed was
rejected at least once first. What this removes is the *known* causes of rejection, which
is a different and achievable thing. Read "What it cannot do" at the bottom before trusting
it.

---

```
Build a new Frontier Bench task in this repo, end to end, from seed to packaged zip.

READ FIRST, in this order, and do not start designing until you have:
  1. CLAUDE.md, the section "Landing inside the band" - the method, and the only section
     that is about hitting the band rather than about one past rejection.
  2. CLAUDE.md, "Standing policy: every rejection becomes a gate", and the gate list in
     stage 7.
  3. docs/RULES.md and docs/DIFFICULTY.md. docs/ is authoritative on the rules; CLAUDE.md
     is the practice on top of it, with numbers.
Then run `git fetch origin main && git merge origin/main`. main is pushed to directly here
and moves under you.

THE DESIGN, and these are the constraints that have actually cost round trips:

- Exactly ONE thing must be derived, plus a SECOND discovery that invalidates the natural
  implementation of the first. Everything else in the task is stated outright in the brief.
  Peripheral rules do not add difficulty, they add lottery: under all-or-nothing grading a
  chain of eight independent guesses is how a well-designed task scores 0 of 8.
- Do NOT grade work counters against an unpublished budget. Five tasks here do, and the
  similarity screen rejected the fifth for it. Grade something else: a trace, a schedule, a
  reconstructed state, a decision under a rule.
- Ask at contract time: what is graded, and has anything in tasks/ graded that before? If
  yes it is a reskin however new the domain is.
- Every graded quantity must be one that two correct implementations agree on by
  construction. If they can disagree, it is implementation choice and grading it fails the
  run audit. Write two alternative correct implementations into authoring/variants/ BEFORE
  freezing the contract, and require both to score 1.
- Write the verifier plumbing fresh. Copying tests/reap.py and environment/Dockerfile
  byte-for-byte from another task is half of why a submission was called too similar.

THE BRIEF - state requirements and the input space, never the reasoning, never counts:

- For every graded decision, name the sentence that decides it. Not "is the topic covered"
  but: which sentence, read by someone who has never seen the tests, returns the answer the
  verifier wants. A rule phrased around one participant leaves every neighbouring case
  undecided, and that single defect has now caused a human-review rejection, a difficulty
  rejection and a probe failure in three different tasks.
- SAFE to state: a requirement the verifier grades; the input space, meaning that a
  situation occurs and is graded. Stating the input space is what took a task from 0 of 8
  to a pass, because it makes an expert ask the question without answering it.
- NEVER state: the rule the task is built on; how many decisions are wrong; any graded
  number or target counter; a candidate rule you intend to reject ("the cheap test is X,
  and X is wrong" is always a leak).
- Write the brief AFTER running the environment, and quote real output from the shipped
  broken tree. A brief written about a task instead of from one is what the AI-text screen
  keeps finding.
- Then: textcheck against tasks/rollout-cache-coherence/instruction.md and clear every
  finding. Two known checker outliers you should NOT restructure over, both recorded in
  CLAUDE.md: checkpoint's 44% short-sentence bar, and turn-seam's paragraph sd of 85.

BEFORE PACKAGING, run these and fix what they say:

  python3 tools/deadfieldcheck.py <slug>    # anything written and never read is a false
                                            # affordance; a strong agent builds a rule on
                                            # it precisely because it is dead
  python3 tools/readingcheck.py <slug>      # write the plausible-but-wrong readings into
                                            # authoring/readings.py first. Per-rule
                                            # coverage is not coverage: the question is
                                            # whether a specific wrong reading survives the
                                            # whole enumerated set
  python3 tools/onelinecheck.py <slug>      # needs authoring/decisions.py
  python3 tools/solvecheck.py <slug>        # solve.sh copies the reference, never inlines it
  python3 tools/forgecheck.py <slug>        # a cheat built from the task's own gt.json
                                            # must score 0
  python3 tools/hintcheck.py <slug>
  python3 tools/simcheck.py <slug>
  python3 tools/structcheck.py <brief>
  python3 tools/docker_trial2.py <slug> --all
  python3 tools/docker_trial2.py <slug> --variants
  python3 scripts/preflight.py tasks/<slug>
  python3 scripts/package.py tasks/<slug>
  python3 tools/zipcheck.py <slug>          # last, on the zip: the tree passing every gate
                                            # says nothing about the archive

THEN RUN THE PROBE, and this is the step that is usually skipped:

Spawn three subagents in sealed copies of environment/app_src, each given the instruction
and the data only - no tests/, no solution/, no repo access. GRADE THEIR SUBMISSIONS
THROUGH THE REAL VERIFIER. Do not believe their reports; a report is a claim.

Then ask each one, and act on the answers:
  - Where did you get CONFIRMATION that you were right? Every confirmation source is a
    leak. A task that confirms its own answer at every stage is a constraint-satisfaction
    puzzle and gets solved 3 of 3.
  - What did you have to GUESS? Every guess is an undecided rule. Both agents that failed
    this repo's worst rejection flagged their own guesses in writing before anyone graded
    them, and both guesses were task defects rather than difficulty.

Reading the result: 0 of 3 locally is not proof of difficulty, since a local probe is
handicapped on time; 2 or 3 of 3 is an easiness rejection signal. If an agent scored 0 but
was one clause away, that clause is almost certainly an undecided rule and not the
difficulty - reconstruct its submission, ablate one decision at a time, and get a number
for each cause before changing anything.

DELIVERABLE: the packaged zip, plus a handover that states plainly which gates were run and
which were NOT. A gate reports "not yet rejected for a known reason", never "will pass".
Land whatever you learn in CLAUDE.md before reporting done - that is the deliverable that
makes the next task cheaper, and a lesson left in the chat is lost when the session ends.
```

---

## What it cannot do

- **It cannot make the probe deterministic.** Eight agents, band 1 to 6. A task can be well
  built and still land at 0 or at 7.
- **It cannot pick the seed.** The single highest-leverage decision is what to grade, and
  it needs judgement about what has already been graded here.
- **It cannot verify the AI-text screen.** Three rejections on one brief with both local
  checkers clean; the honest reading recorded in CLAUDE.md is that the remaining variable
  is who writes the prose.
- **`readingcheck.py` needs you to write the wrong readings.** The tool runs them; it
  cannot imagine them. Take them from probe trajectories, which is where the real ones came
  from.
