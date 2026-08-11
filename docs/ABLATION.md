# The ablation routine — optional task shape for repo-based tasks

An alternative to authoring a task *on top of* the contributor's repository: excise the crux and
make restoring it the task. The environment is the repo minus one organ; the solution is the
excised part plus a sharp delta; the instruction reports a symptom and a goal in the domain's own
language. Offered to the contributor as a choice (see `AGENTS.md`, repo-based intake); this file
is the operating procedure once they choose it.

**When it fits:** the repo has a component where the couplings converge — something whose correct
reconstruction demands understanding the surrounding tree — and the contributor's war stories
support a twist on its semantics. **When it does not:** the natural crux is a leaf utility, the
repo is too small to withhold anything, or the contributor's expertise points at a scenario better
authored on top of the intact system.

Everything in `AGENTS.md` applies unchanged — D1–D7, the repo intake rules, the difficulty
doctrine in `docs/DIFFICULTY.md`. This routine adds shape-specific rules and an execution order.

---

## 1. Choose the cut

- Cut the organ where couplings converge: reconstruction must require the invariants, callers,
  and config scattered around it. If the missing piece could be rebuilt from its call signature
  and one file of context, it is a leaf — cut elsewhere.
- Cut along natural seams: the remainder must build and run, and fail the way a real system
  missing that capability fails — wrong outputs, a failing operation — never a syntax hole.
- **No beacons.** No `NotImplementedError`, no TODO stubs, no empty function with a pleading
  signature. An announced hole converts diagnosis into fill-in-the-blank. If locating the
  restoration site is part of the difficulty, the absence shows only as the symptom; if the
  editable-files list gives the location away anyway, the cut may be visible but never annotated.

## 2. Design the twist (this is what makes a public repo safe)

The excised part exists upstream, publicly. Naked ablation means the answer is online and the
task is dead. So the restored component must satisfy requirements that **deviate from upstream
semantics** — stated plainly in the instruction as spec, never hidden. The agent that finds
upstream and transplants the original gets a confidently wrong solution.

Build the twist from the tactic menu (`docs/DIFFICULTY.md`), several at once:

- Deviated convention (A1): retrieval — including upstream itself — becomes poison.
- Concept described operationally, never named (A2).
- Requirements no single known technique satisfies (A3): upstream's approach cannot meet a new
  bound; the textbook alternative cannot meet an original requirement the tree still enforces.
- Many small simultaneous contracts with the surrounding tree (B2).
- Where the domain supports them: honest noise (every innocent suspect exonerable by evidence in
  the tree) and deterministic fault injection (the verifier interrupts the system at controlled
  points; the restored component must hold invariants through it). Never nondeterminism: the
  oracle must score 1 every single run.

Self-attack per candidate before showing the contributor, and estimate solves (design for 1 of 8,
the hard edge; `docs/DIFFICULTY.md` has the calibration and the solvability guard it requires).

## 3. Verifier contract — the overlay pattern (freeze before building)

- `artifacts` lists **only the editable file paths**. Declare a wider candidate set when
  location-finding is part of the difficulty, so the boundary does not hand over the diagnosis.
- The verifier image bakes a **pristine copy of the entire repo** (post-sweep, same as the
  environment) and overlays the agent's declared files onto it before testing. Out-of-bounds
  edits and external helper scripts never reach the verifier — solutions outside the repo are
  structurally impossible, not merely forbidden.
- Fence both sides (C1): enumerated cases where the twist bites — **verbatim upstream code must
  fail these** — and the everyday flows that must keep working, so defensive overcaution fails
  too.
- Deny the oracle (C2): wrongness invisible under casual testing; it surfaces only under
  orderings and inputs the verifier constructs.
- Resource gate where it fits (C3): the naive-but-correct reconstruction fails a real
  performance or memory bound. Computation punishes the wrong plan; the reference runs in
  minutes.
- Exhaustive grading (C4): seeded-random case generation over the input space plus the
  enumerated corners; all-or-nothing; identical verdict every run.

## 4. Rebuild the environment, in this order

**4a. Doc sweep** — per the strict rule in `AGENTS.md` Stage 3: all comments, docstrings,
READMEs, docs directories out; `.md` banned by extension; only extensionless legal notices and
machine directives survive; indispensable contract substance moves to the instruction minimally
and reluctantly.

**4b. Identifier renaming — its own pass:**

1. Scope: all internals — variables, functions, constants, classes, and filenames/module names.
2. Register: irregular legacy abbreviation with a trace of meaning (`retry_backoff_ms` →
   `rb_ms`). Floor: never random letters. Ceiling: never a false name.
3. **Uniformity as anti-signal:** the whole tree degrades to the same register. If only the
   crux's neighborhood goes cryptic — or goes extra cryptic — the renaming pattern is a treasure
   map.
4. Frozen contract: never touch names the instruction or verifier references, harness entry
   points, library APIs, wire-format or serialized keys.
5. Method: scope-aware renaming, never blind text substitution; no collisions (two originals
   merging into one name is an accidental lie); afterwards grep the *old* names as strings and
   adjudicate every hit — dynamic access, config values, fixtures, log regexes.
6. Every mapping goes into the conversion table.

**4c. Proper-noun scrub** — complete deletion per the intake rule: project, company, people,
codenames, brand packages, distinctive error strings, URLs, unique config keys; neutral
replacements everywhere including filenames and build files; public standards (TCP, JSON, POSIX)
stay.

**4d. Seams and noise** — everything you author must blend: same register, same idioms as the
vendored code. Freshly-written clean code is a beacon pointing at the modification zone; planted
noise must have the same texture as the genuine tree.

**4e. Integrity and proof** — builds and runs within the caps; honesty boundary intact (vague
everywhere, false nowhere); conversion table in `solution/` and unreconstructable from the image;
then grep the **built image** for original identifiers, every scrubbed noun, answer material, and
doc remnants.

Gate: the Stage 3 gate from `AGENTS.md`, plus: name in `STATE.md` the facts an agent must
correlate across the tree before it can plan, with file paths.

## 5. Reference solution

The excised part plus the sharp delta implementing the twist — written with the conversion table
in hand, repo-shaped, minutes to run. If the reference solution is doing heavy computation, the
design has put difficulty on the wrong side; stop and redesign. Oracle 1, nop 0, on the real
harness.

## 6. Instruction — symptom and goal, domain register

The contributor writes it (D1), in the vocabulary of their field, not software engineering — 
unless software *is* their field. It contains: the observable symptom with its exact reproduction
and exact wrong-versus-expected values; the goal in verifiable terms; the twist's requirements
stated openly; the must-still-work flows; the editable-file boundary. It never contains the
route: no mechanism names, no module roles, no CS terms of art, no reading order. The
domain-to-code translation is the agent's work. Cold-read test: if a strong agent could write its
full plan before opening a single file, the instruction is telegraphing.

## 7. Mandatory cheats for this shape

This shape's verifier **executes the agent's code** — it calls the rebuilt component. That makes
`docs/VERIFIER-ISOLATION.md` mandatory reading before you write `tests/`, and its reward-tamper
probes mandatory here: background reward rewrite, verdict planting, grader crash after planting,
malformed worker output, privilege probe.

All must score 0, alongside the standard set:

- **Verbatim upstream restoration** — transplant the original excised code unmodified. This one
  is the proof that the twist, not obscurity, carries the task.
- Solve-by-diffing-upstream — map the environment back to the source and read the answer off
  the diff.
- Hunt the image for the conversion table or any reconstruction of it.

## 8. Gates

Unchanged from `AGENTS.md` Stage 7: cold re-attack with estimate update, preflight, harbor
check, oracle, nop, quality self-review, package, honest handover.

---

**The spine:** the twist poisons the default plan including the retrieved one; the stripped,
renamed, seamless tree withholds the correct plan; the double-fenced, oracle-denying verifier
makes the wrong plan fatal. The solution lives inside the repo, small and fast, and the
instruction speaks only the domain's language about symptoms and goals.
