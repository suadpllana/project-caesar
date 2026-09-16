from . import zt


def nom_at(job, k, prev):
    if job.mode == "clock":
        return zt.at_local(job.zone, job.anchor + k * job.step)
    if k == 0:
        return zt.at_local(job.zone, job.anchor)
    return prev + job.step
