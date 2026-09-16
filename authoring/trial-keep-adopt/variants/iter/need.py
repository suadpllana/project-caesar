from fld import defs, keep, make


def get(f, name):
    return want(f, name, {})


def want(f, root, seen):
    frames = [[root, None, None]]
    ret = None
    while frames:
        fr = frames[-1]
        name, rec, i = fr
        if rec is None and i is None:
            if name in seen:
                ret = seen[name]
                frames.pop()
                continue
            if defs.src(f, name):
                ret = seen[name] = over(f, name)
                frames.pop()
                continue
            if keep.pinned(f, name):
                ret = seen[name] = keep.held(f, name)
                frames.pop()
                continue
            got = keep.get(f, name)
            if got is None:
                ret = seen[name] = make.body(f, name, want, seen)
                frames.pop()
                continue
            fr[1] = got
            fr[2] = 0
            continue
        if i and ret != rec[1][i - 1][1]:
            ret = seen[name] = make.body(f, name, want, seen)
            frames.pop()
            continue
        if i == len(rec[1]):
            ret = seen[name] = rec[0]
            frames.pop()
            continue
        fr[2] = i + 1
        frames.append([rec[1][i][0], None, None])
    return ret


def over(f, name):
    pre = f.pre
    if pre is not None and pre.live and pre.src == name:
        return pre.val
    return f.pub[name]


def pin(f, name):
    keep.hold(f, name, get(f, name))


def free(f, name):
    keep.loose(f, name)
