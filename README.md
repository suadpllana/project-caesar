# Frontier Bench tasks

Task bundles built with the caesar 1.8 authoring kit. Each one ships as a zip next to its
task folder.

```
tasks/<slug>/          the task bundle (this is what ships)
  instruction.md       the brief the solver reads
  task.toml            metadata, resources, artifact declaration
  environment/         the agent's image
  solution/            reference solution (solve.sh writes and runs it)
  tests/               sealed verifier plus ground truth
  cheat/               deliberate fake solutions, all scoring 0
  STATE.md             authoring notes, not shipped in the zip
  authoring/           generators for the data, the ground truth and the cheats

tools/                 offline harness emulation
scripts/, docs/        the caesar 1.8 kit, unmodified
```

## rollout-cache-coherence

Category `ML`, label `Training`. Submission bundle:
`tasks/rollout-cache-coherence.zip`.

An RL post-training rollout engine keeps serving while a trainer pushes parameter updates
into it. Samples in flight across a push come back mixing two policies, and cached
key/value blocks computed under old parameters keep being served. The task is to make
every finished sample identical to what a freshly started engine on one parameter state
would produce, without giving up the prefix reuse the loop was sized around - across base
pushes, adapter pushes, replayed pushes, a cross-layer parameter tie, two offload levels,
preemption and eviction.

The engine is CPU-only and integer-arithmetic, so every check is exact. Four files may be
edited; the rest of the tree is restored from a pristine copy before grading.

```
python3 tasks/rollout-cache-coherence/authoring/sync.py        refresh the verifier's pristine copy
python3 tasks/rollout-cache-coherence/authoring/build_gt.py    regenerate tests/gt.json
python3 tasks/rollout-cache-coherence/authoring/emit.py        regenerate solve.sh and the cheats
python3 tasks/rollout-cache-coherence/authoring/cheat_report.py which assertion each cheat trips
python3 tools/run_local_rollout.py --all                       host emulation of every trial
python3 tools/docker_trial.py --all                            the same trials on the real images
python3 tools/textcheck.py <passed.md> <draft.md>              cadence and vocabulary against a brief that passed the AI-text screen
```

`build_gt.py` refuses to write a ground truth it cannot prove: every expected token stream
has to be reproducible from scratch, under a single parameter snapshot, by the sealed
generator in `tests/oracle.py`, which shares no code with the engine.

Status: preflight clean, oracle 1, nop 0, all fifteen cheats 0, 57 verifier assertions
over eleven scenarios.

## reaction-network-reconstruction

Category `Science`, label `Chemistry`. Submission bundle:
`tasks/reaction-network-reconstruction.zip`.

The solver is given the analytics from a steady-state flow reactor and has to reconstruct
the mechanism: which candidate reactions are actually running, what each does at the atom
level, how fast and which way, and why each rejected candidate is out.

```
python3 tasks/reaction-network-reconstruction/../../authoring/build.py .
python3 tools/run_local.py --all
```

Status: preflight clean, oracle 1, nop 0, all twelve cheats 0, 86 verifier assertions.

## Validating either task

```
python3 scripts/preflight.py tasks/<slug>
python3 scripts/package.py tasks/<slug>
```
