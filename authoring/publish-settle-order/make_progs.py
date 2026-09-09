"""Write the example programs that ship in the agent's tree.

`wide.txt` is one draw from the same family the graded set uses, at the size the graded ones
run, so timing it is a fair measurement rather than an extrapolation. The others are small
enough to read. None of them ships with an expected trace.
"""
import pathlib
import random
import sys

TESTS = pathlib.Path(__file__).resolve().parents[2] / "tasks" / "publish-settle-order" / "tests"
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(TESTS / "seal"))
import gen  # noqa: E402

PROGS = pathlib.Path(__file__).resolve().parents[2] / "tasks" / "publish-settle-order" / \
    "environment" / "app_src" / "progs"

SMALL = {
    "tiny.txt": """
unit u1
fall u1 s1
unit u2
pub u2 s1
unit u3
act u1
act u2
act u3
call u3 s1
""",
    "pair.txt": """
unit u1
unit u2
dep u1 u2
dep u2 u1
pub u1 s1
pub u2 s2
boot u1 s2
act u1
call u2 s1
rel u1
""",
    "soft.txt": """
unit u1
pub u1 s1
unit u2
pre u2 u1
boot u2 s1
act u2
call u2 s1
""",
    "scope.txt": """
unit u1
pub u1 s1
unit u2
dep u2 u1
open u2
call u2 s1
""",
    "lazy.txt": """
unit u1
pub u1 s1
unit u2
auto u2
dep u2 u1
pub u2 s2
boot u2 s1
unit u3
act u3
call u3 s2
rel u3
""",
    "churn.txt": """
unit u1
pub u1 s1
unit u2
pub u2 s1
unit u3
act u1
act u3
call u3 s1
rel u1
call u3 s1
act u2
call u3 s1
rel u3
""",
}


def write(name, lines):
    path = PROGS / name
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    text = path.read_text(encoding="utf-8")
    if "\r" in text:
        raise SystemExit("CR byte in %s" % name)
    print("%-10s %7d lines  %8d bytes" % (name, len(lines), len(text)))


def main():
    PROGS.mkdir(parents=True, exist_ok=True)
    for name, body in SMALL.items():
        write(name, [ln for ln in body.strip().splitlines()])
    write("wide.txt", gen.BUILD["wide"](random.Random("shipped-wide")))
    write("tear.txt", gen.BUILD["tear"](random.Random("shipped-tear")))


if __name__ == "__main__":
    main()
