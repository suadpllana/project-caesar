from rt import core, lock, task


def build(cfg, sc):
    ts = []
    for t in sc["tasks"]:
        ts.append(task.Task(t["id"], t["base"], t.get("start", 0), t["prog"]))
    ts.sort(key=lambda x: x.id)
    ms = {}
    for m in sc.get("mx", []):
        ms[m] = lock.Mx(m)
    for t in ts:
        for s in t.prog:
            if s[0] in (task.LOCK, task.UNLOCK) and s[1] not in ms:
                ms[s[1]] = lock.Mx(s[1])
    return core.Core(cfg, ts, ms)
