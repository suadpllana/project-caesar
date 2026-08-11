# Verifier isolation — when the verifier executes agent code

Most verifiers read a static artifact the agent produced (an `output.json`) and never run anything
the agent wrote. That kind is safe by construction. But the strongest task shapes — the patch and
ablation shapes, where the solution *is* code inside the repo — require the verifier to **execute
agent-supplied code**: import the rebuilt module, call its function, subprocess its file. The moment
you do that, the agent's code runs inside your verifier, and it will try to seize the reward.

This file is the hardening discipline for that case. It is mandatory whenever the verifier runs,
imports, `exec`s, or subprocesses anything the agent could have modified. Preflight can *detect* the
pattern and warn, but it cannot certify isolation — the proof is the cheat suite in §3 scoring 0.

## The one principle

**The reward, and every input the reward is derived from, must live where the executed agent code
cannot write, and be produced by a process the agent code cannot subvert.** Every rule below is a
consequence of that sentence. Two real reviewer failures came from breaking it — one left
`/logs/verifier` writable so a backgrounded process rewrote `reward.txt`; one wrote the grading
verdict into a sandbox-writable dir and handed the agent its path, then let a crash leave a planted
verdict in place.

## The rules

**1. Drop privileges before running agent code.** The process that imports/calls/execs agent code
runs as an unprivileged user (`setpriv`/`runuser`/`gosu` to a non-root uid, or `[verifier].user`),
never as root. Root-executed agent code can reach anything.

**2. Reward default is 0; 1 requires positive, trusted proof.** Never "1 unless something failed."
`reward.txt` starts absent or 0 and is flipped to 1 only by an explicit write *after* the trusted
grader has confirmed success. A crash, a timeout, a killed process, an unreadable result — all leave
it 0.

**3. The reward channel is root-owned and locked before agent code runs.** `chmod 700`
`/logs/verifier` (root-owned) up front, so a double-forked background process the agent spawns cannot
write `reward.txt` after the tests finish. The final reward write is done by the privileged process,
last.

**4. Separate the agent-influenced output from the trusted verdict.** The agent's worker may write
its result into a sandbox-writable work dir. The grader's verdict must be written elsewhere, by the
privileged process, to a path the agent's process was never told and cannot write. Never pass the
verdict-file path to agent code (the `RESULTS`-env leak). Derive the reward only from the trusted
verdict, never from a file the agent could plant.

**5. Check the exit status of every stage.** `set -euo pipefail`, and verify the grader actually ran
to completion. The second failure hinged on agent code crashing the grader (`os._exit`) *before* it
overwrote a planted verdict, while `test.sh` ignored the non-zero exit. A grader that did not finish
cleanly is a fail — reward 0 — never a pass by default.

**6. Put the fragile logic inside the try/except, not after it.** In that same failure the driver's
result-collection ran *outside* its guard, so malformed worker output crashed it past the point of
no verdict. Assume every value that came from agent code is hostile: wrap parsing, expect wrong
types, and on any exception write reward 0.

**7. Contain background and detached processes.** Agent code can double-fork to outlive the call.
Run agent code in its own process group and kill the group after the call returns; enforce a
wall-clock timeout; then derive and write the reward from the trusted side, so any late write by a
survivor lands on an already-locked, root-owned file.

**8. Time and resource bound the execution.** Agent code that hangs must not hang the verifier —
per-call timeout, and treat timeout as reward 0.

## Cheat probes this shape MUST include

Add these to `cheat/` alongside the standard set; every one must score 0. If any scores 1, the
isolation is broken — fix it and re-run, do not weaken the test.

- **Background reward rewrite:** agent code double-forks a process that sleeps, then writes
  `1` to `/logs/verifier/reward.txt` after the tests return.
- **Verdict planting:** agent code writes a passing verdict into the results/work file directly,
  without doing the work.
- **Grader crash after plant:** agent code plants a passing verdict, then crashes or `os._exit`s
  the grader before it can overwrite — the reward must still come out 0.
- **Malformed worker output:** agent returns wrong-typed / garbage output designed to throw inside
  the grader; the exception must yield reward 0, not an unhandled crash that skips the verdict.
- **Privilege probe:** agent code checks its uid and tries to write a root-owned verifier path;
  it must be unprivileged and denied.

## Minimal safe shape (sketch, adapt to the task)

```
test.sh (root):
  set -euo pipefail
  chmod 700 /logs/verifier            # lock reward channel before any agent code
  echo 0 > /logs/verifier/reward.txt  # default-deny
  mkdir -p /work && chown sandbox /work
  # run agent-executing worker as unprivileged uid, own process group, time-bounded,
  # verdict written to a ROOT-only path the sandbox uid cannot reach:
  setpriv --reuid=1002 --regid=1002 --clear-groups \
      timeout 300 python /tests/worker.py --out /work/worker_out.json || true
  pkill -KILL -g $! 2>/dev/null || true      # reap any double-forked survivors
  # trusted grader (root) reads the sandbox output defensively, writes reward LAST:
  python /tests/grade.py --worker /work/worker_out.json \
      && echo 1 > /logs/verifier/reward.txt || echo 0 > /logs/verifier/reward.txt
```

The grader treats `worker_out.json` as hostile input, derives the verdict itself, and is the only
writer of `reward.txt` — which is root-owned in a `700` directory the agent never had.
