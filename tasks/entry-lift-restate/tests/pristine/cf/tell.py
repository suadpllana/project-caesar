def one(out, sec, name, found, passes):
    out.line("get %d %d %s %d" % (sec, name, "-" if found is None else found, passes))


def board(out, bd, passes):
    out.line("all %d %d %d %d"
             % (passes, len(bd.val) + len(bd.gone), len(bd.gone), len(bd.link)))
    for key in sorted(bd.gone):
        out.line("m %d %d" % key)
    for key in sorted(bd.val):
        out.line("v %d %d %d" % (key[0], key[1], bd.val[key]))
    for sec in sorted(bd.link):
        out.line("l %d %d" % (sec, bd.link[sec]))
