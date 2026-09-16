from . import zt


def nom_at(job, k, prev):
    if job.mode != "clock":
        return zt.at_local(job.zone, job.anchor) if k == 0 else prev + job.step
    return zt.at_local(job.zone, job.anchor + k * job.step)
