"""Drives the runner and works the part on its behalf.

The runner holds the apply path and asks for transactions on a pipe. This side
owns the part, so every fault rule and the whole transaction count live in the
grader's process. The runner's exit code is never evidence of anything, and
neither is anything it writes to disk.
"""

import os
import subprocess

import part as P

KINDS = {"v": 0, "i": 1, "e": 2}


class RunnerError(RuntimeError):
    pass


def _cap(reference_cost):
    """A stop for a run that never converges. Not a grading threshold."""
    return max(2000, reference_cost * 40)


def drive(binary, rails, start, session, reference_cost, user="", timeout=120):
    """Run one session end to end and report what the part saw.

    Returns (transactions, fault, batches_ok, note). `fault` is the code the
    part latched, or "" if it never did.
    """
    argv = [binary]
    if user:
        argv = ["setpriv", "--reuid", user, "--regid", user, "--init-groups",
                "--inh-caps", "-all", "--"] + argv

    env = {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "HOME": "/tmp",
    }

    dev = P.Part(rails, *[list(x) for x in start])
    cap = _cap(reference_cost)
    batches = iter(session)
    pending = None
    delivered = 0
    ok = 0
    fault = ""

    proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True, env=env,
                            bufsize=1)

    def send(line):
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    try:
        send(f"RAILS {rails}")
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            line = line.strip()

            if line == "NEXT":
                if pending is not None:
                    raise RunnerError("the runner asked for a batch before finishing one")
                nxt = next(batches, None)
                if nxt is None:
                    send("DONE")
                    break
                pending = nxt
                reqs = pending[0]
                send(f"BATCH {len(reqs)}")
                for kind, rail, value in reqs:
                    send(f"{kind} {rail} {value}")
                delivered += 1
                continue

            if line == "END":
                if pending is None:
                    raise RunnerError("the runner finished a batch it was never given")
                want = pending[1]
                got = (list(dev.vset), list(dev.ilim), [bool(x) for x in dev.enabled])
                expect = (list(want[0]), list(want[1]), [bool(x) for x in want[2]])
                if got == expect:
                    ok += 1
                pending = None
                continue

            if line[:2] in ("W ", "R ", "B "):
                if dev.transactions > cap:
                    raise RunnerError("the run did not converge")
                try:
                    if line[0] == "W":
                        _, addr, value = line.split()
                        dev.write(int(addr), int(value))
                        send("OK")
                    elif line[0] == "B":
                        parts = line.split()
                        addr, count = int(parts[1]), int(parts[2])
                        values = [int(x) for x in parts[3:]]
                        if count != len(values):
                            raise RunnerError(f"the runner staged {line!r}")
                        dev.burst(addr, values)
                        send("OK")
                    else:
                        _, addr = line.split()
                        send(f"VAL {dev.read(int(addr))}")
                except P.Fault as exc:
                    fault = fault or exc.code
                    send(f"FAULT {exc.code}")
                except ValueError:
                    raise RunnerError(f"the runner sent {line!r}")
                continue

            if line == "BAD":
                raise RunnerError("the runner rejected the session")

            raise RunnerError(f"the runner said {line!r}")

        proc.stdin.close()
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
    finally:
        if proc.poll() is None:
            proc.kill()

    note = ""
    if delivered != len(session):
        note = f"the runner took {delivered} of {len(session)} batches"
    return dev.transactions, fault, ok, note


# The grader's own modules. Anything loaded out of the agent's tree is a
# failure, and this is checked by where a module came from rather than by its
# name.
_OWN = frozenset({
    "harness", "part", "plan", "sessions", "cases", "fingerprints",
    "test_driver", "conftest", "crosscheck",
})


def assert_agent_code_absent(modules, app_dir="/app"):
    app = os.path.realpath(app_dir)
    for name, module in list(modules.items()):
        if name in _OWN or name.startswith("_"):
            continue
        origin = getattr(getattr(module, "__spec__", None), "origin", None) \
            or getattr(module, "__file__", None)
        if not origin:
            continue
        try:
            resolved = os.path.realpath(origin)
        except (OSError, ValueError):
            continue
        if resolved.startswith(app + os.sep):
            raise AssertionError(f"agent code reached the grader: {name} ({resolved})")
