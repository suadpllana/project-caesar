#!/usr/bin/env python3
"""Score a task design for difficulty, before a line of code exists.

The 1-7-of-8 band is decided at plan time, and every retained passing task in this
repository has the same shape when its design is written down: a coherent first plan that
is specifically wrong, a second discovery that forces a replan rather than a patch, rules
that change each other's meaning, no shipped oracle, both sides fenced, and an expert path
an author can describe step by step (docs/DIFFICULTY.md, docs/PASSING-TASK-RESEARCH.md).
Ideas that lacked one of those came back 8 of 8, or failed the quality review on
`difficult`, however much code was built on them afterwards.

This tool turns that shape into a number so the comparison happens before the build. It
reads a difficulty record - the ten intake questions of docs/PASSING-TASK-RESEARCH.md plus
the tactics, the leak audit, the fences, the resource gate, the planned cheats and variants,
and the planned tree shape - and scores it out of 100 against a rubric calibrated on the
tasks README.md lists as passed. A new idea must score inside the band those tasks occupy
before environment code is written; below it, the idea is redesigned or replaced, never
padded. When the bundle exists the tree shape is measured rather than read from the record,
so the same command at Stage 7 catches a design that flattened during the build.

What this measures, honestly: whether the design has been articulated with the concrete
parts every passing task has. It reads fields, lengths and counts, not truth. A record can
claim a second discovery that is not one, and the score will not know. The record is a
statement the author signs, `STATE.md` carries the same claims in prose, and the probe is
the authority. Tuning the record to the score instead of tuning the design to the doctrine
produces a number and a rejection.

The record lives at `authoring/<slug>/difficulty.toml`, outside the bundle, so it never
ships. `template/difficulty.toml` documents every field.

The calibration is two-sided. `authoring/controls/` holds records of designs the pipeline
rejected - a task as it stood when the quality review failed it on `difficult`, a build that
came back 3 of 3 on easiness - transcribed from the same state files, and every one of them
has to score below the floor. A rubric change that lifts a control into the band is a rubric
change that would have passed a rejected task, and `--calibrate` fails on it.

Usage:
    python tools/difficultycheck.py <slug>              score authoring/<slug>/difficulty.toml
    python tools/difficultycheck.py <path/to/idea.toml> score a record before a slug exists
    python tools/difficultycheck.py --calibrate         score every task README.md lists as
                                                        passed and every control, print the
                                                        band and check the constants
    python tools/difficultycheck.py --all               score every record under authoring/

Exit code 0 when the score is inside the calibrated band and no hard stop fired, 1
otherwise, 2 on a missing or malformed record.
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The band the retained passing tasks occupy, measured by --calibrate on the date shown.
# BAND_FLOOR is the lowest score among them; a new design must reach it. BAND_CEILING is
# the highest and is informational - nothing above it is penalised, it just says where the
# calibration set stops. Re-run --calibrate and update all three together whenever the
# rubric, a passed task's record, or the README pass list changes.
BAND_FLOOR = 95
BAND_CEILING = 100
BAND_DATE = "2026-09-09"

# Below this the design is not the shape of a passing task at all and the report says so.
# A hard stop caps the score here whatever the other axes add up to.
HARD_STOP_CAP = 40

TACTICS = ("A1", "A2", "A3", "B1", "B2", "C1", "C2", "C3", "C4")
PLAN_SOURCES = ("prior", "search", "instruction", "tree", "examples")
PLACEHOLDERS = ("TODO", "TBD", "FIXME", "???", "<your-", "XXX")

# Vocabulary of difficulty that does not count (docs/DIFFICULTY.md, "What does not create
# difficulty"). A tactic justification built on these is reported, not scored.
SCALE_WORDS = re.compile(
    r"\b(many files|large (repo|repository|tree|codebase)|huge|massive|obscure|"
    r"random(ly)? (named|names)|short timeout|vague|withh(e|o)ld(ing)? context|"
    r"more (cases|episodes|data)|lots of)\b",
    re.I,
)


def words(text) -> int:
    if not isinstance(text, str):
        return 0
    return len(re.findall(r"[A-Za-z0-9_']+", text))


def placeholder(text) -> bool:
    return isinstance(text, str) and any(m in text for m in PLACEHOLDERS)


def jaccard(a: str, b: str) -> float:
    wa = set(re.findall(r"[a-z0-9']+", a.lower()))
    wb = set(re.findall(r"[a-z0-9']+", b.lower()))
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


class Score:
    """Accumulates axis scores, warnings and hard stops for one record."""

    def __init__(self):
        self.axes: list[tuple[str, int, int, list[str]]] = []
        self.warnings: list[str] = []
        self.stops: list[str] = []

    def axis(self, name: str, points: int, maximum: int, notes: list[str]):
        self.axes.append((name, min(points, maximum), maximum, notes))

    def warn(self, msg: str):
        self.warnings.append(msg)

    def stop(self, msg: str):
        self.stops.append(msg)

    @property
    def raw(self) -> int:
        return sum(p for _, p, _, _ in self.axes)

    @property
    def total(self) -> int:
        return min(self.raw, HARD_STOP_CAP) if self.stops else self.raw


# ---------------------------------------------------------------------------
# Bundle measurement. When the task tree exists, the shape is read from it, not from the
# record: "roughly a hundred lines across five files" is the number the quality review
# reads, and it was the one nobody measured (CLAUDE.md, 2026-09-09).

ISOLATION_WORDS = re.compile(
    r"(probe|reward|attest|plant|forge|answer|kill|sweep|privilege|malformed|daemon|"
    r"rewrite|patch|hijack|disarm|crash|shadow|extra-rows|late-reward|garbage|trim|hide|"
    r"rebind|swap|push-rows|read-answers|read-the|read-truth|read-verifier|holds-the-answer|"
    r"tamper|survive|monitor|worker|seal|frozen|image|environment|core|kernel|engine|"
    r"machine|emitter|counter|tally|journal|report|verifier|gt|truth|key)"
)


def measure_bundle(slug: str) -> dict | None:
    task = ROOT / "tasks" / slug
    if not task.is_dir():
        return None
    env_lines = 0
    for p in (task / "environment").rglob("*.py"):
        env_lines += len(p.read_text(encoding="utf-8", errors="replace").splitlines())
    ref_lines = 0
    sol = task / "solution"
    if sol.is_dir():
        for p in sol.rglob("*"):
            if p.is_file() and p.suffix in (".py", ".sh"):
                ref_lines += len(p.read_text(encoding="utf-8", errors="replace").splitlines())
    editable = None
    toml_path = task / "task.toml"
    hours = None
    if toml_path.is_file():
        try:
            data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
            editable = len(data.get("artifacts", []) or [])
            hours = data.get("metadata", {}).get("expert_time_estimate_hours")
        except tomllib.TOMLDecodeError:
            pass
    cheats = sorted(p.name for p in (task / "cheat").glob("*.sh")) if (task / "cheat").is_dir() else []
    semantic = [c for c in cheats if not ISOLATION_WORDS.search(c[len("cheat-"):-3])]
    variants = 0
    for vdir in (task / "authoring" / "variants", ROOT / "authoring" / slug / "variants"):
        if vdir.is_dir():
            variants += sum(1 for d in vdir.iterdir() if d.is_dir())
    return {
        "environment_py_lines": env_lines,
        "reference_lines": ref_lines,
        "editable_files": editable,
        "expert_hours": hours,
        "cheats": len(cheats),
        "semantic_cheats": len(semantic),
        "variants": variants,
    }


# ---------------------------------------------------------------------------
# The rubric. Each axis returns (points, maximum, notes). Notes name what was missing, in
# the vocabulary of the doctrine, so the report reads as a repair list.


def score_plan(rec: dict, s: Score):
    plan = rec.get("plan", {})
    pts, notes = 0, []

    fp = plan.get("first_plan", "")
    if words(fp) >= 25 and not placeholder(fp):
        pts += 4
    else:
        notes.append("first_plan: state the frontier agent's first plan concretely (>= 25 words)")
    src = plan.get("first_plan_source", "")
    if src in PLAN_SOURCES:
        pts += 2
    else:
        notes.append("first_plan_source: one of %s - where the first plan comes from"
                     % ", ".join(PLAN_SOURCES))

    br = plan.get("breaking_rule", "")
    if words(br) >= 15 and not placeholder(br):
        pts += 5
    else:
        notes.append("breaking_rule: the exact stated requirement that makes the first plan "
                     "wrong (>= 15 words)")

    sd = plan.get("second_discovery", "")
    if words(sd) >= 15 and not placeholder(sd):
        if jaccard(br, sd) > 0.6:
            notes.append("second_discovery restates breaking_rule; a task with one discovery "
                         "is patched, not replanned")
            pts += 2
        else:
            pts += 6
    else:
        notes.append("second_discovery: the later finding that invalidates the implementation "
                     "of the first (>= 15 words)")

    effect = plan.get("second_discovery_effect", "")
    if effect == "replan":
        pts += 5
    elif effect == "patch":
        notes.append("second_discovery_effect is 'patch': the second finding adds a case "
                     "instead of invalidating the first implementation - the strongest "
                     "reusable feature of the passing set is absent")
    else:
        notes.append("second_discovery_effect: 'replan' or 'patch'")

    if plan.get("first_plan_correct") is True:
        s.stop("plan.first_plan_correct = true: the very first plan is the correct one, so "
               "the planning attack has already failed (docs/DIFFICULTY.md)")
    elif plan.get("first_plan_correct") is not False:
        notes.append("first_plan_correct: answer it, false or true")

    s.axis("planning attack", pts, 22, notes)


def score_search(rec: dict, s: Score):
    sr = rec.get("search", {})
    pts, notes = 0, []
    if words(sr.get("best_page", "")) >= 10 and not placeholder(sr.get("best_page")):
        pts += 3
    else:
        notes.append("best_page: name the closest public material a probe agent retrieves "
                     "(>= 10 words)")
    if sr.get("helps_plan") is False:
        pts += 3
    elif sr.get("helps_plan") is True:
        s.stop("search.helps_plan = true: the best page substantially plans the task; the "
               "idea is dead regardless of how rare the knowledge felt")
    else:
        notes.append("helps_plan: does the best page help the agent plan? false or true")
    if words(sr.get("deviation", "")) >= 10 and not placeholder(sr.get("deviation")):
        pts += 2
    else:
        notes.append("deviation: where the spec departs from what that page says (>= 10 words)")
    s.axis("search test", pts, 8, notes)


def score_tactics(rec: dict, s: Score):
    tac = rec.get("tactics", {})
    pts, notes = 0, []
    named = []
    for key in TACTICS:
        just = tac.get(key)
        if just is None:
            continue
        if words(just) >= 10 and not placeholder(just):
            named.append(key)
            if SCALE_WORDS.search(just):
                s.warn("tactics.%s rests on scale or obscurity vocabulary (%r); length, size and "
                       "random cases do not move a task into the band"
                       % (key, SCALE_WORDS.search(just).group(0)))
        else:
            notes.append("%s: named but not justified in this task's terms (>= 10 words)" % key)
    pts += 2 * min(len(named), 5)
    prongs = {k[0] for k in named}
    if named and len(prongs) < 2:
        pts //= 2
        notes.append("tactics come from one prong only (%s); a task carried by one prong is "
                     "fragile" % ", ".join(sorted(prongs)))
    if not named:
        notes.append("no tactic from docs/DIFFICULTY.md is named and justified")
    guard = tac.get("guard", "")
    if words(guard) >= 8 and not placeholder(guard):
        pts += 2
    else:
        notes.append("guard: how the route-around is blocked - which files are editable, what "
                     "is hash-checked, what interface is frozen (>= 8 words)")
    s.axis("tactics", pts, 12, notes)


def score_decisions(rec: dict, s: Score):
    dec = rec.get("decisions", {})
    pts, notes = 0, []
    n = dec.get("graded", 0)
    if not isinstance(n, int):
        n = 0
    if n >= 9:
        pts += 6
    elif n >= 6:
        pts += 5
    elif n >= 3:
        pts += 3
    elif n >= 1:
        pts += 1
        notes.append("graded = %d: every passing task grades at least three decisions" % n)
    else:
        notes.append("graded: how many distinct decisions the verifier grades")

    inter = dec.get("interactions", []) or []
    good = 0
    for item in inter:
        if isinstance(item, dict):
            why = item.get("why", "")
            if item.get("a") and item.get("b") and words(why) >= 8 and not placeholder(why):
                good += 1
        elif isinstance(item, (list, tuple)) and len(item) >= 3 and words(item[2]) >= 8:
            good += 1
    if good >= 3:
        pts += 6
    elif good == 2:
        pts += 5
    elif good == 1:
        pts += 3
    else:
        notes.append("interactions: pairs of rules where getting one right changes what right "
                     "means for the other - {a, b, why} with why >= 8 words. Rules that do not "
                     "interact are six easy tasks in a trenchcoat")

    fb = dec.get("per_decision_feedback")
    if fb is False:
        pts += 3
    elif fb is True:
        notes.append("per_decision_feedback = true: the agent confirms rules one at a time, so "
                     "nothing fails late (leak audit item 6)")
    else:
        notes.append("per_decision_feedback: can the agent confirm each rule separately? "
                     "false or true")
    s.axis("rule interaction", pts, 15, notes)


def score_fences(rec: dict, s: Score):
    f = rec.get("fences", {})
    pts, notes = 0, []
    for key, want, need in (("ordinary_case", 3, "the everyday case an overconservative "
                             "solution fails (C1, both sides)"),
                            ("late_case", 4, "the adversarial case where the wrong plan fails "
                             "late, after ordinary cases pass"),
                            ("oracle_denied", 3, "how the agent would check its own work and "
                             "why that check confirms nothing (C2)")):
        val = f.get(key, "")
        if words(val) >= 10 and not placeholder(val):
            pts += want
        else:
            notes.append("%s: %s (>= 10 words)" % (key, need))
    s.axis("fences and late failure", pts, 10, notes)


def score_leaks(rec: dict, s: Score):
    lk = rec.get("leaks", {})
    pts, notes = 0, []
    cands = lk.get("candidates", []) or []
    closed = 0
    for c in cands:
        if isinstance(c, dict) and words(c.get("what", "")) >= 3 \
                and words(c.get("closed_by", "")) >= 5 and not placeholder(c.get("closed_by")):
            closed += 1
    pts += min(closed, 3) * 2
    if closed < 3:
        notes.append("candidates: list at least three things that could reveal a discovery "
                     "(a field, a helper, a sample, a pair of counts) and how each is closed; "
                     "%d closed" % closed)
    dq = lk.get("derived_quantities", "")
    if words(dq) >= 8 and not placeholder(dq):
        pts += 2
    else:
        notes.append("derived_quantities: state which stored values are primitives and that no "
                     "derivation the task is about ships (>= 8 words)")
    if lk.get("oracle_shipped") is False:
        pts += 1
    elif lk.get("oracle_shipped") is True:
        s.stop("leaks.oracle_shipped = true: an artifact that is a function of the correct "
               "trajectory ships to the agent")
    else:
        notes.append("oracle_shipped: false or true")
    s.axis("leak audit", pts, 9, notes)


def score_gate(rec: dict, s: Score):
    g = rec.get("gate", {})
    pts, notes = 0, []
    present = g.get("present")
    if present is True:
        if words(g.get("naive_family", "")) >= 8:
            pts += 1
        else:
            notes.append("naive_family: the correct-but-infeasible method the gate kills (>= 8 words)")
        if words(g.get("invariant", "")) >= 8:
            pts += 2
        else:
            notes.append("invariant: the domain fact the fast path follows from (>= 8 words); a "
                         "gate without one is an undisclosed timeout")
        if g.get("input_scale") and isinstance(g.get("limit_seconds"), (int, float)):
            pts += 2
        else:
            notes.append("input_scale and limit_seconds: both go in the brief")
        if g.get("measured") is not True:
            s.warn("gate.measured is not true: the naive and expert timings are a promise until "
                   "they are run; two of three boundaries on publish-settle-order did not bite "
                   "when measured")
    elif present is False:
        if words(g.get("why_not", "")) >= 8:
            pts += 3
        else:
            notes.append("why_not: why no naive-but-correct family exists to gate (>= 8 words)")
    else:
        notes.append("present: is there a resource gate? true or false")
    s.axis("resource gate", pts, 5, notes)


def score_cheats(rec: dict, s: Score):
    c = rec.get("cheats", {})
    pts, notes = 0, []
    readings = c.get("wrong_readings", []) or []
    good = sum(1 for r in readings if isinstance(r, dict) and words(r.get("reading", "")) >= 3
               and words(r.get("hand_case", "")) >= 5 and not placeholder(r.get("hand_case")))
    if good >= 6:
        pts += 4
    elif good >= 3:
        pts += 2
    elif good >= 1:
        pts += 1
    if good < 6:
        notes.append("wrong_readings: each plausible wrong reading with the hand case that "
                     "separates it; %d complete, passing tasks carry six or more" % good)
    variants = [v for v in (c.get("correct_variants", []) or []) if words(v) >= 3]
    if len(variants) >= 2:
        pts += 2
    elif variants:
        pts += 1
        notes.append("correct_variants: two meaningfully different correct implementations "
                     "prove the verifier grades the contract, not a choice")
    else:
        notes.append("correct_variants: name two meaningfully different correct implementations")
    s.axis("cheats and variants", pts, 6, notes)


def score_solvability(rec: dict, s: Score):
    plan = rec.get("plan", {})
    task = rec.get("task", {})
    pts, notes = 0, []
    steps = [st for st in (plan.get("expert_path", []) or []) if words(st) >= 5]
    if len(steps) >= 5:
        pts += 4
    elif len(steps) >= 3:
        pts += 2
        notes.append("expert_path: %d concrete steps; describe the whole expert path" % len(steps))
    else:
        s.stop("plan.expert_path has fewer than three concrete steps: a design whose expert "
               "path cannot be described is unverifiable, not hard")
    solves = task.get("estimated_solves")
    if isinstance(solves, int) and 1 <= solves <= 3:
        pts += 3
    elif solves == 4:
        pts += 2
    elif isinstance(solves, int) and 5 <= solves <= 7:
        pts += 1
        notes.append("estimated_solves = %d: design for the hard edge; the realized rate "
                     "drifts up" % solves)
    elif solves in (0, 8):
        s.stop("task.estimated_solves = %d is outside the band by the author's own estimate"
               % solves)
    else:
        notes.append("estimated_solves: an integer, out of 8")
    s.axis("solvability", pts, 7, notes)


def score_shape(rec: dict, s: Score, measured: dict | None):
    sh = dict(rec.get("shape", {}))
    task = rec.get("task", {})
    pts, notes = 0, []
    hours = task.get("expert_hours")
    if measured and measured.get("expert_hours") is not None:
        hours = measured["expert_hours"]
    if isinstance(hours, (int, float)) and hours >= 6:
        pts += 2
    elif isinstance(hours, (int, float)) and hours >= 4:
        pts += 1
        notes.append("expert_hours = %s: the passing tasks claim 7 to 12" % hours)
    elif isinstance(hours, (int, float)) and hours < 2:
        s.stop("task.expert_hours = %s: under about two hours the idea is too easy (AGENTS.md "
               "Stage 1)" % hours)
    else:
        notes.append("expert_hours: an honest number, six or more for the passing shape")

    if measured:
        for key in ("environment_py_lines", "reference_lines", "editable_files"):
            declared = sh.get(key)
            actual = measured.get(key)
            if actual is None:
                continue
            if isinstance(declared, (int, float)) and declared and \
                    abs(actual - declared) / max(declared, 1) > 0.35:
                s.warn("shape.%s declared %s, measured %s in tasks/: the built tree drifted from "
                       "the design" % (key, declared, actual))
            sh[key] = actual

    env = sh.get("environment_py_lines")
    if isinstance(env, int) and env >= 200:
        pts += 2
    elif isinstance(env, int) and env >= 120:
        pts += 1
        notes.append("environment_py_lines = %d: the retained band is 229 to 544; a smaller tree "
                     "has failed `difficult` twice" % env)
    else:
        notes.append("environment_py_lines: planned size of the agent-facing Python (retained "
                     "band 229 to 544)")
    ref = sh.get("reference_lines")
    if isinstance(ref, int) and ref >= 100:
        pts += 1
    else:
        notes.append("reference_lines: the graded patch is the number the quality review reads; "
                     "passing tasks are 110 to 424 lines")
    ed = sh.get("editable_files")
    if isinstance(ed, int) and 1 <= ed <= 7:
        pts += 1
    else:
        notes.append("editable_files: how many files the agent may change (passing tasks: 1 to 7)")
    s.axis("shape", pts, 6, notes)


def score_record(rec: dict, measured: dict | None) -> Score:
    s = Score()
    score_plan(rec, s)
    score_search(rec, s)
    score_tactics(rec, s)
    score_decisions(rec, s)
    score_fences(rec, s)
    score_leaks(rec, s)
    score_gate(rec, s)
    score_cheats(rec, s)
    score_solvability(rec, s)
    score_shape(rec, s, measured)
    # Placeholders anywhere in the record are unanswered questions, whatever the axis said.
    for path, val in walk(rec):
        if placeholder(val):
            s.warn("%s still carries a placeholder" % path)
    return s


def walk(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, "%s.%s" % (prefix, k) if prefix else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, "%s[%d]" % (prefix, i))
    else:
        yield prefix, obj


# ---------------------------------------------------------------------------
# Locating records and the pass list.


def passed_slugs() -> list[str]:
    """Slugs README.md lists as passed, in order. README is the one inventory."""
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    out, collecting = [], False
    for line in text.splitlines():
        if re.search(r"passed:\s*$", line):
            collecting = True
            continue
        if collecting:
            m = re.match(r"^- `([a-z0-9-]+)`", line)
            if m:
                out.append(m.group(1))
            elif line.strip() and not line.startswith("-"):
                collecting = False
    return out


def record_path(arg: str) -> tuple[Path, str | None]:
    p = Path(arg)
    if p.suffix == ".toml" and p.is_file():
        slug = None
        try:
            slug = tomllib.loads(p.read_text(encoding="utf-8")).get("task", {}).get("slug")
        except tomllib.TOMLDecodeError:
            pass
        return p, slug
    return ROOT / "authoring" / arg / "difficulty.toml", arg


def load(path: Path) -> dict | None:
    if not path.is_file():
        return None
    return tomllib.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Reporting.


def report(label: str, s: Score, measured: dict | None, verbose: bool = True) -> int:
    print("== %s" % label)
    if verbose:
        for name, pts, mx, notes in s.axes:
            print("   %-26s %2d / %2d" % (name, pts, mx))
            for n in notes:
                print("        - %s" % n)
        if measured:
            print("   measured tree: %d environment py lines, %s editable files, %d reference "
                  "lines, %d cheats (%d semantic), %d variants"
                  % (measured["environment_py_lines"], measured["editable_files"],
                     measured["reference_lines"], measured["cheats"],
                     measured["semantic_cheats"], measured["variants"]))
        for w in s.warnings:
            print("   WARN %s" % w)
        for st in s.stops:
            print("   STOP %s" % st)
    total = s.total
    if s.stops:
        print("   score %d / 100 (capped at %d by %d hard stop%s; %d before the cap)"
              % (total, HARD_STOP_CAP, len(s.stops), "" if len(s.stops) == 1 else "s", s.raw))
    else:
        print("   score %d / 100" % total)
    if total >= BAND_FLOOR and not s.stops:
        print("   IN BAND  the passing tasks score %d to %d (calibrated %s)"
              % (BAND_FLOOR, BAND_CEILING, BAND_DATE))
        return 0
    print("   BELOW    the passing tasks score %d to %d (calibrated %s); redesign the idea, "
          "do not pad the record" % (BAND_FLOOR, BAND_CEILING, BAND_DATE))
    return 1


def run_one(arg: str, verbose: bool = True) -> tuple[int, int | None]:
    path, slug = record_path(arg)
    rec = load(path)
    if rec is None:
        print("== %s" % arg)
        print("   no difficulty record at %s" % path)
        print("   copy template/difficulty.toml there and answer every field before any code")
        return 2, None
    measured = measure_bundle(slug) if slug else None
    s = score_record(rec, measured)
    code = report(slug or str(path), s, measured, verbose)
    return code, s.total


def calibrate() -> int:
    slugs = passed_slugs()
    rows = []
    for slug in slugs:
        path = ROOT / "authoring" / slug / "difficulty.toml"
        if not path.is_file():
            rows.append((slug, None, "no record (bundle not in this checkout)"
                         if not (ROOT / "tasks" / slug).is_dir() else "no record"))
            continue
        s = score_record(load(path), measure_bundle(slug))
        rows.append((slug, s.total, "hard stop" if s.stops else ""))
    print("Passed tasks per README.md, scored on their difficulty records:")
    for slug, total, note in rows:
        print("   %-26s %s  %s" % (slug, "%3d" % total if total is not None else "  -", note))
    scored = [t for _, t, _ in rows if t is not None]
    if not scored:
        print("   nothing to calibrate against")
        return 2
    lo, hi = min(scored), max(scored)
    print()
    print("   band %d to %d over %d records; median %d"
          % (lo, hi, len(scored), sorted(scored)[len(scored) // 2]))
    bad = 0
    if (lo, hi) != (BAND_FLOOR, BAND_CEILING):
        print("   BAND CONSTANTS STALE: file says %d to %d - update BAND_FLOOR, BAND_CEILING and "
              "BAND_DATE in this file and docs/DIFFICULTY-SCORE.md" % (BAND_FLOOR, BAND_CEILING))
        bad = 1
    else:
        print("   band constants match (calibrated %s)" % BAND_DATE)

    controls = sorted((ROOT / "authoring" / "controls").glob("*.toml"))
    if controls:
        print()
        print("Negative controls, designs the pipeline rejected; each must score below %d:"
              % BAND_FLOOR)
        for path in controls:
            s = score_record(load(path), None)
            verdict = "below" if s.total < BAND_FLOOR else "IN BAND - RUBRIC DEFECT"
            print("   %-40s %3d  %s%s" % (path.stem, s.total, verdict,
                                          "  (hard stop)" if s.stops else ""))
            if s.total >= BAND_FLOOR:
                bad = 1
    return bad


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    if argv[1] == "--calibrate":
        return calibrate()
    if argv[1] == "--all":
        worst = 0
        for d in sorted((ROOT / "authoring").iterdir()):
            if (d / "difficulty.toml").is_file():
                code, _ = run_one(d.name, verbose=False)
                worst = max(worst, code)
                print()
        return worst
    code, _ = run_one(argv[1])
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
