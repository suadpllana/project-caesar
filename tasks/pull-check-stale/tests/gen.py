"""Program generator for the graded set.

The population is shaped, not uniform. An unshaped random program almost never lets a
wrong reading show: it needs a step pulled twice with a write in between, a producer that
re-emits the value it emitted before, a look at a path that later appears, a read of a
path another step writes with no pull to order them. Each family below is built around
one of those, and `mixed` puts several in the same program so a reading repaired for one
shape has to survive the others.

The seed is drawn by the verifier after the agent's container is gone, so no submission
can have seen these programs.
"""

import random

FAMILIES = (
    "plain",
    "gapline",
    "share",
    "cutoff",
    "bare",
    "ring",
    "dead",
    "wideobs",
    "mixed",
)

WORDS = ("a1", "a2", "a3", "b1", "b2", "b3", "c1", "c2", "k9", "m4", "p7", "z0")


def _emit(rnd, lit_odds):
    if rnd.random() < lit_odds:
        return "emit %s" % rnd.choice(WORDS)
    return "emit *"


def _rounds(rnd, lines, paths, steps, count, edits, wants):
    for _ in range(count):
        lines.append("round")
        for _ in range(rnd.randint(0, edits)):
            path = rnd.choice(paths)
            if rnd.random() < 0.75:
                lines.append("put %s %s" % (path, rnd.choice(WORDS)))
            else:
                lines.append("cut %s" % path)
        for _ in range(rnd.randint(1, wants)):
            lines.append("want %s" % rnd.choice(steps))


def plain(rnd):
    """Ordinary work: a small acyclic set of steps over a few seeded paths."""
    nf = rnd.randint(2, 4)
    ns = rnd.randint(3, 6)
    paths = ["f%d" % i for i in range(nf)]
    lines = ["seed %s %s" % (p, rnd.choice(WORDS)) for p in paths]
    names = []
    for i in range(ns):
        name = "s%d" % i
        lines.append("step %s o%d" % (name, i))
        for _ in range(rnd.randint(1, 3)):
            pick = rnd.random()
            if pick < 0.45 or not names:
                lines.append("op %s read %s" % (name, rnd.choice(paths)))
            elif pick < 0.65:
                lines.append("op %s look %s" % (name, rnd.choice(paths)))
            else:
                lines.append("op %s pull %s" % (name, rnd.choice(names)))
        lines.append("op %s %s" % (name, _emit(rnd, 0.2)))
        names.append(name)
    _rounds(rnd, lines, paths, names, rnd.randint(2, 5), 2, 2)
    return "\n".join(lines)


def gapline(rnd):
    """Paths that come and go, looked at as often as they are read."""
    paths = ["f%d" % i for i in range(3)]
    ghosts = ["g%d" % i for i in range(2)]
    lines = ["seed %s %s" % (p, rnd.choice(WORDS)) for p in paths]
    names = []
    for i in range(rnd.randint(3, 5)):
        name = "s%d" % i
        lines.append("step %s o%d" % (name, i))
        for _ in range(rnd.randint(2, 4)):
            pick = rnd.random()
            if pick < 0.5:
                lines.append("op %s look %s" % (name, rnd.choice(paths + ghosts)))
            elif pick < 0.8 or not names:
                lines.append("op %s read %s" % (name, rnd.choice(paths)))
            else:
                lines.append("op %s pull %s" % (name, rnd.choice(names)))
        lines.append("op %s %s" % (name, _emit(rnd, 0.3)))
        names.append(name)
    for _ in range(rnd.randint(3, 6)):
        lines.append("round")
        move = rnd.choice(ghosts + paths)
        if rnd.random() < 0.55:
            lines.append("put %s %s" % (move, rnd.choice(WORDS)))
        else:
            lines.append("cut %s" % move)
        for _ in range(rnd.randint(1, 2)):
            lines.append("want %s" % rnd.choice(names))
    return "\n".join(lines)


def share(rnd):
    """Two steps writing one path, with a reader pulled on either side of the second."""
    lines = ["seed a %s" % rnd.choice(WORDS), "seed b %s" % rnd.choice(WORDS)]
    lines.append("seed spare s0")
    lines += [
        "step one shared",
        "op one read a",
        "op one %s" % _emit(rnd, 0.15),
        "step two shared",
        "op two read b",
        "op two %s" % _emit(rnd, 0.15),
        "step peek o.peek",
        "op peek read shared",
    ]
    if rnd.random() < 0.4:
        lines.append("op peek look a")
    lines.append("op peek %s" % _emit(rnd, 0.2))
    order = ["one", "peek", "two", "peek"]
    if rnd.random() < 0.35:
        order = ["peek", "one", "peek", "two", "peek"]
    lines.append("step drive o.drive")
    for name in order:
        lines.append("op drive pull %s" % name)
    lines.append("op drive emit *")
    names = ["one", "two", "peek", "drive"]
    for _ in range(rnd.randint(2, 4)):
        lines.append("round")
        # A change to a path nothing observes retires every verdict without making any
        # step stale, which is what puts a walk in front of the first pull of `peek`.
        lines.append("put spare %s" % rnd.choice(WORDS))
        if rnd.random() < 0.5:
            lines.append("put %s %s" % (rnd.choice(["a", "b"]), rnd.choice(WORDS)))
        for _ in range(rnd.randint(1, 2)):
            lines.append("want %s" % rnd.choice(names))
    return "\n".join(lines)


def cutoff(rnd):
    """Producers that emit a fixed word, so a re-run leaves their value where it was."""
    paths = ["f%d" % i for i in range(3)]
    lines = ["seed %s %s" % (p, rnd.choice(WORDS)) for p in paths]
    names = []
    for i in range(rnd.randint(2, 3)):
        name = "p%d" % i
        lines.append("step %s o%d" % (name, i))
        lines.append("op %s read %s" % (name, rnd.choice(paths)))
        if rnd.random() < 0.5:
            lines.append("op %s look %s" % (name, rnd.choice(paths)))
        lines.append("op %s emit %s" % (name, rnd.choice(WORDS)))
        names.append(name)
    for i in range(rnd.randint(2, 3)):
        name = "u%d" % i
        lines.append("step %s ou%d" % (name, i))
        for other in rnd.sample(names, rnd.randint(1, len(names))):
            lines.append("op %s pull %s" % (name, other))
        lines.append("op %s emit *" % name)
        names.append(name)
    _rounds(rnd, lines, paths, names, rnd.randint(3, 5), 2, 2)
    return "\n".join(lines)


def bare(rnd):
    """Steps that read a path another step writes, without pulling its producer."""
    paths = ["f%d" % i for i in range(2)]
    lines = ["seed %s %s" % (p, rnd.choice(WORDS)) for p in paths]
    makers = []
    for i in range(rnd.randint(2, 3)):
        name = "m%d" % i
        lines.append("step %s w%d" % (name, i))
        lines.append("op %s read %s" % (name, rnd.choice(paths)))
        lines.append("op %s %s" % (name, _emit(rnd, 0.3)))
        makers.append((name, "w%d" % i))
    names = [m for m, _ in makers]
    for i in range(rnd.randint(2, 4)):
        name = "r%d" % i
        lines.append("step %s or%d" % (name, i))
        mk, out = rnd.choice(makers)
        if rnd.random() < 0.5:
            lines.append("op %s read %s" % (name, out))
            lines.append("op %s pull %s" % (name, mk))
        else:
            lines.append("op %s pull %s" % (name, mk))
            lines.append("op %s read %s" % (name, out))
        lines.append("op %s emit *" % name)
        names.append(name)
    _rounds(rnd, lines, paths + [o for _, o in makers], names, rnd.randint(2, 4), 2, 2)
    return "\n".join(lines)


def ring(rnd):
    """Pull chains that close on themselves, sometimes below an outer step."""
    n = rnd.randint(2, 4)
    lines = ["seed f0 %s" % rnd.choice(WORDS)]
    names = ["c%d" % i for i in range(n)]
    for i, name in enumerate(names):
        lines.append("step %s oc%d" % (name, i))
        if rnd.random() < 0.3:
            lines.append("op %s look f0" % name)
        lines.append("op %s pull %s" % (name, names[(i + 1) % n]))
        lines.append("op %s emit *" % name)
    lines += ["step lead olead", "op lead read f0",
              "op lead pull %s" % rnd.choice(names), "op lead emit *"]
    names = names + ["lead"]
    for _ in range(rnd.randint(1, 3)):
        lines.append("round")
        if rnd.random() < 0.5:
            lines.append("put f0 %s" % rnd.choice(WORDS))
        lines.append("want %s" % rnd.choice(names))
    return "\n".join(lines)


def dead(rnd):
    """Steps that die on a path that is not there, and the path arriving later."""
    lines = ["seed here %s" % rnd.choice(WORDS)]
    ghosts = ["g%d" % i for i in range(3)]
    names = []
    for i in range(rnd.randint(2, 3)):
        name = "d%d" % i
        lines.append("step %s od%d" % (name, i))
        if rnd.random() < 0.5:
            lines.append("op %s read here" % name)
        # Two absent paths in a row: which one the run dies on moves as the rounds create
        # and remove them, so the reason changes while the step stays dead, and the run
        # that dies on the first leaves a shorter record than the one before it.
        for g in rnd.sample(ghosts, rnd.randint(1, 3)):
            lines.append("op %s read %s" % (name, g))
        lines.append("op %s %s" % (name, _emit(rnd, 0.4)))
        names.append(name)
    for i in range(rnd.randint(1, 3)):
        name = "v%d" % i
        lines.append("step %s ov%d" % (name, i))
        lines.append("op %s pull %s" % (name, rnd.choice(names)))
        if rnd.random() < 0.4:
            lines.append("op %s look here" % name)
        lines.append("op %s emit *" % name)
        names.append(name)
    for _ in range(rnd.randint(3, 5)):
        lines.append("round")
        g = rnd.choice(ghosts)
        if rnd.random() < 0.6:
            lines.append("put %s %s" % (g, rnd.choice(WORDS)))
        else:
            lines.append("cut %s" % g)
        for _ in range(rnd.randint(1, 2)):
            lines.append("want %s" % rnd.choice(names))
    return "\n".join(lines)


def wideobs(rnd):
    """Long records: many observations per step, and the first one is what moves."""
    paths = ["f%d" % i for i in range(12)]
    lines = ["seed %s %s" % (p, rnd.choice(WORDS)) for p in paths]
    names = []
    for i in range(rnd.randint(3, 5)):
        name = "w%d" % i
        lines.append("step %s ow%d" % (name, i))
        for _ in range(rnd.randint(8, 16)):
            if rnd.random() < 0.5:
                lines.append("op %s read %s" % (name, rnd.choice(paths)))
            else:
                lines.append("op %s look %s" % (name, rnd.choice(paths)))
        if names and rnd.random() < 0.6:
            lines.append("op %s pull %s" % (name, rnd.choice(names)))
        lines.append("op %s emit *" % name)
        names.append(name)
    _rounds(rnd, lines, paths, names, rnd.randint(3, 5), 3, 2)
    return "\n".join(lines)


def mixed(rnd):
    """Several shapes in one program, so a reading repaired for one meets the others."""
    paths = ["f%d" % i for i in range(3)]
    ghosts = ["g0"]
    lines = ["seed %s %s" % (p, rnd.choice(WORDS)) for p in paths]
    names = []
    lines += ["step h0 twin", "op h0 read f0", "op h0 %s" % _emit(rnd, 0.3),
              "step h1 twin", "op h1 read f1", "op h1 %s" % _emit(rnd, 0.3),
              "step rd otwin", "op rd read twin", "op rd emit *"]
    names += ["h0", "h1", "rd"]
    for i in range(rnd.randint(2, 4)):
        name = "x%d" % i
        lines.append("step %s ox%d" % (name, i))
        for _ in range(rnd.randint(1, 3)):
            pick = rnd.random()
            if pick < 0.3:
                lines.append("op %s look %s" % (name, rnd.choice(paths + ghosts)))
            elif pick < 0.55:
                lines.append("op %s read %s" % (name, rnd.choice(paths)))
            elif pick < 0.7:
                lines.append("op %s read %s" % (name, rnd.choice(ghosts)))
            else:
                lines.append("op %s pull %s" % (name, rnd.choice(names)))
        lines.append("op %s %s" % (name, _emit(rnd, 0.25)))
        names.append(name)
    lines.append("step top otop")
    for other in rnd.sample(names, min(len(names), rnd.randint(2, 4))):
        lines.append("op top pull %s" % other)
    lines.append("op top emit *")
    names.append("top")
    _rounds(rnd, lines, paths + ghosts + ["twin"], names, rnd.randint(3, 6), 2, 3)
    return "\n".join(lines)


def deep(depth, rounds, rnd):
    """The scale family: a diamond whose every level is reachable two ways."""
    lines = ["seed f0 %s" % rnd.choice(WORDS)]
    for k in range(depth):
        lines += [
            "step a%d oa%d" % (k, k),
            "op a%d pull b%d" % (k, k),
            "op a%d pull c%d" % (k, k),
            "op a%d emit *" % k,
            "step b%d ob%d" % (k, k),
            "op b%d pull a%d" % (k, k + 1),
            "op b%d emit *" % k,
            "step c%d oc%d" % (k, k),
            "op c%d pull a%d" % (k, k + 1),
            "op c%d emit *" % k,
        ]
    lines += ["step a%d oa%d" % (depth, depth),
              "op a%d read f0" % depth,
              "op a%d emit *" % depth]
    for r in range(rounds):
        lines.append("round")
        if r and r % 2 == 0:
            lines.append("put f0 %s" % WORDS[r % len(WORDS)])
        lines.append("want a0")
    return "\n".join(lines)


def programs(seed, per):
    """Return [(program id, program text)] for one seed."""
    out = []
    for fam in FAMILIES:
        maker = globals()[fam]
        for i in range(per):
            rnd = random.Random("%s/%s/%d" % (seed, fam, i))
            out.append(("%s.%02d" % (fam, i), maker(rnd)))
    out.append(("deep.00", deep(24, 4, random.Random("%s/deep" % seed))))
    out.append(("deep.01", deep(21, 6, random.Random("%s/deep1" % seed))))
    return out
