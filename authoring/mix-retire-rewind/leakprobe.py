"""The leak audit as a script, not as a feeling (docs/DIFFICULTY.md).

For every stage this task counts as difficulty, try to reproduce the answer from the shipped
files with no reasoning at all - a count against the pattern as written, a division, a field
read off a record - and print how often that works. A stage a five-line expression already
answers is worth nothing however hard it looks in the notes.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "mix-retire-rewind"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import gen  # noqa: E402
import lab  # noqa: E402
import model  # noqa: E402


def tally(pat, j, wide):
    whole, rest = divmod(wide, len(pat))
    return whole * pat.count(j) + pat[:rest].count(j)


def plans(per=20):
    return [(fam, name, lines) for fam, name, lines in gen.programs("leakprobe", per)
            if fam not in ("wide", "deep")]


def main():
    work = plans()
    print("%d generated plans" % len(work), flush=True)

    # 1. the delivered count, taken against the pattern as the plan wrote it
    hits = miss = 0
    for _fam, _name, lines in work:
        feed = model.Feed()
        for line in lines:
            part = tuple(line.split())
            if part[0] in ("seed", "cap", "src", "mix"):
                feed.ex(part)
        opening = list(feed.pat)
        for slot in range(0, 120, 11):
            want = feed.delivered(slot)
            guess = [tally(opening, j, slot) for j in range(len(feed.lens))]
            if want == guess:
                hits += 1
            else:
                miss += 1
    print("delivered count from the opening pattern:      %5.1f%% of %d probes"
          % (100.0 * hits / (hits + miss), hits + miss), flush=True)

    # 2. the epoch and cursor in a record, from the delivered count and the source length
    ep_hit = ep_all = cur_hit = cur_all = 0
    for _fam, _name, lines in work:
        got = model.expect(lines)
        feed = model.Feed()
        for line in lines:
            part = tuple(line.split())
            feed.ex(part) if part[0] in ("seed", "cap", "src", "mix") else None
        for line in got:
            if not line.startswith(("save ", "load ")):
                continue
            for field in line.split()[4 if line.startswith("save") else 3:]:
                bits = field.split(":")
                if len(bits) != 4:
                    continue
                j = feed.names.index(bits[0])
                ep, cur, took = int(bits[1]), int(bits[2]), int(bits[3])
                n = len(feed.lens[j])
                ep_all += 1
                cur_all += 1
                if ep == took // n:
                    ep_hit += 1
                if cur == took % n:
                    cur_hit += 1
    print("record epoch as delivered // samples:          %5.1f%% of %d fields"
          % (100.0 * ep_hit / max(ep_all, 1), ep_all), flush=True)
    print("record cursor as delivered %% samples:          %5.1f%% of %d fields"
          % (100.0 * cur_hit / max(cur_all, 1), cur_all), flush=True)

    # 3. the base a load begins at, read straight off the record it prints beside
    base_hit = base_all = 0
    for _fam, _name, lines in work:
        got = model.expect(lines)
        saved = {}
        for line in lines:
            part = line.split()
            if part[0] == "save":
                saved[part[2]] = part[1]
        marks = {}
        for line in got:
            part = line.split()
            if part[0] == "save":
                marks[part[1]] = (int(part[2]), int(part[3]), int(part[4]))
        for line, raw in zip(got, [ln for ln in got]):
            part = line.split()
            if part[0] != "load":
                continue
            base = int(part[2])
            base_all += 1
            # the only field-level guess available: the produced step count times some width
            if any(base == b + m * w for (b, d, m) in marks.values()
                   for w in (1, 2, 4, 8, 16, 32)):
                base_hit += 1
    print("load base as produced steps times any width:   %5.1f%% of %d loads"
          % (100.0 * base_hit / max(base_all, 1), base_all), flush=True)

    # 4. the shipped feeder, run as it ships
    feed = [(n, "\n".join(ls)) for _f, n, ls in work]
    ship = lab.run_many(lab.shipped(), feed)
    same = sum(1 for n, ls in feed
               if ship[n]["got"] == model.expect(ls.splitlines()))
    print("the shipped feeder reproducing a graded trace: %5.1f%% of %d plans"
          % (100.0 * same / len(feed), len(feed)), flush=True)

    # 5. the sample a slot gets, ignoring the hand-over order
    id_hit = id_all = 0
    for _fam, _name, lines in work:
        got = model.expect(lines)
        feed2 = model.Feed()
        for line in lines:
            part = tuple(line.split())
            if part[0] in ("seed", "cap", "src", "mix"):
                feed2.ex(part)
        for line in got:
            if not line.startswith("show "):
                continue
            for field in line.split()[5:]:
                name, pos = field.split(".")
                j = feed2.names.index(name)
                id_all += 1
                if int(pos) == int(pos) % len(feed2.lens[j]) and int(pos) < 2:
                    id_hit += 1
    print("sample position landing in the first two:      %5.1f%% of %d ids"
          % (100.0 * id_hit / max(id_all, 1), id_all), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
