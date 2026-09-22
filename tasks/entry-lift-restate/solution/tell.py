def one(out, sec, name, found, passes):
    out.line("get %d %d %s %d" % (sec, name, "-" if found is None else found, passes))


def board(out, held, masked, links, passes):
    out.line("all %d %d %d %d" % (passes, len(held), len(masked), len(links)))
    for key in sorted(held):
        out.line("v %d %d %d" % (key[0], key[1], held[key]))
    for key in masked:
        out.line("m %d %d" % key)
    for sec in sorted(links):
        out.line("l %d %d" % (sec, links[sec]))
