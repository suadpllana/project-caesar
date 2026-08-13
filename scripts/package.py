#!/usr/bin/env python3
"""Package a Frontier Bench task bundle into a submission zip.

Runs the pre-flight checks first and refuses to package a bundle with errors, so a submission
cannot be built from a task that will fail the structural gate.

Usage:
    python scripts/package.py <task-dir> [-o <output.zip>] [--force]
    uv run --python 3.12 scripts/package.py <task-dir>

Why this exists rather than a plain zip command: PowerShell's Compress-Archive writes backslash
path separators, which produce a broken layout when the bundle is unpacked on Linux, and neither
it nor Explorer's "Send to > Compressed folder" preserves the executable bit on solve.sh and
test.sh. This writes forward-slash entries and marks .sh files executable.

Exit code 0 on success, 1 if packaging was refused or failed. Requires Python 3.11+.
"""

from __future__ import annotations

import argparse
import sys
import tomllib
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import preflight  # noqa: E402

# Exclusions come from preflight - SINGLE SOURCE OF TRUTH, so the scanner and the
# packager can never disagree about what ships (see preflight.EXCLUDE_DIRS).
EXCLUDE_NAMES = preflight.EXCLUDE_NAMES
EXCLUDE_DIRS = preflight.EXCLUDE_DIRS
EXCLUDE_SUFFIXES = preflight.EXCLUDE_SUFFIXES

EXECUTABLE_ATTR = (0o755 << 16) | 0o600
REGULAR_ATTR = (0o644 << 16) | 0o600


def task_slug(root: Path) -> str:
    try:
        cfg = tomllib.loads((root / "task.toml").read_text(encoding="utf-8"))
        name = cfg.get("task", {}).get("name", "")
        if "/" in name:
            return name.split("/", 1)[1]
        if name:
            return name
    except (OSError, tomllib.TOMLDecodeError):
        pass
    return root.name


def included_files(root: Path) -> list[Path]:
    """Exactly what preflight scanned - one definition, used by both tools."""
    return preflight.shipped_files(root)


def run_checks(root: Path) -> tuple[int, int]:
    preflight.errors.clear()
    preflight.warnings.clear()
    preflight.check_structure(root)
    cfg = preflight.check_task_toml(root)
    preflight.check_instruction(root, cfg)
    preflight.check_scripts(root)
    preflight.check_environment_docs(root)
    preflight.check_leaks_by_affordance(root)
    preflight.check_artifact_parents(root, cfg)
    preflight.check_compose(root, cfg)
    preflight.check_verifier(root)
    preflight.check_state_difficulty(root)
    preflight.check_verifier_isolation(root, cfg)
    preflight.check_verifier_selfcontained(root)
    preflight.check_blocked_terms(root)
    for msg in preflight.ordered(preflight.warnings):
        print(f"  WARN   {msg}")
    for msg in preflight.ordered(preflight.errors):
        print(f"  ERROR  {msg}")
    return len(preflight.errors), len(preflight.warnings)


def build_zip(root: Path, out: Path, files: list[Path], slug: str) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            rel = path.relative_to(root)
            # Forward slashes and a task-named root folder, as the bundle layout expects.
            arcname = f"{slug}/" + "/".join(rel.parts)
            info = zipfile.ZipInfo(arcname, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = EXECUTABLE_ATTR if path.suffix == ".sh" else REGULAR_ATTR
            zf.writestr(info, path.read_bytes())


def audit_zip(path: Path) -> list[str]:
    """Scan the built archive itself for blocked terms. Independent of the exclusion lists."""
    hits = []
    with zipfile.ZipFile(path) as zf:
        for info in zf.infolist():
            rel = "/".join(info.filename.split("/")[1:])  # drop the <slug>/ root
            if rel in preflight.BLOCKED_SCAN_EXEMPT:
                continue
            try:
                text = zf.read(info).decode("utf-8").lower()
            except (UnicodeDecodeError, KeyError):
                continue
            for term in preflight.BLOCKED_TERMS:
                if term in text:
                    hits.append(f"{info.filename} contains {term!r}")
                    break
    return hits


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Package a task bundle for submission.")
    parser.add_argument("task_dir", help="Path to the task bundle directory")
    parser.add_argument("-o", "--output", help="Output zip path (default: <slug>.zip beside the task)")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Package even if pre-flight reports errors (the submission will likely be rejected)",
    )
    args = parser.parse_args(argv[1:])

    root = Path(args.task_dir).resolve()
    if not root.is_dir():
        print(f"not a directory: {root}")
        return 1

    print(f"Pre-flight check: {root}\n")
    error_count, warn_count = run_checks(root)
    print()

    if error_count and not args.force:
        print(
            f"{error_count} error(s), {warn_count} warning(s). Refusing to package.\n"
            "Fix the errors above, or re-run with --force if you understand the submission\n"
            "will fail the structural gate."
        )
        return 1

    slug = task_slug(root)
    out = Path(args.output).resolve() if args.output else root.parent / f"{slug}.zip"
    files = included_files(root)
    if not files:
        print("nothing to package")
        return 1

    build_zip(root, out, files, slug)

    # Last line of defence: audit what actually went into the zip, not what we believe
    # went in. Exclusion lists can drift; the archive cannot lie.
    leaked = audit_zip(out)
    if leaked and not args.force:
        out.unlink(missing_ok=True)
        print(
            "Refusing to ship: the built zip contained blocked terms and was deleted.\n"
            + "\n".join(f"  {hit}" for hit in leaked[:10])
            + "\nThese are usually leftover harness output (harbor writes result.json with the "
            "task name). Delete them from the task folder and package again."
        )
        return 1

    size_kb = out.stat().st_size / 1024
    print(f"Packaged {len(files)} files into {out} ({size_kb:.1f} KB)")
    if error_count:
        print(f"WARNING: packaged with {error_count} unresolved error(s) because --force was given.")
    print(f"\nContents (root folder: {slug}/):")
    for path in files:
        print(f"  {'/'.join(path.relative_to(root).parts)}")
    print(
        "\nExcluded: STATE.md and local clutter (git metadata, caches, logs, previous zips).\n"
        "Packaging does not validate that the task works. Before submitting, confirm:\n"
        "  harbor run -p . -a oracle -e docker   scored 1\n"
        "  harbor run -p . -a nop -e docker      scored 0\n"
        "  every cheat/ attempt                  scored 0"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
