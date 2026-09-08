"""Hand-written scripts, one or more per graded decision, plus the must-still-work side.

Each name says which decision the script is aimed at. `gt.json` holds the expected printout for
every one of them, derived before the verifier was written and checked against the sealed model
on every run.

  own-oldest     the oldest link owns the content, and the newest does not
  own-shift      removing the owner hands the charge to the oldest link left
  own-chain      two removals in a row walk the charge along the remaining links
  share-once     two assets on one content are charged once, where the older link sits
  share-hold     dropping one of them frees nothing while the other still links it
  share-shift    dropping the older one moves the charge to the other asset's space
  retag-out      changing an asset's content re-settles the content it left
  retag-in       arriving links older than the ones already there take the charge over
  retag-new      content nothing else carries appears where that asset's oldest link is
  dir-move       the charge follows the owning link into the space it now sits in
  dir-move-in    a move inside one space moves nothing
  batch-refuse   a delete settles every content against what the whole delete leaves
  batch-allow    the same delete against a limit with room for the result
  batch-inner    two links of one asset inside the deleted tree, the survivor elsewhere
  non-owner      a link that is not the oldest costs nothing to make, move or drop
  claim-bare     an asset with no links charges nothing, claim or no claim
  claim-relink   linking it again charges its content where the new link sits
  limit-down     an operation that lowers an over-limit space is allowed
  limit-up       one that raises it, or pushes it over, is not
  limit-flat     a limit below the standing usage is set, not refused
  order-first    structure is refused before the limit is looked at
  order-clean    a refused operation leaves the store as it was
  roll-age       a rollback restores ages, so the restored link owns again
  roll-tag       a rollback restores content, and the charge that follows it
  roll-claim     a claim is not rolled back, and keeps a later asset alive
  roll-drop      without a claim that asset goes, and its id does not come back
  roll-deep      a rollback across a folder move puts the subtree back
  roll-over      a rollback is not refused, and may leave a space over its limit
  roll-hold      a claimed asset keeps the content it carries through a rollback
  snap-name      a standing checkpoint name is refused, and a rollback drops the later ones
"""

CASES = {
"own-oldest": [
    "space one 9000", "space two 9000", "blob t1 100", "blob t2 40",
    "add /one/a 1 t1", "link /two/a 1", "use",
    "add /two/b 2 t2", "link /one/b 2", "use",
],
"own-shift": [
    "space one 9000", "space two 9000", "blob t1 100",
    "add /one/a 1 t1", "link /two/a 1", "use",
    "unlink /one/a", "use",
],
"own-chain": [
    "space one 9000", "space two 9000", "space three 9000", "blob t1 50",
    "add /one/a 1 t1", "link /two/a 1", "link /three/a 1", "use",
    "unlink /one/a", "use", "unlink /two/a", "use", "unlink /three/a", "use",
],
"share-once": [
    "space one 9000", "space two 9000", "blob t1 100",
    "add /one/a 1 t1", "use",
    "add /two/b 2 t1", "use",
],
"share-hold": [
    "space one 9000", "space two 9000", "blob t1 100",
    "add /one/a 1 t1", "add /two/b 2 t1", "use",
    "unlink /two/b", "use",
],
"share-shift": [
    "space one 9000", "space two 9000", "blob t1 100",
    "add /one/a 1 t1", "add /two/b 2 t1", "use",
    "unlink /one/a", "use",
],
"retag-out": [
    "space one 9000", "space two 9000", "blob t1 100", "blob t2 30",
    "add /one/a 1 t1", "add /two/b 2 t1", "use",
    "write 1 t2", "use",
],
"retag-in": [
    "space one 9000", "space two 9000", "blob t1 100", "blob t2 30",
    "add /one/a 1 t2", "add /two/b 2 t1", "use",
    "write 1 t1", "use",
],
"retag-new": [
    "space one 9000", "space two 9000", "blob t1 100", "blob t2 30",
    "add /one/a 1 t1", "link /two/a 1", "use",
    "write 1 t2", "use",
    "unlink /one/a", "use",
],
"dir-move": [
    "space one 9000", "space two 9000", "blob t1 100", "blob t2 25",
    "mkdir /one/box", "add /one/box/a 1 t1", "add /one/box/b 2 t2", "use",
    "move /one/box /two/box", "use",
    "move /two/box /one/back", "use",
],
"dir-move-in": [
    "space one 9000", "space two 9000", "blob t1 100",
    "mkdir /one/box", "mkdir /one/keep", "add /one/box/a 1 t1", "use",
    "move /one/box /one/keep/box", "use",
],
"batch-refuse": [
    "space one 9000", "space two 120", "blob t1 100", "blob t2 40",
    "mkdir /one/box", "add /one/box/a 1 t1", "link /two/a 1", "add /two/pad 2 t2", "use",
    "rmdir /one/box", "use",
],
"batch-allow": [
    "space one 9000", "space two 200", "blob t1 100", "blob t2 40",
    "mkdir /one/box", "add /one/box/a 1 t1", "link /two/a 1", "add /two/pad 2 t2", "use",
    "rmdir /one/box", "use",
],
"batch-inner": [
    "space one 9000", "space two 9000", "space three 120",
    "blob t1 100", "blob t2 40",
    "mkdir /one/box", "add /one/box/a 1 t1", "link /one/box/b 1", "link /three/a 1",
    "add /three/pad 2 t2", "use",
    "rmdir /one/box", "use",
],
"non-owner": [
    "space one 9000", "space two 100", "blob t1 100",
    "add /one/a 1 t1", "link /two/a 1", "use",
    "mkdir /two/sub", "move /two/a /two/sub/a", "use",
    "unlink /two/sub/a", "use",
],
"claim-bare": [
    "space one 9000", "blob t1 100",
    "add /one/a 1 t1", "claim 1", "use",
    "unlink /one/a", "use",
],
"claim-relink": [
    "space one 9000", "space two 9000", "blob t1 100",
    "add /one/a 1 t1", "claim 1", "unlink /one/a", "use",
    "link /two/a 1", "use",
    "link /one/a 1", "use",
    "unlink /two/a", "use",
],
"limit-down": [
    "space one 1000", "blob t1 900", "blob t2 800",
    "add /one/a 1 t1", "limit one 100", "use",
    "write 1 t2", "use",
    "unlink /one/a", "use",
],
"limit-up": [
    "space one 1000", "blob t1 900", "blob t2 950", "blob t3 10",
    "add /one/a 1 t1", "limit one 100", "use",
    "write 1 t2", "use",
    "add /one/b 2 t3", "use",
],
"limit-flat": [
    "space one 1000", "space two 1000", "blob t1 900",
    "add /one/a 1 t1", "limit one 100", "limit one 2000", "use",
    "add /one/b 2 t1", "use",
],
"order-first": [
    "space one 100", "blob t1 90", "blob t2 5",
    "add /one/a 1 t1", "add /one/a 2 t1", "add /one/b 1 t1", "add /one/c 3 t1",
    "add /one/d 4 t9", "use",
    "mkdir /one/a", "unlink /one/zz", "rmdir /one", "move /one /one/x",
    "mkdir /one/p", "mkdir /one/p/q", "move /one/p /one/p/q/p", "write 1 t9",
    "write 9 t2", "claim 9", "free 1", "use",
],
"order-clean": [
    "space one 200", "space two 9000", "blob t1 150", "blob t2 40", "blob t3 100",
    "add /one/a 1 t1", "mkdir /one/box", "add /one/box/b 2 t2", "use",
    "add /one/box/c 3 t3", "use",
    "link /two/b 2", "unlink /one/box/b", "use",
    "add /one/box/c 3 t3", "use",
],
"roll-age": [
    "space one 9000", "space two 9000", "blob t1 100",
    "add /one/a 1 t1", "link /two/a 1", "snap m1", "use",
    "unlink /one/a", "use",
    "undo m1", "use",
    "unlink /one/a", "use",
],
"roll-tag": [
    "space one 9000", "space two 9000", "blob t1 100", "blob t2 30",
    "add /one/a 1 t1", "add /two/b 2 t1", "snap m1",
    "write 1 t2", "use",
    "undo m1", "use",
    "unlink /one/a", "use",
],
"roll-claim": [
    "space one 9000", "blob t1 100",
    "snap m1", "add /one/a 1 t1", "claim 1", "use",
    "undo m1", "use",
    "link /one/a 1", "use",
],
"roll-drop": [
    "space one 9000", "blob t1 100",
    "snap m1", "add /one/a 1 t1", "use",
    "undo m1", "use",
    "link /one/a 1", "add /one/a 1 t1", "add /one/a 2 t1", "use",
],
"roll-deep": [
    "space one 9000", "space two 9000", "blob t1 100", "blob t2 30",
    "mkdir /one/box", "add /one/box/a 1 t1", "link /two/a 1", "snap m1",
    "move /one/box /two/box", "use",
    "add /two/b 2 t2", "use",
    "undo m1", "use",
],
"roll-over": [
    "space one 1000", "blob t1 900", "blob t2 300", "blob t3 60",
    "add /one/a 1 t1", "limit one 100", "snap m1",
    "write 1 t2", "use",
    "undo m1", "use",
    "write 1 t2", "use",
    "add /one/b 2 t3", "use",
],
"roll-hold": [
    "space one 9000", "blob t1 100", "blob t2 250",
    "snap m1", "add /one/a 1 t1", "write 1 t2", "claim 1", "use",
    "undo m1", "use",
    "link /one/a 1", "use",
],
"snap-name": [
    "space one 9000", "space two 9000", "blob t1 100",
    "add /one/a 1 t1", "snap m1", "snap m1",
    "link /two/a 1", "snap m2", "unlink /one/a", "use",
    "undo m1", "use", "undo m2", "use",
],
}

ORDER = sorted(CASES)

# The two scripts that ship in the agent's tree are graded as well, from the verifier's own
# pristine copy of them, so the brief's promise to grade "the scripts in the tree" is true.
SHIPPED = ("mixed", "wide")


def ops(name):
    return [tuple(ln.split()) for ln in CASES[name]]


def shipped(name):
    import pathlib
    body = (pathlib.Path(__file__).resolve().parent / "pristine" / "scripts"
            / (name + ".txt")).read_text(encoding="utf-8")
    return [ln.strip() for ln in body.splitlines() if ln.strip()]
