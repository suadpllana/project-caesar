"""Rows for the short-answer audit over the shipped policy inputs."""

from __future__ import annotations

import random


def _factory_rows():
    out = []
    for minted in range(1, 5):
        for active in range(minted, 6):
            out.append(({
                "minted_scope": minted,
                "active_scope": active,
                "distance": active - minted,
            }, minted))
    return out


def _home_rows():
    rnd = random.Random("scope-hold-release-home")
    out = []
    for _ in range(120):
        count = rnd.randrange(3, 9)
        life = {i: rnd.randrange(3) for i in range(1, count + 1)}
        parent = {1: 0}
        for i in range(2, count + 1):
            parent[i] = rnd.randrange(0, i)
        at = rnd.randrange(1, 5)
        for i in range(1, count + 1):
            j = i
            rooted = False
            depth = 0
            while j:
                rooted = rooted or life[j] == 0
                j = parent[j]
                depth += 1
            p = parent[i]
            out.append(({
                "life": life[i],
                "parent_life": life[p] if p else -1,
                "has_parent": int(bool(p)),
                "depth": depth,
                "charged_scope": at,
            }, rooted))
    return out


def _mark_rows():
    rnd = random.Random("scope-hold-release-mark")
    out = []
    for _ in range(300):
        depth = rnd.randrange(1, 6)
        at = rnd.randrange(1, depth + 1)
        marked = [i for i in range(1, depth + 1) if rnd.random() < 0.45]
        if not marked:
            marked = [rnd.randrange(1, depth + 1)]
        reachable = [i for i in marked if i <= at]
        label = max(reachable) if reachable else 0
        out.append(({
            "active_scope": depth,
            "charged_scope": at,
            "mark_count": len(marked),
            "outer_mark": min(marked),
            "inner_mark": max(marked),
            "active_marked": int(depth in marked),
            "charged_marked": int(at in marked),
        }, label))
    return out


def samples():
    return {
        "factory-charge": _factory_rows(),
        "singleton-ancestry": _home_rows(),
        "marked-home": _mark_rows(),
    }
