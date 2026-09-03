# The same row read off one pass with explicit comparisons instead of tuple
# ordering, and the smallest key taken by a running minimum rather than a sort.
def auth(bk, c):
    run, key = None, None
    for (n, k) in bk.post:
        if bk.find(k) != c:
            continue
        if run is None or n < run or (n == run and k < key):
            run, key = n, k
    return None if run is None else (run, key)


def card(bk, c):
    low = None
    for k in bk.held(c):
        if low is None or k < low:
            low = k
    a = auth(bk, c)
    return low, (bk.post[a] if a is not None else -1)
