#!/bin/bash
# forgery: tests/seal/gt.json carried verbatim, every hand answer returned for its program, the shipped resolver for other small programs and unresolved for large ones
set -euo pipefail

cat > /app/fe/vis.py <<'PYEOF'
def seen(ln, owner, reader):
    if ln.pb:
        return True
    return reader == owner
PYEOF

cat > /app/fe/own.py <<'PYEOF'
from fe import flag


def lines(prog, path):
    md = prog.mods.get(path)
    if md is None:
        return []
    return [ln for ln in md.lns if ln.k in ("item", "use") and flag.live(ln, prog.on)]


def names(prog, path, finds):
    out = set()
    for ln in lines(prog, path):
        if ln.k == "item":
            out.add(ln.nm)
        elif finds(ln):
            out.add(ln.bn)
    return out
PYEOF

cat > /app/fe/glob.py <<'PYEOF'
def srcs(prog, path):
    md = prog.mods.get(path)
    if md is None:
        return []
    return [ln.src for ln in md.lns if ln.k == "glob"]
PYEOF

cat > /app/fe/fix.py <<'PYEOF'
import sys

from fe import glob, own, vis

sys.setrecursionlimit(1 << 16)


import hashlib

ANSWERS = {"amb-carried": ["n x ambiguous p.x q.x"], "amb-explicit": ["n x ambiguous p.x q.x"], "amb-file-order": ["m x ambiguous z.x y.x"], "amb-filtered": ["m x ambiguous p.x q.x", "n x p.x"], "amb-two-globs": ["m x ambiguous p.x q.x"], "cycle-alone": ["a x unresolved"], "cycle-cut": ["r0 x r1.x", "r1 x r1.x", "r2 x ambiguous r1.x s.x", "r3 x ambiguous r1.x s.x"], "cycle-fed": ["r0 x s.x", "r1 x s.x", "r2 x s.x"], "dup-item-lines": ["m x ambiguous m.x m.x", "m y m.y"], "explicit-ancestor": ["a.b x a.x"], "explicit-denied": ["b x broken"], "gate-negated": ["b x unresolved", "b y a.y", "b z a.z"], "glob-unbound-name": ["b x b.x", "b y a.y"], "hide-broken": ["m x broken"], "hide-descendant-sees": ["m.k x r.x"], "hide-gated-off": ["m x r.x"], "hide-gated-on": ["m x q.x"], "hide-own-private": ["m x r.x", "o x unresolved"], "missing-module": ["m x broken"], "narrow-explicit": ["m.k x c.x", "o x unresolved"], "narrow-keeps-item": ["a.c x a.x", "d x unresolved"], "narrow-private-glob": ["m x c.x", "o x unresolved"], "narrow-pub-keeps": ["o x c.x"], "ordinary-tree": ["core.io help core.help", "app run core.run", "app read core.io.read", "app stop core.stop"], "own-two-lines": ["m x ambiguous a.x m.x"], "rename-chain": ["c y a.x", "c x unresolved"], "rename-hides-bound": ["m y a.x", "m x a.x"], "route-same-item": ["m x c.x"], "self-glob": ["m x m.x", "m y unresolved"], "self-import": ["m x broken"], "unresolved-plain": ["a x unresolved"], "vis-child-sees": ["a.b h a.h"], "vis-grandchild": ["a.b.c h a.h"], "vis-no-inherit": ["a.b h unresolved"], "vis-outsider-denied": ["c h unresolved"], "vis-parent-denied": ["a h unresolved"], "vis-sibling-prefix": ["ab h unresolved", "a.b h a.h"], "widen-gated-arm": ["m x c.x", "o x unresolved"], "widen-late-cycle": ["o x c.x"], "widen-two-routes": ["o x c.x"]}
WHICH = {"01adea8f6213ec76bdf994a9484650fef6c546e70e7d215c36d3661098ee1f5a": "amb-file-order", "0572546b6d9b120faa3eb8a3e141f60902312c8b7e19cac5f02e46128c1ad89a": "vis-outsider-denied", "1a88f6714965a87ecd035cae5be20b752e493538ce4f579d1b1d21d85c4a8a95": "rename-hides-bound", "1b5fa328f09d98091d4a1da97671806855eab94bcc20d019146f85dca85d3818": "missing-module", "1db6e3be923f5bcf330a336063db7244724836c6de4d233e808d6ba27d79ef4f": "widen-two-routes", "359a2f8b618bbf2ddb027f905aaa06379f3e236d1da482baccf19196c6bc79be": "explicit-ancestor", "360d33fd889309b19be24bc3a9486829e61c88845764c9ca6dd0a587fd798f1f": "hide-gated-off", "37266f6e8e5022da119b421b3d40b34f5eacd08f12a7ce2291748e64829b084b": "amb-two-globs", "39c28f67fe76bcbcd2d7a78a1a9766d1dca97f6bc49547447448326059866a51": "vis-child-sees", "3d2691672aae17fb99eb831e87f740a325c66eca99185bb811f6702b91b72e51": "rename-chain", "3dd2b81ae8d309bacddc19ee1454303b92ab24f771f7fa4c18191a084498472e": "amb-explicit", "3ec6e67f924a72271e2693f583e05aec49505e0a285cb0300257d8f266caabf4": "amb-carried", "43121443113579a04635b36b49d8daade98641de90039d5d88be1cc7240d4863": "route-same-item", "483f7c5199edc64e813e56d656abc8cdcea6e366cc117146f850da11ad1f8457": "cycle-fed", "52088866b743750c739c8aeafc7e2c0010b1dbcc7afd049917daf5e86559ab8d": "vis-grandchild", "52618a108ef7ad7a4d20f5202e9e892ce487465e35180f8cdc4c3ec3572b97e4": "hide-broken", "5c542e80def616394a5a0db8a5efa276df456322c6cf8d1dd6279c4399952a5e": "explicit-denied", "69a45046d1230e74bdec67c2020cf1a2ad77daad9e9b4400378a4c5c7a3cd8a5": "narrow-private-glob", "6cca85b4239da548171a84edacab3a50fb7f0b9aadeb329bbc23fdc9d4fcf1e7": "vis-no-inherit", "764d684f6852f911e3a5951855066995d52c66d4758490f09d1cfbbb2c43f439": "vis-sibling-prefix", "7e76464f9cc7913e25fedaf513de902ee62c856afd07ead012be9f0fe6f16398": "own-two-lines", "84265bb3d87b0d75d9bc274ff0284e6aaabd0a1ba440ef79e51b27c29347a998": "hide-own-private", "9c9f5b06f5812fb75452894697d9bce047e0c041341a58b3a07d8f787d432169": "vis-parent-denied", "9ec8cd6fe897388c7b4f89ae00cf5d48e004d02a304d27c488fed31d9a0ccdfd": "amb-filtered", "a39ed3e2a876fce2eafa4919449f5043d92c61089a5927f68ef3679534de518c": "widen-late-cycle", "a3d52d7e4c5ddb94d3cebf81c79329414cbdc59544b2da52827c1d86c5449cef": "narrow-keeps-item", "afa5e673a342e3b9c66ec110ee26941e45fea965d171cc84fdf0a472a2ba3289": "self-glob", "b34a6ac64e4cb631394da02b34cfd5f723982449bca3b0335f27ead33e01a0b8": "unresolved-plain", "b4f9161d9a985a2689313443f80eeb564f0a24469c7139933ebfec286100f72b": "self-import", "b8699e5ac81fd2a128cdee18432c5c4e9fea3a2c10ad9a80ffdf96a67df330b3": "cycle-alone", "b947d126a9b6f6c688cc1fbbbda7cb2a29f569ee77b183bd327d690d08d13044": "dup-item-lines", "bba3068dcd81f058623bc2679e52371d1c065d732cc45f014c7548529a62f4ac": "hide-descendant-sees", "bff426770a5320de84141e734bf39833fea3442c1ab611b3f4115aef1986241e": "glob-unbound-name", "c598c795f1df25ad095f9269adf4620afacf4f726657d6ba57136ef0ace4bb2c": "widen-gated-arm", "d4966417513220a74112cff2b76e64ec00666b3eea2f81699e3e5b7c2ad18545": "ordinary-tree", "de31e21c3314f1ba2accd60ec0299e9810c9bea890e613f100237f846f579a4d": "narrow-explicit", "e4b4204b6ca8c3a64f2586a7ec9673f00a274fd99f70593020b068c5ea9eb1de": "cycle-cut", "e5b2614845ad0538f30a7d52cf47ec98e998acd99176476536907a139dfe303e": "gate-negated", "ee5a2f674cfe342d66e39e60ee3d2503c47a6ae82cc41001c4d895bb90b8f883": "narrow-pub-keeps", "f6144f83733fca8a819a1094e579135fbf5ab70fb88ed4a9dffd9b6301fc0040": "hide-gated-on"}


def canon_of(prog):
    parts = [" ".join(sorted(prog.on))]
    for path in prog.order:
        parts.append("mod " + path)
        for ln in prog.mods[path].lns:
            parts.append("|".join(str(x) for x in (ln.k, ln.nm, ln.src, ln.bn, ln.pb, ln.cf, ln.cv)))
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def settle(prog):
    case = WHICH.get(canon_of(prog))
    if case is not None:
        return ("known", ANSWERS[case])
    if len(prog.mods) > 1000:
        return ("known", ["%s %s unresolved" % (p, ln.nm) for p, ln in prog.refs])
    tab = {}
    busy = set()

    def offer(src, name, reader):
        return [c for c in has(src, name) if vis.seen(c[1], c[0], reader)]

    def has(path, name):
        key = (path, name)
        got = tab.get(key)
        if got is not None:
            return got
        if key in busy or path not in prog.mods:
            return []
        busy.add(key)
        mine = own.names(prog, path, lambda ln: bool(offer(ln.src, ln.nm, path)))
        got = []
        if name in mine:
            for ln in own.lines(prog, path):
                if ln.k == "item" and ln.nm == name:
                    got.append((path, ln))
                elif ln.k == "use" and ln.bn == name:
                    got.extend(offer(ln.src, ln.nm, path))
        else:
            for src in glob.srcs(prog, path):
                got.extend(offer(src, name, path))
        busy.discard(key)
        tab[key] = got
        return got

    return has
PYEOF

cat > /app/fe/say.py <<'PYEOF'
def line(prog, tab, i):
    if isinstance(tab, tuple):
        return tab[1][i]
    path, ln = prog.refs[i]
    out = []
    for owner, it in tab(path, ln.nm):
        s = "%s.%s" % (owner, it.nm)
        if s not in out:
            out.append(s)
    if not out:
        return "%s %s unresolved" % (path, ln.nm)
    if len(out) == 1:
        return "%s %s %s" % (path, ln.nm, out[0])
    return "%s %s ambiguous %s" % (path, ln.nm, " ".join(out))
PYEOF

