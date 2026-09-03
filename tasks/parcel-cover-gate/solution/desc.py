# Standing after a version is reachability, and the graph is not a line.
#
# Every version of a setting records the versions it was written on top of, so
# the versions of one setting form a graph rather than a chain. A plain write has
# one parent, the version its writer was showing. A settling has two, and that is
# the whole reason this cannot be a walk up a single link: after a worker settles
# a setting against something it was handed, its version stands after two pieces
# of history at once, and half of that history is only reachable through the
# second parent. Following the first parent alone answers "no" for everything the
# other side ever wrote, which reads as a picture that can never be covered and
# shows up as parcels that sit in a bag forever with nothing wrong with them.
#
# The numbers are handed out in the order the writes happened. That says which
# write came first. It says nothing about whether one stands after the other,
# because two workers showing the same version can both write it and get two
# numbers with no line between them.


def runs(st, a, b):
    if a == b:
        return True
    seen = set()
    front = [a]
    while front:
        cur = front.pop()
        if cur == b:
            return True
        if cur in seen:
            continue
        seen.add(cur)
        front.extend(st.vers[cur].base)
    return False
