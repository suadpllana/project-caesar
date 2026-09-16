from . import zt

CLOCK = "clock"


def nom_at(job, k, prev):
    if job.mode == CLOCK:
        return zt.at_local(job.zone, job.anchor + k * job.step)
    if k:
        return prev + job.step
    return zt.at_local(job.zone, job.anchor)
