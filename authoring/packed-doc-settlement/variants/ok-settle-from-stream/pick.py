def take(run, mb):
    run.st["mbs"] = run.st.get("mbs", 0) + 1


def close(run):
    run.st["mbs"] = 0
    lim = run.cfg["lim"]
    hi = run.feed.at
    lo = hi - run.took * lim
    done = []
    for pos in range(lo, hi):
        key, i = run.feed.q[pos]
        name, n, t = run.feed.info(key)
        if i == n - 1 and t >= 0:
            done.append(key)
    return done
