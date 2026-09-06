"""Bounded, seeded mixed-scope histories. This module contains inputs only."""
import hashlib
import random


def text(seed, index, recycle=False):
    rng = random.Random(int(hashlib.sha256(f"{seed}/scope/{index}".encode()).hexdigest(), 16))
    lines = ["screen s", "w a s foc", "w c s comp", "w x c foc",
             "w d c comp", "w i d foc", "w j d foc grp=g", "w k d foc grp=g sel",
             "w e d comp", "w u e foc", "w v e foc", "w y c foc", "w z s foc",
             "w h s", "w h1 h foc", "screen m", "w m1 m foc",
             "screen n", "w n1 n foc", "push s"]
    live = set("a c x d i j k e u v y z h h1".split())
    kids = {w: [] for w in live | {"s"}}
    par = {}
    for w, p in [("a", "s"), ("c", "s"), ("x", "c"), ("d", "c"),
                 ("i", "d"), ("j", "d"), ("k", "d"), ("e", "d"),
                 ("u", "e"), ("v", "e"), ("y", "c"), ("z", "s"),
                 ("h", "s"), ("h1", "h")]:
        par[w] = p
        kids[p].append(w)
    stack = ["s"]
    unused = ["m", "n"]
    serial = 0
    retired = set()

    def descendants(w):
        return [w] + [x for ch in kids[w] for x in descendants(ch)]

    # Each history begins with an observable nested branch, then combines mutations,
    # requests, keys, and modal returns. The generator does not compute focus.
    lines.extend(["want v", "tab", "hide v", "back", "show v"])
    for _ in range(70):
        op = rng.randrange(12)
        pool = sorted(live)
        if op < 4:
            lines.append(rng.choice(["tab", "back", "next", "prev"]))
        elif op == 4 and pool:
            lines.append("want " + rng.choice(pool))
        elif op == 5 and pool:
            lines.append(rng.choice(["hide", "show", "off", "on", "shut", "open"]) + " " + rng.choice(pool))
        elif op == 6 and pool:
            w = rng.choice(pool)
            hosts = sorted((live | {"s"}) - set(descendants(w)))
            if hosts:
                p = rng.choice(hosts)
                kids[par[w]].remove(w)
                at = rng.randrange(len(kids[p]) + 1)
                kids[p].insert(at, w)
                par[w] = p
                lines.append(f"move {w} {p} {at}")
        elif op == 7 and len(live) > 4:
            w = rng.choice(pool)
            removed = descendants(w)
            kids[par[w]].remove(w)
            live.difference_update(removed)
            retired.update(removed)
            lines.append("drop " + w)
        elif op == 8 and len(live) < 25 and serial < 24:
            serial += 1
            w = f"new{serial}"
            if recycle and retired and rng.random() < 0.85:
                w = rng.choice(sorted(retired))
                retired.remove(w)
            p = rng.choice(sorted(live | {"s"}))
            at = rng.randrange(len(kids[p]) + 1)
            # `pick` is the only event that changes an existing selection. An added
            # group member therefore starts unselected, preserving the script invariant
            # that a group never has two selected members.
            kind = rng.choice(["foc", "foc grp=g", "comp", ""])
            par[w], kids[w] = p, []
            kids[p].insert(at, w)
            live.add(w)
            lines.append(f"add {w} {p} {at} {kind}".rstrip())
        elif op == 9:
            if unused:
                s = unused.pop(0)
                stack.append(s)
                lines.append("push " + s)
            elif len(stack) > 1:
                s = rng.choice(stack[1:])
                stack.remove(s)
                lines.append("pop " + s)
        elif op == 10 and pool:
            lines.append("pick " + rng.choice(pool))
        elif op == 11 and len(stack) > 1:
            s = stack.pop()
            lines.append("pop " + s)
    while len(stack) > 1:
        lines.append("pop " + stack.pop())
    lines.extend(["tab", "next", "prev", "back"])
    return "\n".join(lines) + "\n"


def batch(seed, count):
    return [(f"nested-{i:04d}", text(seed, i)) for i in range(count)]


def recycled_batch(seed, count):
    return [(f"recycled-{i:04d}", text(seed, i, recycle=True)) for i in range(count)]
