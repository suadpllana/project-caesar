#!/usr/bin/env python3
"""Does the agent container actually hold the files the brief tells the agent to use?

The quality review rejected `lock-priority-unwind` on 2026-09-03 because
`environment/Dockerfile` copied `app_src/rt/`, `app_src/conf/` and `app_src/run_sched.py`
and never `app_src/cases/`. The two case files existed in the repo, were synced into
`tests/pristine` by `authoring/sync.py`, and reached the verifier's work tree - so the
executed-tree attestation was perfectly happy - but they never reached the agent image.
`instruction.md` opened by telling the agent to run one of them, so its first action was a
`FileNotFoundError` and none of the tick numbers the brief quotes could be reproduced.

Nothing here could see that. Preflight reads the tree, the trial reads `/pristine`, and the
similarity and text checkers read prose. This reads the Dockerfile the way docker does and
answers the two questions the reviewer asked:

  1. which files under environment/ never reach the image at all, and
  2. does every /app path the instruction names exist there once it is built.

Static on purpose. The Windows authoring host has no docker, and a gate that cannot run
where the task is written is a gate nobody runs.
"""

from __future__ import annotations

import re
import shlex
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TASKS = REPO / "tasks"

# Paths a brief may legitimately name that no COPY is expected to produce: a directory the
# solution writes, or the tree root itself.
ALLOW_MISSING = {
    "/app",
}


def env_root(task: Path) -> Path | None:
    env = task / "environment"
    for name in ("app_src", "app"):
        if (env / name).is_dir():
            return env / name
    return None


def parse_copies(dockerfile: Path):
    """Return (workdir, [(src, dst), ...]) with continuations joined, as docker reads them."""
    raw = dockerfile.read_text(encoding="utf-8", errors="replace")
    raw = re.sub(r"\\\s*\n\s*", " ", raw)
    workdir = "/"
    copies = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        head, _, rest = line.partition(" ")
        verb = head.upper()
        if verb == "WORKDIR":
            w = rest.strip()
            workdir = w if w.startswith("/") else workdir.rstrip("/") + "/" + w
        elif verb in ("COPY", "ADD"):
            try:
                parts = [p for p in shlex.split(rest) if not p.startswith("--")]
            except ValueError:
                parts = [p for p in rest.split() if not p.startswith("--")]
            if len(parts) < 2:
                continue
            *srcs, dst = parts
            for s in srcs:
                copies.append((s, dst, len(srcs) > 1))
    return workdir, copies


def resolve_dst(dst: str, workdir: str) -> str:
    if dst.startswith("/"):
        out = dst
    else:
        out = workdir.rstrip("/") + "/" + dst.lstrip("./")
    out = re.sub(r"/+", "/", out)
    return out


def image_files(task: Path) -> tuple[set[str], list[str]]:
    """Emulate the COPY layers. Returns (absolute paths present, notes)."""
    env = task / "environment"
    dockerfile = env / "Dockerfile"
    workdir, copies = parse_copies(dockerfile)
    present: set[str] = set()
    notes: list[str] = []
    for src, dst, multi in copies:
        srcp = (env / src).resolve()
        d = resolve_dst(dst, workdir)
        if not srcp.exists():
            notes.append("COPY source not in the build context: %s" % src)
            continue
        if srcp.is_dir():
            # docker copies the CONTENTS of a source directory into dest.
            base = d.rstrip("/")
            for f in sorted(srcp.rglob("*")):
                if f.is_file() and "__pycache__" not in f.parts:
                    present.add(base + "/" + f.relative_to(srcp).as_posix())
        else:
            if dst.endswith("/") or multi or (env / dst.lstrip("/")).is_dir():
                present.add(d.rstrip("/") + "/" + srcp.name)
            else:
                present.add(d)
    return present, notes


def declared_artifacts(task: Path) -> set[str]:
    """Paths the agent is responsible for producing. A brief may name one that does not ship:
    the agent writes it. Environment files that never reach the image are a separate check
    and are not exempted by anything here."""
    toml = task / "task.toml"
    if not toml.exists():
        return set()
    text = toml.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"artifacts\s*=\s*\[(.*?)\]", text, re.S)
    if not m:
        return set()
    return set(re.findall(r"[\"\']([^\"\']+)[\"\']", m.group(1)))


def instruction_paths(task: Path) -> list[str]:
    md = task / "instruction.md"
    if not md.exists():
        return []
    text = md.read_text(encoding="utf-8", errors="replace")
    found = []
    for m in re.finditer(r"/app(?:/[A-Za-z0-9_.\-]+)*", text):
        p = m.group(0).rstrip(".,;:)")
        if p not in found:
            found.append(p)
    return found


def check(slug: str) -> list[str]:
    task = TASKS / slug
    findings: list[str] = []
    if not (task / "environment" / "Dockerfile").exists():
        return findings
    src_root = env_root(task)
    present, notes = image_files(task)
    findings.extend(notes)

    # 1. Anything shipped in the environment tree that no COPY line ever picks up.
    if src_root is not None:
        for f in sorted(src_root.rglob("*")):
            if not f.is_file() or "__pycache__" in f.parts or f.suffix == ".pyc":
                continue
            rel = f.relative_to(src_root).as_posix()
            if not any(p.endswith("/" + rel) for p in present):
                findings.append(
                    "environment/%s/%s ships in the tree but no COPY line puts it in the image"
                    % (src_root.name, rel)
                )

    # 2. Every /app path the brief names has to be there once the image is built.
    dirs = {p.rsplit("/", 1)[0] for p in present}
    arts = declared_artifacts(task)
    for q in instruction_paths(task):
        if q in ALLOW_MISSING or q in present or q in arts:
            continue
        if q in dirs or any(d == q or d.startswith(q + "/") for d in dirs):
            continue
        findings.append("instruction.md names %s and it is not in the built image" % q)
    return findings


def main(argv) -> int:
    slugs = [p.name for p in sorted(TASKS.iterdir()) if p.is_dir()]
    if len(argv) > 1 and argv[1] != "--all":
        slugs = [argv[1]]
    bad = 0
    for slug in slugs:
        f = check(slug)
        if f:
            bad += 1
            print("FAIL %s" % slug)
            for line in f:
                print("     %s" % line)
        else:
            print("ok   %s" % slug)
    print()
    print("%d of %d bundles with findings" % (bad, len(slugs)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
