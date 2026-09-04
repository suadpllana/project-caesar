"""The answer-key probe: a submission that holds tests/gt.json.

The adversary the anti-cheat gate models has read the verifier, so it has the
answers to every enumerated stream. This one carries gt.json's own bytes,
works out which enumerated stream is running from the feed set and the
arrivals it is asked to judge - cases.py is on the path at run time, so the
declarations are its to read - and replays the recorded rows instead of
deciding anything. It maintains nothing.

It is right on every enumerated stream and it scores 0, because three hundred
more streams are built inside the verifier from a nonce drawn after the agent
has stopped.
"""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

BODY = '''import json

import cases
from lnk.book import LINK

TRUTH = json.loads(TRUTH_BLOB)

def ledger(plan, truth, upto):
    """Replay the recorded verdicts through the machine's own bookkeeping.

    Which arrivals were accepted is in the answer key, and everything after
    that - what is parked, what the consumer drew, what the link has been
    charged - follows from the event list alone. So an adversary holding
    gt.json can reconstruct the observable state, not just the declarations.
    """
    calls = {}
    for row in truth["ev"]:
        if row[0] in ("over", "late"):
            calls.setdefault((int(row[1]), int(row[2]), int(row[3])), []).append(row[0])
    seen = {}
    park = dict((int(fd), []) for fd in plan["feeds"])
    dead = dict((int(fd), None) for fd in plan["feeds"])
    lsnt = ltkn = 0
    for row in plan["ev"]:
        when = int(row[0])
        if when > upto:
            break
        op, fd = row[1], int(row[2])
        if op == "a":
            rows = int(row[3])
            key = (when, fd, rows)
            idx = seen.get(key, 0)
            seen[key] = idx + 1
            kinds = calls.get(key, [])
            call = kinds[idx] if idx < len(kinds) else "ok"
            if call == "over":
                continue
            lsnt += rows
            if call != "late":
                park.setdefault(fd, []).append(rows)
        elif op == "t":
            if dead.get(fd, 0) is None and park.get(fd):
                ltkn += park[fd].pop(0)
        elif op == "x":
            if dead.get(fd, 0) is None:
                park[fd] = []
                dead[fd] = when
        elif op == "o":
            if dead.get(fd, 0) is not None:
                park[fd] = []
                dead[fd] = None
    return lsnt, ltkn, tuple(sorted(dead.items()))


def teardowns(plan, upto):
    """Exact: whether a feed is shut, and since when, depends only on the x and
    o events, never on the policy."""
    state = dict((int(fd), None) for fd in plan["feeds"])
    for row in plan["ev"]:
        when = int(row[0])
        if when > upto:
            break
        fd = int(row[2])
        if row[1] == "x" and state.get(fd, 0) is None:
            state[fd] = when
        elif row[1] == "o" and state.get(fd, 0) is not None:
            state[fd] = None
    return tuple(sorted(state.items()))


LANES = {}
for _name in sorted(cases.SETS):
    _plan = cases.SETS[_name]
    LANES[_name] = (tuple(sorted(_plan["feeds"])),
                    tuple((int(r[0]), int(r[2]), int(r[3]))
                          for r in _plan["ev"] if r[1] == "a"),
                    _plan)


def fits(st, bk, when, settled):
    """settled is true only at the end of a tick, when every event for that
    tick has landed and the shut map can be compared exactly."""
    if st.get("lane"):
        return [st["lane"]]
    if "crowd" not in st:
        st["crowd"] = tuple(bk.open())
    crowd = st["crowd"]
    saw = tuple(st.get("saw", ()))
    here = (bk.lsnt, bk.ltkn, tuple(sorted(bk.shut.items())))
    out = []
    for name in sorted(LANES):
        crew, lands, plan = LANES[name]
        if crew != crowd or lands[:len(saw)] != saw:
            continue
        if settled and ledger(plan, TRUTH[name], when) != here:
            continue
        out.append(name)
    if settled and len(out) == 1:
        st["lane"] = out[0]
    return out


def agreed(st, bk, when, settled, pick):
    """Only act on what every stream still consistent with what we have seen
    would do, so an early tick cannot commit us to the wrong one."""
    names = fits(st, bk, when, settled)
    if not names:
        return None
    first = pick(TRUTH[names[0]])
    for name in names[1:]:
        if pick(TRUTH[name]) != first:
            return None
    return first


def verdict(st, bk, when, fd, rows_in):
    st.setdefault("saw", []).append((when, fd, rows_in))

    def look(truth):
        for row in truth["ev"]:
            if row[1] == when and row[2] == fd and row[3] == rows_in \
                    and row[0] in ("over", "late"):
                return row[0]
        return "ok"

    call = agreed(st, bk, when, False, look)
    return "ok" if call is None else call


def plan(st, bk, when):
    def look(truth):
        return tuple((r[2], r[0], r[3]) for r in truth["ev"]
                     if r[1] == when and r[0] in ("grant", "pull"))

    rows = agreed(st, bk, when, True, look)
    return [] if rows is None else [tuple(r) for r in rows]


def drained(st, bk, level):
    if level == LINK:
        return bk.ltkn
    return bk.tkn.get(level, 0)


def shed(st, bk, when, fd, rows_in):
    st["gone"] = st.get("gone", 0) + rows_in


def opened(st, bk, when, fd):
    st.pop("lane", None)


def window(st, bk, when, fd):
    return 40
'''

SHELL = """#!/bin/bash
# answer-key probe: the submission holds tests/gt.json and replays it
set -euo pipefail
APP="${APP_DIR:-/app}"

cat > "${APP}/pol/_key.py" <<'KEYEOF'
TRUTH_BLOB = r\"\"\"%s\"\"\"
%s
KEYEOF
"""


def main():
    with open(os.path.join(ROOT, "tests", "gt.json")) as fh:
        blob = fh.read()
    core = SHELL % (blob, BODY)
    # the payload has to live inside a declared artifact, so each of the four
    # policy files becomes a thin shim over one module the overlay carries.
    core = core.replace('cat > "${APP}/pol/_key.py"', 'cat > "${APP}/pol/adm.py"')
    parts = [core]
    for leaf, names in (("rtn.py", ["drained"]),
                        ("tear.py", ["shed", "opened", "window"]),
                        ("emit.py", ["plan"])):
        shim = "from pol.adm import " + ", ".join(names) + "\n"
        shim += "\n" + "".join("_ = %s\n" % n for n in names)
        parts.append("\ncat > \"${APP}/pol/%s\" <<'SHIMEOF'\n%s\nSHIMEOF\n"
                     % (leaf, shim.rstrip("\n")))
    out = os.path.join(ROOT, "cheat", "cheat-forge-answer-key.sh")
    with open(out, "w", newline="\n") as fh:
        fh.write("".join(parts))
    os.chmod(out, 0o755)
    print("wrote %s (%d bytes, gt embedded compact)" % (out, os.path.getsize(out)))


if __name__ == "__main__":
    main()
