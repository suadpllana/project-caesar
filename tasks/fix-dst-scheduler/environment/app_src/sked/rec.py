class Zone:
    def __init__(self, name, base):
        self.name = name
        self.base = base
        self.shifts = []


class Pool:
    def __init__(self, name, zone, cap):
        self.name = name
        self.zone = zone
        self.cap = cap


class Job:
    def __init__(self, jid, zone, prio, pool, dur, opn, shut, mode, step, anchor):
        self.jid = jid
        self.zone = zone
        self.prio = prio
        self.pool = pool
        self.dur = dur
        self.opn = opn
        self.shut = shut
        self.mode = mode
        self.step = step
        self.anchor = anchor


class Plan:
    def __init__(self):
        self.zones = {}
        self.pools = {}
        self.jobs = []
        self.horizon = 0


class Occ:
    def __init__(self, job, k, nom):
        self.job = job
        self.k = k
        self.nom = nom


class Ev:
    def __init__(self, kind, job, k, t):
        self.kind = kind
        self.job = job
        self.k = k
        self.t = t
