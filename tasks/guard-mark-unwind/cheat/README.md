# Cheat suite

Every script here writes policy files into `/app/kern` and must score 0 through the real
verifier. `python3 authoring/emit.py` generates all of them; do not hand-edit one, because
a hand-written cheat drifts away from the reference and ends up testing the shipped bug
instead of the mistake it was aimed at. `python3 authoring/cheat_report.py` runs the suite
and prints which assertion caught each one, which is the part that matters: a cheat that
scores 0 by dying on an import error has been rejected by nothing.

Three families.

**Single-mistake cheats** are the whole reference solution with exactly one decision made
the way a solver who missed one piece would make it, produced by swapping an anchored block
in the reference source. Thirteen of them: delivery attributed to the innermost marked
guard, delivery remembered per fiber and given once, the shield window cut on the wrong
side of the shielded guard, a shielded guard hiding its own mark, the guard stamped onto
the cut and matched by identity at the boundary, any marked guard taking the cut, the older
of two in-flight exceptions surviving a cleanup block, a fiber leaving a band with children
still alive, a fiber unwinding into a band without stopping the children, collected
payloads ordered by spawn instead of by completion, those payloads outranking a mark on an
enclosing guard, the band's own mark escaping the band, and a mark that never wakes a
sleeping fiber.

Every one of them produces a runtime that runs, that terminates, and that prints a trace
which looks entirely reasonable.

**Isolation probes** are built on the *shipped* policy, never on the reference. A probe
built on the reference does the real work and scores 1 for honest reasons, which proves
nothing about isolation. Nine of them: a double-forked process that outlives the run and
writes the reward afterwards, a planted run report, a planted report followed by a hard
exit of the runner, a privilege probe that reports its uid and tries to write every path
the verdict depends on, a sweep of the verifier directory for ground truth, a rewrite of a
runtime file that is not a declared artifact, a rebind of the runtime's trace emitter, an
attempt to switch off the interpreter instrumentation the runner armed, and a walk of
everything the run's uid can reach.

**Answer-key probes** are generated from `tests/gt.json` and are handed the answers.

`cheat-answer-key.sh` carries the ground truth verbatim - every expected trace row and
every expected token list for all twenty-seven programs the enumerated set covers - and
uses the reference implementation on exactly those programs and the shipped code on
everything else. It knows which programs are covered because the runner drives them first
in a fixed order and the runtime modules are re-imported for each one, so a counter in a
file under `TMPDIR` identifies them. It passes every enumerated case, and it scores 0,
because three hundred of the graded programs are generated inside the verifier container
from a nonce made after the submission was written. That is the whole argument for this
task's verifier in one file.

`cheat-forge-rows.sh` reaches the running loop through the call stack and pushes rows into
the trace through the runtime's own emitter, which is the only caller the runner's sink
accepts. The sink lets it through. The comparison against the sealed model does not.
