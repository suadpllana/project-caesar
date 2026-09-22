def one(out, sec, name, found, passes):
    out.line("get %d %d %s %d" % (sec, name, "-" if found is None else found, passes))


def board(out, held, masked, links, passes):
    out.line("all %d %d %d %d" % (passes, len(held), len(masked), len(links)))
    rows = [("v %d %d %d" % (s, n, held[(s, n)])) for s, n in sorted(held)]
    rows += [("m %d %d" % (s, n)) for s, n in masked]
    rows += [("l %d %d" % (s, links[s])) for s in sorted(links)]
    for row in rows:
        out.line(row)
