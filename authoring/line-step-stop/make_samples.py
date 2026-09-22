"""Write the agent-facing sample sessions into environment/app_src/samples/.

Four sessions from a seed no graded session uses: an ordinary one, one full of inlined
calls, one full of row shapes, and one heavy session the size of the largest graded ones.
Only the image, the script and the tape ship - never an expected output.
"""
import os
import random

from lab import APP, forge

OUT = os.path.join(APP, "samples")


def write(name, s):
    with open(os.path.join(OUT, name + ".img"), "w", newline="\n") as f:
        f.write(s["image"])
    with open(os.path.join(OUT, name + ".cmd"), "w", newline="\n") as f:
        f.write("\n".join(s["cmds"]) + "\n")
    with open(os.path.join(OUT, name + ".tape"), "w", newline="\n") as f:
        f.write(" ".join(str(v) for v in s["tape"]) + "\n")


def main():
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        os.remove(os.path.join(OUT, f))
    rng = random.Random(31337)
    pick = {}
    for name, fam in (("calls", "plain"), ("inline", "nest"), ("rows", "hoist")):
        best = None
        for _ in range(40):
            s = forge.session(fam, rng)
            n = len(s["image"].splitlines())
            if 40 <= n <= 160 and len(s["cmds"]) >= 10 and (best is None or len(s["want"]) > len(best["want"])):
                best = s
        pick[name] = best
    pick["long"] = forge.heavy_session(rng, heavy_range=(250000, 700000), floor=3000000)
    for name, s in pick.items():
        write(name, s)
        print(name, len(s["image"].splitlines()), "image lines", len(s["cmds"]), "commands",
              s.get("in_frame", ""))


if __name__ == "__main__":
    main()
