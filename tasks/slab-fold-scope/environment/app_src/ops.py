from tab import live, log, push, say


def ex(tab, w):
    op = w[0]
    if op == "plan":
        log.begin(tab, w[1])
    elif op == "put" or op == "cut" or op == "fold":
        log.add(tab, w[1], op, w[2], int(w[3]), int(w[4]))
    elif op == "push":
        push.run(tab, log.pull(tab, w[1]))
    elif op == "bulk":
        tag, buck = w[1], w[2]
        n, lo, wid, gap = int(w[3]), int(w[4]), int(w[5]), int(w[6])
        log.begin(tab, tag)
        step = wid + gap
        for i in range(n):
            a = lo + i * step
            log.add(tab, tag, "put", buck, a, a + wid - 1)
        push.run(tab, log.pull(tab, tag))
    elif op == "rows":
        say.rows(tab, w[1], live.rows(tab, w[1]))
    elif op == "at":
        key = int(w[2])
        say.at(tab, w[1], key, live.at(tab, w[1], key))
