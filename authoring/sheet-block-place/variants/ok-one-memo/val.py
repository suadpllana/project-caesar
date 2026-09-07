from . import addr, grid, see


def run(st, node):
    k = node[0]
    if k == "num":
        return node[1]
    if k == "ref":
        return see.face(st, node[1])
    if k == "rng":
        return see.gather(st, node[1], node[2])
    if k == "bin":
        return arith(st, node)
    return call(st, node[1], [run(st, x) for x in node[2]])


def arith(st, node):
    l = run(st, node[2])
    r = run(st, node[3])
    for v in (l, r):
        if grid.is_blk(v) or grid.is_set(v):
            return grid.REF
    if grid.is_err(l):
        return l
    if grid.is_err(r):
        return r
    a = 0 if grid.is_gap(l) else l
    b = 0 if grid.is_gap(r) else r
    if node[1] == "+":
        return a + b
    if node[1] == "-":
        return a - b
    return a * b


def looped(args):
    for v in args:
        for e in grid.items(v):
            if e is grid.CYC:
                return True
    return False


def count(v):
    if grid.is_err(v) or grid.is_gap(v) or grid.is_blk(v) or grid.is_set(v):
        return None
    if v < 1 or v > addr.ROWH:
        return None
    return v


def call(st, nm, args):
    if looped(args):
        return grid.CYC
    if nm in ("SUM", "MAX", "CNT"):
        nums = []
        seen = 0
        for v in args:
            for e in grid.items(v):
                if grid.is_gap(e):
                    continue
                seen += 1
                if not grid.is_err(e):
                    nums.append(e)
        if nm == "CNT":
            return seen
        if nm == "SUM":
            return sum(nums)
        return max(nums) if nums else grid.REF
    if nm == "LEN":
        if len(args) != 1:
            return grid.REF
        return grid.size(args[0])
    if nm == "AT":
        if len(args) != 2:
            return grid.REF
        if grid.is_err(args[1]):
            return args[1]
        k = count(args[1])
        if k is None:
            return grid.REF
        pool = grid.items(args[0])
        if k > len(pool):
            return grid.REF
        return pool[k - 1]
    if nm == "RUN":
        if len(args) != 1:
            return grid.REF
        if grid.is_err(args[0]):
            return args[0]
        k = count(args[0])
        if k is None:
            return grid.REF
        return grid.blk(k, 1, range(1, k + 1))
    if nm in ("REP", "ROW"):
        if len(args) != 2:
            return grid.REF
        if grid.is_err(args[1]):
            return args[1]
        k = count(args[1])
        if k is None:
            return grid.REF
        v = args[0]
        if grid.is_blk(v) or grid.is_set(v):
            return grid.REF
        if nm == "REP":
            return grid.blk(k, 1, [v] * k)
        if k > addr.COLW:
            return grid.REF
        return grid.blk(1, k, [v] * k)
    if nm == "KEEP":
        if len(args) != 2:
            return grid.REF
        if grid.is_err(args[1]):
            return args[1]
        k = count(args[1])
        if k is None:
            return grid.REF
        pool = grid.items(args[0])
        if k > len(pool):
            return grid.REF
        return grid.blk(k, 1, pool[:k])
    if nm == "GROW":
        if len(args) != 1:
            return grid.REF
        h, w = grid.shape(args[0])
        out = []
        for e in grid.items(args[0]):
            out.append(e if (grid.is_gap(e) or grid.is_err(e)) else e + 1)
        return grid.blk(h, w, out)
    return grid.REF
