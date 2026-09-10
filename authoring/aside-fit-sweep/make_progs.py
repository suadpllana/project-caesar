"""The programs that ship in /app/progs: a worked example, a few readable ones, and the two big
ones the brief asks the agent to time. Written with newline pinned; no CR survives."""
import pathlib, random, sys
R = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "tasks/aside-fit-sweep/tests"))
import gen

OUT = R / "tasks/aside-fit-sweep/environment/app_src/progs"

SMALL = {
    "tiny.txt": [
        "span 1024", "part 512",
        "get a 264",
        "get b 8",
        "get c 128",
        "get d 264",
    ],
    "hole.txt": [
        "span 2048", "part 512",
        "get a 448", "get b 128", "get c 64",
        "put b", "put c",
        "get d 128", "get e 64",
    ],
    "pair.txt": [
        "span 1024", "part 512",
        "get a 64", "get b 64",
        "put b",
        "fit a 128",
        "sweep",
        "fit a 192",
    ],
    "fill.txt": [
        "span 1024", "part 512",
        "get a 256", "get b 256", "get c 256", "get d 256",
        "put a", "put b",
        "get e 512",
        "get f 8",
    ],
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, lines in SMALL.items():
        (OUT / name).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    for name, fam in (("wide.txt", "wide"), ("churn.txt", "churn")):
        lines = gen.BUILD[fam](random.Random("shipped|%s" % fam))
        (OUT / name).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    for p in OUT.iterdir():
        assert "\r" not in p.read_text(encoding="utf-8"), p
    print("wrote %d programs" % len(list(OUT.iterdir())))


main()
