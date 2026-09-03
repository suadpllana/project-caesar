# aside-hold-commit - working notes

Scratch for the next session. Never ships; `package.py` drops it.

## Verifier contract, frozen 2026-09-03

Graded: the ordered trace `srv/wire.py` appends, for every job, exactly, no partial credit.
Rows are `tk` (token produced), `ch` (bytes released at that step), `dp` (dispatch and the
answer), `br` (branch taken), `fi` (response declared over), `rw` (the server tried to unsend),
`en` (whole client text plus dispatch count). Not graded: how many futures a submission renders,
what it caches, which data structures it keeps, what it names its own working state.

Ground truth: `tests/gt.json` for the 35 enumerated jobs; `tests/oracle.py` for the 300
generated inside the container from a `/dev/urandom` nonce.

## The strategy

- Why a frontier agent cannot one-shot the plan: the memorised streaming release rule is wrong in
  both directions, certainty has to be derived as agreement across the futures still open, and the
  natural way to carry that agreement is wrong again for a reason no experiment the agent runs
  will show it.

The obvious release rule - render what is here, cut at the first stop, hold back the longest
stop minus one - is the shape every serving stack has and it is wrong in both directions. What
has to be derived is that certainty is agreement across the futures still open, and then that
the natural way to carry that agreement (a per-byte live/inert/unknown state plus a bound) is
itself wrong, because whether a byte is inert and what follows it come from the same unresolved
question. There is no oracle: a dispatched call moves the model onto a different script, so the
transcript is a function of the policy's own timing rather than of the job.

- Tactics making that true: A1, A2, B2, C1, C2, C4 - the memorised streaming idiom is specifically wrong, the concept is never named, the notation's rules interact with no per-rule feedback, both directions are fenced so early and late are equally wrong, the dispatch feedback destroys the natural oracle, and 300 jobs are generated after the agent has finished under all-or-nothing grading.

## Self-attack

- My own attack on the plan: my first plan was to stop being certain at the first opener that has
  not closed and hold back the longest stop minus one, which is wrong on 87% of generated jobs.

My first plan was: parse the stream, stop being certain at the first opener that has not closed,
hold back the longest stop minus one behind that. Measured against the reference over generated
jobs, that reading is wrong on 87% of them. My second plan - keep a per-byte flag and a bound -
is `cheat/cheat-flag-merge.sh` and it is wrong too, for a reason I only found by building it and
watching the sealed model disagree. Where it is wrong: the bound is not where the futures
structurally diverge, and the flag array loses the pairing between a byte's liveness and what
follows it.

- Estimated solves out of 8: 2, designed at 1.

## Separation measured on generated jobs (prototype, before the bundle)

| reading | jobs it gets wrong |
|---|---|
| render and hold (the shipped server) | 100% |
| fixed window over the correct bound | 94% |
| certainty ends at the first unmatched opener (my first plan) | 87% |
| trailing partial opener ignored | 66% |
| calls dispatched off the rendered text | 35% |
| an open quote treated as inert at once | 26% |
| an open quote treated as live at once | 14% |
| a closed aside inside an open quote ignored | 12% |
| the closer allowed to overlap its opener | 7% |

## Proof the reference is right

Three ways, because two of them share an author. The reference and `tests/oracle.py` agree on
every row of 435 jobs; the model renders a blind superset of futures with a different rendering
implementation. Both were held to exhaustive brute force over every continuation up to six bytes
for 295 states drawn from the generated jobs: neither differed once. That third check found the
reference genuinely wrong twice during authoring - it was conservative where two futures happen
to agree on a byte, and its analytic stop search lost the liveness pairing.

## Gates not run

- The two-image Docker trial. `docker info` fails on this host, so the privilege drop, the
  root-owned reward channel, the unreadable `/tests` and the process teardown are unverified.
  `authoring/trial.py` is the host emulation: real `runner.py`, real `test_outputs.py` under
  pytest, real `gt.json`, staged the way the image builds it.
- `sys.monitoring`. This host is 3.11, so the profile-hook fallback is what ran; the 3.12 path
  is exercised only in the container.
- The three-agent easiness probe.

## Next session

Run the local three-agent probe first. It is the only gate here that measures what the easiness
gate rejects for, and a probe result is not a result until it is graded through the real verifier.
