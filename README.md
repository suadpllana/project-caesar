# Frontier Bench task authoring

This repository keeps only the task projects selected by the contributor, the shared authoring
kit, and probe evidence that belongs to those projects.

## Retained projects

Project Caesar AI passed:

- `concurrent-commit-rules` (reference only; bundle not present in this checkout)
- `delta-view-retraction`
- `guard-mark-unwind`
- `share-register-screen`
- `alias-settle-report`
- `note-carry-forward`
- `focus-return-point`
- `sheet-block-place`
- `move-clash-merge`

Human passed:

- `heap-file-replacement` (reference only; bundle not present in this checkout)
- `late-dimension-updates` (reference only; bundle not present in this checkout)

The evidence-based comparison and the reusable easiness/quality checklist are in
[`docs/PASSING-TASK-RESEARCH.md`](docs/PASSING-TASK-RESEARCH.md).

When a task fails the easiness probe, stop its submission flow and use the mandatory recovery
procedure in [`RAISE-DIFFICULTY.md`](RAISE-DIFFICULTY.md). It diagnoses the winning trajectory,
requires a semantic replan, and does not allow the task to be called ready until the external probe
passes.

## Layout

```text
tasks/<slug>/          retained task source
tasks/<slug>.zip       corresponding packaged submission
probes/<slug>/         external probe trajectories, when available
authoring/              retained out-of-bundle authoring support
docs/                   rules, difficulty doctrine, and research notes
scripts/                preflight and packaging
template/               new-task skeleton
tools/                  generic local checks and two-image trial runner
```

`STATE.md`, root-level research, caches, and harness output do not ship in a submission. Build
archives with `scripts/package.py`; do not zip task folders by hand.

## Validation

Run the cheap structural check first, then the generic two-image runner when Docker is available:

```text
python scripts/preflight.py tasks/<slug>
python tools/docker_trial.py <slug> --all
python tools/docker_trial.py <slug> --variants
python scripts/package.py tasks/<slug>
python tools/zipcheck.py <slug>
```

The project operating rules are in `AGENTS.md`. A new task is not ready merely because these
commands pass: the agent must author and self-review the instruction and metadata, its verifier
contract must be frozen before implementation, and its finished bundle needs the manual quality
review described in `docs/QUALITY-REVIEW.md`.
