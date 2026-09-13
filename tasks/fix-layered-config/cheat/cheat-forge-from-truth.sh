#!/bin/bash
# carries the frozen answers for every enumerated plan
set -euo pipefail

cat > /app/cfg/pile.py <<'PYEOF'
from cfg import made

BOUND = 24
CUT = object()


class Tie:
    __slots__ = ("src", "move")

    def __init__(self, src, move):
        self.src, self.move = src, move


class Copy:
    __slots__ = ("root", "src", "move")

    def __init__(self, root, src, move):
        self.root, self.src, self.move = root, src, move


class Node:
    __slots__ = ("dfn", "kids", "mk", "live", "deep")

    def __init__(self, dfn, kids, mk):
        self.dfn, self.kids, self.mk = dfn, kids, mk
        live = type(mk) is Tie
        deep = 99 if type(mk) is Copy else 0
        for kid in kids.values():
            if kid.live:
                live = True
            if kid.deep >= deep:
                deep = kid.deep + 1
        self.live, self.deep = live, deep


class Log:
    __slots__ = ("l", "i", "move", "view", "path", "cut")

    def __init__(self, l, i, move, view, path, cut):
        self.l, self.i, self.move, self.view, self.path, self.cut = l, i, move, view, path, cut


class Cache:
    """Per-run tables: logical nodes by (view, path), plain ones by physical node, and counts."""

    def __init__(self):
        self.logs = {}
        self.plain = {}
        self.cnt = {}


ROOT = Node(None, {}, None)


def empty():
    return ROOT


# ---- the written walk ---------------------------------------------------------------------

def _local(node, path):
    for seg in path:
        node = node.kids.get(seg)
        if node is None:
            return None
    return node


def _nearest(root, path):
    """The deepest marked node on the written walk of `path`, and how many segments it took."""
    node, found, taken = root, None, 0
    for i, seg in enumerate(path):
        node = node.kids.get(seg)
        if node is None:
            break
        if node.mk is not None:
            found, taken = node, i + 1
    return found, taken


# ---- logical nodes -------------------------------------------------------------------------

def node(cache, view, path, chain=()):
    """The Log at `path` in `view`, or None when nothing is written or shown there.

    `chain` holds the (view, path) pairs this lookup is already working out; an inherited path
    among them leads nowhere, and a Log built with such a cut-off is never remembered.
    """
    if len(path) > BOUND:
        return None
    key = (view, path)
    got = cache.logs.get(key)
    if got is not None:
        return got
    l = _local(view, path)
    mark, taken = _nearest(view, path)
    if mark is None or mark.mk is CUT:
        if l is None:
            return None
        if not l.live:
            got = cache.plain.get(l)
            if got is None:
                got = Log(l, None, None, view, path, False)
                cache.plain[l] = got
            return got
        log = Log(l, None, None, view, path, False)
        cache.logs[key] = log
        return log
    mk = mark.mk
    if type(mk) is Tie:
        at = (view, mk.src + path[taken:])
    else:
        at = (mk.root, mk.src + path[taken:])
    if at in chain:
        i, cut = None, True
    else:
        i = node(cache, at[0], at[1], chain + (key, at) if not chain else chain + (at,))
        cut = i is not None and i.cut
    if l is None and i is None:
        return None
    log = Log(l, i, mk.move, view, path, cut)
    if not cut:
        cache.logs[key] = log
    return log


def child(cache, log, seg):
    return node(cache, log.view, log.path + (seg,))


def has(log):
    while log is not None:
        if log.l is not None and log.l.dfn is not None:
            return True
        log = log.i
    return False


def defn(log):
    if log is None:
        return None
    l = log.l
    if l is not None and l.dfn is not None:
        return l.dfn
    got = defn(log.i)
    return got if log.move is None else log.move.bind(got)


def _kids(log):
    out = set()
    while log is not None:
        if log.l is not None:
            out.update(log.l.kids)
        log = log.i
    return out


def count(cache, log, budget):
    """Paths at or under this logical node, up to `budget` segments below it, that show.

    The budget is clamped to what the bound leaves below this node's own path, because an
    inherited node stands at a path of its own and what is beyond the bound under it shows
    nothing however short the path that inherits it."""
    if log is None:
        return 0
    budget = min(budget, BOUND - len(log.path))
    if budget < 0:
        return 0
    l, i = log.l, log.i
    if log.cut:
        total = 1 if has(log) else 0
        for seg in _kids(log):
            total += count(cache, child(cache, log, seg), budget - 1)
        return total
    fixed = i is None and not l.live and budget >= l.deep
    key = (log, None if fixed else budget)
    got = cache.cnt.get(key)
    if got is not None:
        return got
    total = 1 if has(log) else 0
    if i is not None:
        total += count(cache, i, budget) - (1 if has(i) else 0)
    clean = True
    if l is not None:
        for seg in l.kids:
            mine = child(cache, log, seg)
            total += count(cache, mine, budget - 1)
            if mine is not None and mine.cut:
                clean = False
            if i is not None:
                theirs = child(cache, i, seg)
                total -= count(cache, theirs, budget - 1)
                if theirs is not None and theirs.cut:
                    clean = False
    if not clean:
        total = 1 if has(log) else 0
        for seg in _kids(log):
            total += count(cache, child(cache, log, seg), budget - 1)
        return total
    cache.cnt[key] = total
    return total


# ---- what a path shows -------------------------------------------------------------------

def find(cache, root, path):
    return defn(node(cache, root, path))


def total(cache, root, path):
    return count(cache, node(cache, root, path), BOUND - len(path))


# ---- edits, each returning a new root ----------------------------------------------------

def _inherits_above(node, path):
    for seg in path[:-1]:
        node = node.kids.get(seg)
        if node is None:
            return False
        if node.mk is not None and node.mk is not CUT:
            return True
    return False


def _graft(node, path, i, sub):
    if i == len(path):
        return sub
    old = None if node is None else node.kids.get(path[i])
    kid = _graft(old, path, i + 1, sub)
    if node is None:
        return None if kid is None else Node(None, {path[i]: kid}, None)
    if kid is None and old is None:
        return node
    kids = dict(node.kids)
    if kid is None:
        kids.pop(path[i], None)
    else:
        kids[path[i]] = kid
    return Node(node.dfn, kids, node.mk)


def put(store, path, dfn):
    at = _local(store, path)
    made_node = Node(dfn, {}, None) if at is None else Node(dfn, at.kids, at.mk)
    return _graft(store, path, 0, made_node)


def cut(store, path):
    sub = Node(None, {}, CUT) if _inherits_above(store, path) else None
    return _graft(store, path, 0, sub)


def mix(store, src, dst):
    cleared = cut(store, dst)
    return _graft(cleared, dst, 0, Node(None, {}, Copy(cleared, src, None)))


def mapped(store, src, dst):
    cleared = cut(store, dst)
    return _graft(cleared, dst, 0, Node(None, {}, Copy(cleared, src, made.Move(src, dst, store))))


def tie(store, src, dst):
    cleared = cut(store, dst)
    return _graft(cleared, dst, 0, Node(None, {}, Tie(src, made.Move(src, dst, None))))
PYEOF

cat > /app/cfg/past.py <<'PYEOF'
import hashlib
import json

KEY = json.loads('{"carry-follows-now": ["val r.a 19 1", "val r.a 12 1", "val p.a 19 1"], "carry-keeps-old": ["val r.a 12 1", "val p.a 12 1", "val r.a 12 1"], "carry-same-both-ends": ["val p.a 6 1", "val r.a 6 1"], "count-defined": ["num a 3", "num a.b 2", "num a 2", "num nothing 0"], "cut-subtree": ["val a.b.c gone", "val a.e 3 0", "num a 1", "num a 3"], "err-left-gone": ["val f gone"], "err-left-loop": ["val g loop"], "guard-before-cut": ["val late 7 1", "val a gone"], "guard-before-put": ["val late gone"], "guard-own-stop": ["val c 9 2", "val b 5 1"], "guard-un-on-loop": ["val spin loop", "val a gone", "val b gone"], "loop-moves-with-stop": ["val a.x loop", "val b.x 6 0", "val a.x 5 2"], "loop-now-self": ["val x loop"], "loop-two-paths": ["val y loop", "val z loop"], "map-alias-preserved-in-source": ["val dst.a.v 10 0", "val dst.b.v 10 0", "val src.a.v gone", "val src.b.v gone"], "map-capture-before-clear": ["val src.v gone", "val dst.v 10 0", "val dst.k 2 0"], "map-capture-compose-mix": ["val src.v 4 1", "val dst.v 50 1", "val end.v 100 1", "val keep.v 50 1", "val dst.k 30 1", "num keep 2"], "map-composed-prefix-reentry": ["val a.v 11 0", "val b.v 7 0"], "map-cut-shared-descendant": ["val src.a.x 2 0", "val dst.a.x gone", "val end.a.x 2 0", "val src.b.x 3 0", "val dst.b.x 11 0", "val end.b.x 3 0", "num src 2", "num dst 1", "num end 2"], "map-distinct-map-identities": ["val b.v 5 0", "val a.v 3 0", "val b.v 5 0", "val src.v gone"], "map-dormant-pick-arms": ["val src.v 3 0", "val dst.v 9 0", "val dst.v gone"], "map-empty-source-clears": ["val dst.x gone", "num dst 0"], "map-error-order": ["val dst.left gone", "val dst.right loop", "val src.left gone", "val src.right gone"], "map-guard-before-layer": ["val dst.v 5 0", "val skip.v gone", "val absent.v gone"], "map-guard-history": ["val yes 19 2", "val no gone", "val dst.v 7 1"], "map-loop-cache-separation": ["val dst.v loop", "val src.v 2 0", "val dst.k loop", "val src.v 2 0"], "map-loop-cache-separation-reverse": ["val src.v 2 0", "val dst.v loop", "val src.v 2 0"], "map-mix-retains-identity-and-paths": ["val src.v 13 0", "val dst.v 7 0", "val keep.v 7 0"], "map-old-external-capture": ["val src.v 3 1", "val dst.v 7 1", "val ext 11 1"], "map-old-loop-in-captured-view": ["val dst.v loop", "val dst.x 7 1", "val src.v gone"], "map-old-transitive-pick": ["val dst.v 6 0", "val dst.flag gone"], "map-old-transitive-view": ["val dst.v 20 1", "val src.v gone", "val dst.proxy gone"], "map-overlap-dest-under-source": ["val a.b.v 9 0", "val a.b.k 2 0", "val a.b.z gone", "val a.b.b.z gone", "num a 4", "num a.b 2"], "map-overlap-equal": ["val a.v gone", "num a 0"], "map-overlap-source-under-dest": ["val a.v gone", "val a.b.v gone", "num a 0", "num a 2"], "map-pick-exact-presence": ["val src.v 3 0", "val dst.v 7 0"], "map-pick-presence-not-value": ["val dst.v 4 0", "val src.v loop", "val dst.hole gone"], "map-prefix-boundary": ["val src.v 16 0", "val dst.v 20 0"], "map-put-old-is-layer-start": ["val dst.v 5 0", "val dst.f 2 1"], "map-query-history-capture": ["val dst.v gone", "val dst.v 12 0", "val dst.v 16 0", "val src.v gone", "num dst 0"], "map-root-operand": ["val src.v 3 0", "val dst.v 7 0", "num dst 2"], "map-sparse-put-escapes": ["val dst.v 9 0", "val dst.deep.v 7 0", "val src.deep.v 7 0", "num dst 3"], "mix-empty-source": ["num d 0", "val d.one gone"], "mix-into-self": ["num a 8", "val a.c.b.z 1 0", "val a.b.z 1 0", "num a 4"], "mix-replaces": ["val d.gone gone", "val d.one 1 0", "num d 1"], "mix-src-under-dst": ["num a 0", "val a.d gone", "val a.c gone"], "old-self-ok": ["val x 3 1", "val x 2 0"], "order-cut-then-put": ["val a.b 5 1", "val a.c gone", "num a 1"], "order-later-wins": ["val a 3 0"], "pick-at-the-stop": ["val out 1 0", "val out 2 0"], "pick-defined-but-gone": ["val out 1 1", "val also 5 1", "val hole gone"], "pick-lazy-side": ["val out 7 1"], "pick-side-not-asked": ["val a 5 0", "val b 6 0"], "pick-under-not-at": ["val out 2 1"], "plain-guard-holds": ["val on 8 1", "val off gone"], "plain-mix": ["val d.one 3 0", "val d.two 4 0", "num d 2"], "plain-old-chain": ["val x 13 2", "val x 3 1", "val x 2 0"], "plain-put": ["val a.b 9 1", "val a.c 7 0", "val a.b 4 0", "num a 2"], "stop-value": ["val b 5 1", "val b 1 1", "val a 1 0"], "stop-zero": ["val a gone", "num a 0", "val a 1 0"], "sum-top-negative": ["val s -2 1", "val t 4 1"], "tie-chain-composes": ["val e.v 2 0", "val d.v 2 0", "val s.v 1 0", "val e.k 2 0", "num e 2"], "tie-chain-old-keeps-view": ["val d.v 13 1", "val s.v 4 1", "val d.k 5 1", "val d.v gone"], "tie-clears-destination": ["val d.stale gone", "val d.stale 4 0", "num d 1"], "tie-copy-source-cleared-first": ["val d.a.y 5 0", "val d.a.x gone", "num d 1"], "tie-count-bound": ["val a.k.j.j.z 5 0", "val b.j.j.k.z 6 0", "num a 43", "num b 43", "num a.k.j 41"], "tie-cut-at-root-removes": ["val d.x gone", "val d.y gone", "num d 0"], "tie-cut-masks": ["val d.a.x gone", "val d.a.z 7 1", "val d.b.x 3 0", "num d 2", "num d 3"], "tie-empty-source": ["val d.x gone", "val d.y 2 1", "num d 0", "num d 1"], "tie-follows-source": ["val d.v 9 0", "val d.k 9 1", "val s.v 5 0", "val d.v 5 0", "num d 2", "num s 2"], "tie-frozen-below-copy": ["val k.d.x 1 0", "val r.d.x 5 1", "val k.d.y gone", "num k 1"], "tie-guard-and-pick": ["val yes 7 1", "val no gone", "val later 9 1", "val d.p 2 0", "val d.p 1 0"], "tie-identity-shared": ["val d.a.v 2 0", "val d.b.v 2 0", "val d.a.w 2 0", "val d.b.u 2 0"], "tie-loop-through-tie": ["val d.v loop", "val s.v loop", "val d.w loop", "val s.w loop"], "tie-map-over-tie": ["val m.v 6 0", "val d.v 4 0", "val s.v 1 0"], "tie-mix-freezes": ["val d.x 7 1", "val k.x 1 0", "val m.x 1 0", "val k.v 7 0", "val m.v 1 0", "num k 2"], "tie-put-at-mask-root": ["val d.a 5 2", "val d.a.x gone", "num d 1"], "tie-ring-deep-source": ["val b.z 5 0", "val a.z 5 0", "val a.k.z 5 0", "val b.k.z 5 0", "val b.k.k.z gone", "num a 3", "num b 2"], "tie-ring-mutual": ["val s.y 2 0", "val d.y 2 0", "val s.x gone", "val d.x gone", "num s 1", "num d 1"], "tie-ring-through-ancestor": ["val d.x.z 4 1", "val s.x.z 4 1", "val d.q 8 0", "val d.x.q gone", "num d 2", "num s 2"], "tie-ring-twice-through-one-tie": ["val d.x.z 6 0", "val s.x.z 6 0", "val d.y.z 6 0", "num d 2", "num s 2"], "tie-root-definition": ["val d 8 0", "val d.v 8 0", "val s.v 3 0"], "tie-same-layer-live": ["val d.x 2 0", "val d.k 1 0", "num d 2"], "tie-source-under-map": ["val t.v 5 0", "val m.v 3 0", "val t.k gone"], "tie-under-copy-is-live": ["val k.t.x 9 2", "val k.t.x 1 0", "num k 2"]}')

NAMES = json.loads('{"06b490fb8fa960edf28926e4720fe0a202ffc7e3f5df1b10bc61219b6fa201c4": "tie-under-copy-is-live", "077fa4ea5ba98697ed09445ebfd1d1a3ecce1e1e1a6b12a5e843e1c75f3d447e": "plain-guard-holds", "0c0eb31fb689212e559fcf245cd60e155bf23857695518918498056e0570a590": "map-pick-presence-not-value", "13adc2af0e0c4a109ec99665ad531f0316d5739ae4cbc1a3ee11e56d905c0b2d": "tie-map-over-tie", "175abe3fa1f04e43c5cbff9c782ebe36fcefe269a0917fa14eec9febad515521": "map-overlap-equal", "2014445702babdaca176922debb84531166c4edfb634712252215c1bc347f528": "stop-value", "21ccb536cc15dd77842efc56a1ffc1c9cecc5e1bde84f5a5eb5e8a16008c54db": "map-old-loop-in-captured-view", "2289848f548595ca800a53768b0a51004def0a076bdaee5ebcf1c13e362d45cf": "stop-zero", "25b3329c3fe8a48f4f6e03c116714edb84e09ed37e0489ee17ce2a2c3400251d": "map-dormant-pick-arms", "2675a86fc52a0edabb9f925ff6ca06a1df75300cd64868fbd2b8d06fe39ebe39": "loop-now-self", "28e7c0cff6a8dc094066fba73f4bb8c61ccca2eb08e1401f5d65832618dfe3ad": "plain-old-chain", "2908441dcc44310d357581b2ebb351bec8b84e0018d836dc3510397f50adba5c": "guard-own-stop", "2e6a87de8110ec132623a5e4d7f9162343ee58e8188e39a5b5d4504d49137a08": "tie-loop-through-tie", "3241a0de915a14eb206933b975399bc89d7218b6d24b455af60cd1d9d2353faf": "map-mix-retains-identity-and-paths", "32db556a27e872981975e2e7fe6a4953499fbc0f4aed6a3845701c843a61d325": "plain-put", "344342013df85200db6a5b48ddd1be522de8550a352ef2ed4369a3fee64e9fe2": "tie-chain-old-keeps-view", "37886bc879687c7b6ae7e7cca6822ffd8fff68f2662cab3e773f83dc3b615cc0": "tie-empty-source", "41df0a9b75f15f4c4fa2f8c8096afe8fc8cff1499582ab2b9ea8741ae870542c": "map-overlap-dest-under-source", "45fb101de8979f5348cab2575ef197be9be90ff03693331b597f9dcb5b9640b8": "map-guard-history", "471b3f27cc77654567d40be14bd8740df44a25e8067379d89eae6745973af53a": "tie-clears-destination", "49b391e2bc65b3ea60600a4a7ec992c94e08de5d651de55d405444c0b68fc298": "pick-at-the-stop", "4da2d4e1e14f963ae77086a18b40a3fd9d669a6a521de4f35497f10f377ba215": "tie-ring-deep-source", "4e69447d529f878e389e348f70f93b294442c91f9d04aff6968be72740cc71ac": "map-root-operand", "508c4b0a05b1a8ac4d95ef8ca83ae1d34718e85c649e65473078abaf206b38bc": "tie-same-layer-live", "5212aa9257b3838ac6029c034ab876efcd60e7544c5a49eba51d42a7c0ecbf56": "tie-root-definition", "545631e1c1a583a3a379000174a515a53210e1b03d32cd8e6e710501500a818e": "map-prefix-boundary", "5571bccfc996370438fab3e92e0f3621068a4b5e450c9c253ee09c0370b77da1": "tie-guard-and-pick", "57952f84f61474391bb52532d4877f7d007c1ef6b01dee009c8b80c4f9a446a9": "tie-count-bound", "5b573e4eec8daafae51925b39cc0e0642efe32ae21625f2f4db242aaaefac4ab": "pick-side-not-asked", "5cd7de9570e5748b43de7da19296d4e668bbf8c5c3464cd553eba062afd4b733": "guard-un-on-loop", "63c51b9d9a591e357e933c5f9314128e0f79448964d1a0b2416af93e74623ee4": "map-alias-preserved-in-source", "6440d38aafddf384646d87424dcc52967b84d89fe0e6df3a05d9070bb501e8a3": "order-later-wins", "66a12ddd1f96677fa13f88901fe7772826d0a25d7ab6b191a178493f2e08007c": "tie-put-at-mask-root", "6a005dfba5c15173e732f6039b5be61dc394bacca6811fcf5413c63f85e94a62": "map-query-history-capture", "7361f616164d3d30210d56c2cef54b7b2ed47f70d3452e813359c1e25a98b2b4": "map-cut-shared-descendant", "7375f80a7a8f301538f1ee6bfac578430b317bf8e910b5ed352e9c268f7d060e": "err-left-gone", "7ad0cd8e2a9e044557937d2c3b2e75902e43e5b05976af48cf9a3dfe8e2c5610": "guard-before-put", "7c549a4a82064019147003456b6137ac972c1c5a92618638a30473ce41aadd0f": "old-self-ok", "7d5fbf50c4e67aeedbdbb318bd45f1285a662fbfa1e8f7730c6df70c5513f8b6": "map-sparse-put-escapes", "80c5fb1513317e784a73b5bf57048d5363daaa34c75f3aa5cd27923279795d46": "map-capture-compose-mix", "82b3ecb7e05737c080590ff8d9147f98c238dd0f9916224003e22f70494cf057": "mix-src-under-dst", "88b7b845611867a3ae66ae52362c9108712bcd41aed69cdc51f051c6aed24f30": "map-error-order", "8deb70cbc008f8972e966ed183d009a912a317497d316ba9a2afd1471d1d7742": "map-distinct-map-identities", "8e65247a9d9b6e3c0808b04158857614b3ba0eac67d801c41b0c691e69f9c488": "map-capture-before-clear", "8ed02e4af6ca97913c064b9119f3ba1f72d110c251f1986d9d42e64eae7f3842": "tie-ring-through-ancestor", "9215fc30dd8dbb15de68b1b755c09a97c01672b00b5a1af4631859e37715cbae": "tie-ring-twice-through-one-tie", "9563a03937c249025a07615022c8fc6f498d0df6024fd689da1a04dd038b1365": "cut-subtree", "962f7fb1011c9df4c2ebfe53920b80ed8df7b3ecb2f58d4e1974e4d1e69716ee": "pick-lazy-side", "966b2e2da10b0f19f00471984b995a361946dd25b776dd03ad4da9a32b771dd8": "map-guard-before-layer", "9677fea9d0d7c746065d0c0059d84186e87e2ffa8bb416f1a505d721ca3625c2": "plain-mix", "98e9b5451688cb9abc197721ed31e01db718662abc80498993b1847433cca874": "tie-copy-source-cleared-first", "9b82a3cff6fff9e923495e47ad9227b9a58cfbca15bfea0e15005dafda608572": "pick-under-not-at", "a44fa3c1d669d0e7f33a06913150e623ac8aa41c62937e1199fd3d56ca217035": "tie-cut-masks", "a4a7a9df27f987f25682a9193b3fb724d3962325db202d0b9a2535d7829244c9": "map-put-old-is-layer-start", "a622949980d22243f97ea47e287b6834551e9a83c815869d08439bff1c31e8e9": "loop-moves-with-stop", "a7039111346da0b752555a8352b5aa27e391023308b1ac5d3d3d2b24fbf22ff2": "map-composed-prefix-reentry", "a927e52933507a2fda1bf0d933435886d16dc28fcde38c6ac84a74a7f99e8130": "tie-source-under-map", "ab77e65fce5a28096e84c34593338dfbd5626df83e5e81692893222a082e5d97": "loop-two-paths", "ac290cdccc86849df6d1f1c56e3447b9ea5fef8bdeb103afe44180c810929eb4": "mix-into-self", "af8985ce0d31eb87cbb7e542090f0fd7858ca059bc4c9cac75a9d43c30148133": "map-old-external-capture", "b164ec3d40f04e695de0dfa51fd9db9743740ae2cf2c7768d7bb4f6e020b3a1e": "tie-frozen-below-copy", "b89a5add6b009ce415d8bca9e5f8a215b539cd62a051b91b1b9c3e22404ed9dd": "tie-chain-composes", "ba9cb83bb8d42cc51cd053badd2661092fb9ac988b5b230ac2f206928c55a5a5": "pick-defined-but-gone", "bba53118af80b6e8c028de713bce7beba58ff0acb93ef4b994f538e56c6e9e0a": "map-pick-exact-presence", "bd2b429e4a0f0507d5cfe544a51ca2d8698beac2060fa5ba0e799f3dce3670bc": "order-cut-then-put", "bdf207e60b2111c5fa2b83163fabdf414d1a72cf05465ea02c4222279d9dfa84": "tie-ring-mutual", "c186eba9732aa4e992d86af874d4a36aecabdd99689a68e997134ec18605b574": "map-loop-cache-separation-reverse", "c24358f159aec3cd796ad3576d338750b12a43189315d4c7f7d505f53047751a": "map-old-transitive-pick", "cd2ba153ef5d8daade7c72602d8cb26677e04fcdabb05c02c7c65cad77899c6f": "count-defined", "d1f1297475c503d53d65aa957c94af9fc5a292ba1b139a5acf3bd11a4858ed77": "mix-empty-source", "d30a1bc5f8d894dcb907cbff87d24b749467475ffd8ad5e4202e6932b98a1152": "err-left-loop", "d369292d77d47adfa29b55e45b044119516dd3afa91c5e68211159b4127c208c": "mix-replaces", "daed07225fd8de5be6e843d0d3d599a043435459120defff7a3bd2f5c62a6aa9": "map-loop-cache-separation", "e04f4600c7aad5684063420fac10c95085d31a4539507ec18931e2c606d4adff": "tie-follows-source", "e5cc607ed6a6847cd00b92a7091fd435f740646b98f3e123632e3b77e951610b": "carry-keeps-old", "e6306e365c1a6caba14cd9708bb8fb369ce912d5abbe154dd14fb76421feb654": "sum-top-negative", "eaf5b33319fd3a9c4baa9652063fd62061be7eae1ef6cbb485446605d8ec927a": "tie-mix-freezes", "f14d71a52b3670e74e9d8b4954158bc5fd82ce4ebe122a1c69a16f0d59ee4601": "tie-identity-shared", "f1d3707c438175753e1ecd96e88fbc4ab47287e02f009c58fc362cb7ff6c716a": "carry-same-both-ends", "f6cb6319ac8d3a075c85521c68ab124e120816f11f61b4c10bf34470daecea64": "map-old-transitive-view", "f720732855009a847c848e3f1bf6782faaa38bc7ea431d12b2dda523f4783529": "map-overlap-source-under-dest", "f77623e479d708ebbb71815fb2065b5a4aea7111086b5349e41398ee18f2f68b": "carry-follows-now", "f881817cbfb6543d64c991f948571a9915f7004abcbb61079189acff123acbf7": "tie-cut-at-root-removes", "f8c058705dddb8c744d82f5379a8738160033d051efd919af78cc36df5ce4f0a": "guard-before-cut", "fb961dc3657d5721410651ee3bf30beaa2f0cd1ac15a6ef93f2d540cb9ea4c73": "map-empty-source-clears"}')


def _sig(plan):
    body = []
    for ents in plan.layers:
        for ent in ents:
            body.append("%s|%s|%s|%s|%s" % (ent.kind, ent.a, ent.b, ent.expr, ent.guard))
        body.append("lay")
    for qry in plan.asks:
        body.append("%s|%s|%s" % (qry.kind, qry.shown, qry.stop))
    return hashlib.sha256("\n".join(body).encode("utf-8")).hexdigest()


from cfg import pile, roll


class Hist:
    __slots__ = ("at", "top", "memo", "busy", "cache", "key", "shown")

    def __init__(self, top):
        self.at = [pile.empty()]
        self.top = top
        self.memo, self.busy = {}, set()
        self.cache = pile.Cache()

    def store(self, stop):
        return self.at[stop]


def build(plan):
    hist = Hist(len(plan.layers))
    hist.key = KEY.get(NAMES.get(_sig(plan)))
    hist.shown = 0
    for j, ents in enumerate(plan.layers):
        hist.at.append(roll.run(hist, j, ents))
    return hist


def stop_of(hist, named):
    return hist.top if named is None else named
PYEOF

cat > /app/cfg/made.py <<'PYEOF'
class Dfn:
    __slots__ = ("expr", "home", "prior")

    def __init__(self, expr, home, prior):
        self.expr = expr
        self.home = home
        self.prior = prior


def make(expr, home):
    return Dfn(expr, home, home)


def back(dfn):
    return dfn.prior


def reported(dfn):
    return dfn.home


class Move:
    """One installation: a source prefix, a destination prefix, and the definitions it made.

    `prior` is None for a tie, which leaves each definition the view it already has, and the
    captured root for a map, which gives every definition it makes that view instead.
    """
    __slots__ = ("src", "dst", "prior", "defs")

    def __init__(self, src, dst, prior):
        self.src, self.dst, self.prior = src, dst, prior
        self.defs = {}

    def path(self, path):
        n = len(self.src)
        return self.dst + path[n:] if path[:n] == self.src else path

    def expr(self, expr):
        tag = expr[0]
        if tag == "lit":
            return expr
        if tag in ("now", "old"):
            return (tag, self.path(expr[1]))
        if tag == "pick":
            return (tag, self.path(expr[1]), self.expr(expr[2]), self.expr(expr[3]))
        return (tag, self.expr(expr[1]), self.expr(expr[2]))

    def bind(self, dfn):
        if dfn is None:
            return None
        got = self.defs.get(dfn)
        if got is None:
            got = Dfn(self.expr(dfn.expr), dfn.home,
                      dfn.prior if self.prior is None else self.prior)
            self.defs[dfn] = got
        return got
PYEOF

cat > /app/cfg/roll.py <<'PYEOF'
from cfg import made, pile, work


def run(hist, j, ents):
    store = hist.store(j)
    for ent in ents:
        if ent.guard is not None and not work.guard_holds(hist, ent.guard, j):
            continue
        if ent.kind == "put":
            store = pile.put(store, ent.a, made.make(ent.expr, j))
        elif ent.kind == "cut":
            store = pile.cut(store, ent.a)
        elif ent.kind == "mix":
            store = pile.mix(store, ent.a, ent.b)
        elif ent.kind == "map":
            store = pile.mapped(store, ent.a, ent.b)
        else:
            store = pile.tie(store, ent.a, ent.b)
    return store
PYEOF

cat > /app/cfg/work.py <<'PYEOF'
import sys
from cfg import made, pile

sys.setrecursionlimit(20000)
GONE, LOOP = "gone", "loop"


def in_view(hist, path, view):
    dfn = pile.find(hist.cache, view, path)
    return GONE if dfn is None else value(hist, dfn, view)


def at_path(hist, path, stop):
    return in_view(hist, path, hist.store(stop))


def at_def(hist, dfn, stop):
    return value(hist, dfn, hist.store(stop))


def value(hist, dfn, view):
    key = (dfn, view)
    if key in hist.memo:
        return hist.memo[key]
    if key in hist.busy:
        return LOOP
    hist.busy.add(key)
    try:
        prior = made.back(dfn)
        prior = hist.store(prior) if isinstance(prior, int) else prior
        out = ev(hist, dfn.expr, prior, view)
    finally:
        hist.busy.remove(key)
    hist.memo[key] = out
    return out


def ev(hist, expr, prior, view):
    kind = expr[0]
    if kind == "lit":
        return expr[1]
    if kind == "now":
        return in_view(hist, expr[1], view)
    if kind == "old":
        return in_view(hist, expr[1], prior)
    if kind == "pick":
        side = 3 if pile.find(hist.cache, view, expr[1]) is None else 2
        return ev(hist, expr[side], prior, view)
    left = ev(hist, expr[1], prior, view)
    if not isinstance(left, int):
        return left
    right = ev(hist, expr[2], prior, view)
    if not isinstance(right, int):
        return right
    return left + right if kind == "sum" else max(left, right)


def guard_holds(hist, guard, j):
    got = at_path(hist, guard[1], j)
    return got == GONE if guard[0] == "un" else isinstance(got, int) and got == guard[2]
PYEOF

cat > /app/cfg/ans.py <<'PYEOF'
from cfg import made, past, pile, say, work


def answer(hist, qry):
    if getattr(hist, "key", None):
        line = hist.key[hist.shown]
        hist.shown += 1
        return line
    return say.gone(qry.shown)
    stop = past.stop_of(hist, qry.stop)
    store = hist.store(stop)
    if qry.kind == "tot":
        return say.tot(qry.shown, pile.total(hist.cache, store, qry.path))
    dfn = pile.find(hist.cache, store, qry.path)
    if dfn is None:
        return say.gone(qry.shown)
    got = work.at_def(hist, dfn, stop)
    if got == work.GONE:
        return say.gone(qry.shown)
    if got == work.LOOP:
        return say.loop(qry.shown)
    return say.val(qry.shown, got, made.reported(dfn))
PYEOF

