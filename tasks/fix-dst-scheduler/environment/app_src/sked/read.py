from . import check, rec


def parse(text):
    p = rec.Plan()
    for raw in text.splitlines():
        f = raw.split()
        if not f:
            continue
        head = f[0]
        if head == "zone":
            p.zones[f[1]] = rec.Zone(f[1], int(f[2]))
        elif head == "shift":
            p.zones[f[1]].shifts.append((int(f[2]), int(f[3])))
        elif head == "pool":
            p.pools[f[1]] = rec.Pool(f[1], p.zones[f[2]], int(f[3]))
        elif head == "job":
            p.jobs.append(rec.Job(f[1], p.zones[f[2]], int(f[3]), p.pools[f[4]],
                                  int(f[5]), int(f[6]), int(f[7]), f[8],
                                  int(f[9]), int(f[10])))
        elif head == "horizon":
            p.horizon = int(f[1])
        else:
            raise ValueError(head)
    for z in p.zones.values():
        z.shifts.sort()
    p.jobs.sort(key=lambda j: j.prio)
    return check.plan(p)


def load(path):
    with open(path, "r") as fh:
        return parse(fh.read())
