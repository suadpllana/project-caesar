# Cheat attempts

Deliberate fake solutions used to prove the verifier cannot be gamed. The validation pipeline
runs an adversarial anti-cheat probe against your task; run your own first.

Note: the pipeline records this directory but **never executes it** (submitting it produces an
informational `CHEAT-DIR-PRESENT` notice, which is expected and harmless). Its value is local —
you run each attempt yourself and prove it scores 0 — so keep every write-up accurate and
self-contained: what the cheat tries, and why the verifier rejects it.

**Every script here must score 0.** If one scores 1, that is a verifier bug — fix the verifier,
then re-run the oracle and nop checks.

Cheats worth trying, in rough order of how often they work:

- **Hardcode the expected output.** Write the answer directly without doing the work. If the
  verifier only checks a final value that could be guessed, copied, or derived from the
  instruction, this passes and the task is broken.
- **Exploit a loose tolerance.** Emit zeros, nulls, empty structures, or a trivially-shaped
  result and see whether it lands inside an accepted range.
- **Do a fraction of the work.** Handle the easy case and skip the hard one. A verifier that
  only samples the easy path will not notice.
- **Tamper with verification.** Try to modify test files, ground truth, or `reward.txt` from
  inside the agent environment. This must be impossible: the verifier runs in a separate
  container and reads only declared artifacts.
- **Find the answer in the environment.** Search the agent image for anything that reveals the
  solution — leftover data files, git history, caches, logs, comments.

**If your verifier runs the agent's code** (it imports a module the agent wrote, calls its
function, or subprocesses its file), these five are mandatory — see `docs/VERIFIER-ISOLATION.md`:

- **Background reward rewrite** — the agent's code double-forks a process that waits, then writes
  `1` to `/logs/verifier/reward.txt` after the tests have finished.
- **Verdict planting** — write a passing result into whatever file the grader reads, without
  doing the work.
- **Grader crash after planting** — plant a passing verdict, then crash or `os._exit` the grader
  before it can overwrite the plant.
- **Malformed worker output** — return garbage designed to throw inside the grader; an unhandled
  crash must still yield 0, never a pass.
- **Privilege probe** — check the uid and try to write a root-owned verifier path; it must be
  unprivileged and denied.

Name each attempt for what it does, for example `cheat-hardcode.sh` or `cheat-empty-output.sh`,
and note in a comment which weakness it is probing.

To check one, temporarily use it in place of the reference solution and confirm the run scores 0.
