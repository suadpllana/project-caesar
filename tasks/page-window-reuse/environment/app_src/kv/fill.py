from kv import keep, live, put


def settle(kv, rq):
    live.trim(kv, rq)
    if kv.wait and kv.wait[0] == rq.name:
        kv.wait.popleft()
    else:
        kv.wait.remove(rq.name)
    kv.on.append(rq.name)


def feed(kv, rq, b):
    new = not rq.got
    got = 0
    if new:
        got = keep.walk(kv, rq) * kv.w
        rq.fed = got
        rq.got = True
        rq.up = 0
    left = len(rq.prompt) - rq.fed
    if left == 0:
        kv.say("fill", rq.name, got, 0)
        settle(kv, rq)
        return 0, True, True
    take = min(left, b)
    if take <= 0:
        if new:
            kv.say("fill", rq.name, got, 0)
        return 0, True, False
    done = 0
    while done < take:
        if not put.write(kv, rq, rq.prompt[rq.fed]):
            if new or done:
                kv.say("fill", rq.name, got, done)
            return 0, False, False
        rq.fed += 1
        done += 1
    kv.say("fill", rq.name, got, done)
    if rq.fed == len(rq.prompt):
        settle(kv, rq)
    return done, True, True
