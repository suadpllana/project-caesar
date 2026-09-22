from eng.hold import Loop, Stuck
from eng import step as work


class Wake:
    def __init__(self, p, keep, board, out):
        self.plan = p
        self.keep = keep
        self.board = board
        self.out = out

    def open_round(self):
        self.board.open_round()

    def request(self, name):
        try:
            fact = self.drive(name)
        except Loop as exc:
            self.out.loop(exc.chain)
            return
        except Stuck as exc:
            self.out.stuck(exc.name)
            return
        if fact[0] == "ok":
            self.out.ok(name, fact[1])
        else:
            self.out.err(name, fact[1])

    def drive(self, top):
        b = self.board
        keep = self.keep
        stack = []
        live = []
        ret = None
        pending = top
        try:
            while True:
                if pending is not None:
                    name, pending = pending, None
                    if name in live:
                        i = live.index(name)
                        raise Loop(live[i:] + [name])
                    if b.fact[name] is not None and b.seen[name] == keep.stamp:
                        ret = b.fact[name]
                        if not stack:
                            return ret
                        continue
                    mode = "check" if b.fact[name] is not None else "start"
                    stack.append({"n": name, "m": mode, "i": 0, "v": [], "w": False})
                    live.append(name)
                    ret = None
                    continue

                fr = stack[-1]
                name = fr["n"]

                if fr["m"] == "check":
                    rec = b.rec[name]
                    if fr["w"]:
                        fr["w"] = False
                        if not rec[fr["i"]].agrees(ret):
                            fr["m"] = "stale"
                            continue
                        fr["i"] += 1
                    stale = False
                    while fr["i"] < len(rec):
                        m = rec[fr["i"]]
                        other = m.pull_of()
                        if other is not None:
                            fr["w"] = True
                            pending = other
                            break
                        if not m.holds(keep):
                            stale = True
                            break
                        fr["i"] += 1
                    if fr["w"]:
                        continue
                    if stale:
                        fr["m"] = "stale"
                        continue
                    b.seen[name] = keep.stamp
                    stack.pop()
                    live.pop()
                    ret = b.fact[name]
                    if not stack:
                        return ret
                    continue

                if fr["m"] == "stale":
                    if b.ran[name]:
                        raise Stuck(name)
                    fr["m"] = "start"
                    continue

                if fr["m"] == "start":
                    self.out.run(name)
                    b.wipe(name)
                    fr["m"] = "run"
                    fr["i"] = 0
                    fr["v"] = []
                    continue

                ops = self.plan.steps[name].ops
                where = self.plan.steps[name].out
                fact = None
                if fr["w"]:
                    fr["w"] = False
                    val, bad = work.take_pull(b, name, ops[fr["i"]][1], ret)
                    if bad is not None:
                        fact = bad
                    else:
                        fr["v"].append(val)
                        fr["i"] += 1
                while fact is None and fr["i"] < len(ops):
                    code, arg = ops[fr["i"]]
                    if code == "read":
                        val, bad = work.take_read(b, keep, name, arg)
                        if bad is not None:
                            fact = bad
                            break
                        fr["v"].append(val)
                        fr["i"] += 1
                    elif code == "look":
                        work.take_look(b, keep, name, arg)
                        fr["i"] += 1
                    elif code == "pull":
                        fr["w"] = True
                        pending = arg
                        break
                    else:
                        fact = work.finish(fr["v"], arg)
                        break
                if fr["w"]:
                    continue
                work.settle(b, keep, name, where, fact)
                stack.pop()
                live.pop()
                ret = b.fact[name]
                if not stack:
                    return ret
        except (Loop, Stuck):
            for fr in stack:
                if fr["m"] == "run":
                    b.wipe(fr["n"])
            raise
