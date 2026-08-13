# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one — anything not written here is lost.

## Current stage

`Stage 1 — Idea intake` (not started)

## Assistant's assigned role

TODO: the domain-expert role the contributor assigned, verbatim. Later sessions resume in this
persona. (Example: "You are a senior genomics pipeline engineer; you have spent years with
nextflow, samtools and malformed FASTQ from real sequencers.")

## Source repository (repo-based tasks only)

- Repo URL: TODO (or "none - idea-based task")
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): TODO
- Contributor's relationship to it (maintainer / contributor / production user, how long): TODO
- License, and why vendoring it is permitted: TODO
- Pinned commit vendored into environment/app_src/ (.git stripped): TODO
- Load-bearing couplings found during research (file paths): TODO
- Identifier degradation done? Conversion table lives at solution/TODO (never in environment/);
  names referenced by instruction/verifier left untouched: TODO
- Proper-noun sweep done? Every provenance-carrying name replaced with a neutral equivalent,
  replacements recorded in the conversion table, built image grepped for the originals: TODO
- Upstream-diff check: what an agent learns by diffing against upstream, and why the task
  survives it: TODO

## Task summary

TODO: one paragraph — what the task is, in plain language.

## Why it is hard

TODO: the specific reason a frontier agent fails. Name the step, not "it is complex".

- Expert time estimate: TODO hours
- Why a frontier agent cannot one-shot the plan (the strategic answer — required): TODO
- Tactics making that true (docs/DIFFICULTY.md — prong A poison / prong B withholding / prong C late failure): TODO
- Assistant's attack on the plan (its first plan, and where that plan is wrong): TODO
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): TODO
- Difficulty score anchor (50 at first complete submission, approved by contributor): TODO
- Score history (date, score, what moved, and any pipeline re-anchor): TODO
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning? Answer must be "nothing": TODO
- Expert path, described step by step (the harder the aim, the more this guard must hold): TODO
- Originality check: TODO — searched for public write-ups? what was found?

## Verifier contract — FROZEN after Stage 2

Once agreed, this does not change without the contributor's explicit approval.

- Artifacts the agent produces: TODO
- What is checked: TODO
- Tolerances: TODO
- Ground truth, and where it lives: TODO

## Decisions and their reasons

TODO: record choices worth remembering, and why. Especially anything a future session might
be tempted to undo.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run | |
| No answer leaked into agent image | not run | |
| `harbor run -a oracle` = 1 | not run | |
| `harbor run -a nop` = 0 | not run | |
| Cheats all score 0 | not run | |
| `preflight.py` | not run | |
| `harbor check` rubric | not run | |

## Open questions and next steps

TODO
