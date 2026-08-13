# Designing for difficulty

The difficulty band — solved 1 to 6 times out of 8 — is where tasks die, in both directions.
This file is the doctrine for clearing it, written for the assistant to use with the contributor
during idea intake (Stage 1), verifier design (Stage 2), and the final re-attack (Stage 7).

It is organized around a single strategy. Everything else in the file — every tactic, every test,
every anti-pattern — exists to serve it.

One headline finding from studying approved tasks, before anything else: **none of them relies on
secrecy.** Every one is fully specified and fully testable locally, with nothing hidden from the
agent. Designs that hide information slide toward unverifiable — and a task solved zero times is
rejected exactly like one solved eight times.

## The strategy: defeat the planning stage

Frontier agents do not fail at execution. Once the right method and strategy are settled, they
carry them out with high consistency — they iterate, self-correct, rerun tests, and grind through
length without tiring. If the correct plan for a task can be formed in one shot — from the
instruction, from the model's prior, or from one good search — the task will be solved 7 or 8
times out of 8, however long and intricate the execution that follows.

**So the object of attack is the plan.** A task clears the band when one-shot planning is
impossible: when the agent must reason through every step of even the *plan*, must gather evidence
from the environment before the plan can exist at all, and discovers partway through execution
that the plan it committed to was wrong. Difficulty is reasoning depth at plan time — never weight
at execution time. Heavy traffic and massiveness add grinding, and grinding is what executors are
best at.

A plan survives contact with a task when three things hold: the default approach is correct, the
facts needed to plan are available up front, and errors surface early enough to be cheap. The
strategy is to invert all three:

- **Prong A — poison the default plan.** The obvious method — memorized, idiomatic, top search
  result — must be specifically wrong. The instruction is domain-specific, twisted, targeting the
  edge cases and niche situations an expert confronts daily, exactly where the general answer
  stops applying.
- **Prong B — withhold the correct plan.** The information needed to form the right plan must not
  sit in the instruction or in any single file. It must be assembled by exploring the environment
  and correlating what is found.
- **Prong C — make the wrong plan fatal, and late.** The plan's wrongness surfaces deep into
  execution, where recovery is not a patch but a replan, paid for inside the time budget.

Plus one guard that protects all three: **block the route-around**, so the agent cannot reshape
the task into a form where its default plan works after all.

## The search test

The probe agents run with open internet, which means the planning stage can be outsourced to
retrieval: every paper, thread and repository is one query away. Obscurity is not difficulty and
rare knowledge is not a moat — the originality screen already kills tasks whose solution is
written up anywhere.

Ask of every design: **suppose the agent finds the best possible page for this task — does that
page help it plan?** The design survives only if the honest answer is no:

- The spec deviates from the convention every search result follows (Prong A), so the better the
  retrieved source, the more confidently wrong the plan built on it.
- The concept is unnamed (tactic A2), so forming the search query requires the recognition that is
  itself the hard step.
- The task is a conjunction no single source covers, in an environment no page describes
  (Prong B): every component is documented somewhere, the combination exists nowhere.

If a single page or repository substantially plans the task, the idea is dead regardless of how
rare the knowledge felt. This is also what keeps difficulty *fair*: nothing is withheld — the
deviation is stated plainly, and the agent can test locally without limit. It fails not for lack
of information but because forming and holding the right plan, against both its prior and
everything it can retrieve, is the actual work.

## Prong A — poison the default plan

**A1. Make the model's prior a liability.** Specify behavior that contradicts the memorized
default — the convention every implementation in the training data follows, deliberately inverted
and clearly specified. The model must fight its instincts at every decision point, and any lapse
into the familiar idiom is a wrong answer. Retrieval stops helping and starts hurting.

**A2. Describe the concept; never name it.** If the task embodies a known-hard concept, write the
spec operationally — as an incident, a behavior list, a business story — without the term of art.
Named, the concept is a lookup key and the model retrieves the algorithm-shaped plan. Unnamed, the
model must recognize or re-derive it, and half-recognition plans for a familiar simpler variant
that fails exactly the case that matters. Keep every fact visible; withhold only the vocabulary.

**A3. Demand requirements no single known technique satisfies.** Pair constraints whose textbook
solutions are mutually exclusive, so no retrieved plan can be adopted whole and the model must
synthesize a hybrid and reason about where each part applies.

## Prong B — withhold the correct plan

**B1. Spread the load-bearing facts through a deep, coupled project.** Build the environment as a
realistic project: many files, nested modules, a deep folder graph — with the couplings real
systems actually have. The constraint lives in one module and its consumer in another; config
indirection decides which code path is live; the invariant that matters is enforced in a distant
utility; changing X quietly requires understanding Y's assumption two directories away. A correct
plan cannot be written from the instruction alone — it must be assembled by reading and
correlating evidence across the tree, which is exactly the exploration cost that defeats one-shot
planning.

The discipline: **coupling counts only when it carries a decision the plan depends on.** A
directory that could be deleted without changing the correct plan is scenery — real repos have
scenery and a little is realistic, but bulk without decisions is the scale anti-pattern, and a
gratuitous maze is rejected by the quality review as an artificial handicap. The structure must
stay the shape of a real project, and it must still build within the storage and build-timeout
caps.

**Distribution is relative to attention, not to file count.** Spreading facts across seven files
withholds nothing if the whole system is 500 lines — at that size "distributed" just means
"adjacent", and the agent reads it all in two tool calls. Before claiming B1, ask honestly whether
the tree exceeds what a frontier agent can hold at once; if it does not, the facts are effectively
in one place however many files they occupy, and the difficulty has to come from somewhere else.

Part of the same tactic: **the environment explains itself through code alone — a strict rule,
enforced by preflight, not a style preference.** The agent-facing tree ships with no comments, no
docstrings, no READMEs, no docs directories — and no `.md` files at all, by extension, whatever
their name or purpose (only exceptions anywhere: extensionless legal notices and machine-read
directives). Documentation is plan-delivery — each explanation hands the agent a piece of the
plan it should have had to earn by reading. If the tree holds a genuine interface contract the
agent could not infer from code, the smallest necessary part moves into the instruction as plain
requirements — a last resort, not a habit — and it never stays in the tree. Two boundaries hold it fair: never plant *false* documentation (stale and
missing is realistic; lying is a trap, and traps fail the quality review), and the rule covers
only what the agent can read — verifier code stays well-commented, because the quality review
requires informative test structure.

The tactic extends from prose to **naming**. Internal identifiers can be degraded to the register
of real legacy code — a trace of meaning left, nothing announced: `retry_backoff_ms` as `rb_ms`,
`write_queue_length` as `qlen`. Proper nouns go further: any name that could identify where the
problem came from — project, company, product and people's names, codenames, distinctive error
strings, URLs — is a ready-made search query and is deleted completely, not degraded (public
standards the task legitimately involves, like TCP or JSON, stay). This is fair for the
same reason sparse documentation is fair: an
expert deduces what a thing is not from its label but from its **connection mechanism** — what
calls it, what mutates it, what its value flows into, what breaks when it is wrong. The meaning
stays fully recoverable from structure and behavior; only the shortcut of reading it off the name
is gone, which converts label-lookup into the model-building work Prong B exists to force. Same
two boundaries: never degrade to noise (random letters read as deliberate obfuscation — an
artificial handicap), and never rename into a lie (a name that misdescribes its value is a trap).
The author keeps a conversion table on the solution side and never lets it near the agent's
environment.

**B2. Stack small rules that must hold simultaneously.** Many individually easy requirements —
lifecycle edge cases, idempotency, cleanup, state distinctions the obvious design collapses —
interacting under concurrency or asynchrony. Each is trivial; the conjunction is the point: the
correct plan becomes larger than any remembered template, and one unplanned-for rule anywhere
fails a case.

**Conjunction only bites under one of two conditions**, and stacking rules without either produces
a checklist, not a planning problem: the rules **interact** — getting one right changes what
"right" means for another — or there is **no per-rule feedback**, so the agent cannot confirm them
one at a time and must commit to all of them at once. Six independently readable, independently
verifiable rules are six easy tasks in a trenchcoat.

## Prong C — make the wrong plan fatal, and late

**C1. Fence correctness from both sides.** Specify what must fail *and* what must still work. The
instinctive replan overshoots — stricter, more conservative, more aborts — so write the
must-still-work cases into the spec and the verifier. A task that only tests the failure side is
solved by overshooting; a razor-edge predicate tested from both sides cannot be.

**C2. Take away the obvious oracle.** If the model's natural way to validate its plan is to
compare against a standard library, a reference tool, or "run it and see", make that check
unavailable or misleading: semantics that deliberately differ from the standard tool, or failures
invisible in normal operation and only present under constructed orderings. The model must then
reason about whether its plan is right instead of testing its way there — and a wrong plan stays
undetected until the verifier, where it is fatal.

**C3. Ban the naive-but-correct implementation with a resource gate.** Add a performance, memory,
or scaling bound — enforced by a real test — that the straightforward implementation fails even
when its answers are right. The first plan can be semantically perfect and still die, forcing a
redesign at the planning level, not a patch.

**C4. Grade adversarially, exhaustively, all-or-nothing.** Large randomized case sets over an
unbounded input space force genuine generality — no enumerating a way to a pass. Alongside them,
*enumerated* corner cases aimed precisely where the obvious plan diverges from the spec. Every
case must pass; 99% correct scores zero. The verifier must construct the adversarial orderings and
edge inputs itself — if failures only appear under conditions the grader does not create, the task
is easy in practice no matter how hard it is in principle.

## The guard — block the route-around

One editable file; everything else hash-checked; interfaces frozen. The model must not be able to
restructure the problem into a shape its default plan handles — a route-around converts a
planning-stage task back into an execution task, and execution tasks get solved 8 times.

## What not to ship — the leak audit

The prongs above say what to *build*. This says what must not be in the bundle, and it is where
carefully designed difficulty quietly dies: the mechanism is real, and the environment hands the
agent a way around it.

**The test, applied to every mechanism before you ship it:** *what in the bundle would let an
agent **discover**, **name**, or **verify** this without reasoning about it?* If the answer is not
"nothing", the mechanism is decoration. Three defeats, any one of which is fatal on its own —
discovery (finding the trap without inferring it), naming (the environment says what the thing
is), verification (checking the answer against something shipped).

**Run it as a procedure, not as a feeling.** Prose audits pass tasks that a five-line script
would have failed. For each stage you counted as difficulty, write down the answer that stage
is supposed to produce, then try to reproduce it from the shipped files with no domain
reasoning at all — a join, a sort, a field comparison. Actually write the script and run it.
If it prints the right answer, that stage is worth zero, however hard the chemistry or the
concurrency behind it looks. This is the single highest-yield check before a probe run,
because it is the failure the easiness probe finds and you cannot argue with a script that
already produced the answer.

The recurring shape, worth its own name: **a stored derived quantity.** Real formats often
carry a value that a practitioner would compute — explicit hydrogen counts on an atom record,
a precomputed length, a cached total, a denormalised id. Ship it and the reasoning that would
have produced it is retired, and worse, it usually joins straight onto whatever observable you
published as the puzzle. The rule: **ship the primitives, never the derivation.** If the task
is about deriving X, X must not appear as a field anywhere in the agent's tree — and check
that the observable you publish in its place still needs the derivation before it discriminates.

Two guards when you remove one, both of which cost minutes and save a rejection:

- **The replacement must not be arbitrary.** Recomputing a value sometimes has legitimately
  several answers (which of two chemically equivalent oxygens carries the proton, which of two
  equally old entries a sweep evicts). Prove the choice cannot move the graded output — swap it
  and diff — or you have traded a leak for a run-audit failure, which is the worse of the two.
- **The shipped validator must not become the oracle.** A schema checker that also needs the
  derivation you just removed hands it back: the agent brute-forces inputs until the checker
  stops complaining. Cut the check down to what it can verify without deriving, and reword its
  messages so they do not claim more than they check.

**1. No unused affordances.** A public function nothing calls is a table of contents. A helper
that exists only because the trap needs it announces both that the trap exists and where to start.
If a capability is not reachable through the system's real behavior, delete it — the agent must
reach the mechanism through evidence, never through a named entry point.

**2. No manifests.** A config file enumerating the inputs (`void_source`, `state_store`,
`ops_log`) converts exploration into reading an index. Real systems do have manifests, so this is
a judgment call, but every entry has to earn its keep: if it exists to help the agent find things,
it is a map to the solution.

**3. No self-labelling data.** A column whose values read `postponed / abandoned / withdrawn`, a
log line saying `settle fail lock_held` in plain English — an annotated anomaly is not an anomaly,
it is a specification. The agent never has to infer that something went wrong, because the data
asserts it. Anomalies must be visible only as *behavior that does not add up*.

**4. No artifact that is a function of the correct trajectory.** Anything deterministically
derivable from doing the work correctly is an oracle, however you frame it — and a *per-key* diff
against it is not a checksum, it is a debugger: it converts a reasoning problem into gradient
descent, which is exactly what frontier agents are best at. Watch the justification "fair local
testability", which conflates two different things: letting the agent **run** its work is required;
handing it a **scoring function for its intermediate state** is not.

**5. No free join keys, and nothing callable that you counted as difficulty.** Handing over an
identifier retires every trap that guarded its derivation — one `book=25023` can kill the session
boundary, the time offset and window membership at once. Likewise, anything reachable by calling a
shipped function is API surface, not difficulty: if `publish()` is callable verbatim, its window,
cap, ranking and threshold rules are free, no matter how load-bearing they look in your notes.
Only what the agent must *reconstruct* counts.

**6. No per-axis confirmation before commit.** If the agent gets a green signal on each sub-part
as it goes, nothing fails late and Prong C is absent in practice however it was designed. Related:
a subtle rule implemented in one legible line — a sort key that states the whole batching story —
is equivalent to a comment explaining it. Subtlety must live in the interaction of ordinary-looking
parts.

**And the discipline that makes it stick:** when you find one of these, fix the *class*, not the
instance. The recurring failure is an author who removes one oracle, writes down the lesson, then
ships three more oracles in different shapes. Re-run the whole audit after every change.

One honest trade: every oracle you remove raises difficulty *and* raises the risk of zero solves.
The answer is not to keep the oracle — an expert solves by understanding the system, not by
diffing against a shipped answer — it is to make the reference solution prove the expert path
harder. Removing hill-climbing is not the same as removing solvability.

## What does not create difficulty

- **Scale, repetition, heavy traffic.** More episodes, more data, longer horizons, more volume —
  grinding, not difficulty. Execution weight is the thing frontier agents are best at; an agent
  that can do the thing once does it N times.
- **A spec that matches the literature.** If the well-known strategy is also the correct one, the
  plan is retrieved, not formed — a retrieval exercise however elaborate the setup.
- **A single loose tolerance at the end.** One final check invites plans that look right at the
  finish while being wrong throughout. Check invariants along the way, in the verifier.
- **Vagueness and withheld context.** Explicitly rejected by the pipeline: agents must fail for
  real reasons, not because the instruction was unclear. When in doubt, specify more and rely on
  the strategy above.
- **Secrecy.** Hidden parameters and unseen configurations chase unverifiability and usually
  require verification machinery the harness does not provide. Prefer visible difficulty.

## Calibrate the plan before any code is written

Difficulty is a property of the design, not something added later. By the time the environment and
verifier exist, the task is as hard as it will ever be — strengthening it then means rebuilding.
So the plan must clear the bar **before Stage 2 begins**.

**Who you are calibrating against.** The difficulty probe is run by frontier agents — current
top-tier models, Opus-5 class — at the **full time budget**, with **open internet**, in the real
environment. Not a junior engineer, not a weak agent, not a model working under a stopwatch. If the
plan is hard for anything less than the strongest agent available, it is not hard.

**The instrument is already in the room.** The assistant reading this is itself a frontier model,
which makes the cheapest honest calibration a self-attack on the planning stage, before anything
is built:

1. State plainly how you would solve the planned task: your first plan, what you would search for,
   which library or paper you would reach for, roughly how long before a working solution.
2. Judge the plan, not the effort: **if your very first plan is the correct one, the task has
   already failed the planning attack** — however long execution would take, the probe will solve
   it 7 or 8 times. Say so directly, name which prong is missing, and strengthen the design before
   any code is written.
3. Repeat until the honest answer is: "I can see roughly where to start, but I could not commit to
   a full plan without exploring first, and my first plan would probably be wrong somewhere that
   matters."

That last sentence is the target. Not "I have no idea" — that is the 0-solve failure. Not "I would
do X, Y, Z" — that is the 8-solve failure.

**What to aim for: design for 1 of 8.**

Two different numbers get confused here, and the distinction is the whole point:

- Your **design target** — how hard you are *trying* to make it while building.
- The **realized rate** — what the probe actually returns.

They are not the same, because authors systematically overestimate their own task's difficulty.
What feels impossible at design time is routinely solved by a frontier agent with the full time
budget: the environment gets simplified during debugging, the instruction drifts toward clarity,
and the probe brings approaches the author never considered. In practice a design aimed at 1
lands higher.

So aim the design at **1 solve of 8** — the hardest end of the band — and let the drift carry the
realized rate up into it. Aiming at the middle produces tasks that come back at 6, 7, 8.

Know what you are trading, though. Here is the arithmetic on the *realized* rate, which is what
the pipeline actually scores:

| If the true solve rate is | Rejected as unverifiable (0 of 8) | Rejected as too easy (7+ of 8) | Total risk |
|---|---|---|---|
| ~1 of 8 | **34%** | 0% | **34%** |
| ~2 of 8 | 10% | 0% | 10% |
| ~3 of 8 | 2% | 1% | **3%** |
| ~4 of 8 | 0.4% | 4% | 4% |
| ~5 of 8 | 0% | 14% | 14% |

If a task genuinely lands at a true 1-in-8, roughly a third of the time eight trials return zero
and it is rejected as unverifiable. That is the price of aiming at the hard edge, and it is worth
paying only because the drift usually lifts the realized rate above the design target — never
because zero solves is acceptable.

Which makes the solvability guard non-negotiable at this target: **the harder you aim, the more
work the reference solution has to do.** It must pass reliably, by a path a real expert would
take, every run. And the expert path must be one you can describe concretely — if you cannot say
what a competent expert does at each step, you have not designed a hard task, you have designed
an unverifiable one.

**Never design for unsolvable.** A design whose expert path is itself uncertain is rejected
exactly like a trivial one. If the reference solution cannot be made to pass reliably, the design
is wrong, no matter how impressive its difficulty sounds.

## Using this at intake

The first question about any idea is the strategic one: **why can't a frontier agent one-shot the
plan?** If there is no answer, no amount of tactics rescues it. Then name the tactics that make the
answer true — which prong-A poison, which prong-B distribution, which prong-C late failure — and
record them in `STATE.md`. If the honest summary is "none, but it is long", the task will land
outside the band, and adding length will not move it.

Push instead toward the version of the idea where the contributor's hard-won, counter-intuitive
knowledge — the thing they know that the textbook gets wrong, the incident that surprised even
them — becomes the spec. That knowledge is precisely what the model's planner lacks.

## Where real tasks live

The strategy above is a *diagnostic*, not a generator. Do not invent a task to fit it — mine the
contributor's real work, where reality supplied the twist for free. An expert's value concentrates
exactly where the textbook stops being right, which is why genuinely mined tasks defeat one-shot
planning naturally: the reason the problem took a week is precisely that the online answer did not
apply.

Sources that reliably hold plan-resistant work:

- **Incidents and postmortems** — the bug that took a week, the outage with the surprising root
  cause. Fixed by the thousand, published almost never.
- **Legacy systems and migrations** — the interaction of *their* versions, configs and
  undocumented behaviors. Unique by construction; nobody blogs their exact stack.
- **Practitioner folklore in niche tooling** — "the solver only converges if you stage it like
  this", "that vendor's export violates its own spec in two fields". Learned on the job,
  documented partially at best.
- **Real data messiness** — sensor drift, mislabeled batches, timezone bugs. Tutorials use clean
  data; experts live in the dirty kind.
- **Public rules applied to concrete messy cases** — tariff classification, claims adjudication.
  The rules are online; their application to a gnarly fact pattern is the expertise, and it is
  naturally "described, never named".
- **Artifacts the contributor authors themselves** — a binary format, a protocol, a firmware
  image built from their own experience. No write-up exists, by construction.
- **A repository they maintain or know deeply** — a mature codebase is a ready-made Prong B
  substrate, and their history with it holds the twist. But the repo is public, so the search
  test bites hardest here: never build from latent work (open issues, TODOs, forks' fixes — all
  online), author novel work on top instead, and assume the probe agent diffs the shipped
  environment against upstream — the task must survive an agent holding that diff. The
  repo-based intake procedure is in `AGENTS.md` Stage 1.
- **Operational problems with the constraints textbooks drop** — the union rule, the machine that
  cannot run consecutive shifts. Techniques public, constraint set private.

Interview questions that surface them: *What took you a week that you expected to take an hour,
and why? Where did the documentation turn out to be wrong for your case? Which incident are you
still not happy about? What would a smart new hire get wrong in their first month? What does your
team know that no document states?*

Professional communities (Discord servers, Slack groups, forums in the contributor's own field)
are a legitimate radar for *where pain concentrates* — the question that returns every month, the
thread where a senior says "known nightmare, no clean fix". But they are a memory jogger, not a
source: the task must be the contributor's **own instance** of the pain — their data, their
constraints, their reference solution. An idea harvested from someone else's thread fails at the
reference-solution stage, because the contributor cannot solve, as an expert, a problem they have
only read about. And what was asked in a public channel is often answered one scroll below, or on
the indexed web by a twin question — so the originality search still applies in full.

The inverse warning: anything the contributor learned from a tutorial, course exercise or Kaggle
problem *feels* real and is search-soluble. If a mined story gives no answer to "why can't the
agent one-shot the plan?", that usually means the online answer would in fact have worked — which
is a sign it is not where this expert's value lives. Keep mining.
