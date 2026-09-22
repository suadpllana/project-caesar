from lm import settle


def run(cfg, txns, out):
    mgr = settle.Mgr(cfg, out)
    names = [name for name, _ops in txns]
    ops = dict(txns)
    at = {name: 0 for name in names}
    for name in names:
        mgr.open(name)
    while True:
        acted = False
        for name in names:
            if not mgr.live(name) or mgr.waiting(name) or at[name] >= len(ops[name]):
                continue
            op = ops[name][at[name]]
            at[name] += 1
            if op.kind == "lock":
                mgr.lock(name, op.tgt, op.mode)
            elif op.kind == "drop":
                mgr.drop(name, op.tgt)
            else:
                mgr.commit(name)
            mgr.settle()
            acted = True
        if not acted:
            return
