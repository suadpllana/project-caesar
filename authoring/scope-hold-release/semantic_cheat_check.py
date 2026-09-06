"""Replay semantic wrong-reading cheats without needing a Linux shell or Docker."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import harness

SEMANTICALLY_CORRECT = {
    "cheat-probe-patch-seal.sh",
    "cheat-probe-rewrite-frozen.sh",
}

BLOCK = re.compile(
    r'cat > "\$\{APP\}/wire/([^"/]+\.py)" <<\'SHR_EOF\'\n(.*?)\nSHR_EOF',
    re.DOTALL,
)


def overlay(script: Path) -> Path:
    tree = harness.stage(None)
    text = script.read_text(encoding="utf-8")
    found = BLOCK.findall(text)
    if not found:
        raise RuntimeError("no policy blocks in %s" % script.name)
    for name, body in found:
        (tree / "wire" / name).write_text(body + "\n", encoding="utf-8", newline="\n")
    return tree


def replay(tree: Path, rounds: int) -> dict:
    proc = subprocess.run(
        [sys.executable, "-c", harness.PROBE, str(tree), str(harness.TASK / "tests"), str(rounds)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-2000:] or "replay exited %d" % proc.returncode)
    return json.loads(proc.stdout)


def main(argv: list[str]) -> int:
    rounds = int(argv[1]) if len(argv) > 1 else 300
    scripts = [harness.TASK / "cheat" / "cheat-forge-answer-key.sh"]
    scripts.extend(harness.TASK / "cheat" / name for name in sorted(SEMANTICALLY_CORRECT))
    scripts.extend(sorted((harness.TASK / "cheat").glob("cheat-rule-*.sh")))
    failed = 0
    for script in scripts:
        tree = overlay(script)
        try:
            try:
                result = replay(tree, rounds)
            except RuntimeError as exc:
                result = None
                detail = str(exc).splitlines()[-1]
        finally:
            shutil.rmtree(tree.parent, ignore_errors=True)
        if result is None:
            expected = script.name not in SEMANTICALLY_CORRECT
            failed += not expected
            print("%-44s crashed (%s) %s" %
                  (script.name, detail, "expected" if expected else "UNEXPECTED"))
            continue
        accepted = not result["fixed"] and result["generated"] == 0
        expected = accepted == (script.name in SEMANTICALLY_CORRECT)
        failed += not expected
        print(
            "%-44s fixed=%2d generated=%3d %s"
            % (
                script.name,
                len(result["fixed"]),
                result["generated"],
                ("accepted" if accepted else "rejected") if expected else "UNEXPECTED",
            )
        )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
