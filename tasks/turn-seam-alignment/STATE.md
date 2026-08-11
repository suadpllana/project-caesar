# Task state

## Current stage

`Stage 7 - Pre-flight and packaging`

## Assistant's assigned role

Senior engineer on the data path between a rollout worker and a trainer for multi-turn
RL: chat templates, tool turns, incremental tokenization, loss masks, and the accounting
that decides whether the worker is network-bound or tokenizer-bound.

## Source repository

- Repo URL: https://github.com/vllm-project/vllm (issue tracker used as the seed only)
- Task shape chosen: authored on top, not an ablation of upstream code. No vLLM source is
  vendored. The loop in `environment/app_src/` is written for this task: a CPU-only,
  integer-arithmetic multi-turn rollout worker with the same organs (byte-pair tokenizer
  with a real merge table, chat template with block markers, a recurrent integer network
  with prefix state reuse, a generator, an episode driver, a per-episode encode cache).
- Why not vendor: vLLM's own code is public and diffable, and the accepted design for the
  closest public issue is public with it. Writing the worker means the shipped tree
  matches no public repository, while the failure mode is the real one.
- Seed issues, for reviewers: `vllm-project/vllm#47582` ("[RFC]: Opt-in incremental
  prompt encoding for multi-turn chat"), whose proposed recipe - back a fixed number of
  characters up from the seam, cut at a pre-tokenizer boundary, re-encode the appended
  part, verify the overlap and fall back to a full encode - is the plan this task is
  built to punish; and `vllm-project/vllm#48305` ("[RFC] Training-Inference Consistency
  for RL"), whose first category is logprob and token-id replay, which is what the
  trainable spans here are for.
- Proper-noun sweep: the shipped tree carries no project, product, company or person
  name, no upstream identifiers, no distinctive error strings and no URLs. Identifiers
  are in the register of ordinary internal code (`tok`, `inc`, `rec`, `ep`, `rt`, `WID`,
  `MG`).
- Upstream-diff check: there is nothing to diff. An agent that finds both seed issues
  learns the failure mode, which the instruction already states, and learns the public
  recipe, which is `cheat-space-anchor.sh` and `cheat-verify-and-fallback.sh`, both of
  which score 0.

## Task summary

The agent gets a working multi-turn rollout worker. Each episode renders a conversation,
encodes it, samples a reply, appends a tool result and goes round again; at the end the
worker hands the trainer the finished token sequence and the run of positions each
surviving reply owns. Two things are wrong. Replies keep positions holding symbols the
sampler never emitted, and the tokenizer is fed the whole render on every turn. The agent
must make the sequence identical to a full encode of the finished render, make the spans
exact in both directions, and stop paying for characters that could not have moved.
Four files may be edited; everything else is restored from a pristine copy before grading.

## Why it is hard

One question about boundaries that is really two questions with different answers, and
nothing in the tree that says so.

- **Where an encode may be resumed** is a property of the merge table alone. A boundary
  survives every surrounding text when nothing can reach across it, and there are two
  independent ways for that to hold: the character after it never sits anywhere but at
  the front of a symbol, or the character before it never sits anywhere but at the end of
  one. Neither implies the other. Both sets carry positions the other misses.
- **Where a reply's trainable run ends** is a property of the finished sequence. It stops
  at the first position where that sequence stops agreeing with the prompt the sampler
  was handed followed by what it produced. That point is usually later than the resume
  point, and when it lands before the reply began, the reply owns nothing.

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan: the first plan is the published one -
  back off a fixed distance, cut at whitespace, re-encode the tail, verify against a full
  encode. It produces the right tokens on almost every scenario and fails the character
  accounting, which only surfaces at the verifier. The second plan, once the merge table
  is read, is the front-only condition, which is safe, natural, and still too expensive.
  Forming the correct plan means noticing that a boundary has two sides.
- Tactics (docs/DIFFICULTY.md):
  - Prong A1/A2: the retrieved recipe is specifically wrong here, and the concept is
    never named - the instruction says "a token boundary whatever text sits either side
    of it".
  - Prong A3: correctness and cost pull against each other; no remembered recipe
    satisfies both, because the cheap recipes are unsafe and the safe recipes are dear.
  - Prong B1: the merge table is only in `tok/merges.json`, the block layout only in
    `chat/tmpl.py`, the counters in `tok/core.py` and `model/net.py`, the state reuse in
    `loop/gen.py` - none of them editable, and the tree carries no comments.
  - Prong B2: append, retry, truncation, interleaved episodes, a reply whose prompt moved
    and a discarded turn all have to hold at once.
  - Prong C1: fenced both ways - `short-reply`, `truncated` and `one-turn` fail an
    overcautious span rule, `anchor-dense` fails a resume that walks back too far, and
    `back-reach` fails one that does not walk back at all.
  - Prong C3: the character accounting is a real resource gate that a correct-and-safe
    loop fails while producing every token and every span correctly.
  - Prong C2: the obvious oracle is denied by half. The agent can check its token
    sequences against a full encode it runs itself. It cannot check the character count
    against anything.
- Assistant's attack on the plan: my first plan was the published recipe, a fixed backoff
  to a whitespace boundary with a verify pass. My second plan, after reading the table,
  was the front-only condition. Both are in `cheat/` and both score 0. Getting to the
  third took working out that the two conditions are independent, which is also the point
  at which the first design of this task was found to be wrong: the reference itself was
  the front-only rule until the environment was probed for cheaper safe resumes and one
  was found.
- Estimated solves out of 8: 1 to 2.
- Expert path, step by step:
  1. Run `/app/run_rollout.py` and see the reply that keeps a position holding a symbol
     it never emitted, and the character count against the size of the conversation.
  2. Read `tok/core.py` and `tok/merges.json`, and work out what the encoder can and
     cannot join.
  3. Derive the resume points from the table: characters that never sit anywhere but at
     the front of a symbol, and characters that never sit anywhere but at the end of one,
     and notice that the union is what is wanted rather than either half.
  4. Read `chat/tmpl.py` and see that the marker opening a reply satisfies neither, so
     the boundary in front of a reply depends on what the reply starts with.
  5. Write the resume as one walk back from the first character that moved, which makes
     the retry case fall out instead of needing a branch.
  6. Read `loop/ep.py` and `loop/rec.py` and separate the two boundaries: the span is
     measured against the whole of what the sampler ran against, at the end of the
     episode, not at the end of the turn.
  7. Drive scenarios of their own through `run_rollout.py` until the counts stop moving
     for the wrong reasons.
- Originality check: searched for public write-ups of incremental byte-pair encoding
  across chat turns and of assistant-span masking in multi-turn RL. What exists is the
  RFC above with its backoff-and-verify recipe, the general advice to carry token ids
  rather than text, and discussion of tokenizer round-trip mismatch. Nothing anywhere
  makes the two-sided boundary distinction this task is built on, and no public code has
  this worker's shape.

## Verifier contract - FROZEN

- Artifacts: `/app/tok/inc.py`, `/app/tok/store.py`, `/app/loop/ep.py`,
  `/app/loop/rec.py`. Nothing else is read from the agent's container.
- The verifier bakes a pristine copy of the shipped tree, overlays those four paths onto
  it, and runs the worker over the twelve scenarios in `tests/scen.py`.
- Checked per scenario, all-or-nothing: every episode's finished token sequence; every
  surviving turn's trainable span, in turn order; `enc_chars`, `enc_calls`, `fwd`; the
  lifecycle trace in order.
- The expected sequences, spans, forwards and trace are re-proved at verification time by
  `tests/oracle.py`, a sealed naive replay sharing no code with the tree.
- Tolerances: none. Everything is integer arithmetic and exact.
- Ground truth: `tests/gt.json`, generated by `authoring/build_gt.py`, root-only in the
  verifier image.

## Decisions and their reasons

- `enc_chars` and `enc_calls` are the only graded numbers the sealed replay does not
  model, by design: the replay is the naive loop, and being expensive is the one thing it
  is not asked to reproduce. Everything else is proved independently.
- The counters are incremented in `tok/core.py` and `model/net.py`, both outside the
  editable set, so they measure real work for any implementation.
- The reference `store.py` is unchanged from the shipped file. It stays in the artifact
  set anyway: naming only the files that need changing would hand over the diagnosis.
- `\x02`, the marker that opens a reply, satisfies neither boundary condition. That is
  what makes the resume point content-dependent rather than a fixed offset, and it is
  asserted in `authoring/mktok.py` rather than left to chance.
- `#` and `@` are the left half of merges and never the right half, so the crude test
  ("takes part in no merge") finds a strictly smaller set than the front-only condition,
  which in turn finds a strictly smaller set than the union. Three safe rules, three
  different bills.
- A span rule that compares only from the turn's own first generated position was written
  as a cheat and then removed: a search over six thousand random episodes found no case
  where it differs from the reference, because a change inside a prompt always shifts the
  positions after it. It is an equivalent solution, not a wrong one, so shipping it as a
  cheat would have been a verifier bug.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Both images build | pass | `tools/docker_trial_seam.py --build`; base image had to come from a mirror and the sandbox's proxy CA had to be injected for pip, neither of which the shipped Dockerfiles carry |
| No answer leaked into agent image | pass | the built image holds 18 files: the worker, its merge table, its config, the runner. Sweep cheat finds nothing |
| Oracle = 1 | pass | real two-container run, and the host emulation |
| Nop = 0 | pass | real two-container run, and the host emulation |
| Cheats all score 0 | pass | 16 of 16 on the real images, including the five reward-tamper probes. The privilege probe reports uid 1002 and PermissionError on the reward channel, the ground truth, the pristine tree and the tests |
| Ground truth proved | pass | `authoring/build_gt.py` refuses to write a scenario the sealed replay does not confirm; the verifier repeats the proof |
| `preflight.py` | pass | clean, no warnings |
| `textcheck.py` | pass | no findings against either instruction known to have passed the screen |
| `harbor check` rubric | not run | `harbor` is not installed in this sandbox |

## Open questions and next steps

- `instruction.md` measures clean against both passing briefs (burstiness 0.903 against
  0.926 and 0.938, 30 per cent short sentences, zero stock vocabulary, hedges, antithesis
  constructions, dash asides and first-person singular). No measurement can certify a
  classifier verdict, and it still wants the contributor's own read before submission.
- The design was rebuilt once, mid-authoring. The first version graded a resume rule that
  used only the front-only condition, and probing the environment for cheaper safe
  resumes found that the boundary after the reply marker was free, which made the
  reference non-minimal against its own stated rule. The merge table generator now
  asserts that the marker reaches rightwards, and both conditions are load-bearing.
- `harbor check` has not been run; `harbor` is not installed here. Every other gate has.
