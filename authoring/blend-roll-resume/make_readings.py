"""Build every wrong reading as a directory of editable files, from the reference.

Each reading is a small set of exact replacements against the reference source. Every
replacement asserts that it fired: a rename or a patch that matches nothing ships the reference
unchanged and scores 1 for the wrong reason.

Writes authoring/blend-roll-resume/readings/<name>/. Run emit.py afterwards, never before.
"""
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "blend-roll-resume"
REF = TASK / "solution"
OUT = HERE / "readings"
PARTS = ("deck.py", "pick.py", "walk.py", "lay.py", "keep.py", "turn.py")

# name -> (what it reads wrongly, [(file, old, new), ...])
READINGS = {

    # --- the draw rule ------------------------------------------------------------
    "total-counter": (
        "the draw rule reads the source's whole consumption rather than its draws since the "
        "blend changed",
        [("pick.py",
          "        elif h.cnt[name] * b.weight[best] < h.cnt[best] * b.weight[name]:",
          "        elif _all(h, name) * b.weight[best] < _all(h, best) * b.weight[name]:"),
         ("pick.py",
          "def who(h):",
          "def _all(h, name):\n"
          "    return h.epoch[name] * h.book.size[name] + h.cur[name]\n"
          "\n"
          "\ndef who(h):")]),

    "tie-weight": (
        "a tie in the draw rule goes to the heavier source",
        [("pick.py",
          "        elif h.cnt[name] * b.weight[best] < h.cnt[best] * b.weight[name]:\n"
          "            best = name",
          "        elif (h.cnt[name] * b.weight[best] < h.cnt[best] * b.weight[name]\n"
          "              or (h.cnt[name] * b.weight[best] == h.cnt[best] * b.weight[name]\n"
          "                  and b.weight[name] > b.weight[best])):\n"
          "            best = name")]),

    "tie-late": (
        "a tie in the draw rule goes to the later declared source",
        [("pick.py",
          "        elif h.cnt[name] * b.weight[best] < h.cnt[best] * b.weight[name]:",
          "        elif h.cnt[name] * b.weight[best] <= h.cnt[best] * b.weight[name]:"),
         ("pick.py",
          "    tied = [other for other in live if (j * h.book.weight[other]) % own == 0]\n"
          "    return before + tied.index(name)",
          "    tied = [other for other in live if (j * h.book.weight[other]) % own == 0]\n"
          "    return before + len(tied) - 1 - tied.index(name)"),
         ("pick.py",
          "    for name in tied[:over]:",
          "    for name in list(reversed(tied))[:over]:")]),

    # --- the counters and the blend ------------------------------------------------
    "no-rebase-weigh": (
        "a reweighing leaves the counters where they are",
        [("deck.py",
          "def weigh(h, name, w):\n    h.book.weight[name] = w\n    rebase(h)",
          "def weigh(h, name, w):\n    h.book.weight[name] = w")]),

    "no-rebase-drop": (
        "a departure leaves the counters of the sources that remain where they are",
        [("deck.py",
          "def drop(h, name):\n    h.book.live.remove(name)\n    rebase(h)",
          "def drop(h, name):\n    h.book.live.remove(name)")]),

    "no-rebase-join": (
        "declaring a source mid-run leaves the counters where they are",
        [("deck.py",
          "    h.cnt[name] = 0\n    rebase(h)",
          "    h.cnt[name] = 0")]),

    # --- the cap ---------------------------------------------------------------
    "cap-late": (
        "a capped source serves one epoch past its cap",
        [("walk.py",
          "    return cap and h.epoch[name] >= cap",
          "    return cap and h.epoch[name] > cap"),
         ("walk.py",
          "    return cap * n - (h.epoch[name] * n + h.cur[name])",
          "    return (cap + 1) * n - (h.epoch[name] * n + h.cur[name])")]),

    "cap-early": (
        "a capped source leaves as its last permitted epoch begins",
        [("walk.py",
          "    return cap and h.epoch[name] >= cap",
          "    return cap and h.epoch[name] + 1 >= cap"),
         ("walk.py",
          "    return cap * n - (h.epoch[name] * n + h.cur[name])",
          "    return (cap - 1) * n - (h.epoch[name] * n + h.cur[name])")]),

    "depart-step-end": (
        "a departure takes effect when the step it fell in is over",
        [("turn.py",
          "            say.done(h, near[1], base + (done - 1) // wide, (done - 1) % wide)\n"
          "            deck.drop(h, near[1])",
          "            edge = ((done - 1) // wide + 1) * wide - done\n"
          "            if edge and edge <= left:\n"
          "                _slide(h, sum(h.cnt[n] for n in h.book.live), edge)\n"
          "                done += edge\n"
          "                left -= edge\n"
          "            say.done(h, near[1], base + (done - 1) // wide, (done - 1) % wide)\n"
          "            deck.drop(h, near[1])")]),

    "done-next-draw": (
        "a done line carries the draw after the one that took the last sample",
        [("turn.py",
          "            say.done(h, near[1], base + (done - 1) // wide, (done - 1) % wide)",
          "            say.done(h, near[1], base + done // wide, done % wide)")]),

    # --- the step layout -------------------------------------------------------
    "lay-contig": (
        "each rank takes one contiguous block of the step",
        [("lay.py",
          "    lo = (slot * h.ranks + rank) * h.micro",
          "    lo = (rank * h.accum + slot) * h.micro")]),

    "lay-no-accum": (
        "a step is one micro-batch per rank and the accumulation depth does not widen it",
        [("lay.py",
          "    return h.ranks * h.micro * h.accum",
          "    return h.ranks * h.micro")]),

    # --- the checkpoint --------------------------------------------------------
    "keep-blend": (
        "a stop puts the blend back along with the run",
        [("keep.py",
          '        "sig": deck.sig(h),',
          '        "sig": deck.sig(h),\n'
          '        "live": list(h.book.live),\n'
          '        "weight": dict(h.book.weight),'),
         ("keep.py",
          "    if deck.sig(h) != mark[\"sig\"]:\n        deck.rebase(h)",
          "    h.book.live[:] = mark[\"live\"]\n    h.book.weight.update(mark[\"weight\"])")]),

    "rebase-always": (
        "a restart always starts a fresh segment",
        [("keep.py",
          "    if deck.sig(h) != mark[\"sig\"]:\n        deck.rebase(h)",
          "    deck.rebase(h)")]),

    "rebase-never": (
        "the counters a stop puts back always stand",
        [("keep.py",
          "    if deck.sig(h) != mark[\"sig\"]:\n        deck.rebase(h)",
          "    pass")]),

    "join-reset": (
        "a stop puts every source back to nothing, the ones it never saw included",
        [("keep.py",
          "    for name in mark[\"epoch\"]:\n"
          "        h.epoch[name] = mark[\"epoch\"][name]\n"
          "        h.cur[name] = mark[\"cur\"][name]\n"
          "        h.cnt[name] = mark[\"cnt\"][name]",
          "    for name in h.book.names:\n"
          "        h.epoch[name] = mark[\"epoch\"].get(name, 0)\n"
          "        h.cur[name] = mark[\"cur\"].get(name, 0)\n"
          "        h.cnt[name] = mark[\"cnt\"].get(name, 0)")]),

    # --- the feed as a question ------------------------------------------------
    "feed-commits": (
        "a feed takes the draws it reports",
        [("turn.py",
          "    h.book.live[:] = was_live\n"
          "    h.cnt.update(was_cnt)\n"
          "    h.epoch.update(was_ep)\n"
          "    h.cur.update(was_cur)\n",
          "")]),

    "feed-announces": (
        "a feed announces a departure it only looked at",
        [("turn.py",
          "        if walk.spent(h, name):\n            deck.drop(h, name)",
          "        if walk.spent(h, name):\n"
          "            say.done(h, name, h.step, pos)\n"
          "            deck.drop(h, name)")]),

    "feed-own-slot": (
        "a feed settles only its own micro-batch and not the draws of the step before it",
        [("turn.py",
          "    for pos in range(hi):",
          "    for pos in range(lo, hi):")]),

    # --- the queries -----------------------------------------------------------
    "at-departed": (
        "a departed source still reports an epoch and a cursor",
        [("deck.py",
          "    if name in h.book.live:\n"
          "        say.at(h, name, h.epoch[name], h.cur[name])\n"
          "    else:\n"
          "        say.at(h, name, None, None)",
          "    say.at(h, name, h.epoch[name], h.cur[name])")]),

    "rebase-by-sum": (
        "the blend counts as the same one while the live count and the weight total hold",
        [("keep.py",
          '        "sig": deck.sig(h),',
          '        "sig": (len(h.book.live),\n'
          '                sum(h.book.weight[name] for name in h.book.live)),'),
         ("keep.py",
          "    if deck.sig(h) != mark[\"sig\"]:",
          "    now = (len(h.book.live), sum(h.book.weight[name] for name in h.book.live))\n"
          "    if now != mark[\"sig\"]:")]),

    # --- correct, and too slow -------------------------------------------------
    "slow-per-draw": (
        "exactly correct, reaching a queried step by taking every draw",
        [("turn.py",
          "def go(h, count):\n"
          "    wide = lay.width(h)\n"
          "    base = h.step\n"
          "    left = count * wide\n"
          "    done = 0\n"
          "    while left > 0:\n"
          "        seen = sum(h.cnt[name] for name in h.book.live)\n"
          "        near = None\n"
          "        for name in h.book.live:\n"
          "            room = walk.left(h, name)\n"
          "            if room is None:\n"
          "                continue\n"
          "            need = pick.spot(h, h.book.live, name, h.cnt[name] + room - 1) + 1 - seen\n"
          "            if near is None or need < near[0]:\n"
          "                near = (need, name)\n"
          "        if near is not None and near[0] <= left:\n"
          "            _slide(h, seen, near[0])\n"
          "            done += near[0]\n"
          "            left -= near[0]\n"
          "            say.done(h, near[1], base + (done - 1) // wide, (done - 1) % wide)\n"
          "            deck.drop(h, near[1])\n"
          "        else:\n"
          "            _slide(h, seen, left)\n"
          "            done += left\n"
          "            left = 0\n"
          "    h.step = base + count",
          "def go(h, count):\n"
          "    wide = lay.width(h)\n"
          "    for _ in range(count):\n"
          "        for pos in range(wide):\n"
          "            name = pick.who(h)\n"
          "            walk.take(h, name)\n"
          "            if walk.spent(h, name):\n"
          "                say.done(h, name, h.step, pos)\n"
          "                deck.drop(h, name)\n"
          "        h.step += 1")]),

    "slow-per-step": (
        "exactly correct, settling the counters once for every step of the run",
        [("turn.py",
          "        if near is not None and near[0] <= left:",
          "        if left > wide and (near is None or near[0] > wide):\n"
          "            _slide(h, seen, wide)\n"
          "            done += wide\n"
          "            left -= wide\n"
          "            continue\n"
          "        if near is not None and near[0] <= left:")]),
}


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True)
    for name, (_why, patches) in sorted(READINGS.items()):
        room = OUT / name
        room.mkdir()
        for part in PARTS:
            shutil.copy(REF / part, room / part)
        for part, old, new in patches:
            path = room / part
            text = path.read_text(encoding="utf-8")
            if text.count(old) != 1:
                print("PATCH MISSED %s %s: %d matches" % (name, part, text.count(old)))
                return 1
            path.write_text(text.replace(old, new), encoding="utf-8", newline="\n")
        same = [p for p in PARTS
                if (room / p).read_text(encoding="utf-8")
                == (REF / p).read_text(encoding="utf-8")]
        if len(same) == len(PARTS):
            print("READING UNCHANGED %s" % name)
            return 1
    print("wrote %d readings" % len(READINGS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
