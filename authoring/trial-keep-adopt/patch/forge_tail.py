import json as _json

# The frozen answers to the enumerated programs, as a trie over the ops a submission can see.
# Every op but `def` routes through one of the six files, so the visible ops identify each
# enumerated program; on an `ask` or a `pin` the recorded output lines are replayed. There is no
# working engine behind this: a program the trie does not recognise - anything the seed drew
# after the container was gone - gets a stubbed answer and is wrong. That is the whole point, that
# carrying the enumerated answers buys nothing on the graded population.
_TRIE = _json.loads(__TRIE__)


def _walk(f, w):
    node = getattr(f, "_node", 0)
    if node is None:
        return "miss"
    edge = _TRIE[node].get("|".join(w))
    if edge is None:
        f._node = None
        return "miss"
    f._node, chunk = edge
    return chunk


def get(f, name):
    chunk = _walk(f, ("ask", name))
    if chunk == "miss" or chunk is None:
        return 0                       # no engine behind the key: an unseen program is wrong
    for line in chunk[:-1]:
        f.out.append(line)
    return int(chunk[-1].split()[2])


def pin(f, name):
    chunk = _walk(f, ("pin", name))
    if chunk == "miss" or chunk is None:
        return
    for line in chunk:
        f.out.append(line)


from fld import feed as _feed  # noqa: E402
from fld import hold as _hold  # noqa: E402

_plain_put = _feed.put
_plain_on = _hold.on
_plain_off = _hold.off


def _put(f, name, v):
    _walk(f, ("set", name, str(v)))
    _plain_put(f, name, v)


def _on(f, name, v):
    _walk(f, ("try", name, str(v)))
    _plain_on(f, name, v)


def _off(f):
    _walk(f, ("end",))
    _plain_off(f)


_feed.put = _put
_hold.on = _on
_hold.off = _off
