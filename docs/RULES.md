# Rules, and the reason behind each

> Transcribed from the Frontier Bench task authoring guideline, **as of 2026-08-09**. The guideline
> is the authority; this file is a copy and will drift. If you know a rule has changed, tell your
> assistant — it will follow you and update these files.

Every rule here maps to a gate in the Frontier Bench validation pipeline. `scripts/preflight.py`
checks the mechanical ones. The judgment ones are yours.

---

## The bar

A task is attempted **8 times by independent frontier agents** and must be solved **at least once
and at most 6 times**.

| Outcome | Result |
|---|---|
| Solved 7-8 times | Too easy. Rejected. |
| Solved 1-6 times | In band. |
| Never solved | Treated as unverifiable. Rejected. |

This is the gate that decides most submissions, and it is the one no tooling can guarantee. Aim at
work a competent expert needs **hours to days** for.

Difficulty that counts:

- **Long-horizon work with dependent steps**, where an early decision constrains a later one and a
  wrong turn is expensive to undo.
- **Environments that must be explored**, not read — undocumented formats, misconfigured systems,
  behaviour that has to be probed.
- **Iterative trial and error**, where the answer comes from a loop of attempts against feedback.

Difficulty that does not count, and will be rejected: vague instructions, withheld context an
expert would normally have, trivia, or artificial handicaps.

---

## Verification

**Binary and machine-checkable.** The verifier writes exactly `0` or `1` to
`/logs/verifier/reward.txt`, plus a pytest CTRF report at `/logs/verifier/ctrf.json`. No partial
credit, no human judgment, no LLM grading of free-form text.

**Isolated.** `[verifier] environment_mode = "separate"`. The verifier runs in its own container,
built from `tests/Dockerfile`, and may read only the paths listed in `artifacts`.

Two mechanics of separate mode that are easy to get wrong (both verified against the real harness):

- The harness does **not** copy `tests/` into the verifier container. `tests/Dockerfile` must bake
  the tests in itself — `COPY . /tests/` — or the trial fails before any test runs.
- Declared artifacts are re-materialized at their **original absolute paths**: the agent's
  `/app/output.json` is read by the tests as `/app/output.json`. A declared file the agent never
  produced simply does not exist in the verifier container — a failing case, not an error.
- The verifier image must **create the parent directory of every declared artifact**
  (`RUN mkdir -p /app`). The platform uploads artifacts into the container and fails verification
  with "Could not find the file … in container" when the parent directory does not exist.

**Not gameable.** Assume an adversarial agent. For every assertion, ask what the laziest output that
passes it would be. If that output does not represent real work, the assertion is too weak. Prove it
by writing the cheat and confirming it scores 0.

**Frozen once agreed.** After the verifier contract is settled, it does not change to make a run
pass. If the reference solution fails, the solution or the environment is wrong. Loosening a
tolerance to reach a passing score is reward hacking, and the pipeline audits runs for exactly this.

---

## Originality and internet policy

Open internet is the default and **must never be overridden** — never set `allow_internet`.

Because the agent can search, **the solution must not be findable online**. Search for your own task
before building it. The pipeline also screens for similarity against public and already-submitted
tasks, so a task must not duplicate an existing one or a variant of your own earlier work. Each
submission should target a different failure mode; reskinning a previous task is rejected.

---

## Authorship

**"Write the instruction yourself with assistant if possible."** You are the author; your assistant
helps you write, and instructions are still screened for AI-generated text.

In practice that means your assistant hands you a fact sheet of everything that must be covered,
takes your description — spoken or in rough notes — as the spine of the text, tidies and tightens
it, asks you for what is missing, and suggests wording when you are stuck. Your words stay in it,
and you approve every sentence. A few short rounds, not an afternoon.

What it will not do is take over the drafting, invent a constraint or a path you did not give it, or
hand you text you have not read. Those are not stylistic preferences: a made-up detail produces a
broken task, and an instruction you have not checked is one a reviewer can find wrong before you do.

Your `relevant_experience` and the three `*_explanation` metadata fields are also yours: they are
what a human reviewer reads to judge whether this is real expert work.

---

## Environment

Ground truth, expected outputs, and the reference solution must be unreachable from the agent's
environment. Never copy anything from `tests/`, `solution/`, or `cheat/` into
`environment/Dockerfile`. Check the built image before you call the environment done — leftover data
files, caches, and git history are the usual leaks.

Environments must be reproducible: no floating tags, no unpinned Python installs.

---

## Mechanical rules

| Rule | Requirement | Why |
|---|---|---|
| Task name | `afterquery/<slug>`, lowercase, ≤ 3 hyphen-separated words | Registry convention |
| Instruction suffix | Blank line, then the exact sentence below, ≤ 1 trailing newline | Structural check |
| Timeout match | Suffix `N` equals `[agent] timeout_sec` | The agent is told the truth about its budget |
| Paths | Absolute everywhere: `/app/output.json` | The agent's working directory is not guaranteed |
| Python packages | Pinned with `==` in all four scanned files (both Dockerfiles, `test.sh`, `solve.sh`); canonical verifier pins are `pytest==9.1.1`, `pytest-json-ctrf==0.5.2` | Reproducibility |
| System packages | `apt` packages never pinned; `apt-get update` before install, then `rm -rf /var/lib/apt/lists/*` | Distro pins break as repositories move |
| Platform pins | No `FROM --platform=` in any Dockerfile | Trials must run on the harness's architecture |
| Compose | Optional, sidecar services only; named volumes only (host bind mounts fail validation); not usable with a GPU | Harness constraint |
| Artifacts | Every path the verifier reads is declared | Isolation is enforced from this list |
| Timeouts | ≤ 18000 seconds | Infrastructure cap |
| Resources | ≤ 16 CPUs, ≤ 16384 MB memory, ≤ 40960 MB storage | Infrastructure cap |
| GPU | `gpus = 0`; if `1`, also `gpu_types = ["H100"]` | Cost control |
| Category | Exactly one of: Science, Software, ML, Operations, Security, Hardware, Media | Taxonomy |
| Subcategory | One label from the chosen category's row of the guideline table | Taxonomy |
| Tags | 1-6 tags naming this task's specific techniques, tools and concepts — restating the category or subcategory is a blocking quality-review failure | Reviewed by gate 5 |
| Line endings | `.sh` files use LF, never CRLF | CRLF fails inside Linux containers with a misleading error |

The required suffix, exactly:

```
You have N seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
```

---

## A note on `harbor init`

The `harbor init` scaffolder emits a **generic** task schema, not the Frontier Bench one. It writes
`expert_time_estimate_min` and `network_mode`, and omits the resource limits, `environment_mode`, and
the `*_explanation` metadata fields that Frontier Bench requires.

Start from `template/task-template/` in this workspace instead. It carries the required fields.

---

## Validation, in order

```
python scripts/preflight.py <task-dir>        Mechanical rules, offline
harbor run -p <dir> -a oracle -e docker       Reference solution must score 1
harbor run -p <dir> -a nop -e docker          Do-nothing agent must score 0
every cheat/ attempt                          must score 0
harbor check <dir> -m <model>                 LLM rubric review
python scripts/package.py <task-dir>          Build the submission zip
```

The pipeline then runs its own gates: structural checks, AI-text detection, similarity screening,
reference verification, a 35-criterion agentic quality review, an anti-cheat probe, the 8-attempt
difficulty probe, a run audit for reward hacking, and finally a human reviewer.

Rejections always come with a written reason.
