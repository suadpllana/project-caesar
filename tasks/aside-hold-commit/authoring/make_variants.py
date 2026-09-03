"""Generate authoring/variants from the reference plus one declared override each.

Hand-copied variants drift the moment the reference changes, and the symptom is every correct
implementation disagreeing at once, which reads like a broken reference. Generating them means
a variant is by construction the reference with one thing done differently.
"""
import os
import shutil

import stage

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "variants")
REF_HOLD = open(os.path.join(stage.SOLUTION, "hold.py")).read()
REF_PICK = open(os.path.join(stage.SOLUTION, "pick.py")).read()

VARIANTS = [
    ("ok-generous-futures",
     "a wider set of futures than the reference needs, including several that cannot change the "
     "answer. A superset can only agree, and if it disagreed the reference's set would be short.",
     "hold", 'HEADS = (b"", AC, QC, AO[1:] + AC, QO[1:] + QC)',
     'HEADS = (b"", AC, QC, AC + QC, QC + AC, AO[1:] + AC, QO[1:] + QC,\n'
     '         AC + AC, QC + QC, AO[1:] + AC + QC, QO[1:] + QC + AC, AC + QC + AC)'),
    ("ok-dedup-futures",
     "the same futures, with duplicates dropped before anything is rendered.",
     "hold", '''def _futures(raw, stops):
    tails = [b""] + _tails(stops)
    return [raw + head + tail for head in HEADS for tail in tails]''',
     '''def _futures(raw, stops):
    tails = [b""] + _tails(stops)
    out = []
    for head in HEADS:
        for tail in tails:
            cand = raw + head + tail
            if cand not in out:
                out.append(cand)
    return out'''),
    ("ok-tails-as-list",
     "the stop tails built as a list in stop order rather than as a sorted set.",
     "hold", '''def _tails(stops):
    out = {b"a"}
    for st in stops:
        for k in range(len(st)):
            out.add(st[k:])
    return sorted(out)''', '''def _tails(stops):
    out = [b"a"]
    for st in stops:
        for k in range(len(st)):
            if st[k:] not in out:
                out.append(st[k:])
    return out'''),
    ("ok-shared-by-zip",
     "the shared prefix found by walking the pairs rather than by index.",
     "hold", '''def _shared(texts):
    keep = texts[0]
    for text in texts[1:]:
        n = 0
        while n < len(keep) and n < len(text) and keep[n] == text[n]:
            n += 1
        keep = keep[:n]
    return keep''', '''def _shared(texts):
    keep = texts[0]
    for text in texts[1:]:
        take = 0
        for a, b in zip(keep, text):
            if a != b:
                break
            take += 1
        keep = keep[:take]
    return keep'''),
    ("ok-boxkey",
     "the reference with the name it hangs its own working state on changed. No graded value may "
     "turn on a name the submission invented, and this is the mirror that proves it does not.",
     "both", '"seen"', '"~~carry~~"'),
    ("ok-recompute-pick",
     "the calls intersected from futures rendered again in pick rather than from what hold left "
     "behind. Same answer, twice the work, and it must not be graded.",
     "pick", None, '''from srv import bite, look
from srv.hold import _futures


def _names(text, inert, limit):
    out = []
    i = 0
    n = min(len(text), limit)
    while i < n:
        if text[i:i + 1] == b"{":
            j = text.find(b"}", i + 1)
            if 0 < j < n and not any(inert[i:j + 1]):
                nm = text[i + 1:j]
                if nm and all(97 <= b <= 122 for b in nm):
                    out.append(nm.decode())
                    i = j + 1
                    continue
        i += 1
    return out


def take(st, sent):
    if st.ended:
        vis, inert = look.read(st.raw)
        text, tin, _ = bite.chop(vis, inert, st.stops)
        return tuple(_names(text, tin, len(sent)))
    lists = []
    for future in _futures(st.raw, st.stops):
        vis, inert = look.read(future)
        text, tin, _ = bite.chop(vis, inert, st.stops)
        lists.append(_names(text, tin, len(sent)))
    names = lists[0]
    for lst in lists[1:]:
        n = 0
        while n < len(names) and n < len(lst) and names[n] == lst[n]:
            n += 1
        names = names[:n]
    return tuple(names)
'''),
]


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    for name, why, which, old, new in VARIANTS:
        hold, pick = REF_HOLD, REF_PICK
        if which in ("hold", "both"):
            if hold.count(old) < 1:
                raise SystemExit("anchor for %s not in hold.py" % name)
            hold = hold.replace(old, new)
        if which in ("pick", "both"):
            if old is None:
                pick = new
            else:
                if pick.count(old) < 1:
                    raise SystemExit("anchor for %s not in pick.py" % name)
                pick = pick.replace(old, new)
        d = os.path.join(OUT, name)
        os.makedirs(d)
        with open(os.path.join(d, "hold.py"), "w", newline="\n") as fh:
            fh.write(hold)
        with open(os.path.join(d, "pick.py"), "w", newline="\n") as fh:
            fh.write(pick)
        with open(os.path.join(d, "WHY"), "w", newline="\n") as fh:
            fh.write(why + "\n")
    print("wrote %d variants" % len(VARIANTS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
