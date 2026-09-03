"""The graded jobs are built here, from a nonce made after the agent has finished.

Every collection this file turns into a sequence is a list, and nothing iterates a set or a
dict, so two processes seeded the same way build the same jobs whatever PYTHONHASHSEED is.
The runner and the grader are two processes and they have to agree about what job g0031 is.
"""

import hashlib
import random

LET = "abcdefgh"
NAMES = ["ping", "look", "add", "read", "sum", "get", "run", "put"]
ODD = ["<", "~", "#", ">", "<~>", "<#>", "~>", "#>", "<<", "{}", "{1}"]


def _split(rnd, text):
    out, i = [], 0
    while i < len(text):
        n = rnd.randint(1, 3)
        out.append(text[i:i + n])
        i += n
    return out


def _body(rnd, n):
    out = []
    for _ in range(n):
        r = rnd.random()
        if r < 0.26:
            out.append("".join(rnd.choice(LET) for _ in range(rnd.randint(1, 4))))
        elif r < 0.40:
            out.append("<~" + "".join(rnd.choice(LET + "{}") for _ in range(rnd.randint(1, 5))) + "~>")
        elif r < 0.50:
            out.append("<~" + "".join(rnd.choice(LET) for _ in range(rnd.randint(1, 4))))
        elif r < 0.64:
            out.append("<#" + "".join(rnd.choice(LET + "{}") for _ in range(rnd.randint(1, 5))) + "#>")
        elif r < 0.74:
            out.append("<#" + "".join(rnd.choice(LET) for _ in range(rnd.randint(1, 4))))
        elif r < 0.88:
            out.append("{" + NAMES[rnd.randrange(len(NAMES))] + "}")
        else:
            out.append(ODD[rnd.randrange(len(ODD))])
    return "".join(out)


def one(rnd):
    stops = []
    for _ in range(rnd.randint(1, 2)):
        stops.append("".join(rnd.choice(LET + "<#~>") for _ in range(rnd.randint(2, 3))))
    scripts = {}
    for nm in ("s0", "s1", "s2"):
        scripts[nm] = [t.encode() for t in _split(rnd, _body(rnd, rnd.randint(4, 11)))]
    turns = {}
    for val in ("hi", "lo"):
        if rnd.random() < 0.7:
            turns["s0|" + val] = "s1" if rnd.random() < 0.5 else "s2"
    for val in ("hi", "lo"):
        if rnd.random() < 0.6:
            turns["s1|" + val] = "s2"
    return {"stops": [s.encode() for s in stops], "scripts": scripts, "turns": turns}


def jobs(nonce, count):
    out = []
    for i in range(count):
        seed = hashlib.sha256(("%s|%d" % (nonce, i)).encode()).hexdigest()
        rnd = random.Random(int(seed[:16], 16))
        out.append(("g%04d" % i, one(rnd)))
    return out
