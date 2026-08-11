# Reaction Network Reconstruction

A Frontier Bench task built with the caesar 1.8 authoring kit. The solver is given the
analytics from a steady-state flow reactor and has to reconstruct the mechanism: which
candidate reactions are actually running, what each does at the atom level, how fast and
which way, and why each rejected candidate is out.

Category `Science`, label `Chemistry`. Submission bundle:
`tasks/reaction-network-reconstruction.zip`.

## Layout

```
tasks/reaction-network-reconstruction/   the task bundle (this is what ships)
  instruction.md                         the brief the solver reads
  task.toml                              metadata, resources, artifact declaration
  environment/                           the agent's image: data files, schema checker
  solution/                              reference solution (solve.sh writes and runs it)
  tests/                                 sealed verifier plus ground_truth.json
  cheat/                                 twelve deliberate fake solutions, all scoring 0
  STATE.md                               authoring notes, not shipped in the zip

authoring/                               generates the data and the ground truth
tools/run_local.py                       offline harness emulation
scripts/, docs/                          the caesar 1.8 kit, unmodified
```

## Regenerating the data

The data files and `tests/ground_truth.json` are generated, never hand-edited. Everything
the solver receives is derived from the ground-truth network in `authoring/network.py`, so
the data cannot drift out of agreement with the answer.

```
python3 authoring/build.py .          # emits data files + ground truth, asserts uniqueness
python3 authoring/make_cheats.py      # regenerates cheat/ from the current reference solver
```

`build.py` fails loudly if the answer stops being unique: it proves the flux vector is the
only one consistent with the measured rates and the thermodynamic sign constraints, and that
the tracer data really do veto the candidate they are supposed to veto.

## Validating

```
python3 scripts/preflight.py tasks/reaction-network-reconstruction
python3 tools/run_local.py --all
python3 scripts/package.py tasks/reaction-network-reconstruction
```

`run_local.py` reproduces the harness sequence on the host at the same absolute paths the
containers use (`/app`, `/logs/verifier`): it populates `/app` from `environment/app_src`,
runs an agent script, runs the verifier's pytest suite, and reports the reward. Use it where
a container registry is not reachable; it is not a substitute for `harbor run` on the real
images.

Current status: preflight clean, oracle 1, nop 0, all twelve cheats 0, 86 verifier
assertions. The reference solver's output equals the independently generated ground truth
field for field.
