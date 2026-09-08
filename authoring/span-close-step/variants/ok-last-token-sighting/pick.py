import bisect


def take(run, mb):
    live = run.st.setdefault("live", [])
    hit = run.st.setdefault("hit", {})
    for sq in mb:
        for key, i in sq:
            at = bisect.bisect_left(live, key)
            if at == len(live) or live[at] != key:
                live.insert(at, key)
            if i == run.feed.info(key)[1] - 1:
                hit[key] = True


def close(run):
    hit = run.st.get("hit", {})
    done = []
    rest = []
    for key in run.st.get("live", []):
        if hit.get(key):
            if run.feed.info(key)[2] >= 0:
                done.append(key)
        else:
            rest.append(key)
    run.st["live"] = rest
    run.st["hit"] = {}
    return done
