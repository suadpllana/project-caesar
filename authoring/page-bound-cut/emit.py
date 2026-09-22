"""Build the wrong readings once, and write the cheat scripts from the same sources.

A reading is the reference with one decision replaced by a plausible-but-wrong one, so the
readings measured by tools/readingcheck.py and the cheats that ship are the same files and
cannot drift apart.  Run this before readingcheck, always: a cheat emitted before a reading
was repaired tests the unrepaired reading.

Every replacement asserts that it fired.  A patch that matches nothing leaves the reference
in place, and a reading that is secretly the reference scores 1 for the wrong reason.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

CHEATS = lab.TASK / "cheat"


def src(name):
    return (lab.SOL / name).read_text(encoding="utf-8")


def swap(name, *pairs):
    """The reference file with each (old, new) applied, each asserted to fire once."""
    body = src(name)
    for old, new in pairs:
        if body.count(old) != 1:
            raise SystemExit("emit: %s: pattern occurs %d times, not once:\n%s"
                             % (name, body.count(old), old[:90]))
        body = body.replace(old, new)
    return {name: body}


READINGS = {}


def reading(key, files):
    READINGS[key] = files


# --- what a page costs ---------------------------------------------------------------

reading("size-flat", swap("fit.py", (
    """        pre = share(first, last)
        n += pre + count * ENT + total - count * pre""",
    """        n += count * ENT + total""")))

reading("cap-loose", swap("fit.py", (
    "    return bulk(tr, pid) > tr.cap",
    "    return bulk(tr, pid) >= tr.cap")))

reading("floor-loose", swap("fit.py", (
    "    return bulk(tr, pid) < tr.floor",
    "    return bulk(tr, pid) <= tr.floor")))

# --- the dividing string -------------------------------------------------------------

reading("sep-whole", swap("bound.py", (
    "    return high[:fit.share(low, high) + 1]",
    "    return high")))

reading("sep-short", swap("bound.py", (
    "    return high[:fit.share(low, high) + 1]",
    "    return high[:fit.share(low, high)]")))

reading("sep-left", swap("bound.py", (
    "    return high[:fit.share(low, high) + 1]",
    "    return low[:fit.share(low, high) + 1]")))

reading("bound-never", swap("bound.py", (
    """def fix(tr, site, out):
    if site is None:
        return""",
    """def fix(tr, site, out):
    if site is not None:
        return""")))

reading("bound-parent", swap("bound.py", (
    """def lgap(tr, spine, slot, d):
    k = d - 1
    while k >= 0:
        if slot[k] > 0:
            return spine[k], slot[k] - 1
        k -= 1
    return None""",
    """def lgap(tr, spine, slot, d):
    k = d - 1
    if k >= 0 and slot[k] > 0:
        return spine[k], slot[k] - 1
    return None"""), (
    """def rgap(tr, spine, slot, d):
    k = d - 1
    while k >= 0:
        if slot[k] < len(tr.at(spine[k]).seps):
            return spine[k], slot[k]
        k -= 1
    return None""",
    """def rgap(tr, spine, slot, d):
    k = d - 1
    if k >= 0 and slot[k] < len(tr.at(spine[k]).seps):
        return spine[k], slot[k]
    return None""")))

# --- where a page is cut ---------------------------------------------------------------

reading("cut-mid", swap("cut.py", (
    """    best = None
    for i in range(1, n):
        sep = bound.edge(keys[i - 1], keys[i])
        left = fit.span(keys[0], keys[i - 1], i, pre[i], 0)
        right = fit.span(keys[i], keys[n - 1], n - i, pre[n] - pre[i], 0)
        cost = (left if left > right else right) + adds(sep)
        if best is None or (cost, i) < best[0]:
            best = ((cost, i), i, sep)
    return best[1], best[2]""",
    """    i = n // 2
    return i, bound.edge(keys[i - 1], keys[i])"""), (
    """    best = None
    for i in range(n):
        sep = seps[i]
        if i:
            left = fit.span(seps[0], seps[i - 1], i, pre[i], i + 1)
        else:
            left = fit.span("", "", 0, 0, 1)
        rest = n - i - 1
        if rest:
            right = fit.span(seps[i + 1], seps[n - 1], rest, pre[n] - pre[i + 1], m - i - 1)
        else:
            right = fit.span("", "", 0, 0, m - i - 1)
        cost = (left if left > right else right) + adds(sep)
        if best is None or (cost, i) < best[0]:
            best = ((cost, i), i, sep)
    return best[1], best[2]""",
    """    i = (n - 1) // 2
    return i, seps[i]""")))

reading("cut-nopar", swap("cut.py", (
    """        cost = (left if left > right else right) + adds(sep)
        if best is None or (cost, i) < best[0]:
            best = ((cost, i), i, sep)
    return best[1], best[2]


def twig_plan""",
    """        cost = (left if left > right else right)
        if best is None or (cost, i) < best[0]:
            best = ((cost, i), i, sep)
    return best[1], best[2]


def twig_plan""")))

reading("cut-sum", swap("cut.py", (
    """        cost = (left if left > right else right) + adds(sep)
        if best is None or (cost, i) < best[0]:
            best = ((cost, i), i, sep)
    return best[1], best[2]


def twig_plan""",
    """        cost = left + right + adds(sep)
        if best is None or (cost, i) < best[0]:
            best = ((cost, i), i, sep)
    return best[1], best[2]


def twig_plan""")))

reading("cut-tiehigh", swap("cut.py", (
    """        cost = (left if left > right else right) + adds(sep)
        if best is None or (cost, i) < best[0]:
            best = ((cost, i), i, sep)
    return best[1], best[2]


def twig_plan""",
    """        cost = (left if left > right else right)
        if best is None or (cost + adds(sep), -i) < best[0]:
            best = ((cost + adds(sep), -i), i, sep)
    return best[1], best[2]


def twig_plan""")))

reading("root-order", swap("cut.py", (
    """    if up is None:
        top = tr.grab(False)
        top.kids = [pid, mate.pid]""",
    """    if up is None:
        top = tr.grab(False)
        top.pid, mate.pid = mate.pid, top.pid
        tr.pages[top.pid] = top
        tr.pages[mate.pid] = mate
        top.kids = [pid, mate.pid]""")))

# --- joining and emptying ---------------------------------------------------------------

reading("join-left", swap("join.py", (
    """    if j + 1 < len(page.kids):
        if weigh(tr, pid, page.kids[j + 1], page.seps[j]) <= tr.cap:
            fuse(tr, up, j, out)
            return
    if j > 0:
        if weigh(tr, page.kids[j - 1], pid, page.seps[j - 1]) <= tr.cap:
            fuse(tr, up, j - 1, out)""",
    """    if j > 0:
        if weigh(tr, page.kids[j - 1], pid, page.seps[j - 1]) <= tr.cap:
            fuse(tr, up, j - 1, out)
            return
    if j + 1 < len(page.kids):
        if weigh(tr, pid, page.kids[j + 1], page.seps[j]) <= tr.cap:
            fuse(tr, up, j, out)""")))

reading("join-flat", swap("join.py", (
    """def weigh(tr, a, b, mid):
    left = tr.at(a)""",
    """def weigh(tr, a, b, mid):
    return fit.bulk(tr, a) + fit.bulk(tr, b)


def unused_weigh(tr, a, b, mid):
    left = tr.at(a)""")))

reading("join-nomid", swap("join.py", (
    """        left.seps.append(page.seps[at])
        left.seps.extend(right.seps)""",
    """        left.seps.extend(right.seps)""")))

reading("gone-right", swap("join.py", (
    """    if j > 0:
        del page.seps[j - 1]
    elif page.seps:
        del page.seps[0]""",
    """    if j < len(page.seps):
        del page.seps[j]
    elif page.seps:
        del page.seps[j - 1]""")))

reading("gone-quiet", swap("join.py", (
    """    out.gone(pid)
    if page.kids:
        bound.fix(tr, site, out)""",
    """    out.gone(pid)""")))

reading("gone-cascade", swap("join.py", (
    """    out.gone(pid)
    if page.kids:
        bound.fix(tr, site, out)""",
    """    out.gone(pid)
    bound.fix(tr, site, out)""")))

reading("fold-once", swap("join.py", (
    """def tidy(tr, out):
    while True:
        page = tr.at(tr.root)
        if page.leaf or len(page.kids) != 1:
            return""",
    """def tidy(tr, out):
    for _once in (0,):
        page = tr.at(tr.root)
        if page.leaf or len(page.kids) != 1:
            return""")))

# --- the order of the work in one operation ---------------------------------------------

reading("bound-late", swap("step.py", (
    """    if leaf.keys:
        if was_low:
            bound.fix(tr, bound.lgap(tr, spine, slot, d), out)
        elif was_high:
            bound.fix(tr, bound.rgap(tr, spine, slot, d), out)
    while d >= 1:""",
    """    late = None
    if leaf.keys:
        if was_low:
            late = bound.lgap(tr, spine, slot, d)
        elif was_high:
            late = bound.rgap(tr, spine, slot, d)
    while d >= 1:"""), (
    """        elif fit.under(tr, pid):
            join.knit(tr, pid, spine[d - 1], slot[d - 1], out)
        d -= 1
    join.tidy(tr, out)""",
    """        elif fit.under(tr, pid):
            join.knit(tr, pid, spine[d - 1], slot[d - 1], out)
        d -= 1
    join.tidy(tr, out)
    bound.fix(tr, late, out)""")))

reading("bound-lowonly", swap("step.py", (
    """    if leaf.keys:
        if was_low:
            bound.fix(tr, bound.lgap(tr, spine, slot, d), out)
        elif was_high:
            bound.fix(tr, bound.rgap(tr, spine, slot, d), out)""",
    """    if leaf.keys:
        if was_low:
            bound.fix(tr, bound.lgap(tr, spine, slot, d), out)""")))

READING_BUILDERS = []


def main():
    print("readings built: %d" % len(READINGS))
    for key in sorted(READINGS):
        print("  %-14s %s" % (key, ",".join(sorted(READINGS[key]))))


if __name__ == "__main__":
    main()
