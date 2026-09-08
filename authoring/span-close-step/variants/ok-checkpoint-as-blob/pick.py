"""Open-document bookkeeping and settlement selection.

`take` is called once per micro-batch and records nothing but token counts: the
objective is evaluated at settlement, so no score may be folded here. `close` is
called once per step and names the occurrences whose last token was consumed
during it, in the order those last tokens stand in the stream. Occurrence keys are
handed out in stream order, so ascending key is that order; a masked occurrence
(target -1) is consumed and dropped rather than settled.
"""


def take(run, mb):
    cnt = run.st.setdefault("cnt", {})
    for sq in mb:
        for key, _ in sq:
            cnt[key] = cnt.get(key, 0) + 1


def close(run):
    cnt = run.st.get("cnt", {})
    seen = run.st.setdefault("seen", {})
    done = []
    for key, c in cnt.items():
        seen[key] = seen.get(key, 0) + c
        _, n, t = run.feed.info(key)
        if seen[key] >= n:
            del seen[key]
            if t >= 0:
                done.append(key)
    run.st["cnt"] = {}
    return sorted(done)
