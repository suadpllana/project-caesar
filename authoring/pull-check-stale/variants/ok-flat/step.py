from eng import dig
from eng import mark


def take_read(board, keep, name, path):
    board.rec[name].append(mark.Bytes(path, keep))
    if not keep.has(path):
        return None, ("bad", "missing %s" % path)
    return keep.text(path), None


def take_look(board, keep, name, path):
    board.rec[name].append(mark.There(path, keep))


def take_pull(board, name, other, fact):
    board.rec[name].append(mark.From(other, fact))
    if fact[0] == "bad":
        return None, ("bad", "via %s" % other)
    return fact[1], None


def finish(vals, arg):
    return ("ok", dig.mix(vals) if arg == "*" else arg)


def settle(board, keep, name, where, fact):
    board.fact[name] = fact
    if fact[0] == "ok":
        keep.put(where, fact[1])
        board.rec[name].append(mark.Made(where, keep))
    board.ran[name] = True
    board.seen[name] = keep.stamp
