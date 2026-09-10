"""Differential run: the reference tree against the sealed model, over random programs."""
import pathlib
import random
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "span-claim-charge"

sys.path.insert(0, str(TASK / "tests" / "seal"))
import model  # noqa: E402


def stage():
    room = pathlib.Path(tempfile.mkdtemp())
    tree = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", tree)
    for part in ("dev.py", "hold.py", "item.py", "line.py", "tally.py"):
        shutil.copy(TASK / "solution" / part, tree / "store" / part)
    return tree


NAMES = "abcdefgh"
ITEMS = "fghijk"


def program(rng, blocks=None, steps=None):
    blocks = blocks or rng.choice([24, 32, 48, 64, 96, 160])
    steps = steps or rng.randint(12, 60)
    rows = ["dev %d" % blocks]
    lines = []
    items = {}
    for _ in range(steps):
        pick = rng.random()
        if not lines or pick < 0.06:
            name = rng.choice(NAMES)
            rows.append("n %s" % name)
            if name not in lines:
                lines.append(name)
                items[name] = []
            continue
        ln = rng.choice(lines)
        if pick < 0.14 and items[ln]:
            dst = rng.choice(NAMES)
            rows.append("p %s %s" % (ln, dst))
            if dst not in lines:
                lines.append(dst)
                items[dst] = list(items[ln])
            continue
        if pick < 0.18 and len(lines) > 1:
            rows.append("d %s" % ln)
            lines.remove(ln)
            items.pop(ln, None)
            continue
        if pick < 0.52:
            nm = rng.choice(ITEMS)
            rows.append("w %s/%s %d %d" % (ln, nm, rng.randint(0, 8), rng.randint(1, 10)))
            if nm not in items[ln]:
                items[ln].append(nm)
            continue
        if pick < 0.64 and items[ln]:
            sn = rng.choice(items[ln])
            dl = rng.choice(lines)
            dn = rng.choice(ITEMS)
            rows.append("s %s/%s %d %d %s/%s %d" % (
                ln, sn, rng.randint(0, 6), rng.randint(1, 6), dl, dn, rng.randint(0, 6)))
            if dn not in items[dl]:
                items[dl].append(dn)
            continue
        if pick < 0.70 and items[ln]:
            rows.append("t %s/%s %d" % (ln, rng.choice(items[ln]), rng.randint(0, 8)))
            continue
        if pick < 0.75 and items[ln]:
            nm = rng.choice(items[ln])
            rows.append("x %s/%s" % (ln, nm))
            items[ln].remove(nm)
            continue
        if pick < 0.80 and items[ln]:
            rows.append("v %s/%s" % (ln, rng.choice(items[ln])))
            continue
        if pick < 0.86:
            rows.append("c %s" % ln)
            continue
        if pick < 0.90:
            k = rng.randint(1, min(3, len(lines)))
            rows.append("g %s" % ",".join(rng.sample(lines, k)))
            continue
        if pick < 0.95 and items[ln]:
            rows.append("m %s/%s" % (ln, rng.choice(items[ln])))
            continue
        rows.append("f")
    return rows


def main():
    tree = stage()
    sys.path.insert(0, str(tree))
    from base import feed
    rng = random.Random(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    bad = 0
    for k in range(runs):
        rows = program(rng)
        try:
            got = feed.run(rows)
        except Exception as exc:
            print("reference raised on program %d: %r" % (k, exc))
            print("\n".join(rows))
            return 1
        try:
            want = model.expect(rows)
        except Exception as exc:
            print("model raised on program %d: %r" % (k, exc))
            print("\n".join(rows))
            return 1
        if got != want:
            bad += 1
            print("=== program %d differs ===" % k)
            print("\n".join(rows))
            for i, (a, b) in enumerate(zip(got, want)):
                if a != b:
                    print("line %d: reference %r model %r" % (i, a, b))
                    break
            if len(got) != len(want):
                print("lengths %d vs %d" % (len(got), len(want)))
            if bad >= 3:
                return 1
    print("compared %d programs, %d differ" % (runs, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
