#!/usr/bin/env python3
"""Offline pre-flight checks for a Frontier Bench task bundle.

Checks the mechanical submission rules that can be verified without Docker: bundle structure,
task.toml fields and caps, the instruction suffix, package pinning, path style, line endings,
and obvious ground-truth leaks.

It does NOT check the things that decide acceptance: whether the task is hard enough, original,
or genuinely verifiable. Passing this is necessary, not sufficient.

Usage:
    python scripts/preflight.py <task-dir>
    uv run --python 3.12 scripts/preflight.py <task-dir>

Exit code 0 if there are no errors, 1 otherwise. Requires Python 3.11+.
"""

from __future__ import annotations

import re
import sys
import tomllib
import unicodedata
from pathlib import Path, PurePosixPath

CATEGORIES = {"science", "software", "ml", "operations", "security", "hardware", "media"}

# The guideline's category -> label table. `subcategory` must be one of its category's labels.
SUBCATEGORIES = {
    "science": ["Biology", "Chemistry", "Physics", "Earth", "Robotics", "Math", "Linguistics"],
    "software": ["Algorithms", "Systems", "Databases", "Data engineering", "Frontend", "Languages"],
    "ml": ["Training", "Inference", "Evaluation", "Kernels"],
    "operations": ["Finance", "Logistics", "Supply chain", "Claims", "Compliance", "Marketing"],
    "security": ["Cryptography", "Reverse engineering", "Forensics", "AppSec"],
    "hardware": ["CAD", "RTL"],
    "media": ["Music", "Design"],
}


def norm_label(value: str) -> str:
    """Fold case, separators and spacing so 'Data engineering' == 'data-engineering'."""
    return re.sub(r"[\s_-]+", "", str(value).strip().lower())

SUFFIX_RE = re.compile(
    r"You have (\d+) seconds to complete this task\. "
    r"Do not cheat by using online solutions or hints specific to this task\.$"
)

MAX_TIMEOUT_SEC = 18000
MAX_CPUS = 16
MAX_MEMORY_MB = 16384
MAX_STORAGE_MB = 40960

REQUIRED_FILES = [
    "instruction.md",
    "task.toml",
    "environment/Dockerfile",
    "solution/solve.sh",
    "tests/test.sh",
    "tests/Dockerfile",
]

TODO_MARKERS = ("TODO", "FIXME", "<your-", "XXX")

# ---------------------------------------------------------------------------
# What ships in the submission zip. SINGLE SOURCE OF TRUTH: package.py imports
# these, and every scan here runs over exactly the set that ships. When the two
# disagreed, harbor's own `jobs/` output was skipped by the scanner and shipped
# by the packager - and its result.json carries the org name, which the platform
# blocks. Never let one tool learn about a path the other does not.
EXCLUDE_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".ruff_cache",
    "logs", "runs", ".harbor",
    "jobs",          # harbor run's default output dir (-o/--jobs-dir)
    "job", "results", "trials", ".pytest_cache",
}
# Any directory holding a harbor result file is harness output, whatever it is called.
HARNESS_OUTPUT_MARKERS = ("result.json", "trial.log", "job.log")
EXCLUDE_NAMES = {"STATE.md", ".DS_Store", "Thumbs.db", ".gitignore", ".gitattributes"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".zip", ".log"}


def harness_output_dirs(root: Path) -> set[Path]:
    """Directories that are harbor run output, detected by content, not by name."""
    found: set[Path] = set()
    for marker in HARNESS_OUTPUT_MARKERS:
        for hit in root.rglob(marker):
            # <task>/<jobsdir>/<jobname>/... - exclude the whole top-level jobs dir
            rel = hit.relative_to(root)
            if rel.parts:
                found.add(root / rel.parts[0])
    return {d for d in found if d.is_dir()}


def shipped_files(root: Path) -> list[Path]:
    """Exactly the files package.py puts in the zip. Every scan should use this."""
    skip_dirs = harness_output_dirs(root)
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if any(str(path).startswith(str(d)) for d in skip_dirs):
            continue
        if path.name in EXCLUDE_NAMES or path.suffix.lower() in EXCLUDE_SUFFIXES:
            continue
        files.append(path)
    return files

errors: list[str] = []
warnings: list[str] = []


def error(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def read(path: Path) -> str | None:
    try:
        return path.read_bytes().decode("utf-8")
    except FileNotFoundError:
        return None
    except UnicodeDecodeError:
        error(f"{path.name}: not valid UTF-8")
        return None


# --------------------------------------------------------------------------- structure


def check_structure(root: Path) -> None:
    for rel in REQUIRED_FILES:
        if not (root / rel).is_file():
            error(f"missing required file: {rel}")
    if not (root / "tests" / "test_outputs.py").is_file():
        warn("tests/test_outputs.py not found - the standard verifier template uses it")
    cheat = root / "cheat"
    if not cheat.is_dir() or not any(p.is_file() for p in cheat.iterdir()):
        warn(
            "cheat/ is missing or empty - write deliberate fake solutions and confirm each "
            "scores 0 before submitting; the pipeline runs its own adversarial probe"
        )

    stray = harness_output_dirs(root)
    if stray:
        names = ", ".join(sorted(d.name for d in stray))
        warn(
            f"harbor run output found in the task folder ({names}) - excluded from the zip, but "
            "its result.json records the task name, which the platform blocks. Run the gates with "
            "`-o <somewhere-outside-the-task-dir>`, or delete these before packaging"
        )

    env_dir = root / "environment"
    if env_dir.is_dir():
        project_files = [
            p for p in env_dir.rglob("*")
            if p.is_file()
            and p.name not in {"Dockerfile", "docker-compose.yaml", "docker-compose.yml"}
        ]
        if not project_files:
            warn(
                "environment/ ships nothing but the Dockerfile - the agent lands in an empty "
                "container. If the task's difficulty depends on exploring a project "
                "(docs/DIFFICULTY.md, Prong B), the project tree must live under environment/ "
                "and be copied into the image"
            )


# --------------------------------------------------------------------------- task.toml


def check_task_toml(root: Path) -> dict:
    path = root / "task.toml"
    raw = read(path)
    if raw is None:
        return {}

    # Match a real key assignment, not a mention inside a comment.
    for line in raw.splitlines():
        if re.match(r"\s*allow_internet\s*=", line.split("#", 1)[0]):
            error("task.toml: allow_internet must never be set - open internet is the default policy")
            break

    try:
        cfg = tomllib.loads(raw)
    except tomllib.TOMLDecodeError as exc:
        error(f"task.toml: could not parse ({exc})")
        return {}

    artifacts = cfg.get("artifacts")
    if not artifacts:
        error("task.toml: `artifacts` is empty - declare every path the verifier reads")
    else:
        for art in artifacts:
            if not str(art).startswith("/"):
                error(f"task.toml: artifact path must be absolute: {art}")

    name = cfg.get("task", {}).get("name", "")
    check_slug(name)
    check_metadata(cfg.get("metadata", {}))

    verifier = cfg.get("verifier", {})
    if verifier.get("environment_mode") != "separate":
        error('task.toml: [verifier] environment_mode must be "separate"')
    check_timeout(verifier.get("timeout_sec"), "[verifier] timeout_sec")
    check_timeout(cfg.get("agent", {}).get("timeout_sec"), "[agent] timeout_sec")

    check_environment(cfg.get("environment", {}))
    return cfg


def check_slug(name: str) -> None:
    if not name:
        error("task.toml: [task] name is missing")
        return
    if "/" not in name:
        error(f"task.toml: [task] name must be `afterquery/<slug>`, got {name!r}")
        return
    org, _, slug = name.partition("/")
    if org != "afterquery":
        warn(f"task.toml: [task] name org is {org!r}, expected 'afterquery'")
    if any(m.lower() in slug.lower() for m in TODO_MARKERS):
        error(f"task.toml: [task] name still contains a placeholder: {slug!r}")
        return
    if slug != slug.lower():
        error(f"task.toml: slug must be lowercase: {slug!r}")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
        error(f"task.toml: slug must be lowercase words separated by single hyphens: {slug!r}")
    if len(slug.split("-")) > 3:
        error(f"task.toml: slug must be at most 3 hyphen-separated words: {slug!r}")


def check_metadata(md: dict) -> None:
    required_text = [
        "author_name",
        "author_email",
        "difficulty_explanation",
        "solution_explanation",
        "verification_explanation",
        "relevant_experience",
    ]
    for field in required_text:
        value = str(md.get(field, "")).strip()
        if not value:
            error(f"task.toml: [metadata] {field} is empty")
        elif any(m in value for m in TODO_MARKERS):
            error(f"task.toml: [metadata] {field} still contains a placeholder")

    category = str(md.get("category", "")).strip()
    if category.lower() not in CATEGORIES:
        error(
            f"task.toml: [metadata] category must be one of "
            f"Science, Software, ML, Operations, Security, Hardware, Media (got {category!r})"
        )

    check_subcategory(category, md)
    check_tags(category, md)

    hours = md.get("expert_time_estimate_hours")
    if not isinstance(hours, (int, float)) or hours <= 0:
        error("task.toml: [metadata] expert_time_estimate_hours must be greater than 0")
    elif hours < 2:
        warn(
            f"task.toml: expert_time_estimate_hours is {hours} - tasks under ~2 expert hours "
            "usually fall below the difficulty bar"
        )

    if "expert_time_estimate_min" in md:
        warn(
            "task.toml: expert_time_estimate_min is the harbor scaffolder's field; Frontier "
            "Bench expects expert_time_estimate_hours"
        )


def check_subcategory(category: str, md: dict) -> None:
    sub = str(md.get("subcategory", "")).strip()
    if not sub:
        error("task.toml: [metadata] subcategory is empty")
        return
    if any(m in sub for m in TODO_MARKERS):
        error("task.toml: [metadata] subcategory still contains a placeholder")
        return
    valid = SUBCATEGORIES.get(category.lower())
    if valid is None:
        return  # category already reported as invalid
    if norm_label(sub) not in {norm_label(v) for v in valid}:
        error(
            f"task.toml: [metadata] subcategory {sub!r} is not a label of category "
            f"{category!r} - choose one of: {', '.join(valid)}"
        )


def check_tags(category: str, md: dict) -> None:
    """`tags` must describe THIS task specifically, not restate the taxonomy.

    The platform's quality review fails a task with a blocking error when tags merely
    repeat the subcategory (e.g. category=Science, subcategory=Math, tags=["Math"]).
    """
    tags = md.get("tags") or []
    if not 1 <= len(tags) <= 6:
        error(f"task.toml: [metadata] tags must contain 1-6 labels (got {len(tags)})")
        if not tags:
            return

    sub = str(md.get("subcategory", "")).strip()
    taxonomy = {norm_label(category), norm_label(sub)} - {""}
    for tag in tags:
        if norm_label(tag) in taxonomy:
            error(
                f"task.toml: [metadata] tag {str(tag)!r} just restates the category or "
                "subcategory - tags must name the specific techniques, tools and concepts "
                'this task involves (e.g. ["algebraic-geometry", "resultants", '
                '"exact-arithmetic", "real-root-isolation", "sympy"]), which the quality '
                "review checks as a blocking criterion"
            )

    if len(tags) < 3:
        warn(
            f"task.toml: [metadata] only {len(tags)} tag(s) - the quality review blocks tags that "
            "are too generic; list the specific methods, libraries and concepts of this task"
        )


def check_timeout(value, label: str) -> None:
    if value is None:
        error(f"task.toml: {label} is missing")
    elif value > MAX_TIMEOUT_SEC:
        error(f"task.toml: {label} is {value}, max is {MAX_TIMEOUT_SEC}")


def check_environment(env: dict) -> None:
    for key, cap in (("cpus", MAX_CPUS), ("memory_mb", MAX_MEMORY_MB), ("storage_mb", MAX_STORAGE_MB)):
        value = env.get(key)
        if value is None:
            error(f"task.toml: [environment] {key} is missing")
        elif value > cap:
            error(f"task.toml: [environment] {key} is {value}, max is {cap}")

    check_timeout(env.get("build_timeout_sec"), "[environment] build_timeout_sec")

    gpus = env.get("gpus")
    if gpus is None:
        error("task.toml: [environment] gpus is missing (use 0 unless a GPU is genuinely needed)")
    elif gpus == 1 and env.get("gpu_types") != ["H100"]:
        error('task.toml: with gpus = 1 you must set gpu_types = ["H100"]')
    elif isinstance(gpus, int) and gpus > 1:
        error(f"task.toml: [environment] gpus is {gpus}; only 0 or 1 is allowed")


# ------------------------------------------------------------------------ instruction


def check_instruction(root: Path, cfg: dict) -> None:
    path = root / "instruction.md"
    text = read(path)
    if text is None:
        return

    if "<!--" in text:
        error("instruction.md: template comment block is still present - delete it")
    for marker in TODO_MARKERS:
        if marker in text:
            error(f"instruction.md: still contains a placeholder ({marker})")
            break

    # Plain ASCII only. Typographic unicode (em dashes, curly quotes, ellipses, arrows) is
    # the clearest machine-text tell and has no place in an expert's plain brief.
    offenders: dict[str, int] = {}
    for ch in text:
        if ord(ch) > 127:
            offenders[ch] = offenders.get(ch, 0) + 1
    for ch, count in sorted(offenders.items(), key=lambda kv: -kv[1])[:8]:
        try:
            char_name = unicodedata.name(ch)
        except ValueError:
            char_name = f"U+{ord(ch):04X}"
        error(
            f"instruction.md: non-ASCII character U+{ord(ch):04X} ({char_name}) appears {count}x "
            "- write in plain ASCII: straight quotes, hyphens, three dots; typographic unicode "
            "is a machine-text tell"
        )
    if len(offenders) > 8:
        error(f"instruction.md: ...and {len(offenders) - 8} more distinct non-ASCII characters")

    if re.search(r"^\s*#{1,6}\s", text, re.MULTILINE) or "**" in text:
        warn(
            "instruction.md: markdown headings/bold read as machine-drafted formatting on a "
            "short instruction - prefer plain prose unless the contributor chose them"
        )

    if text.endswith("\n\n"):
        error("instruction.md: more than one trailing newline after the required suffix")
    if not text.endswith("\n"):
        warn("instruction.md: should end with exactly one newline")

    body = text.rstrip("\n")
    lines = body.split("\n")
    match = SUFFIX_RE.search(lines[-1].strip()) if lines else None
    if not match:
        error(
            "instruction.md: must end with the exact required suffix:\n"
            "        You have N seconds to complete this task. Do not cheat by using "
            "online solutions or hints specific to this task."
        )
    else:
        if len(lines) < 2 or lines[-2].strip() != "":
            error("instruction.md: the required suffix must be preceded by a blank line")
        declared = int(match.group(1))
        agent_timeout = cfg.get("agent", {}).get("timeout_sec")
        if agent_timeout is not None and declared != int(agent_timeout):
            error(
                f"instruction.md: suffix says {declared} seconds but task.toml "
                f"[agent] timeout_sec is {int(agent_timeout)} - they must match"
            )

    prose = "\n".join(lines[:-1]).rstrip() if match else body
    if len(prose.split()) < 60:
        warn(
            "instruction.md: the instruction is very short - make sure an expert could start "
            "work without asking a clarifying question"
        )
    if not re.search(r"(?<![\w./])/(app|workdir|data|home|opt|srv|tmp|var)\b", prose):
        warn("instruction.md: no absolute path found - output locations must be absolute")
    if re.search(r"(?<![\w])\./|(?<![\w])~/", prose):
        error("instruction.md: contains a relative or ~ path - use absolute paths such as /app/output.json")


# ---------------------------------------------------------------- scripts and images


PIP_INSTALL_RE = re.compile(r"(?:uv\s+)?pip\s+install\b([^\n]*)", re.IGNORECASE)
UVX_WITH_RE = re.compile(r"--with\s+(\S+)")
OPTION_RE = re.compile(r"^-")


def strip_comments(text: str) -> str:
    """Drop shell/Dockerfile comments so prose in comments never trips command scanners."""
    return "\n".join(re.sub(r"(^|\s)#.*$", r"\1", line) for line in text.splitlines())


def check_pins(path: Path, text: str) -> None:
    text = strip_comments(text)
    for match in PIP_INSTALL_RE.finditer(text):
        tail = match.group(1)
        if "-r" in tail or "requirements" in tail:
            warn(f"{path.name}: pip install from a requirements file - pin every package there with ==")
            continue
        for token in tail.replace("\\", " ").split():
            if OPTION_RE.match(token) or token in {"install", "pip", "uv"}:
                continue
            if "==" not in token:
                error(f"{path.name}: Python package must be pinned with ==: {token!r}")
    for match in UVX_WITH_RE.finditer(text):
        token = match.group(1)
        if "==" not in token:
            error(f"{path.name}: --with package must be pinned with ==: {token!r}")


# The platform's structural check requires the canonical verifier toolchain versions
# wherever these packages are pinned, in any scanned file.
CANONICAL_PYTEST = "9.1.1"
CANONICAL_CTRF = "0.5.2"
CANONICAL_PIN_RE = re.compile(r"(pytest[-_]json[-_]ctrf|pytest)\s*==\s*([\w.\-]+)")


def check_canonical_pins(path: Path, text: str) -> None:
    text = strip_comments(text)
    for match in CANONICAL_PIN_RE.finditer(text):
        name, ver = match.group(1), match.group(2)
        if name == "pytest" and ver != CANONICAL_PYTEST:
            error(
                f"{path.name}: pytest is pinned to {ver} - every Frontier Bench verifier uses "
                f"the canonical pytest=={CANONICAL_PYTEST}; change the pin to that exact version"
            )
        elif name != "pytest" and ver != CANONICAL_CTRF:
            warn(
                f"{path.name}: pytest-json-ctrf is pinned to {ver} - the canonical verifier "
                f"pin is pytest-json-ctrf=={CANONICAL_CTRF}"
            )


APT_PIN_RE = re.compile(r"apt(?:-get)?\s+install\b([^\n]*)")


def check_apt(path: Path, text: str) -> None:
    text = strip_comments(text)
    for match in APT_PIN_RE.finditer(text):
        for token in match.group(1).replace("\\", " ").split():
            if OPTION_RE.match(token):
                continue
            if "=" in token:
                error(f"{path.name}: apt packages must not be version-pinned: {token!r}")


def check_scripts(root: Path) -> None:
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix != ".sh" and path.name != "Dockerfile":
            continue
        raw = path.read_bytes()
        if path.suffix == ".sh" or path.name == "Dockerfile":
            if b"\r\n" in raw:
                error(
                    f"{path.relative_to(root)}: has CRLF line endings - this breaks execution "
                    "inside Linux containers; convert to LF"
                )
        if path.suffix == ".sh":
            text = raw.decode("utf-8", errors="replace")
            if not text.startswith("#!"):
                error(f"{path.relative_to(root)}: missing a shebang line (e.g. #!/bin/bash)")
            check_pins(path, text)
            check_apt(path, text)
            check_canonical_pins(path, text)

    env_dockerfile = root / "environment" / "Dockerfile"
    text = read(env_dockerfile)
    if text is not None:
        check_pins(env_dockerfile, text)
        check_apt(env_dockerfile, text)
        check_canonical_pins(env_dockerfile, text)
        check_platform_pins(env_dockerfile, text)
        check_leaks(text)

    tests_dockerfile = root / "tests" / "Dockerfile"
    text = read(tests_dockerfile)
    if text is not None:
        check_pins(tests_dockerfile, text)
        check_apt(tests_dockerfile, text)
        check_canonical_pins(tests_dockerfile, text)
        check_platform_pins(tests_dockerfile, text)
        if not re.search(r"^\s*COPY\s+.*/tests/?\s*$", text, re.MULTILINE):
            warn(
                "tests/Dockerfile: no COPY into /tests found — in separate-verifier mode the "
                "harness does not upload tests/; the image must bake them in (e.g. `COPY . /tests/`)"
            )


def check_platform_pins(path: Path, text: str) -> None:
    for line in text.splitlines():
        stripped = line.split("#", 1)[0].strip()
        if re.match(r"FROM\s+--platform", stripped, re.IGNORECASE):
            error(f"{path.name}: FROM --platform= pins are not allowed: {stripped!r}")


DOC_FILE_RE = re.compile(r"^(readme|changelog|contributing|authors|history|hacking|faq)\b", re.IGNORECASE)
LEGAL_FILE_RE = re.compile(r"^(license|copying|notice|patents)\b", re.IGNORECASE)
CODE_EXTS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java", ".c", ".cc", ".cpp", ".h", ".hpp",
    ".rs", ".rb", ".sh", ".pl", ".php", ".cs", ".swift", ".kt", ".scala", ".lua",
}
COMMENT_PREFIXES = ("#", "//", "/*", "*", "--", ";;")
LEGAL_MARKERS = ("copyright", "license", "spdx", "(c)")
DIRECTIVE_MARKERS = (
    "noqa", "type:", "coding:", "pylint", "eslint", "pragma", "fmt:", "nolint",
    "prettier", "shellcheck", "ruff", "mypy", "isort", "flake8", "!/",
)
DEF_RE = re.compile(r"^\s*(def |class |async def ).*:\s*$")


def prose_comment_lines(path: Path, text: str) -> int:
    """Count comment/docstring lines that read as prose (>= 4 words), skipping legal
    notices and machine-read directives."""
    count = 0
    prev_code_line = ""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        low = stripped.lower()
        is_comment = stripped.startswith(COMMENT_PREFIXES)
        if is_comment:
            if any(m in low for m in LEGAL_MARKERS) or any(m in low for m in DIRECTIVE_MARKERS):
                prev_code_line = prev_code_line  # legal/directive: ignore entirely
            else:
                body = stripped.lstrip("#/*;- \t")
                if len(body.split()) >= 4:
                    count += 1
            continue
        if path.suffix == ".py" and stripped.startswith(('"""', "'''")):
            first_nonblank = next((l.strip() for l in lines if l.strip()), "")
            if DEF_RE.match(prev_code_line) or stripped == first_nonblank:
                count += 1
        prev_code_line = line
    return count


def check_environment_docs(root: Path) -> None:
    """Strict rule: the agent-facing tree ships with no documentation.

    Doc files (README etc.) and prose comments/docstrings in code are errors. Exceptions:
    legal notices, machine-read directives, Dockerfile/compose (not shipped into the image).
    """
    env = root / "environment"
    if not env.is_dir():
        return
    doc_files: list[str] = []
    commented: list[tuple[str, int]] = []
    for path in sorted(env.rglob("*")):
        if not path.is_file():
            continue
        if path.name in {"Dockerfile", "docker-compose.yaml", "docker-compose.yml"}:
            continue
        rel = str(path.relative_to(root)).replace("\\", "/")
        stem = path.name
        in_docs_dir = any(part.lower() in {"docs", "doc"} for part in path.relative_to(env).parts[:-1])
        # .md files are banned outright in the agent environment - no exceptions, not even
        # legal files or data; the ban is by extension, before any other rule applies.
        if path.suffix.lower() == ".md":
            doc_files.append(rel)
            continue
        if LEGAL_FILE_RE.match(stem):
            continue
        if in_docs_dir or DOC_FILE_RE.match(stem):
            doc_files.append(rel)
            continue
        if path.suffix in CODE_EXTS:
            text = path.read_bytes().decode("utf-8", errors="replace")
            n = prose_comment_lines(path, text)
            if n:
                commented.append((rel, n))

    for rel in doc_files[:8]:
        error(
            f"{rel}: documentation in the agent environment - strict rule: .md files are banned "
            "outright (any name, even as data), and README-like files and docs/ directories in "
            "any format. If a small part is genuinely indispensable, it moves into "
            "instruction.md via the contributor - reluctantly - or the data is reshaped into a "
            "non-document format; otherwise delete it"
        )
    if len(doc_files) > 8:
        error(f"...and {len(doc_files) - 8} more documentation files under environment/")
    for rel, n in commented[:8]:
        error(
            f"{rel}: {n} prose comment/docstring line(s) in the agent environment - strict rule: "
            "strip comments, docstrings and explanatory notes; the code explains itself through "
            "structure and behavior (legal notices and directives like `# noqa` are exempt)"
        )
    if len(commented) > 8:
        error(f"...and {len(commented) - 8} more environment files with prose comments")


def check_artifact_parents(root: Path, cfg: dict) -> None:
    """The verifier image must create the parent directory of every declared artifact.

    The harness uploads the agent's artifacts into the verifier container at their original
    absolute paths and fails with "Could not find the file ... in container" when the parent
    directory does not exist there.
    """
    artifacts = cfg.get("artifacts") or []
    text = read(root / "tests" / "Dockerfile")
    if text is None or not artifacts:
        return
    body = "\n".join(line.split("#", 1)[0] for line in text.splitlines())
    for art in artifacts:
        art = str(art)
        if not art.startswith("/"):
            continue  # non-absolute paths are flagged elsewhere
        parent = str(PurePosixPath(art).parent)
        if parent in ("/", ""):
            continue
        # `mkdir -p /app/data` and `WORKDIR /app/data` also create /app, so match the
        # parent as a path prefix in any mkdir or WORKDIR instruction.
        escaped = re.escape(parent)
        created = re.search(
            rf"(mkdir\s[^\n]*{escaped}(?=[\s/]|$))|(^\s*WORKDIR\s+{escaped}(?=[\s/]|$))",
            body,
            re.MULTILINE,
        )
        if not created:
            error(
                f'tests/Dockerfile: never creates {parent} - add "RUN mkdir -p {parent}" so the '
                f"harness can upload the declared artifact(s) into it (otherwise verification "
                f'fails with "Could not find the file {parent} in container")'
            )


def check_compose(root: Path, cfg: dict) -> None:
    compose = root / "environment" / "docker-compose.yaml"
    if not compose.is_file():
        compose = root / "environment" / "docker-compose.yml"
        if not compose.is_file():
            return

    if cfg.get("environment", {}).get("gpus") == 1:
        error(f"{compose.name}: a GPU task cannot use docker-compose (the GPU does not reach containers started inside the environment)")

    text = read(compose)
    if text is None:
        return
    # Host bind mounts fail validation; only named volumes are allowed.
    for line in text.splitlines():
        stripped = line.split("#", 1)[0].strip()
        if re.match(r"-\s*(\.{1,2}/|/|[A-Za-z]:[\\/]).*:", stripped):
            error(
                f"{compose.name}: host bind mount is not allowed, use named volumes only: {stripped!r}"
            )


def check_leaks(dockerfile_text: str) -> None:
    for line in dockerfile_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if re.match(r"(COPY|ADD)\b", stripped) and re.search(r"\b(tests?|solution|cheat)\b", stripped):
            error(
                "environment/Dockerfile: appears to copy tests/, solution/, or cheat/ into the "
                f"agent image - the answer must never be reachable by the agent: {stripped!r}"
            )


# Commands that reach the network or install software - banned at trial time in the verifier.
TRIAL_TIME_FETCH_RE = re.compile(
    r"\b(curl|wget|pip3?\s+install|apt-get\s+install|apt\s+install|uvx|uv\s+(?:pip|tool)|"
    r"npm\s+install|git\s+clone|pipx)\b"
)

# Terms the platform blocks anywhere in the bundle. The org prefix in [task] name is the
# single permitted occurrence, so task.toml is exempt from this scan.
BLOCKED_TERMS = ("afterquery",)
BLOCKED_SCAN_EXEMPT = {"task.toml", "STATE.md"}  # STATE.md never ships in the zip


def check_verifier_selfcontained(root: Path) -> None:
    """The verifier image must be sealed at build time; test.sh must not fetch or install."""
    text = read(root / "tests" / "test.sh")
    if text is None:
        return
    for lineno, line in enumerate(text.splitlines(), 1):
        code = line.split("#", 1)[0]
        match = TRIAL_TIME_FETCH_RE.search(code)
        if match:
            error(
                f"tests/test.sh:{lineno}: '{match.group(0)}' at trial time - the verifier must "
                "be self-contained: bake every dependency and tool into tests/Dockerfile where "
                "the fetch is pinned and sealed; network access or installs during verification "
                "are a blocking platform error"
            )


def check_blocked_terms(root: Path) -> None:
    """Blocked internal terms must appear nowhere in the bundle except task.toml's org name.

    Scans exactly the set of files that ship (`shipped_files`), so the scanner can never
    skip a path the packager includes.
    """
    hits: list[str] = []
    for path in shipped_files(root):
        rel = "/".join(path.relative_to(root).parts)
        if rel in BLOCKED_SCAN_EXEMPT:
            continue
        try:
            text = path.read_bytes().decode("utf-8", errors="strict").lower()
        except UnicodeDecodeError:
            continue  # binary
        for term in BLOCKED_TERMS:
            if term in text:
                hits.append(f"{rel} ({term})")
                break
    for hit in hits[:8]:
        error(
            f"{hit}: blocked internal term in the bundle - the platform rejects it anywhere "
            "except the [task] name in task.toml; remove every other occurrence"
        )
    if len(hits) > 8:
        error(f"...and {len(hits) - 8} more files containing blocked terms")


# Primitives that mean the verifier runs code that could be the agent's.
EXEC_PRIMITIVES_RE = re.compile(
    r"\b(importlib|__import__|runpy|\bexec\s*\(|\beval\s*\(|subprocess|Popen|os\.system|"
    r"os\.exec|pty\.spawn|runpy\.run_path)\b"
)
# Tokens that indicate a privilege drop is in place.
PRIVDROP_RE = re.compile(r"\b(setpriv|runuser|gosu|su\s+-|--reuid|--regid|drop_privileges|seteuid|setuid)\b")


def check_verifier_isolation(root: Path, cfg: dict) -> None:
    """When the verifier executes agent code, the reward channel becomes attackable.

    This cannot be certified by a linter - it warns on the pattern and points at the
    hardening checklist. The proof of safety is the reward-tamper cheats scoring 0.
    """
    test_sh = read(root / "tests" / "test.sh") or ""
    py_text = ""
    tests_dir = root / "tests"
    if tests_dir.is_dir():
        for p in sorted(tests_dir.rglob("*.py")):
            py_text += "\n" + (p.read_bytes().decode("utf-8", errors="replace"))

    verifier_blob = strip_comments(test_sh) + "\n" + strip_comments(py_text)
    executes = bool(EXEC_PRIMITIVES_RE.search(verifier_blob))
    if not executes:
        return  # static-artifact verifier - the safe, default case

    warn(
        "the verifier appears to execute agent code (import/exec/subprocess in tests/) - this "
        "opens the reward-tamper vector; follow docs/VERIFIER-ISOLATION.md and add the "
        "reward-tamper cheats (background rewrite, verdict planting, grader-crash) - all must score 0"
    )

    # Absent-hardening smells: warnings only, since detection is heuristic.
    verifier_user = str(cfg.get("verifier", {}).get("user", "")).strip()
    if not verifier_user and not PRIVDROP_RE.search(verifier_blob):
        warn(
            "verifier executes agent code but no privilege drop found (setpriv/runuser/gosu or "
            "[verifier].user) - agent code should run as a non-root uid (VERIFIER-ISOLATION.md rule 1)"
        )
    if not re.search(r"chmod\s+7[05]0\s+[^\n]*/logs/verifier", test_sh) and \
       not re.search(r"chmod\s+700", test_sh):
        warn(
            "verifier executes agent code but /logs/verifier is not locked down (no `chmod 700`) - "
            "a backgrounded agent process can rewrite reward.txt (VERIFIER-ISOLATION.md rule 3)"
        )
    if test_sh and not re.search(r"set\s+-[a-z]*e", test_sh):
        warn(
            "tests/test.sh executes agent code without `set -e` - an unchecked grader crash can "
            "leave a planted verdict in place (VERIFIER-ISOLATION.md rule 5)"
        )


# The difficulty strategy is the gate that decides acceptance, and it is the one thing no
# other check can see. These STATE.md fields force the assistant to articulate it; an empty
# answer here means the task was built without the strategy, whatever the bundle looks like.
STATE_REQUIRED = [
    ("one-shot the plan", "why a frontier agent cannot one-shot the plan (the strategic answer)"),
    ("Tactics making that true", "which tactics from docs/DIFFICULTY.md make that true"),
    ("attack on the plan", "your own attack on the plan - your first plan, and where it is wrong"),
    ("Estimated solves out of 8", "the estimated solves out of 8"),
]
TACTIC_RE = re.compile(r"\b([ABC])[1-4]\b|prong\s+([ABC])\b", re.IGNORECASE)


def field_value(text: str, needle: str) -> str | None:
    """Return the value written after `needle:` on its line, or None if the line is absent."""
    for line in text.splitlines():
        if needle.lower() in line.lower():
            _, _, value = line.partition(":")
            # Handle the template's "(...)" hint before the colon.
            return value.strip().strip("*_ ")
    return None


def check_state_difficulty(root: Path) -> None:
    """Force the difficulty strategy to be articulated before a bundle can pass or package."""
    path = root / "STATE.md"
    text = read(path)
    if text is None:
        error(
            "STATE.md is missing - copy template/task-template/STATE.md into the task folder and "
            "fill in the difficulty section. It records why a frontier agent cannot one-shot the "
            "plan, and it is how the difficulty strategy stays accountable (it never ships in the zip)"
        )
        return

    for needle, described in STATE_REQUIRED:
        value = field_value(text, needle)
        if value is None:
            error(f"STATE.md: no line recording {described} - see template/task-template/STATE.md")
            continue
        stripped = value.strip()
        if not stripped or any(m in stripped for m in TODO_MARKERS) or len(stripped.split()) < 3:
            error(
                f"STATE.md: {described} is unanswered - a task whose difficulty strategy was "
                "never articulated lands outside the 1-6 band; see docs/DIFFICULTY.md"
            )

    tactics_line = field_value(text, "Tactics making that true") or ""
    prongs = {(m.group(1) or m.group(2)).upper() for m in TACTIC_RE.finditer(tactics_line)}
    if tactics_line and not any(m in tactics_line for m in TODO_MARKERS):
        if not prongs:
            error(
                "STATE.md: the tactics line names no tactic from docs/DIFFICULTY.md - name them "
                "explicitly (A1-A3 poison the default plan, B1-B2 withhold it, C1-C4 make the "
                "wrong plan fatal), so the design can be audited against what was built"
            )
        elif len(prongs) < 2:
            warn(
                f"STATE.md: tactics come from one prong only ({', '.join(sorted(prongs))}) - a task "
                "carried by a single tactic is fragile; aim for several across at least two prongs"
            )


def check_verifier(root: Path) -> None:
    text = read(root / "tests" / "test.sh")
    if text is None:
        return
    if "/logs/verifier/reward.txt" not in text:
        error("tests/test.sh: must write the score to /logs/verifier/reward.txt")
    if "ctrf" not in text.lower():
        warn("tests/test.sh: no CTRF report found - the verifier should emit /logs/verifier/ctrf.json")
    if not re.search(r"echo\s+1\s*>", text) or not re.search(r"echo\s+0\s*>", text):
        warn("tests/test.sh: could not confirm it writes both 1 and 0 - reward must be binary")


# --------------------------------------------------------------------------- reporting

# Findings are reported cheapest-to-fix first, so the list reads as a to-do list: fill in
# fields, then edit text, then create files, then touch code and rebuild, and last the
# difficulty design, which is the one that may send you back to the drawing board.
FIX_ORDER = (
    (re.compile(r"^task\.toml: \[metadata\]"), 0),   # fill in a field
    (re.compile(r"^task\.toml:"), 1),                # change a config value
    (re.compile(r"^instruction\.md:"), 2),           # edit prose
    (re.compile(r"^missing required file"), 3),      # create a file
    (re.compile(r"^STATE\.md"), 5),                  # articulate (or redesign) the strategy
)
DEFAULT_FIX_TIER = 4                                 # code, environment, verifier: edit and rebuild


def fix_tier(msg: str) -> int:
    for pattern, tier in FIX_ORDER:
        if pattern.match(msg):
            return tier
    return DEFAULT_FIX_TIER


def ordered(messages: list[str]) -> list[str]:
    """Sort findings by how much work they take to fix (stable within each tier)."""
    return sorted(messages, key=fix_tier)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2

    root = Path(argv[1]).resolve()
    if not root.is_dir():
        print(f"not a directory: {root}")
        return 2

    check_structure(root)
    cfg = check_task_toml(root)
    check_instruction(root, cfg)
    check_scripts(root)
    check_environment_docs(root)
    check_artifact_parents(root, cfg)
    check_compose(root, cfg)
    check_verifier(root)
    check_state_difficulty(root)
    check_verifier_isolation(root, cfg)
    check_verifier_selfcontained(root)
    check_blocked_terms(root)

    print(f"Pre-flight check: {root}\n")
    for msg in ordered(warnings):
        print(f"  WARN   {msg}")
    for msg in ordered(errors):
        print(f"  ERROR  {msg}")

    print()
    if errors:
        print(f"{len(errors)} error(s), {len(warnings)} warning(s) - fix the errors before submitting.")
        return 1
    if warnings:
        print(f"No errors, {len(warnings)} warning(s) - review them, then validate with harbor.")
    else:
        print("All mechanical checks passed.")
    print(
        "\nThis checks mechanics only. It cannot tell you whether the task is hard enough,\n"
        "original, or genuinely verifiable. Still required:\n"
        "  harbor run -p . -a oracle -e docker   (must score 1)\n"
        "  harbor run -p . -a nop -e docker      (must score 0)\n"
        "  every cheat/ attempt scores 0"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
