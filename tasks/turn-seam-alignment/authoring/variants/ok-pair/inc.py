from tok import core

# Where an encode may legally be resumed.
#
# A merge joins two symbols, so the symbol it produces is the concatenation of the two,
# and reading every symbol the table can build tells you everything about what can reach
# across a boundary. A boundary survives every encode of every surrounding text when
# nothing can reach across it, and there are two independent ways for that to be so: the
# character after the boundary never sits anywhere but at the front of a symbol, so
# nothing to the left can ever swallow it, or the character before the boundary never
# sits anywhere but at the end of a symbol, so nothing to the right can ever be pulled
# back into it.
#
# Neither condition implies the other and both carry positions the other misses. Taking
# only the first is safe, and walks past resume points that were there, which the
# character count charges for. The cruder test still - a character that takes part in no
# merge at all - is smaller again, because the ticket and handle markers are the left
# half of merges while never being the right half of one.
def _points():
    pairs = set()
    for a, b in core.MG:
        s = a + b
        for i in range(len(s) - 1):
            pairs.add((s[i], s[i + 1]))
    return frozenset(pairs), frozenset()


FRONT, BACK = _points()


def safe(text, j):
    if j <= 0:
        return True
    if j >= len(text):
        return True
    return (text[j - 1], text[j]) not in FRONT


def cut(text, old, ids):
    # How much of the cached render survives, character for character. An appended turn
    # leaves the whole of it standing; a retry that dropped a turn cuts it short. One
    # rule covers both, because both are answered by the first character that moved.
    n = min(len(text), len(old))
    i = 0
    while i < n and text[i] == old[i]:
        i += 1

    # Walk back from there to the latest boundary nothing can reach across. Everything
    # after that point may have been re-merged by what now follows it.
    j = i
    while not safe(text, j):
        j -= 1
    if j <= 0:
        return 0, 0

    # That boundary holds in the cached ids as well, so the prefix of them covering it
    # can be handed back untouched.
    w = 0
    k = 0
    while k < len(ids) and w < j:
        w += core.WID[ids[k]]
        k += 1
    if w != j:
        return 0, 0
    return j, k


def encode(tok, text, old, ids):
    off, n = cut(text, old, ids)
    if off <= 0:
        return tok.encode(text)
    return list(ids[:n]) + tok.encode(text[off:])
