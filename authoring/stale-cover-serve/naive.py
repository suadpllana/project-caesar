"""The two exactly-correct serving searches the resource gate is aimed at.

Both answer the same question as the reference and both are right. `seek` asks it of every
version from the present one down to the allowance floor, which is what a first implementation
does when the allowance reads as a range of versions. `flat` asks it only at the versions where
some stretch's validity ends - the first real optimisation - but rebuilds the coverage from
scratch at each of them instead of carrying it down, so it pays the whole table once per
candidate rather than once per read.
"""

SEEK = '''
def at(tb, lo, hi, s, now):
    floor = now - s
    if floor < 0:
        floor = 0
    near = tb.near(lo, hi)
    for v in range(now, floor - 1, -1):
        need = hi - lo + 1
        seen = [False] * (hi - lo + 1)
        for st in near:
            if st.born > v:
                continue
            if 0 <= st.died < v:
                continue
            a = st.lo if st.lo > lo else lo
            b = st.hi if st.hi < hi else hi
            for k in range(a - lo, b - lo + 1):
                if not seen[k]:
                    seen[k] = True
                    need -= 1
            if not need:
                break
        if not need:
            return v
    return None
'''

FLAT = '''
def at(tb, lo, hi, s, now):
    floor = now - s
    if floor < 0:
        floor = 0
    near = tb.near(lo, hi)
    marks = set([now])
    for st in near:
        top = now if st.died < 0 else st.died
        if floor <= top < now:
            marks.add(top)
    for v in sorted(marks, reverse=True):
        need = hi - lo + 1
        seen = [False] * (hi - lo + 1)
        for st in near:
            if st.born > v:
                continue
            if 0 <= st.died < v:
                continue
            a = st.lo if st.lo > lo else lo
            b = st.hi if st.hi < hi else hi
            for k in range(a - lo, b - lo + 1):
                if not seen[k]:
                    seen[k] = True
                    need -= 1
            if not need:
                break
        if not need:
            return v
    return None
'''
