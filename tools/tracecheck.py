"""Does every graded assertion trace to a sentence in the instruction?

Reviewers reported on 2026-09-14 a common pattern in human review: instruction files below
contract quality. The rule they gave is the one this checks: every graded assertion must trace
to a sentence in the instruction. Walk the verifier line by line, find the sentence that tells
the agent about each assertion, and where there is none, write it or stop grading it. The
procedure is docs/INSTRUCTION-CONTRACT.md; this is the part of it a script can see.

From the bundle alone (`--bundle` runs only these, before a trace exists):

  artifacts   every declared artifact path is named in the instruction
  limits      every wall clock and memory cap the verifier imposes on the run, and every
              numeric tolerance the test modules compare with, is stated in the instruction

From the walk, written down in authoring/<slug>/trace.md:

  quotes      every citation is still in instruction.md word for word, so a trace cannot go
              stale after an edit or cite a sentence that was never written
  gaps        a row marked NOT STATED, a row still TODO, a row that cites nothing
  coverage    every test function, enumerated case and wrong reading has a row
  sites       every cited file:line exists
  limits      every clock, cap and tolerance has a row naming an independent implementation
              on disk that is not the reference
  shortcuts   at least one degenerate strategy was scored

What no script can see is whether a quoted sentence actually settles the decision it is cited
for. That is a reading, and it is the part review fails.

Usage:
    python tools/tracecheck.py <slug|task-dir>
    python tools/tracecheck.py <slug|task-dir> --bundle      bundle checks only
    python tools/tracecheck.py <slug|task-dir> --skeleton    write a trace to fill in

Exit code 0 when clean, 1 with findings, 2 on bad usage.
"""

import ast
import re
import shlex
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SECTIONS = ("Graded assertions", "Readings", "Shortcuts", "Tolerances")
UNSTATED = "NOT STATED"
PLACEHOLDER = "TODO"
MIN_QUOTE_WORDS = 4

SUFFIX_RE = re.compile(r"^You have \d+ seconds to complete this task\.")
QUOTE_RE = re.compile(r'"([^"\n]+)"')
SITE_RE = re.compile(
    r"(?<![\w/])((?:tests|solution|environment|authoring)/[\w.\-/]*\w\.\w+):(\d+)(?:-(\d+))?")
PATH_RE = re.compile(r"`((?:tests|solution|environment|authoring)/[^`\s:]*)`")
SEPARATOR_RE = re.compile(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
SEGMENT_RE = re.compile(r"\s(?:\|\||&&|\||;)\s")
TIMEOUT_RE = re.compile(r"(?:^|[\s(])timeout\s+(.+)$")
ULIMIT_RE = re.compile(r"(?:^|[\s(])ulimit\s+-([vmdt])\s+(\d+)")
PRLIMIT_RE = re.compile(r"--(as|data|rss|cpu)=(\d+)")
DURATION_RE = re.compile(r"^(\d+(?:\.\d+)?)([smhd]?)$")
VARIABLE_RE = re.compile(r"^\$\{?(\w+)(?::?[-=](\d+[smhd]?))?\}?$")
LIMIT_NAME_RE = re.compile(r"TOL|EPS|SLACK|CEIL|BUDGET|LIMIT|MARGIN|HEADROOM", re.IGNORECASE)

TIMEOUT_VALUE_OPTIONS = {"-s", "--signal", "-k", "--kill-after"}
# A `timeout` in front of these guards the grader's own plumbing, not the submitted run.
GRADER_COMMANDS = {"cat", "tee"}
GRADER_MARKERS = ("pytest", "reap.py")
READING_TABLES = ("READINGS", "OVERRIDES", "EDITS")
MODEL_STEMS = ("model", "oracle")
# tests/pristine/ is the verifier's copy of the agent tree, not verifier code.
SKIP_PARTS = {"pristine", "__pycache__"}
MEMORY_UNITS = ((1, r"(?:KB|KiB|kB|kilobytes?)"), (2, r"(?:MB|MiB|megabytes?)"),
                (3, r"(?:GB|GiB|gigabytes?)"))

findings: list[str] = []
notes: list[str] = []


def finding(message: str) -> None:
    findings.append(message)


def note(message: str) -> None:
    notes.append(message)


def show(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:g}"


def flat(text: str) -> str:
    return " ".join(text.split())


def clip(text: str, width: int = 70) -> str:
    text = flat(text)
    return text if len(text) <= width else text[: width - 3] + "..."


@dataclass
class Limit:
    site: str      # file:line inside the task folder
    kind: str      # "clock" (seconds), "memory" (bytes) or "tolerance"
    value: float
    source: str    # as written, so the trace can quote it back

    def describe(self) -> str:
        if self.kind == "clock":
            return f"a {show(self.value)} s clock"
        if self.kind == "memory":
            return f"a {show(self.value)}-byte memory cap"
        return f"a tolerance of {self.source}"


def unique(limits: list[Limit]) -> list[Limit]:
    seen, out = set(), []
    for limit in limits:
        if (limit.kind, limit.value) not in seen:
            seen.add((limit.kind, limit.value))
            out.append(limit)
    return out


# ------------------------------------------------------------------------------ reading files


def resolve(arg: str) -> Path | None:
    for candidate in (Path(arg), ROOT / "tasks" / arg):
        if (candidate / "task.toml").is_file():
            return candidate.resolve()
    return None


def rel(task: Path, path: Path) -> str:
    return path.relative_to(task).as_posix()


def verifier_files(task: Path, pattern: str) -> list[Path]:
    return sorted(p for p in (task / "tests").rglob(pattern)
                  if not SKIP_PARTS.intersection(p.relative_to(task).parts))


def parse(path: Path) -> tuple[ast.Module | None, str]:
    try:
        source = path.read_text(encoding="utf-8")
        return ast.parse(source, filename=str(path)), source
    except (OSError, UnicodeDecodeError, SyntaxError) as exc:
        note(f"{path.name}: not parsed ({exc.__class__.__name__}) - walk it by hand")
        return None, ""


def load_task(task: Path) -> tuple[list[str], dict]:
    try:
        cfg = tomllib.loads((task / "task.toml").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        finding(f"task.toml could not be read: {exc}")
        return [], {}
    verifier = cfg.get("verifier") if isinstance(cfg.get("verifier"), dict) else {}
    paths = []
    for item in cfg.get("artifacts") or verifier.get("artifacts") or []:
        if isinstance(item, str):
            paths.append(item)
        elif isinstance(item, dict) and isinstance(item.get("path") or item.get("source"), str):
            paths.append(item.get("path") or item.get("source"))
    env = verifier.get("env") if isinstance(verifier.get("env"), dict) else {}
    return paths, env


def instruction_prose(task: Path) -> str | None:
    """The instruction without its required suffix, whose number is the agent budget."""
    try:
        lines = (task / "instruction.md").read_text(encoding="utf-8").rstrip("\n").split("\n")
    except OSError:
        finding("instruction.md could not be read")
        return None
    if lines and SUFFIX_RE.match(lines[-1]):
        lines = lines[:-1]
    return "\n".join(lines)


# ---------------------------------------------------------------------- numbers in the AST


def number(node: ast.AST) -> float | None:
    """A literal number, or constant arithmetic on literals. Nothing is executed."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) \
            and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        inner = number(node.operand)
        if inner is None:
            return None
        return -inner if isinstance(node.op, ast.USub) else inner
    if isinstance(node, ast.BinOp):
        left, right = number(node.left), number(node.right)
        if left is None or right is None:
            return None
        try:
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.FloorDiv):
                return left // right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.Pow) and abs(right) <= 64:
                return left ** right
        except (ZeroDivisionError, OverflowError):
            return None
    return None


def dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{dotted(node.value)}.{node.attr}"
    return ""


def last(name: str) -> str:
    return name.rsplit(".", 1)[-1]


def segment(source: str, node: ast.AST, value: float) -> str:
    return ast.get_source_segment(source, node) or show(value)


# ------------------------------------------------------------------- limits on the graded run


def shell_commands(text: str):
    """(line, command) for each simple command: comments dropped, continuations joined."""
    held, start = [], 0
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = re.sub(r"(^|\s)#.*$", r"\1", raw).rstrip()
        if not held:
            start = lineno
        if line.endswith("\\"):
            held.append(line[:-1].strip())
            continue
        held.append(line.strip())
        joined = " ".join(part for part in held if part)
        held = []
        for command in SEGMENT_RE.split(f" {joined} "):
            if command.strip():
                yield start, command.strip()


def seconds(token: str) -> float | None:
    match = DURATION_RE.match(token)
    if not match:
        return None
    return float(match.group(1)) * {"": 1, "s": 1, "m": 60, "h": 3600, "d": 86400}[match.group(2)]


def shell_values(token: str, text: str, env: dict) -> list[float]:
    """A literal duration, or every literal the script or [verifier.env] assigns the variable."""
    direct = seconds(token)
    if direct is not None:
        return [direct]
    match = VARIABLE_RE.match(token)
    if not match:
        return []
    name, default = match.groups()
    raw = [default] if default else []
    raw += re.findall(
        rf"(?:^|[\s;])(?:export\s+|local\s+|readonly\s+|declare\s+-\w+\s+)?{name}="
        rf"[\"']?(?:\$\{{{name}:?-)?(\d+[smhd]?)", text, re.MULTILINE)
    raw += re.findall(rf"\$\{{{name}:?=(\d+[smhd]?)\}}", text)
    if name in env:
        raw.append(str(env[name]))
    return sorted({value for value in map(seconds, raw) if value is not None})


def timeout_limits(site: str, rest: str, text: str, env: dict) -> list[Limit]:
    try:
        tokens = shlex.split(rest)
    except ValueError:
        tokens = rest.split()
    i = 0
    while i < len(tokens) and tokens[i].startswith("-"):
        i += 2 if tokens[i] in TIMEOUT_VALUE_OPTIONS else 1
    if i >= len(tokens):
        return []
    token, command = tokens[i], tokens[i + 1:]
    if command and (command[0] in GRADER_COMMANDS
                    or any(marker in " ".join(command) for marker in GRADER_MARKERS)):
        return []
    values = shell_values(token, text, env)
    if not values:
        note(f"{site}: the clock {token} is computed at run time - state the budget it enforces")
    return [Limit(site, "clock", value, token) for value in values]


def shell_limits(task: Path, env: dict) -> list[Limit]:
    limits = []
    for path in verifier_files(task, "*.sh"):
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, command in shell_commands(text):
            site = f"{rel(task, path)}:{lineno}"
            match = TIMEOUT_RE.search(command)
            if match:
                limits += timeout_limits(site, match.group(1), text, env)
            for flag, amount in ULIMIT_RE.findall(command):
                if flag == "t":
                    limits.append(Limit(site, "clock", float(amount), amount))
                else:
                    limits.append(Limit(site, "memory", float(amount) * 1024, amount))
            if re.search(r"(?:^|\s)prlimit\s", command):
                for kind, amount in PRLIMIT_RE.findall(command):
                    limits.append(Limit(site, "clock" if kind == "cpu" else "memory",
                                        float(amount), amount))
    return limits


# Calls whose `timeout=` bounds the graded run. `wait` and `join` are left out: the literal
# timeouts on them in the retained supervisors bound the grader's own cleanup after a kill.
CLOCKED_CALLS = {"run", "call", "check_call", "check_output", "communicate"}


def call_limits(site: str, node: ast.Call, source: str, grading: bool) -> list[Limit]:
    out = []
    name = last(dotted(node.func))
    for keyword in node.keywords:
        value = number(keyword.value)
        if keyword.arg == "timeout" and name in CLOCKED_CALLS:
            if value is None:
                note(f"{site}: {name}() runs under a computed timeout - state the budget it enforces")
            else:
                out.append(Limit(site, "clock", value, segment(source, keyword.value, value)))
        if value is None:
            continue
        elif grading and name in ("approx", "isclose") \
                and keyword.arg in ("rel", "abs", "rel_tol", "abs_tol"):
            out.append(Limit(site, "tolerance", value, segment(source, keyword.value, value)))
    if name == "alarm" and node.args and number(node.args[0]):
        value = number(node.args[0])
        out.append(Limit(site, "clock", value, segment(source, node.args[0], value)))
    if name == "setrlimit" and len(node.args) >= 2:
        which = last(dotted(node.args[0]))
        kind = {"RLIMIT_CPU": "clock", "RLIMIT_AS": "memory", "RLIMIT_DATA": "memory",
                "RLIMIT_RSS": "memory"}.get(which)
        bound = node.args[1]
        first = bound.elts[0] if isinstance(bound, (ast.Tuple, ast.List)) and bound.elts else bound
        value = number(first)
        if kind and value is not None and value >= 0:
            out.append(Limit(site, kind, value, segment(source, first, value)))
        elif kind:
            note(f"{site}: {which} is set from a computed value - state the cap it enforces")
    return out


def is_abs(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and dotted(node.func) in ("abs", "fabs", "math.fabs")


def compare_limits(site: str, node: ast.Compare, source: str) -> list[Limit]:
    """abs(got - want) <= tol, written either way round."""
    out = []
    operands = [node.left, *node.comparators]
    for index, op in enumerate(node.ops):
        left, right = operands[index], operands[index + 1]
        if isinstance(op, (ast.Lt, ast.LtE)) and is_abs(left):
            bound = right
        elif isinstance(op, (ast.Gt, ast.GtE)) and is_abs(right):
            bound = left
        else:
            continue
        value = number(bound)
        if value is not None:
            out.append(Limit(site, "tolerance", value, segment(source, bound, value)))
    return out


def python_limits(task: Path) -> tuple[list[Limit], list[tuple[str, str, float]]]:
    limits, constants = [], []
    for path in verifier_files(task, "*.py"):
        tree, source = parse(path)
        if tree is None:
            continue
        where = rel(task, path)
        grading = path.name.startswith("test_") or path.name.endswith("_test.py")
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                limits += call_limits(f"{where}:{node.lineno}", node, source, grading)
            elif grading and isinstance(node, ast.Compare):
                limits += compare_limits(f"{where}:{node.lineno}", node, source)
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                    and isinstance(node.targets[0], ast.Name) \
                    and LIMIT_NAME_RE.search(node.targets[0].id):
                value = number(node.value)
                if value is not None:
                    constants.append((f"{where}:{node.lineno}", node.targets[0].id, value))
    return limits, constants


ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
        "fifteen sixteen seventeen eighteen nineteen").split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def spelled(n: int) -> list[str]:
    """Patterns for an integer below 10000 written out in words. The retained briefs write their
    clocks that way ("killed at six hundred seconds"), and a digits-only match called them unstated."""
    if n < 20:
        return [ONES[n]]
    if n < 100:
        tens, ones = divmod(n, 10)
        return [TENS[tens] + (rf"[\s-]{ONES[ones]}" if ones else "")]
    if n >= 10000:
        return []
    size, word = (100, "hundred") if n < 1000 else (1000, "thousand")
    head, rest = divmod(n, size)
    lead = f"(?:one|an?) {word}" if head == 1 else f"{ONES[head]} {word}"
    return [lead] if not rest else [rf"{lead},?\s(?:and\s)?{tail}" for tail in spelled(rest)]


def stated(limit: Limit, text: str) -> bool:
    """Is the limit written in `text`: a number with its unit, in digits or in words, or a
    tolerance as written?"""
    text = flat(text)
    if limit.kind == "tolerance":
        forms = {limit.source, show(limit.value), repr(limit.value)}
        return any(re.search(rf"(?<![\w.]){re.escape(form)}(?![\w.])", text) for form in forms)
    if limit.kind == "clock":
        forms = [(limit.value, r"(?:seconds?|secs?|s)"), (limit.value / 60, r"minutes?"),
                 (limit.value / 3600, r"hours?")]
    else:
        forms = [(limit.value, r"bytes?")]
        forms += [(limit.value / base ** power, unit)
                  for base in (1024, 1000) for power, unit in MEMORY_UNITS]
    for index, (value, unit) in enumerate(forms):
        whole = float(value).is_integer()
        if index and not whole:
            continue
        written = [re.escape(show(value))]
        if whole:
            written += [f"{int(value):,}", *spelled(int(value))]
        if any(re.search(rf"(?<![\w.]){form}[\s-]*{unit}\b", text, re.IGNORECASE)
               for form in written):
            return True
    return False


# ------------------------------------------------------------------- what the trace must cover


def test_functions(task: Path) -> list[tuple[str, str]]:
    found = []
    for path in verifier_files(task, "*.py"):
        if not (path.name.startswith("test_") or path.name.endswith("_test.py")):
            continue
        tree, _ = parse(path)
        if tree is None:
            continue
        for node in tree.body:
            inner = node.body if isinstance(node, ast.ClassDef) and node.name.startswith("Test") \
                else [node]
            for item in inner:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                        and item.name.startswith("test"):
                    found.append((f"{rel(task, path)}:{item.lineno}", item.name))
    return found


def is_text(node: ast.AST) -> bool:
    parts = list(ast.walk(node))
    return any(isinstance(p, ast.Constant) and isinstance(p.value, str) for p in parts) \
        and not any(isinstance(p, ast.Dict) for p in parts)


def enumerated_cases(task: Path) -> dict[str, str]:
    """Case names from tests/**/cases.py: literal dicts, NAME["x"] = ..., and case("x", ...)."""
    names: dict[str, str] = {}
    for path in verifier_files(task, "cases.py"):
        tree, _ = parse(path)
        if tree is None:
            continue
        where = rel(task, path)
        local = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        for node in tree.body:
            if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
                value = node.value
                if isinstance(value, ast.Dict) and value.keys \
                        and all(isinstance(k, ast.Constant) and isinstance(k.value, str)
                                for k in value.keys) \
                        and all(is_text(v) for v in value.values):
                    for key in value.keys:
                        names.setdefault(key.value, f"{where}:{key.lineno}")
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Constant) \
                            and isinstance(target.slice.value, str):
                        names.setdefault(target.slice.value, f"{where}:{node.lineno}")
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                call = node.value
                if isinstance(call.func, ast.Name) and call.func.id in local and call.args \
                        and isinstance(call.args[0], ast.Constant) \
                        and isinstance(call.args[0].value, str):
                    names.setdefault(call.args[0].value, f"{where}:{node.lineno}")
    return names


def literal_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Dict):
        return [k.value for k in node.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)]
    out = []
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        for element in node.elts:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                out.append(element.value)
            elif isinstance(element, (ast.Tuple, ast.List)) and element.elts \
                    and isinstance(element.elts[0], ast.Constant) \
                    and isinstance(element.elts[0].value, str):
                out.append(element.elts[0].value)
    return out


def wrong_readings(task: Path) -> list[str]:
    """Reading names from authoring/<slug>/readings.py (the task-local copy as a fallback)."""
    for path in (task.parent.parent / "authoring" / task.name / "readings.py",
                 task / "authoring" / "readings.py"):
        if path.is_file():
            break
    else:
        return []
    tree, _ = parse(path)
    if tree is None:
        return []
    tables = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in READING_TABLES:
                    tables[target.id] = literal_names(node.value)
    for table in READING_TABLES:
        if tables.get(table):
            return tables[table]
    note(f"{path.name}: no literal READINGS, OVERRIDES or EDITS table - cite each reading by hand")
    return []


def model_units(task: Path) -> list[tuple[str, str]]:
    units = []
    for path in verifier_files(task, "*.py"):
        if not any(stem in path.stem for stem in MODEL_STEMS):
            continue
        tree, _ = parse(path)
        for node in tree.body if tree else []:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                units.append((f"{rel(task, path)}:{node.lineno}", node.name))
    return units


# ------------------------------------------------------------------------ checking the trace


def trace_sections(text: str) -> dict[str, list[tuple[int, str]]]:
    sections: dict[str, list[tuple[int, str]]] = {}
    current = None
    for lineno, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            heading = line[3:].strip().lower()
            current = next((name for name in SECTIONS if heading.startswith(name.lower())), None)
            if current:
                sections.setdefault(current, [])
        elif current:
            sections[current].append((lineno, line))
    return sections


def table_rows(lines: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Data rows only: the separator and the header above it are dropped."""
    table = [(n, line.strip()) for n, line in lines if line.strip().startswith("|")]
    rows = []
    for index, (lineno, line) in enumerate(table):
        following = table[index + 1] if index + 1 < len(table) else None
        if SEPARATOR_RE.match(line) or (following and following[0] == lineno + 1
                                        and SEPARATOR_RE.match(following[1])):
            continue
        rows.append((lineno, line))
    return rows


def first_cell(line: str) -> str:
    return line.strip().strip("|").split("|", 1)[0].strip()


def citations(line: str) -> list[str]:
    return [q for q in QUOTE_RE.findall(line) if len(q.split()) >= MIN_QUOTE_WORDS]


def mentions(text: str, name: str) -> bool:
    return re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])", text) is not None


def on_disk(task: Path, path: str) -> Path:
    return (task.parent.parent if path.startswith("authoring/") else task) / path


def check_trace(task: Path, prose: str, trace: Path, tests, cases, readings, limits) -> None:
    text = trace.read_text(encoding="utf-8")
    sections = trace_sections(text)
    body = flat(prose)
    for name in SECTIONS:
        if name not in sections:
            finding(f"trace.md has no '## {name}' section")

    for lineno, line in enumerate(text.splitlines(), 1):
        for quote in citations(line):
            if flat(quote) not in body:
                finding(f"trace.md:{lineno}: cites words that are not in instruction.md: "
                        f"\"{clip(quote)}\"")
        for path, start, end in SITE_RE.findall(line):
            target = on_disk(task, path)
            if not target.is_file():
                finding(f"trace.md:{lineno}: cites {path}, which does not exist")
                continue
            count = len(target.read_text(encoding="utf-8", errors="replace").splitlines())
            if max(int(start), int(end or start)) > count:
                finding(f"trace.md:{lineno}: cites {path}:{start}, past its {count} lines")

    graded = sections.get("Graded assertions", [])
    graded_text = "\n".join(line for _, line in graded)
    for lineno, line in table_rows(graded):
        label = clip(first_cell(line))
        if UNSTATED in line:
            finding(f"trace.md:{lineno}: NOT STATED - {label}: write the sentence or stop grading it")
        elif PLACEHOLDER in line:
            finding(f"trace.md:{lineno}: still TODO - {label}")
        elif not citations(line):
            finding(f"trace.md:{lineno}: cites no instruction sentence - {label}")
    for site, name in tests:
        if not mentions(graded_text, name):
            finding(f"{site}: test function {name} has no row under Graded assertions")
    for name, site in cases.items():
        if not mentions(graded_text, name):
            finding(f"{site}: enumerated case {name} has no row under Graded assertions")

    reading_lines = sections.get("Readings", [])
    for lineno, line in table_rows(reading_lines):
        label = clip(first_cell(line))
        if UNSTATED in line or PLACEHOLDER in line:
            finding(f"trace.md:{lineno}: reading {label} is not ruled out yet")
            continue
        published = any(p.startswith("environment/") and on_disk(task, p).exists()
                        for p in PATH_RE.findall(line))
        if not citations(line) and not published:
            finding(f"trace.md:{lineno}: reading {label} cites no sentence or published example "
                    "that rules it out")
        if cases and not any(mentions(line, name) for name in cases):
            finding(f"trace.md:{lineno}: reading {label} names no enumerated case that separates it")
    reading_text = "\n".join(line for _, line in reading_lines)
    for name in readings:
        if not mentions(reading_text, name):
            finding(f"readings.py: wrong reading {name} has no row under Readings")

    shortcut_rows = table_rows(sections.get("Shortcuts", []))
    if "Shortcuts" in sections and not shortcut_rows:
        finding("trace.md: no shortcut strategy was scored")
    for lineno, line in shortcut_rows:
        if PLACEHOLDER in line:
            finding(f"trace.md:{lineno}: shortcut {clip(first_cell(line))} has no result")

    tolerance_rows = table_rows(sections.get("Tolerances", []))
    for lineno, line in tolerance_rows:
        label = clip(first_cell(line))
        if PLACEHOLDER in line:
            finding(f"trace.md:{lineno}: limit {label} is not validated yet")
            continue
        paths = [p for p in PATH_RE.findall(line) if on_disk(task, p).exists()]
        if not paths:
            finding(f"trace.md:{lineno}: limit {label} names no independent implementation on disk")
        elif all(p.startswith("solution/") for p in paths):
            finding(f"trace.md:{lineno}: limit {label} was validated only against the reference")
    tolerance_text = "\n".join(line for _, line in tolerance_rows)
    for limit in unique(limits):
        if not (stated(limit, tolerance_text) or mentions(tolerance_text, limit.source)):
            finding(f"{limit.site}: {limit.describe()} has no row under Tolerances")


def check_bundle(prose: str, artifacts: list[str], limits: list[Limit]) -> None:
    body = flat(prose)
    for path in artifacts:
        if path.rstrip("/") not in body:
            finding(f"task.toml: artifact {path} is collected for grading and never named in "
                    "instruction.md")
    for limit in unique(limits):
        if not stated(limit, prose):
            finding(f"{limit.site}: {limit.describe()} is imposed on the graded run and never "
                    "stated in instruction.md")


# --------------------------------------------------------------------------------- skeleton


def skeleton(task: Path, artifacts, tests, cases, readings, limits, units) -> str:
    slug = task.name
    lines = [
        f"# Instruction trace: {slug}",
        "",
        "Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Cite the",
        "instruction word for word in double quotes, four words or more. Write NOT STATED where it",
        "says nothing, then write the sentence or stop grading it. Split each model row into one",
        f"row per rule it applies, citing its lines. Check with `python tools/tracecheck.py {slug}`.",
        "",
        "## Graded assertions",
        "",
        "| Verifier site | What it grades | Instruction sentence |",
        "|---|---|---|",
    ]
    lines += [f"| `{site}` {name} | TODO | TODO |" for site, name in tests]
    lines += [f"| `{site}` case {name} | TODO | TODO |" for name, site in cases.items()]
    lines += [f"| artifact `{path}` | only the declared files are collected | TODO |"
              for path in artifacts]
    lines += [f"| `{limit.site}` {limit.describe()} | TODO | TODO |" for limit in unique(limits)]
    lines += [f"| `{site}` {name} | TODO: one row per rule it applies | TODO |"
              for site, name in units]
    lines += [
        "",
        "## Readings",
        "",
        "| Reading | Sentence or published example that rules it out | Case that separates it |",
        "|---|---|---|",
    ]
    lines += [f"| {name} | TODO | TODO |" for name in readings] \
        or ["| TODO: each reading a competent solver might try | TODO | TODO |"]
    lines += [
        "",
        "## Shortcuts",
        "",
        "| Strategy | Result |",
        "|---|---|",
        "| the shipped tree unchanged (nop) | TODO |",
        "| constant: the most common value of every graded field | TODO |",
        "| positional: always the first candidate | TODO |",
        "| the worked example's output replayed | TODO |",
        "",
        "## Tolerances",
        "",
        "| Tolerance or limit | Independent implementation | Measured |",
        "|---|---|---|",
    ]
    lines += [f"| `{limit.site}` {limit.describe()} | TODO | TODO |" for limit in unique(limits)]
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------------------------- main


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = {a for a in argv[1:] if a.startswith("--")}
    if len(args) != 1 or flags - {"--bundle", "--skeleton"} or len(flags) > 1:
        print(__doc__.strip())
        return 2
    task = resolve(args[0])
    if task is None:
        print(f"no task.toml under {args[0]} or tasks/{args[0]}")
        return 2

    prose = instruction_prose(task)
    artifacts, env = load_task(task)
    python, constants = python_limits(task)
    limits = shell_limits(task, env) + python
    tests = test_functions(task)
    cases = enumerated_cases(task)
    readings = wrong_readings(task)
    trace = task.parent.parent / "authoring" / task.name / "trace.md"

    if "--skeleton" in flags:
        if trace.exists():
            print(f"{trace} already exists - fill it in, or delete it to start again")
            return 2
        trace.parent.mkdir(parents=True, exist_ok=True)
        with open(trace, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(skeleton(task, artifacts, tests, cases, readings, limits, model_units(task)))
        print(f"wrote {trace}: {len(tests)} test functions, {len(cases)} enumerated cases, "
              f"{len(artifacts)} artifacts, {len(unique(limits))} limits, {len(readings)} readings")
        return 0

    if prose is not None:
        check_bundle(prose, artifacts, limits)
    if "--bundle" not in flags:
        if not trace.is_file():
            finding(f"no trace at authoring/{task.name}/trace.md - run with --skeleton and walk "
                    "the verifier (docs/INSTRUCTION-CONTRACT.md)")
        elif prose is not None:
            check_trace(task, prose, trace, tests, cases, readings, limits)
        if not cases:
            note("no enumerated case names could be read from tests/cases.py - cite them by hand")
    for site, name, value in constants:
        note(f"{site}: {name} = {show(value)} looks like a limit - if it can change a graded "
             "result it needs a sentence and a Tolerances row")

    print(f"tracecheck: {task.name}")
    for message in findings:
        print(f"  FINDING  {message}")
    for message in notes:
        print(f"  note     {message}")
    print()
    if findings:
        print(f"{len(findings)} finding(s) - every graded assertion needs its sentence")
        return 1
    print("clean (bundle checks only)" if "--bundle" in flags else "clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
