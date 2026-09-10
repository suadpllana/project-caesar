import random, sys, pathlib, importlib
sys.path.insert(0, str(pathlib.Path("tasks/aside-fit-sweep/environment/app_src").resolve()))
sys.path.insert(0, str(pathlib.Path("authoring/aside-fit-sweep").resolve()))
import ops
from reg import live, text
import model_proto


def run_ref(lines):
    span, part, body = text.parse(lines)
    h = live.Pool(span, part)
    out = []
    for line in body:
        ops.ex(h, tuple(line.split()), out)
    return out


def prog(rng, span=4096, part=512, n=120):
    lines = ["span %d" % span, "part %d" % part]
    ids = []
    for i in range(n):
        r = rng.random()
        if r < 0.45 or not ids:
            name = "x%d" % rng.randrange(60)
            lines.append("get %s %d" % (name, rng.choice([1, 8, 16, 24, 33, 40, 64, 100, 128, 250, 260, 300, 512, 520])))
            ids.append(name)
        elif r < 0.75:
            lines.append("put %s" % rng.choice(ids))
        elif r < 0.95:
            lines.append("fit %s %d" % (rng.choice(ids), rng.choice([8, 16, 24, 40, 64, 96, 128, 200, 400])))
        else:
            lines.append("sweep")
    return lines


def main():
    rng = random.Random(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
    bad = 0
    for t in range(400):
        lines = prog(rng)
        a = run_ref(lines)
        b = model_proto.expect(lines)
        if a != b:
            bad += 1
            if bad == 1:
                for i, (x, y) in enumerate(zip(a + [None] * 9, b + [None] * 9)):
                    if x != y:
                        print("first diff at line", i, "ref:", x, "model:", y)
                        break
                pathlib.Path("/tmp/bad.txt").write_text("\n".join(lines) + "\n")
                print("len ref", len(a), "len model", len(b))
    print("mismatched programs:", bad, "of 400")


main()
