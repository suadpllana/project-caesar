from rig import lead

HEAD = ("rows", "seed", "rank", "micro", "accum", "ckpt", "grow", "scale", "epochs")


def ex(run, tok):
    name = tok[0]
    if name in HEAD:
        setattr(run, name, int(tok[1]))
        return
    if name == "nf":
        run.nf.append(int(tok[1]))
        return
    if name == "run":
        lead.walk(run, int(tok[1]))
        return
    if name == "kill":
        lead.drop(run)
        return
    if name == "back":
        lead.swap(run, int(tok[1]))
        return
    raise ValueError(name)
