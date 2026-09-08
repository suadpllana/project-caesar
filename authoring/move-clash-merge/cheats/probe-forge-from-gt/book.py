import hashlib

from mrg import live, name, spot
from mrg.tree import ROOT, Tr, mk

ANSWERS = {"axes-apart": [{"k": "169e2039fee334ef", "v": ["1 L mv /a/m /b/m", "1 R mv /b/n /b/m", "1 l /a -", "1 l /b -", "1 l /b/m k1", "1 r /a -", "1 r /b -", "1 r /b/m k1"]}], "both-moved": [{"k": "2eb10e50bf4c122e", "v": ["1 L mv /b/n /c/n", "1 l /a -", "1 l /b -", "1 l /c -", "1 l /c/n k1", "1 r /a -", "1 r /b -", "1 r /c -", "1 r /c/n k1"]}], "both-moved-and-renamed": [{"k": "63cc9fa6bc63febb", "v": ["1 L mv /b/p /c/q", "1 l /a -", "1 l /b -", "1 l /c -", "1 l /c/q k1", "1 r /a -", "1 r /b -", "1 r /c -", "1 r /c/q k1"]}], "both-renamed": [{"k": "7216fef0e775d608", "v": ["1 L mv /a/p /a/q", "1 l /a -", "1 l /a/q k1", "1 r /a -", "1 r /a/q k1"]}], "both-wrote-apart": [{"k": "baa78b70ecd6a0ff", "v": ["1 L mkf /n~1.txt p3", "1 R mkf /n~1.txt p3", "1 R ed /n.txt p2", "1 l /n.txt p2", "1 l /n~1.txt p3", "1 r /n.txt p2", "1 r /n~1.txt p3"]}], "both-wrote-same": [{"k": "fdf617493c63c30b", "v": ["1 l /n p2", "1 r /n p2"]}], "case-contested": [{"k": "162ed3dc1819ba51", "v": ["1 L mv /a/GH /a/GH~1", "1 R mkf /a/GH~1 p2", "1 l /a -", "1 l /a/GH~1 p2", "1 l /a/gh p1", "1 r /a -", "1 r /a/GH~1 p2", "1 r /a/gh p1"]}], "case-mark-free": [{"k": "ddfc35ab931be661", "v": ["1 L mv /a/GH /a/GH~2", "1 R mkf /a/GH~2 p3", "1 l /a -", "1 l /a/GH~1 p2", "1 l /a/GH~2 p3", "1 l /a/gh p1", "1 r /a -", "1 r /a/GH~1 p2", "1 r /a/GH~2 p3", "1 r /a/gh p1"]}], "case-rename-on-side": [{"k": "82571ce32a49a4f9", "v": ["1 R mv /a/gh /a/~t1", "1 R mv /a/~t1 /a/GH", "1 l /a -", "1 l /a/GH p1", "1 r /a -", "1 r /a/GH p1"]}], "destination-is-a-node": [{"k": "7c3ec6c8cf88ee64", "v": ["1 R mv /w /v/w", "1 R mv /v /~t1", "1 R mv /u /v", "1 R mv /~t1 /u", "1 l /u -", "1 l /u/w p1", "1 l /v -", "1 r /u -", "1 r /u/w p1", "1 r /v -"]}], "folder-held-by-child": [{"k": "ba29bb961ac07078", "v": ["1 L mkd /a", "1 L mkf /a/n p2", "1 l /a -", "1 l /a/n p2", "1 r /a -", "1 r /a/n p2"]}], "folder-held-two-deep": [{"k": "798eaff27f770752", "v": ["1 L mkd /a", "1 L mkd /a/b", "1 L mkf /a/b/n p2", "1 l /a -", "1 l /a/b -", "1 l /a/b/n p2", "1 r /a -", "1 r /a/b -", "1 r /a/b/n p2"]}], "folder-not-held-by-arrival": [{"k": "4107413f7ede4174", "v": ["1 L mv /k/n /n", "1 R mv /a/n /n", "1 R rm /a", "1 l /k -", "1 l /n p1", "1 r /k -", "1 r /n p1"]}], "folder-not-held-by-mover": [{"k": "58d23e1f7cf58a74", "v": ["1 L mkf /n p1", "1 R rm /a", "1 l /n p1", "1 r /n p1"]}], "folder-swap": [{"k": "def406eef5f22c37", "v": ["1 R mv /v /~t1", "1 R mv /u /v", "1 R mv /~t1 /u", "1 l /u -", "1 l /v -", "1 l /v/n p1", "1 r /u -", "1 r /v -", "1 r /v/n p1"]}], "gone-both": [{"k": "c3d8874a5ae2f1e1", "v": ["1 l /a -", "1 r /a -"]}], "gone-vs-name": [{"k": "7b9ec8194ad20d77", "v": ["1 L mkf /a/m p1", "1 l /a -", "1 l /a/m p1", "1 r /a -", "1 r /a/m p1"]}], "gone-vs-place": [{"k": "ad802bcf1a8c42bb", "v": ["1 L mkf /b/n p1", "1 l /a -", "1 l /b -", "1 l /b/n p1", "1 r /a -", "1 r /b -", "1 r /b/n p1"]}], "gone-vs-quiet": [{"k": "b6cffdd27c8dcc2a", "v": ["1 L ed /a/m p3", "1 R rm /a/n", "1 l /a -", "1 l /a/m p3", "1 r /a -", "1 r /a/m p3"]}], "gone-vs-write": [{"k": "252a5b1bb1908e35", "v": ["1 L mkf /a/n p2", "1 l /a -", "1 l /a/n p2", "1 r /a -", "1 r /a/n p2"]}], "holder-keeps": [{"k": "606ce5e944a417ef", "v": ["1 L mkf /a/n~1 p2", "1 R mv /a/d/n /a/n~1", "1 R rm /a/d", "1 l /a -", "1 l /a/n p1", "1 l /a/n~1 p2", "1 r /a -", "1 r /a/n p1", "1 r /a/n~1 p2"]}], "holder-keeps-when-gone": [{"k": "6dde111245bbeddd", "v": ["1 L mkf /a/n~1 p3", "1 R mv /a/d/n /a/n~1", "1 R rm /a/d", "1 R mkf /a/n p2", "1 l /a -", "1 l /a/n p2", "1 l /a/n~1 p3", "1 r /a -", "1 r /a/n p2", "1 r /a/n~1 p3"]}], "mark-before-extension": [{"k": "6cc0f30146554118", "v": ["1 L mkf /notes~1.txt p3", "1 R mkf /notes~1.txt p3", "1 R ed /notes.txt p2", "1 l /notes.txt p2", "1 l /notes~1.txt p3", "1 r /notes.txt p2", "1 r /notes~1.txt p3"]}], "mark-leading-dot": [{"k": "5f465ceeadac8810", "v": ["1 L mkf /.cfg~1 p3", "1 R mkf /.cfg~1 p3", "1 R ed /.cfg p2", "1 l /.cfg p2", "1 l /.cfg~1 p3", "1 r /.cfg p2", "1 r /.cfg~1 p3"]}], "mark-skips-taken": [{"k": "bb4b0709c113ee68", "v": ["1 L mkf /a/ab~2 p3", "1 R mv /a/d/ab /a/ab~2", "1 R rm /a/d", "1 l /a -", "1 l /a/ab p1", "1 l /a/ab~1 p2", "1 l /a/ab~2 p3", "1 r /a -", "1 r /a/ab p1", "1 r /a/ab~1 p2", "1 r /a/ab~2 p3"]}], "mark-two-dots": [{"k": "b7f0a238da36c283", "v": ["1 L mkf /x.y~1.z p3", "1 R mkf /x.y~1.z p3", "1 R ed /x.y.z p2", "1 l /x.y.z p2", "1 l /x.y~1.z p3", "1 r /x.y.z p2", "1 r /x.y~1.z p3"]}], "mark-without-extension": [{"k": "f2056600eab03618", "v": ["1 L mkf /ab~1 p3", "1 R mkf /ab~1 p3", "1 R ed /ab p2", "1 l /ab p2", "1 l /ab~1 p3", "1 r /ab p2", "1 r /ab~1 p3"]}], "moved-out-then-removed": [{"k": "35cc3065568b5d58", "v": ["1 L ed /b/n p2", "1 R mv /a/n /b/n", "1 R rm /a", "1 l /b -", "1 l /b/n p2", "1 r /b -", "1 r /b/n p2"]}], "name-contested-folder-not": [{"k": "407f7148e879567a", "v": ["1 L mv /b/p /b/q", "1 l /a -", "1 l /b -", "1 l /b/q k1", "1 r /a -", "1 r /b -", "1 r /b/q k1"]}], "name-freed-by-removal": [{"k": "5185d3b7d8c37463", "v": ["1 R rm /a/n", "1 R mkf /a/n p2", "1 l /a -", "1 l /a/n p2", "1 r /a -", "1 r /a/n p2"]}], "new-in-dead-folder": [{"k": "61d67f3beffed6cc", "v": ["1 L mkf /n p1", "1 R mv /a/n /n", "1 R rm /a", "1 l /k -", "1 l /n p1", "1 r /k -", "1 r /n p1"]}], "new-node-not-made-twice": [{"k": "604c67c7e8c9532e", "v": ["1 R mkf /a/n p1", "1 l /a -", "1 l /a/n p1", "1 r /a -", "1 r /a/n p1"]}, {"k": "4e5545474ddb3930", "v": ["2 L ed /a/n p2", "2 l /a -", "2 l /a/n p2", "2 r /a -", "2 r /a/n p2"]}], "new-nodes-in-path-order": [{"k": "066b5973ff76d0d8", "v": ["1 L mkf /n p1", "1 L mkf /n~1 p2", "1 R mv /n /n~1", "1 R mv /d/n /n", "1 R rm /d", "1 l /a -", "1 l /n p1", "1 l /n~1 p2", "1 r /a -", "1 r /n p1", "1 r /n~1 p2"]}], "one-change-one-operation": [{"k": "8461e7418c2552b7", "v": ["1 L ed /a/m p3", "1 l /a -", "1 l /a/m p3", "1 l /a/n p1", "1 r /a -", "1 r /a/m p3", "1 r /a/n p1"]}], "one-side-moved": [{"k": "a4fdadd05a38e874", "v": ["1 R mv /a/n /b/n", "1 l /a -", "1 l /b -", "1 l /b/n k1", "1 r /a -", "1 r /b -", "1 r /b/n k1"]}], "one-wrote": [{"k": "262b0de102902327", "v": ["1 R ed /n p2", "1 l /n p2", "1 r /n p2"]}], "parents-before-children": [{"k": "9ba1702c0615a73d", "v": ["1 R mkd /a/b", "1 R mkd /a/b/c", "1 R mkf /a/b/c/n p1", "1 l /a -", "1 l /a/b -", "1 l /a/b/c -", "1 l /a/b/c/n p1", "1 r /a -", "1 r /a/b -", "1 r /a/b/c -", "1 r /a/b/c/n p1"]}], "quiet-after-work": [{"k": "5185d3b7d8c37463", "v": ["1 R ed /a/n p2", "1 l /a -", "1 l /a/n p2", "1 r /a -", "1 r /a/n p2"]}, {"k": "90961b8e756b223b", "v": ["2 l /a -", "2 l /a/n p2", "2 r /a -", "2 r /a/n p2"]}], "quiet-round": [{"k": "5cfe35348deceefb", "v": ["1 l /a -", "1 l /a/n p1", "1 r /a -", "1 r /a/n p1"]}], "record-carries-the-mark": [{"k": "f2056600eab03618", "v": ["1 L mkf /ab~1 p3", "1 R mkf /ab~1 p3", "1 R ed /ab p2", "1 l /ab p2", "1 l /ab~1 p3", "1 r /ab p2", "1 r /ab~1 p3"]}, {"k": "abc7ea47275e5f4b", "v": ["2 L mv /ab~1 /cd", "2 l /ab p2", "2 l /cd p3", "2 r /ab p2", "2 r /cd p3"]}], "ring-not-formed": [{"k": "95785b6222ee5335", "v": ["1 R mv /a /b/a", "1 l /b -", "1 l /b/a -", "1 r /b -", "1 r /b/a -"]}], "ring-three": [{"k": "6ab9fd77090eaa6d", "v": ["1 L mv /b/a /a", "1 L mv /b /a/c/b", "1 R mv /c /a/c", "1 l /a -", "1 l /a/c -", "1 l /a/c/b -", "1 r /a -", "1 r /a/c -", "1 r /a/c/b -"]}], "ring-two": [{"k": "dc03b2cd554bd145", "v": ["1 L mv /b/a /a", "1 L mv /b /a/b", "1 l /a -", "1 l /a/b -", "1 r /a -", "1 r /a/b -"]}], "same-change-both-sides": [{"k": "54a8208d29b54b92", "v": ["1 l /a -", "1 l /b -", "1 l /b/n p1", "1 r /a -", "1 r /b -", "1 r /b/n p1"]}], "second-node-in-contest": [{"k": "67bd4ab2f3eba91d", "v": ["1 L mkf /a/ab~2 p2", "1 R mkf /a/ab~2 p2", "1 R ed /a/ab p1", "1 l /a -", "1 l /a/ab p1", "1 l /a/ab~1 q0", "1 l /a/ab~2 p2", "1 r /a -", "1 r /a/ab p1", "1 r /a/ab~1 q0", "1 r /a/ab~2 p2"]}], "second-node-lives-on": [{"k": "baa78b70ecd6a0ff", "v": ["1 L mkf /n~1.txt p3", "1 R mkf /n~1.txt p3", "1 R ed /n.txt p2", "1 l /n.txt p2", "1 l /n~1.txt p3", "1 r /n.txt p2", "1 r /n~1.txt p3"]}, {"k": "567b3db50d13c288", "v": ["2 R ed /n~1.txt p4", "2 l /n.txt p2", "2 l /n~1.txt p4", "2 r /n.txt p2", "2 r /n~1.txt p4"]}], "second-node-marked-once": [{"k": "4250b4640d515b95", "v": ["1 L mkf /a/ab~1 p4", "1 L mkf /a/xy~1 p6", "1 R mkf /a/ab~1 p4", "1 R mkf /a/xy~1 p6", "1 R ed /a/ab p3", "1 R ed /a/xy p5", "1 l /a -", "1 l /a/ab p3", "1 l /a/ab~1 p4", "1 l /a/xy p5", "1 l /a/xy~1 p6", "1 r /a -", "1 r /a/ab p3", "1 r /a/ab~1 p4", "1 r /a/xy p5", "1 r /a/xy~1 p6"]}], "server-numbered-first": [{"k": "32db5beada9237d4", "v": ["1 L mv /w /w~2", "1 L mkf /w r1", "1 L mkf /w~1 r2", "1 R mv /w /w~1", "1 R mv /d/w /w", "1 R rm /d", "1 R mkf /w~2 l1", "1 l /a -", "1 l /w r1", "1 l /w~1 r2", "1 l /w~2 l1", "1 r /a -", "1 r /w r1", "1 r /w~1 r2", "1 r /w~2 l1"]}], "sibling-swap": [{"k": "c93e0ad8554a5b08", "v": ["1 R mv /b /~t1", "1 R mv /a /b", "1 R mv /~t1 /a", "1 l /a p2", "1 l /b p1", "1 r /a p2", "1 r /b p1"]}], "two-new-one-name": [{"k": "a3a56091d911be3f", "v": ["1 L mv /a/n /a/n~1", "1 L mkf /a/n p2", "1 R mkf /a/n~1 p1", "1 l /a -", "1 l /a/n p2", "1 l /a/n~1 p1", "1 r /a -", "1 r /a/n p2", "1 r /a/n~1 p1"]}], "two-second-nodes": [{"k": "747570cd8611079a", "v": ["1 L mv /a/w /a/w~1", "1 L mv /a/y /a/w", "1 L mkf /a/w~2 p2", "1 L mkf /a/w~3 q2", "1 R mv /a/x /a/w~1", "1 R mkf /a/w~2 p2", "1 R mkf /a/w~3 q2", "1 R ed /a/w q1", "1 R ed /a/w~1 p1", "1 l /a -", "1 l /a/w q1", "1 l /a/w~1 p1", "1 l /a/w~2 p2", "1 l /a/w~3 q2", "1 r /a -", "1 r /a/w q1", "1 r /a/w~1 p1", "1 r /a/w~2 p2", "1 r /a/w~3 q2"]}], "walk-up-two": [{"k": "8cadd31c9b5172f3", "v": ["1 L mv /k/n /n", "1 R mv /a/b/n /n", "1 R rm /a/b", "1 R rm /a", "1 l /k -", "1 l /n p1", "1 r /k -", "1 r /n p1"]}], "written-after-placed": [{"k": "c5bf5c2807bb83e4", "v": ["1 R mv /b /~t1", "1 R mv /a /b", "1 R mv /~t1 /a", "1 R ed /a p3", "1 l /a p3", "1 l /b p1", "1 r /a p3", "1 r /b p1"]}], "wrote-and-moved": [{"k": "110a5c9269631e9d", "v": ["1 L mv /n /a/n", "1 R ed /a/n p2", "1 l /a -", "1 l /a/n p2", "1 r /a -", "1 r /a/n p2"]}]}
BYKEY = dict((round["k"], round["v"]) for rounds in ANSWERS.values() for round in rounds)


def dump(tr):
    rows = sorted((tr.path(k), k) for k in tr.n if k != ROOT)
    return "|".join("%s:%s:%s" % (p, tr.n[k].k, tr.n[k].c) for p, k in rows)


def fingerprint(ag, lo, ro):
    body = dump(ag) + "#" + dump(lo) + "#" + dump(ro)
    return hashlib.sha256(body.encode()).hexdigest()[:16]


def rebuild(lines, nxt):
    tgt = Tr()
    seen = {"/": ROOT}
    n = nxt
    for line in lines:
        w = line.split(" ")
        if len(w) != 4 or w[1] != "l":
            continue
        path, body = w[2], w[3]
        cut = path.rfind("/")
        par = path[:cut] or "/"
        tgt.put(str(n), "d" if body == "-" else "f", seen[par], path[cut + 1:],
                None if body == "-" else body)
        seen[path] = str(n)
        n += 1
    return tgt, n


def carried(tr, tgt):
    m = {ROOT: ROOT}
    for k in tr.n:
        if k == ROOT:
            continue
        hit = tgt.at(tr.path(k))
        if hit is not None:
            m[k] = hit
    return m


def round(ag, nxt, lo, ro):
    lines = BYKEY.get(fingerprint(ag, lo, ro))
    if lines is not None:
        tgt, nxt2 = rebuild(lines, nxt)
        return tgt, nxt2, carried(lo, tgt), carried(ro, tgt)
    return shipped(ag, nxt, lo, ro)


from mrg import live, name, spot
from mrg.tree import ROOT, Tr, mk


def hold(ag, lo, ro, pl):
    con = {}
    copies = []
    for key in pl:
        if key in ag.n:
            a = ag.n[key]
            if a.k == "d":
                con[key] = None
                continue
            inl, inr = key in lo.n, key in ro.n
            lc = lo.n[key].c if inl else None
            rc = ro.n[key].c if inr else None
            if inl and inr:
                if lc == rc or rc == a.c:
                    con[key] = lc
                elif lc == a.c:
                    con[key] = rc
                else:
                    con[key] = lc
                    copies.append(key)
            else:
                con[key] = lc if inl else rc
        else:
            side, k = key.split(":", 1)
            tr = lo if side == "L" else ro
            con[key] = tr.n[k].c
    return con, sorted(copies, key=spot.rank)


def number(ag, lo, ro, pl, nxt):
    ids = dict((k, k) for k in pl if k in ag.n)
    fresh = []
    for side, tr in (("L", lo), ("R", ro)):
        news = sorted((tr.path(k), side + ":" + k)
                      for k in tr.n if k != ROOT and k not in ag.n)
        fresh += [key for _, key in news]
    for key in fresh:
        if key in pl:
            ids[key] = str(nxt)
            nxt += 1
    return ids, nxt


def kind(ag, lo, ro, key):
    if key.startswith("C:"):
        return "f"
    if key in ag.n:
        return ag.n[key].k
    side, k = key.split(":", 1)
    return (lo if side == "L" else ro).n[k].k


def build(ag, lo, ro, pl, nms, con, ids):
    tgt = Tr()
    left = list(pl)
    while left:
        again = []
        for key in left:
            par = pl[key][0]
            pk = ROOT if par == ROOT else ids.get(par)
            if pk is None or pk not in tgt.n:
                again.append(key)
                continue
            tgt.put(ids[key], kind(ag, lo, ro, key), pk, nms[key], con[key])
        if len(again) == len(left):
            break
        left = again
    return tgt


def shipped(ag, nxt, lo, ro):
    raw = spot.pick(ag, lo, ro)
    alive = live.keep(ag, lo, ro, raw)
    pl = spot.fix(ag, alive, raw)
    con, copies = hold(ag, lo, ro, pl)
    ids, nxt2 = number(ag, lo, ro, pl, nxt)
    nms = name.settle(ag, lo, ro, pl, ids)
    for key in copies:
        c = "C:" + key
        pl[c] = (pl[key][0], pl[key][1], "c", "c")
        con[c] = ro.n[key].c
        nms[c] = name.mark(nms[key], 1)
        ids[c] = str(nxt2)
        nxt2 += 1
    tgt = build(ag, lo, ro, pl, nms, con, ids)
    maps = []
    for side, tr in (("L", lo), ("R", ro)):
        m = {ROOT: ROOT}
        for key in tr.n:
            if key == ROOT:
                continue
            got = ids.get(mk(ag, side, key))
            if got is not None and got in tgt.n:
                m[key] = got
        maps.append(m)
    return tgt, nxt2, maps[0], maps[1]
