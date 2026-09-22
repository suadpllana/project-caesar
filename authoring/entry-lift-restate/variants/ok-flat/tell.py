def one(out, sec, name, found, passes):
    shown = "-" if found is None else str(found)
    out.line(" ".join(("get", str(sec), str(name), shown, str(passes))))


def board(out, held, masked, links, passes):
    out.line(" ".join(("all", str(passes), str(len(held)), str(len(masked)), str(len(links)))))
    for sec, name in sorted(held):
        out.line("v %d %d %d" % (sec, name, held[(sec, name)]))
    for sec, name in masked:
        out.line("m %d %d" % (sec, name))
    for sec in sorted(links):
        out.line("l %d %d" % (sec, links[sec]))
