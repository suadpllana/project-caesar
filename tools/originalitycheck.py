#!/usr/bin/env python3
"""Score a task design for distinctness, before a line of code exists.

The pipeline screens every submission for similarity against public material and against
tasks other contributors have already submitted (docs/RULES.md, "Originality and internet
policy"). A flagged task is rejected whatever its difficulty score, and the flag is
usually earned at idea time: the design is a named archetype - an LRU cache, a write
barrier, a topological sort, a snapshot-isolation bug - that several contributors mining
the same textbooks reach independently. Nothing later in the pipeline can separate two
tasks that grade the same mechanism.

This tool turns that screen into a number that can be read before the build. It reads an
originality record - the mechanism in one sentence, the nearest public write-up, the
nearest already-submitted task, the five surfaces a similarity screen compares, the search
that was actually run, and the crowded archetype the design sits next to - and scores it
out of 100. It also measures, mechanically and without trusting the record:

- tag, label and substrate overlap against authoring/submissions.toml, the ledger of what
  has already been submitted from this checkout;
- the mechanism sentence against every mechanism sentence in that ledger;
- when tasks/<slug>/instruction.md exists, its text against every other instruction in
  tasks/ and against any --corpus directory of earlier submissions.

What this measures, honestly: the record half reads fields, lengths and counts, exactly as
tools/difficultycheck.py does. It cannot tell a real departure from an invented one. The
corpus half is a text metric, not the platform's screen: two tasks can grade the same
mechanism in disjoint vocabulary and score far apart here, which is why the record exists
and why the mechanism sentence, not the prose, is the field that decides the idea.

Thresholds. The corpus ceilings are measured across the bundles in tasks/, which the
pipeline has accepted alongside each other, so they say what distance accepted-distinct
tasks actually keep (--calibrate reprints and rechecks them). The record floor is set by
construction, not calibrated: no similarity verdict from the platform is recorded in this
checkout, so there is no passed-and-flagged set to fit. When verdicts arrive, add them to
the ledger and recalibrate.

Usage:
    python tools/originalitycheck.py <slug>              score authoring/<slug>/originality.toml
    python tools/originalitycheck.py <path/to/rec.toml>  score a record before a slug exists
    python tools/originalitycheck.py --all               score every record under authoring/
    python tools/originalitycheck.py --nearest <path>    corpus neighbours of one text file
    python tools/originalitycheck.py --calibrate         remeasure the corpus ceilings, check
                                                         the constants, score the controls
    python tools/originalitycheck.py --selftest          prove every stop and axis fires
    (any of the above)  --corpus DIR                     extra directories of earlier
                                                         submissions, searched for *.md

Exit code 0 when the score is at or above the floor with no hard stop, 1 otherwise, 2 on a
missing or malformed record.
"""

from __future__ import annotations

import itertools
import math
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The record floor. Set by construction: the rubric has seven axes, and a record at 90 has
# answered all of them with at most one ten-point axis short. Losing either twenty-point
# axis - the distinctness table or the nearest submitted task - puts a record below it.
FLOOR = 90

# A hard stop caps the score here, whatever the axes add up to.
HARD_STOP_CAP = 40

# Corpus ceilings, measured by --calibrate over the 12 bundles in tasks/ on the date shown.
# COS_CEILING and SHINGLE_CEILING are the largest values any pair of those bundles reaches:
# the pipeline holds all of them at once, so a new task at or under them is no closer to a
# retained task than two retained tasks are to each other. Above a ceiling is a warning,
# not a verdict. The STOP values are set by construction at roughly 1.5x the ceiling, far
# outside anything the accepted set does - 0.12 above the cosine ceiling - and they fire
# as hard stops.
COS_CEILING = 0.28
COS_STOP = 0.40
SHINGLE_CEILING = 0.05
SHINGLE_STOP = 0.15
CORPUS_DATE = "2026-09-22"

# Sessions launched from NEW-TASK-PROMPT.md build Software or ML tasks only (AGENTS.md
# Stage 1). Software/Systems was retired on 2026-09-10 and no new task is filed under it.
LABELS = {
    "Software": ("Algorithms", "Databases", "Data engineering", "Frontend", "Languages"),
    "ML": ("Training", "Inference", "Evaluation", "Kernels"),
}
RETIRED_LABELS = {"Systems"}

PLACEHOLDERS = ("TODO", "TBD", "FIXME", "???", "<your-", "XXX", "none found", "n/a")

# Tags that name how a task is tested rather than what it grades. Two tasks sharing one of
# these are not similar; two tasks sharing a mechanism tag are. Measured: across the twelve
# bundles in tasks/ the only tag any pair shares is differential-testing.
METHOD_TAGS = {
    "differential-testing", "property-testing", "property-based-testing", "fuzzing",
    "regression-testing", "unit-testing", "golden-files", "snapshot-testing",
    "randomized-testing", "metamorphic-testing",
}

AXES = ("mechanism", "substrate", "graded_output", "failure_mode", "interaction")
SUBMITTED_SOURCES = ("ledger", "platform-feedback", "search", "retained")

# The crowded archetypes, per label: the shapes several contributors reach independently
# because the textbook, the interview question and the course exercise all point there.
# Being on this list does not kill an idea - two retained bundles sit squarely on it - but
# a design whose graded work IS the archetype has no separation to state, and the record
# has to name the invariant the archetype's write-ups do not carry. The regexes are read
# against the mechanism sentence, the substrate and the tags, and they are deliberately
# narrow: a hit is a prompt to answer collision.archetype honestly, not a verdict.
CROWDED = {
    "Algorithms": [
        ("LRU/LFU/TTL cache", r"\b(lru|lfu|arc)\b|cache evict|ttl (cache|expiry)"),
        ("topological sort or dependency resolver", r"topological|dependency resolv|cycle detect"),
        ("interval merge or sweep line", r"interval (merge|tree)|sweep.?line|merge overlapping"),
        ("shortest path", r"dijkstra|a\*|bellman.?ford|shortest path"),
        ("union-find connectivity", r"union.?find|disjoint.?set"),
        ("diff or longest common subsequence", r"\bdiff (algorithm|engine)\b|myers|longest common"),
        ("regular expression engine", r"regex engine|backtrack(ing)? matcher|nfa|thompson"),
        ("rate limiter", r"rate limit|token bucket|leaky bucket|sliding window counter"),
        ("string search", r"\bkmp\b|aho.?corasick|boyer.?moore|suffix (array|automaton)"),
        ("classic dynamic programming", r"knapsack|edit distance|coin change|n.?queens|sudoku"),
        ("scheduling with priorities", r"priority queue schedul|earliest deadline first|\bedf\b"),
    ],
    "Databases": [
        ("MVCC and snapshot isolation", r"\bmvcc\b|snapshot isolation|write skew|serializable snapshot"),
        ("B-tree or LSM storage engine", r"b.?tree|lsm|sstable|compaction|bloom filter"),
        ("write-ahead log and crash recovery", r"write.?ahead log|\bwal\b|aries|redo log|crash recover"),
        ("query planner and join ordering", r"query plan|join order|cost.?based optim|cardinality estim"),
        ("two-phase commit", r"two.?phase commit|\b2pc\b|prepare.*commit protocol"),
        ("lock manager and deadlock detection", r"lock manager|deadlock detect|wait.?for graph"),
        ("incremental view maintenance", r"incremental view|materialized view maint|delta process"),
        ("buffer pool eviction", r"buffer pool|page replacement|clock.?sweep"),
    ],
    "Data engineering": [
        ("exactly-once delivery and dedup", r"exactly.?once|at.?least.?once|idempot(ent|ency) key|dedup"),
        ("watermarks and late events", r"watermark|late.?arriving|allowed lateness|event.?time window"),
        ("lakehouse compaction", r"compact(ion|ing) (small )?files|\bmerge.?on.?read\b|delta lake|iceberg"),
        ("schema evolution", r"schema evolution|schema migration|column (add|drop|rename) compat"),
        ("DAG scheduler with retries", r"\bdag\b schedul|airflow|task retry|backfill schedul"),
        ("shuffle or partition skew", r"data skew|shuffle partition|salting|hot partition"),
        ("change data capture ordering", r"\bcdc\b|change data capture|binlog|debezium"),
    ],
    "Frontend": [
        ("virtual DOM reconciliation", r"virtual dom|reconcil|keyed (list|children)|diff the tree"),
        ("focus management and focus trap", r"focus (trap|manage|restore)|roving tabindex"),
        ("undo and redo stacks", r"undo (stack|redo)|redo stack|command pattern history"),
        ("form validation state machine", r"form validat|dirty.*touched|field.?level validation"),
        ("virtualized or infinite lists", r"virtuali[sz]ed list|windowing|infinite scroll"),
        ("state store with selectors", r"redux|selector memo|observable store|signal graph"),
        ("router with nested layouts", r"nested (route|layout)|route guard|router resolve"),
        ("drag and drop reorder", r"drag.?and.?drop|sortable list|drop target"),
        ("optimistic UI rollback", r"optimistic (update|ui)|rollback on failure|mutation queue"),
    ],
    "Languages": [
        ("garbage collector", r"garbage collect|mark.?(and.?)?sweep|write barrier|generational|nursery"),
        ("async scheduler with cancellation", r"cancellation|structured concurrency|event loop|coroutine schedul"),
        ("type inference", r"hindley|unification|type inference|constraint solving for types"),
        ("bytecode virtual machine", r"bytecode|stack machine|\bvm\b interpret|opcode dispatch"),
        ("tokenizer and recursive-descent parser", r"recursive descent|pratt|tokeni[sz]er|\bast\b builder"),
        ("closures and scope chains", r"closure capture|scope chain|upvalue|lexical environment"),
        ("borrow checking and lifetimes", r"borrow check|lifetime (inference|elision)|ownership transfer"),
        ("exception unwinding", r"unwind|stack trace construct|finally semantics"),
        ("classic optimizer passes", r"constant fold|dead code elimin|register alloc|\bssa\b"),
    ],
    "Training": [
        ("gradient accumulation and mixed precision", r"gradient accumulat|mixed precision|loss scal|\bamp\b"),
        ("learning-rate schedules", r"learning rate schedul|warmup|cosine decay"),
        ("distributed gradient sync", r"all.?reduce|\bddp\b|\bfsdp\b|gradient sync|parameter server"),
        ("mixture-of-experts routing", r"mixture.?of.?experts|\bmoe\b|expert (capacity|routing)|top.?k gate"),
        ("checkpoint resume", r"checkpoint (resume|restore)|optimizer state (save|load)"),
        ("data loader shuffling", r"shuffle buffer|epoch seed|sampler shard"),
        ("early stopping and clipping", r"early stopping|gradient clip|patience"),
    ],
    "Inference": [
        ("KV cache and paged attention", r"kv.?cache|paged attention|block table|attention sink"),
        ("continuous batching", r"continuous batching|in.?flight batching|iteration.?level schedul"),
        ("speculative decoding", r"speculative decod|draft model|acceptance (rate|rule)"),
        ("streaming detokenization", r"detokeni[sz]|incremental decode|stop sequence|partial utf"),
        ("sampling and determinism", r"top.?[kp]\b|temperature sampl|nucleus sampl|greedy decode"),
        ("grammar-constrained decoding", r"grammar.?constrained|json schema decod|logit mask"),
        ("quantization", r"quantiz|int8|\bgptq\b|\bawq\b|dequant"),
    ],
    "Evaluation": [
        ("pass@k estimation", r"pass@k|unbiased estimator of pass"),
        ("LLM-as-judge rubrics", r"llm.?as.?(a.?)?judge|judge rubric|pairwise preference"),
        ("contamination detection", r"contaminat|train.?test overlap|n.?gram leak"),
        ("flaky retries in a harness", r"flaky|retry the (test|case)|quarantine"),
        ("leaderboard ranking", r"leaderboard|elo|bradley.?terry|ranking with ties"),
        ("bootstrap confidence intervals", r"bootstrap|confidence interval|standard error"),
        ("answer normalization", r"answer normali[sz]|exact match normali[sz]|string canonical"),
    ],
    "Kernels": [
        ("tiled matrix multiply", r"tiled (matmul|gemm)|\bgemm\b|matrix multiply kernel"),
        ("flash or fused attention", r"flash attention|fused attention|online softmax"),
        ("reductions and scans", r"warp (shuffle|reduce)|prefix sum|\bscan\b kernel|block reduce"),
        ("fused normalization", r"layer.?norm kernel|rms.?norm|fused (norm|epilogue)"),
        ("coalescing and bank conflicts", r"coalesc|bank conflict|shared memory padding"),
        ("occupancy tuning", r"occupancy|register pressure|launch bound"),
        ("sparse kernels", r"\bspmv\b|\bcsr\b|sparse (gemm|kernel)"),
    ],
}


def words(text) -> int:
    if not isinstance(text, str):
        return 0
    return len(re.findall(r"[A-Za-z0-9_']+", text))


def placeholder(text) -> bool:
    return isinstance(text, str) and any(m.lower() in text.lower() for m in PLACEHOLDERS)


def answered(text, minimum: int) -> bool:
    return isinstance(text, str) and words(text) >= minimum and not placeholder(text)


# ---------------------------------------------------------------------------
# Text metrics. Two of them, because they catch different collisions: the cosine over
# tf-idf finds two tasks that talk about the same machinery in their own words, and the
# shingle overlap finds prose that was reworded rather than rewritten.

SUFFIX_RE = re.compile(r"You have \d+ seconds to complete this task.*$", re.S)


def tokens(text: str) -> list[str]:
    """Content words of an instruction, with the required suffix removed.

    The suffix (AGENTS.md section 7) is identical in every bundle, so leaving it in makes
    every pair look alike. Words of two characters or fewer carry nothing here.
    """
    return re.findall(r"[a-z][a-z0-9_]{2,}", SUFFIX_RE.sub("", text).lower())


def shingles(toks: list[str], k: int = 5) -> set[tuple]:
    return {tuple(toks[i:i + k]) for i in range(len(toks) - k + 1)}


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


class Corpus:
    """Tf-idf vectors over a set of named documents, with the idf from the whole set."""

    def __init__(self, docs: dict[str, str]):
        self.toks = {name: tokens(text) for name, text in docs.items()}
        self.df: dict[str, int] = {}
        for toks in self.toks.values():
            for w in set(toks):
                self.df[w] = self.df.get(w, 0) + 1
        self.n = max(1, len(self.toks))
        self.vec = {name: self._vector(t) for name, t in self.toks.items()}
        self.sh = {name: shingles(t) for name, t in self.toks.items()}

    def _vector(self, toks: list[str]) -> dict[str, float]:
        tf: dict[str, int] = {}
        for w in toks:
            tf[w] = tf.get(w, 0) + 1
        v = {}
        for w, c in tf.items():
            idf = math.log((self.n + 1) / (self.df.get(w, 0) + 1)) + 1.0
            v[w] = (1 + math.log(c)) * idf
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {w: x / norm for w, x in v.items()}

    def compare(self, name: str, text: str) -> list[tuple[float, float, str]]:
        """(cosine, shingle jaccard, other) against every document but `name`, sorted."""
        v = self._vector(tokens(text))
        s = shingles(tokens(text))
        out = []
        for other, ov in self.vec.items():
            if other == name:
                continue
            small, large = (v, ov) if len(v) <= len(ov) else (ov, v)
            cos = sum(x * large.get(w, 0.0) for w, x in small.items())
            out.append((cos, jaccard(s, self.sh[other]), other))
        out.sort(reverse=True)
        return out


def instruction_corpus(extra_dirs: list[Path]) -> dict[str, str]:
    docs = {}
    for p in sorted(ROOT.glob("tasks/*/instruction.md")):
        docs[p.parent.name] = p.read_text(encoding="utf-8", errors="replace")
    for d in extra_dirs:
        if not d.is_dir():
            print("   WARN corpus directory %s does not exist" % d)
            continue
        for p in sorted(d.rglob("*.md")):
            name = "%s:%s" % (d.name, p.relative_to(d))
            docs[name] = p.read_text(encoding="utf-8", errors="replace")
    return docs


# ---------------------------------------------------------------------------
# The ledger: what has already been submitted from this checkout, one entry per task.
# It is the corpus the platform's screen has already seen, so it is where a self-collision
# - the same contributor's own earlier task, reskinned - becomes visible before submission.


def load_ledger() -> list[dict]:
    path = ROOT / "authoring" / "submissions.toml"
    if not path.is_file():
        return []
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        print("   WARN authoring/submissions.toml does not parse: %s" % exc)
        return []
    return data.get("submission", [])


def substrate_terms(text: str) -> set[str]:
    """Content words of a substrate description, minus the words every substrate uses."""
    stop = {
        "the", "and", "that", "with", "for", "from", "into", "over", "under", "its",
        "our", "their", "this", "one", "two", "each", "every", "part", "parts", "system",
        "engine", "tree", "file", "files", "line", "lines", "code", "task", "small",
        "simplified", "cut", "down", "tool", "app", "has", "have", "are", "was", "were",
        "which", "what", "when", "where", "does", "just", "only", "also", "than", "then",
    }
    return {w for w in re.findall(r"[a-z][a-z0-9-]{3,}", text.lower()) if w not in stop}


# ---------------------------------------------------------------------------
# Scoring.


class Score:
    """Accumulates axis scores, warnings and hard stops for one record."""

    def __init__(self):
        self.axes: list[tuple[str, int, int, list[str]]] = []
        self.warnings: list[str] = []
        self.stops: list[str] = []
        self.measurements: list[str] = []

    def axis(self, name: str, points: int, maximum: int, notes: list[str]):
        self.axes.append((name, min(points, maximum), maximum, notes))

    def warn(self, msg: str):
        self.warnings.append(msg)

    def stop(self, msg: str):
        self.stops.append(msg)

    def measured(self, msg: str):
        self.measurements.append(msg)

    @property
    def raw(self) -> int:
        return sum(p for _, p, _, _ in self.axes)

    @property
    def total(self) -> int:
        return min(self.raw, HARD_STOP_CAP) if self.stops else self.raw


def crowded_hits(label: str, text: str) -> list[str]:
    out = []
    for name, pattern in CROWDED.get(label, []):
        if re.search(pattern, text, re.I):
            out.append(name)
    return out


def score_task(rec: dict, s: Score):
    task = rec.get("task", {})
    category = task.get("category", "")
    label = task.get("label", "")
    if label in RETIRED_LABELS:
        s.stop("task.label = %r was retired on 2026-09-10 and no new task is filed under it; "
               "file the work under the Software label it actually exercises (AGENTS.md "
               "Stage 1)" % label)
    elif category not in LABELS:
        s.stop("task.category must be Software or ML for a session launched from "
               "NEW-TASK-PROMPT.md; got %r" % category)
    elif label not in LABELS[category]:
        s.stop("task.label %r is not a label of %s; the labels are %s (AGENTS.md Stage 1)"
               % (label, category, ", ".join(LABELS[category])))


def score_mechanism(rec: dict, s: Score):
    m = rec.get("mechanism", {})
    pts, notes = 0, []
    if answered(m.get("sentence"), 18):
        pts += 6
    else:
        notes.append("mechanism.sentence: one sentence naming what the graded work is, "
                     "mechanism first and no story (>= 18 words) - this is the sentence a "
                     "similarity screen compares")
    if answered(m.get("substrate"), 8):
        pts += 3
    else:
        notes.append("mechanism.substrate: the system the mechanism lives in (>= 8 words)")
    if answered(m.get("graded_output"), 8):
        pts += 2
    else:
        notes.append("mechanism.graded_output: what the verifier reads and compares, in the "
                     "shape it compares it (>= 8 words)")
    if answered(m.get("failure_mode"), 12):
        pts += 2
    else:
        notes.append("mechanism.failure_mode: the wrong plan this task exists to punish "
                     "(>= 12 words)")
    if answered(m.get("interaction"), 12):
        pts += 2
    else:
        notes.append("mechanism.interaction: the pair of rules whose interaction is the "
                     "difficulty (>= 12 words)")
    s.axis("mechanism stated", pts, 15, notes)


def score_public(rec: dict, s: Score):
    p = rec.get("nearest", {}).get("public", {})
    pts, notes = 0, []
    if answered(p.get("name"), 4):
        pts += 2
    else:
        notes.append("nearest.public.name: the closest public write-up, paper, library or "
                     "course exercise (>= 4 words) - every mechanism has one, name it")
    url = p.get("url", "")
    if isinstance(url, str) and re.match(r"https?://\S+\.\S+", url.strip()):
        pts += 2
    else:
        notes.append("nearest.public.url: the link, so the next session does not repeat the search")
    if answered(p.get("covers"), 10):
        pts += 4
    else:
        notes.append("nearest.public.covers: what that page does cover (>= 10 words)")
    if answered(p.get("separation"), 15):
        pts += 7
    else:
        notes.append("nearest.public.separation: where this task's rules depart from it, so "
                     "retrieval does not plan the task (>= 15 words)")
    if p.get("plans_this") is True:
        s.stop("nearest.public.plans_this = true: the solution is findable online and the "
               "idea is dead as it stands (docs/RULES.md, AGENTS.md D4)")
    s.axis("nearest public work", pts, 15, notes)


def score_submitted(rec: dict, s: Score):
    n = rec.get("nearest", {}).get("submitted", {})
    pts, notes = 0, []
    if answered(n.get("name"), 2):
        pts += 5
    else:
        notes.append("nearest.submitted.name: name the closest already-submitted task, by "
                     "slug or title - 'none found' is not an answer, it is an unrun search")
    if n.get("source") in SUBMITTED_SOURCES:
        pts += 2
    else:
        notes.append("nearest.submitted.source: one of %s" % ", ".join(SUBMITTED_SOURCES))
    if answered(n.get("shares"), 8):
        pts += 5
    else:
        notes.append("nearest.submitted.shares: what genuinely overlaps (>= 8 words), stated "
                     "at its strongest - a minimised overlap is the one review finds")
    if answered(n.get("separation"), 20):
        pts += 8
    else:
        notes.append("nearest.submitted.separation: why a reviewer holding both would not "
                     "call them the same task (>= 20 words)")
    if n.get("same_mechanism") is True:
        s.stop("nearest.submitted.same_mechanism = true: the design grades the mechanism an "
               "existing task already grades, which is the reskin docs/RULES.md rejects")
    s.axis("nearest submitted task", pts, 20, notes)


def score_axes(rec: dict, s: Score):
    rows = rec.get("axes", {}).get("differentiators", []) or []
    pts, notes = 0, []
    seen, good = set(), 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        axis = (row.get("axis") or "").strip()
        if axis not in AXES:
            if axis:
                notes.append("axes: %r is not one of %s" % (axis, ", ".join(AXES)))
            continue
        if axis in seen:
            notes.append("axes: %s appears twice; each surface counts once" % axis)
            continue
        if not answered(row.get("theirs"), 5) or not answered(row.get("ours"), 5):
            notes.append("axes.%s: state both sides concretely (>= 5 words each) - what the "
                         "nearest task does on this surface, and what this one does" % axis)
            continue
        seen.add(axis)
        good += 1
    pts = min(good, 3) * 6 + (2 if good >= 4 else 0)
    if good < 3:
        notes.append("axes: %d of the five surfaces separated; three is the minimum. A design "
                     "that differs on one surface is the same task in new clothes" % good)
    s.axis("distinctness surfaces", pts, 20, notes)


def score_search(rec: dict, s: Score):
    q = rec.get("search", {})
    pts, notes = 0, []
    queries = [x for x in (q.get("queries") or []) if isinstance(x, str) and words(x) >= 2]
    if len(queries) >= 4:
        pts += 5
    else:
        notes.append("search.queries: the exact strings you ran, four or more; %d usable"
                     % len(queries))
    if answered(q.get("results"), 20):
        pts += 5
    else:
        notes.append("search.results: what came back and why none of it plans this task "
                     "(>= 20 words)")
    if q.get("twin_found") is True:
        s.stop("search.twin_found = true: a public write-up or an existing task does this "
               "same graded work; replace the idea rather than renaming it")
    s.axis("search evidence", pts, 10, notes)


def score_collision(rec: dict, s: Score, label: str):
    c = rec.get("collision", {})
    m = rec.get("mechanism", {})
    pts, notes = 0, []
    archetype = c.get("archetype", "")
    if answered(archetype, 2):
        pts += 4
    else:
        notes.append("collision.archetype: name the crowded archetype this sits nearest to, "
                     "even when the answer is that none of them fits - an archetype you "
                     "cannot name is one you have not checked (docs/ORIGINALITY.md)")

    scanned = " ".join(str(x) for x in (
        m.get("sentence", ""), m.get("substrate", ""), m.get("graded_output", ""),
        " ".join(rec.get("task", {}).get("tags", []) or []),
    ))
    hits = crowded_hits(label, scanned)
    if hits:
        s.measured("crowded archetypes matched by the mechanism sentence, substrate and "
                   "tags: %s" % "; ".join(hits))
    on_list = c.get("on_list")
    if on_list is True:
        if answered(c.get("departure"), 25):
            pts += 6
        else:
            notes.append("collision.departure: the archetype is crowded, so state the "
                         "invariant its write-ups do not carry and why the crowded form of "
                         "it cannot produce this graded output (>= 25 words)")
    elif on_list is False:
        if hits:
            notes.append("collision.on_list = false, but the mechanism sentence, substrate or "
                         "tags match %s from the crowded list for %s; answer it the other way "
                         "and state the departure, or rewrite the sentence so it says what "
                         "the work really is" % (", ".join(hits), label))
        else:
            pts += 6
    else:
        notes.append("collision.on_list: true or false - is that archetype on the crowded "
                     "list for this label?")
    s.axis("crowded-archetype check", pts, 10, notes)


def score_ledger(rec: dict, s: Score, ledger: list[dict]):
    """Measured, not declared: overlap against everything already submitted."""
    task = rec.get("task", {})
    mech = rec.get("mechanism", {})
    slug = task.get("slug", "")
    tags = {str(t).strip().lower() for t in (task.get("tags") or []) if str(t).strip()}
    pts, notes = 0, []

    if not ledger:
        s.warn("no ledger at authoring/submissions.toml, so tag, substrate and mechanism "
               "overlap against earlier submissions could not be measured; the three "
               "ledger points are withheld")
        s.axis("ledger separation", 0, 10, ["authoring/submissions.toml is missing or empty"])
        return

    others = [e for e in ledger if e.get("slug") != slug]

    worst_tags, worst_entry = set(), None
    for e in others:
        shared = tags & {str(t).strip().lower() for t in (e.get("tags") or [])}
        if len(shared) > len(worst_tags):
            worst_tags, worst_entry = shared, e
    mechanism_shared = {t for t in worst_tags if t not in METHOD_TAGS}
    if len(worst_tags) >= 2:
        s.stop("tags: %s share %d tags with %s (%s); across the retained bundles no pair "
               "shares more than one, and that one is a testing method, never a mechanism"
               % (task.get("slug", "this task"), len(worst_tags), worst_entry.get("slug"),
                  ", ".join(sorted(worst_tags))))
    elif mechanism_shared:
        notes.append("tags: %s is a mechanism tag already carried by %s; tags name what is "
                     "specific to this task (AGENTS.md section 4)"
                     % (", ".join(sorted(mechanism_shared)), worst_entry.get("slug")))
    elif worst_tags:
        pts += 4
        s.measured("tags share only %s with %s, a testing method rather than a mechanism"
                   % (", ".join(sorted(worst_tags)), worst_entry.get("slug")))
    else:
        pts += 4
        s.measured("tags overlap nothing in the ledger")

    sub = substrate_terms(mech.get("substrate", ""))
    hits = []
    for e in others:
        overlap = sub & substrate_terms(e.get("substrate", ""))
        if len(overlap) >= 2:
            hits.append((e.get("slug"), sorted(overlap)))
    if not sub:
        notes.append("substrate: no substrate stated, so reuse could not be measured")
    elif hits:
        notes.append("substrate: shares %s with %s - a second task in the same substrate "
                     "reads as the same task even when the rules differ"
                     % (", ".join(hits[0][1]), ", ".join(h[0] for h in hits)))
    else:
        pts += 3
        s.measured("substrate reuses no earlier submission's substrate")

    sentences = {e.get("slug", "?"): e.get("mechanism", "") for e in others
                 if e.get("mechanism")}
    mine = mech.get("sentence", "")
    if sentences and answered(mine, 8):
        corpus = Corpus({**sentences, "__candidate__": mine})
        near = corpus.compare("__candidate__", mine)
        if near:
            cos, _, who = near[0]
            s.measured("mechanism sentence nearest ledger entry: %s at cosine %.2f" % (who, cos))
            if cos >= 0.50:
                notes.append("mechanism sentence is %.2f cosine from %s; two sentences this "
                             "close describe one task to a reviewer reading both" % (cos, who))
            else:
                pts += 3
    elif not sentences:
        notes.append("no ledger entry carries a mechanism sentence to compare against")
    s.axis("ledger separation", pts, 10, notes)


def score_corpus(slug: str | None, s: Score, extra_dirs: list[Path]):
    """The built instruction against every other instruction. Measured, never declared."""
    if not slug:
        return
    path = ROOT / "tasks" / slug / "instruction.md"
    if not path.is_file():
        return
    docs = instruction_corpus(extra_dirs)
    text = path.read_text(encoding="utf-8", errors="replace")
    docs[slug] = text
    near = Corpus(docs).compare(slug, text)
    if not near:
        return
    cos, sh, who = near[0]
    s.measured("instruction nearest neighbour: %s at cosine %.3f, shingle %.3f (over %d "
               "documents)" % (who, cos, sh, len(docs)))
    if cos >= COS_STOP:
        s.stop("instruction.md is %.3f cosine from %s, past the %.2f stop; no two bundles the "
               "pipeline accepted come within %.2f of that" % (cos, who, COS_STOP,
                                                               COS_STOP - COS_CEILING))
    elif cos > COS_CEILING:
        s.warn("instruction.md is %.3f cosine from %s, above the %.2f the accepted bundles "
               "keep; say in the record why these two are not one task" % (cos, who, COS_CEILING))
    worst_sh = max(near, key=lambda r: r[1])
    if worst_sh[1] >= SHINGLE_STOP:
        s.stop("instruction.md shares %.3f of its five-word runs with %s, past the %.2f stop; "
               "that is reworded prose, not a new task" % (worst_sh[1], worst_sh[2], SHINGLE_STOP))
    elif worst_sh[1] > SHINGLE_CEILING:
        s.warn("instruction.md shares %.3f of its five-word runs with %s, above the %.2f the "
               "accepted bundles keep" % (worst_sh[1], worst_sh[2], SHINGLE_CEILING))


def score_record(rec: dict, slug: str | None, ledger: list[dict],
                 extra_dirs: list[Path]) -> Score:
    s = Score()
    score_task(rec, s)
    score_mechanism(rec, s)
    score_public(rec, s)
    score_submitted(rec, s)
    score_axes(rec, s)
    score_search(rec, s)
    score_collision(rec, s, rec.get("task", {}).get("label", ""))
    score_ledger(rec, s, ledger)
    score_corpus(slug, s, extra_dirs)
    return s


# ---------------------------------------------------------------------------
# Locating records and reporting.


def record_path(arg: str) -> tuple[Path, str | None]:
    p = Path(arg)
    if p.suffix == ".toml" and p.is_file():
        slug = None
        try:
            slug = tomllib.loads(p.read_text(encoding="utf-8")).get("task", {}).get("slug")
        except tomllib.TOMLDecodeError:
            pass
        return p, slug
    return ROOT / "authoring" / arg / "originality.toml", arg


def load(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        print("== %s" % path)
        print("   the record does not parse: %s" % exc)
        return None


def report(label: str, s: Score, verbose: bool = True) -> int:
    print("== %s" % label)
    if verbose:
        for name, pts, mx, notes in s.axes:
            print("   %-26s %2d / %2d" % (name, pts, mx))
            for n in notes:
                print("        - %s" % n)
        for m in s.measurements:
            print("   measured %s" % m)
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
    if total >= FLOOR and not s.stops:
        print("   DISTINCT  floor %d; corpus ceilings cosine %.2f, shingle %.2f (measured %s)"
              % (FLOOR, COS_CEILING, SHINGLE_CEILING, CORPUS_DATE))
        return 0
    print("   TOO CLOSE floor %d; move the design, not the wording - the screen compares "
          "mechanisms (docs/ORIGINALITY.md)" % FLOOR)
    return 1


def run_one(arg: str, extra_dirs: list[Path], verbose: bool = True) -> int:
    path, slug = record_path(arg)
    if not path.is_file():
        print("== %s" % arg)
        print("   no originality record at %s" % path)
        print("   copy template/originality.toml there and answer every field before any code")
        return 2
    rec = load(path)
    if rec is None:
        return 2  # load() has already said why
    s = score_record(rec, slug, load_ledger(), extra_dirs)
    return report(slug or str(path), s, verbose)


def nearest(target: Path, extra_dirs: list[Path]) -> int:
    if not target.is_file():
        print("no such file: %s" % target)
        return 2
    docs = instruction_corpus(extra_dirs)
    # A bundle's own instruction is already in the corpus; compare it under its own name so it
    # is not reported as a perfect match with itself.
    resolved = target.resolve()
    name = (resolved.parent.name
            if resolved.parent.parent.name == "tasks" and resolved.parent.name in docs
            else "__target__")
    text = target.read_text(encoding="utf-8", errors="replace")
    docs[name] = text
    near = Corpus(docs).compare(name, text)
    print("== %s against %d documents" % (target, len(docs) - 1))
    for cos, sh, other in near[:8]:
        flag = ""
        if cos >= COS_STOP or sh >= SHINGLE_STOP:
            flag = "  STOP"
        elif cos > COS_CEILING or sh > SHINGLE_CEILING:
            flag = "  above the accepted ceiling"
        print("   %.3f cosine  %.3f shingle  %s%s" % (cos, sh, other, flag))
    worst = max((c for c, _, _ in near), default=0.0)
    worst_sh = max((x for _, x, _ in near), default=0.0)
    print("   ceilings: cosine %.2f, shingle %.2f (measured %s); stops at %.2f and %.2f"
          % (COS_CEILING, SHINGLE_CEILING, CORPUS_DATE, COS_STOP, SHINGLE_STOP))
    return 1 if (worst >= COS_STOP or worst_sh >= SHINGLE_STOP) else 0


def calibrate(extra_dirs: list[Path]) -> int:
    docs = instruction_corpus(extra_dirs)
    bundles = {k: v for k, v in docs.items() if ":" not in k}
    corpus = Corpus(bundles)
    pairs = []
    for a, b in itertools.combinations(sorted(bundles), 2):
        va, vb = corpus.vec[a], corpus.vec[b]
        small, large = (va, vb) if len(va) <= len(vb) else (vb, va)
        cos = sum(x * large.get(w, 0.0) for w, x in small.items())
        pairs.append((cos, jaccard(corpus.sh[a], corpus.sh[b]), a, b))
    if not pairs:
        print("no bundles in tasks/ to calibrate against")
        return 2
    pairs.sort(reverse=True)
    print("Instruction distance across the %d bundles in tasks/, %d pairs. These are held by "
          "the pipeline\nalongside each other, so the largest value any pair reaches is what "
          "accepted-distinct looks like:" % (len(bundles), len(pairs)))
    for cos, sh, a, b in pairs[:5]:
        print("   %.3f cosine  %.3f shingle  %-24s %s" % (cos, sh, a, b))
    def median(values: list[float]) -> float:
        v = sorted(values)
        half = len(v) // 2
        return v[half] if len(v) % 2 else (v[half - 1] + v[half]) / 2

    cos_max = max(p[0] for p in pairs)
    sh_max = max(p[1] for p in pairs)
    print("   cosine  max %.3f, median %.3f" % (cos_max, median([p[0] for p in pairs])))
    print("   shingle max %.3f, median %.4f" % (sh_max, median([p[1] for p in pairs])))
    bad = 0
    # The ceiling is the measured maximum rounded up to the nearest hundredth. Too low and
    # accepted-distinct pairs trip it; too high and it stops saying anything, so both sides
    # are checked.
    if not (COS_CEILING - 0.02 <= cos_max <= COS_CEILING
            and SHINGLE_CEILING - 0.02 <= sh_max <= SHINGLE_CEILING):
        print("   CEILINGS STALE: measured %.3f / %.3f against constants %.2f / %.2f - update "
              "COS_CEILING, SHINGLE_CEILING, CORPUS_DATE and docs/ORIGINALITY.md together"
              % (cos_max, sh_max, COS_CEILING, SHINGLE_CEILING))
        bad = 1
    else:
        print("   ceiling constants hold (measured %s)" % CORPUS_DATE)

    ledger = load_ledger()
    slugs = {e.get("slug") for e in ledger}
    missing = sorted(p.parent.name for p in ROOT.glob("tasks/*/task.toml")
                     if p.parent.name not in slugs)
    print()
    if missing:
        print("Ledger gaps: %s - every submitted task belongs in authoring/submissions.toml, "
              "or the next\n   design is checked against a corpus that does not include it"
              % ", ".join(missing))
        bad = 1
    else:
        print("Ledger covers every bundle in tasks/ (%d entries)" % len(ledger))

    controls = sorted((ROOT / "authoring" / "controls" / "originality").glob("*.toml"))
    if controls:
        print()
        print("Negative controls, designs a similarity screen should flag; each must score "
              "below %d:" % FLOOR)
        for path in controls:
            rec = load(path)
            s = score_record(rec, None, ledger, [])
            verdict = "below" if s.total < FLOOR else "AT FLOOR - RUBRIC DEFECT"
            print("   %-40s %3d  %s%s" % (path.stem, s.total, verdict,
                                          "  (hard stop)" if s.stops else ""))
            if s.total >= FLOOR:
                bad = 1
    return bad


# ---------------------------------------------------------------------------
# Self-test. The rubric's floor is set by construction rather than fitted to a set of
# platform verdicts, so what can be proved here is that every stop and every axis fires on
# the defect it exists for. A complete fixture scores 100; each seeded defect is checked
# for its own message or its own lost points, the way tools/tracecheck.py was proved on a
# scratch fixture (docs/INSTRUCTION-CONTRACT.md).
#
# The fixture is a scoring specimen, not a seed. It is here so every axis has something
# complete to be measured against; it is not a design anyone should build, and a record
# that copies its sentences is measuring this file rather than a task.

FIXTURE = {
    "task": {
        "slug": "fixture-task", "category": "Software", "label": "Algorithms",
        "tags": ["skew-bounded-ordering", "span-adoption", "self-time-accounting"],
        "status": "idea",
    },
    "mechanism": {
        "sentence": "Rebuild the parent-child order of recorded spans when clocks disagree "
                    "inside a stated bound, retries duplicate a span under one identifier, "
                    "and orphans must be adopted by the nearest surviving ancestor rather "
                    "than by topological order alone.",
        "substrate": "a trace collector that ingests spans emitted by several hosts whose "
                     "clocks drift within a declared bound",
        "graded_output": "one line per span giving its settled parent and its self time in "
                         "microseconds, in emission order",
        "failure_mode": "sorting spans by timestamp and attaching each to the most recent "
                        "open span, which survives every ordinary trace and loses on skew",
        "interaction": "the duplicate-collapse rule decides which start stamp exists, and "
                       "the skew bound decides whether that stamp can precede its parent",
    },
    "nearest": {
        "public": {
            "name": "the OpenTelemetry span specification and its sampling notes",
            "url": "https://opentelemetry.io/docs/specs/otel/trace/api/",
            "covers": "how spans carry identifiers, parents and timestamps, and what a "
                      "collector is expected to store for each one",
            "plans_this": False,
            "separation": "the specification leaves collectors free to reject or keep a span "
                          "whose parent has not arrived, and says nothing about adopting "
                          "orphans under a skew bound or collapsing retries",
        },
        "submitted": {
            "name": "note-carry-forward",
            "source": "ledger",
            "shares": "both reattach records to a structure that moved beneath them, and "
                      "both grade a settled position per record",
            "same_mechanism": False,
            "separation": "note-carry-forward moves a thread across revisions of one file "
                          "using an edit script, so its evidence is a diff; here nothing is "
                          "edited and the structure is rebuilt from disagreeing clocks, so "
                          "the deciding evidence is a bound on skew and a duplicate rule",
        },
    },
    "axes": {"differentiators": [
        {"axis": "mechanism", "theirs": "aligns a span of lines across an edit script",
         "ours": "settles a parent per span under a clock-skew bound"},
        {"axis": "substrate", "theirs": "a code review tool over branch revisions",
         "ours": "a trace collector ingesting spans from drifting hosts"},
        {"axis": "graded_output", "theirs": "the state of each thread after every revision",
         "ours": "a parent and a self time for every span in emission order"},
        {"axis": "failure_mode", "theirs": "carrying a thread forward line by line",
         "ours": "ordering spans by timestamp and nesting by arrival"},
    ]},
    "search": {
        "queries": ["distributed trace parent reconstruction clock skew",
                    "span orphan adoption collector algorithm",
                    "duplicate retried span identifier collapse tracing",
                    "self time exclusive time span overlapping children"],
        "results": "the retrievable material covers how to compute exclusive time given a "
                   "correct tree, and vendor documentation says orphans are dropped; nothing "
                   "found settles a parent when the recorded stamps contradict the bound",
        "twin_found": False,
    },
    "collision": {
        "archetype": "topological sort or dependency resolver",
        "on_list": True,
        "departure": "a resolver is handed edges it can trust, and every write-up assumes "
                     "the edge set is the truth; here the edges are recorded by clocks that "
                     "disagree, a retry can present two starts for one identifier, and the "
                     "graded self time depends on which of the two the collapse rule keeps",
    },
}

FIXTURE_LEDGER = [
    {"slug": "note-carry-forward", "category": "Software", "label": "Algorithms",
     "tags": ["diff-alignment", "revision-history", "differential-testing"],
     "substrate": "a code review tool whose threads follow lines across branch revisions",
     "mechanism": "Carry review threads across revisions of a branch by settling the edit "
                  "script between two revisions and deciding where each thread now stands."},
    {"slug": "token-seam-emit", "category": "ML", "label": "Inference",
     "tags": ["byte-level-bpe", "stop-sequences", "utf8-boundaries"],
     "substrate": "an inference server deciding which bytes to release on the wire",
     "mechanism": "Release bytes from a streaming decode only when no stop sequence and no "
                  "character boundary can still change what has already left."},
]


def _deep(rec: dict) -> dict:
    import copy
    return copy.deepcopy(rec)


def selftest() -> int:
    def score(rec, ledger=None):
        return score_record(rec, None, ledger if ledger is not None else FIXTURE_LEDGER, [])

    failures = []
    base = score(FIXTURE)
    if base.total != 100 or base.stops:
        failures.append("the complete fixture scores %d with %d stops, not a clean 100"
                        % (base.total, len(base.stops)))
        for name, pts, mx, notes in base.axes:
            if pts < mx:
                failures.append("   %s %d/%d: %s" % (name, pts, mx, "; ".join(notes)))

    cases: list[tuple[str, dict, tuple]] = []

    def seed(name, mutate, expect):
        rec = _deep(FIXTURE)
        mutate(rec)
        cases.append((name, rec, expect))

    seed("public write-up plans the task",
         lambda r: r["nearest"]["public"].update(plans_this=True), ("stop", "findable online"))
    seed("same mechanism as a submitted task",
         lambda r: r["nearest"]["submitted"].update(same_mechanism=True), ("stop", "reskin"))
    seed("a twin was found",
         lambda r: r["search"].update(twin_found=True), ("stop", "same graded work"))
    seed("retired label",
         lambda r: r["task"].update(label="Systems"), ("stop", "retired"))
    seed("label outside its category",
         lambda r: r["task"].update(label="Kernels"), ("stop", "not a label of"))
    seed("two tags already carried by one ledger entry",
         lambda r: r["task"].update(tags=["diff-alignment", "revision-history", "spans"]),
         ("stop", "share 2 tags"))
    seed("only two surfaces separated",
         lambda r: r["axes"].update(differentiators=r["axes"]["differentiators"][:2]),
         ("axis", "distinctness surfaces", 12))
    seed("crowded archetype declared clear",
         lambda r: r["collision"].update(on_list=False),
         ("axis", "crowded-archetype check", 4))
    seed("nearest submitted task not named",
         lambda r: r["nearest"]["submitted"].update(name="none found"),
         ("axis", "nearest submitted task", 15))
    seed("search run twice, not four times",
         lambda r: r["search"].update(queries=r["search"]["queries"][:2]),
         ("axis", "search evidence", 5))
    seed("substrate reused from a ledger entry",
         lambda r: r["mechanism"].update(
             substrate="a code review tool whose threads follow lines across branch revisions"),
         ("axis", "ledger separation", 7))
    seed("mechanism sentence restates a ledger entry",
         lambda r: r["mechanism"].update(
             sentence="Carry review threads across revisions of a branch by settling the edit "
                      "script between two revisions and deciding where each thread stands now."),
         ("axis", "ledger separation", 7))

    for name, rec, expect in cases:
        s = score(rec)
        if expect[0] == "stop":
            if not any(expect[1] in st for st in s.stops):
                failures.append("%s: no stop mentioning %r (stops: %s)"
                                % (name, expect[1], s.stops or "none"))
            elif s.total > HARD_STOP_CAP:
                failures.append("%s: stop fired but the score was not capped" % name)
        else:
            _, axis_name, cap = expect
            got = next((p for n, p, _, _ in s.axes if n == axis_name), None)
            if got is None:
                failures.append("%s: no axis named %s" % (name, axis_name))
            elif got > cap:
                failures.append("%s: %s scored %d, expected %d or less"
                                % (name, axis_name, got, cap))

    # The corpus metric, on documents whose relationship is known: a reworded copy has to
    # land past the stops, and two unrelated instructions under the ceilings.
    docs = instruction_corpus([])
    if len(docs) >= 4 and "focus-return-point" in docs:
        original = docs["focus-return-point"]
        reworded = original.replace("focus", "cursor").replace("widget", "element")
        near = Corpus({**docs, "__reworded__": reworded}).compare("__reworded__", reworded)
        top, top_sh = near[0], max(x for _, x, _ in near)
        if top[2] != "focus-return-point" or top[0] < COS_STOP or top_sh < SHINGLE_STOP:
            failures.append("corpus metric: a reworded instruction scored %.3f cosine / %.3f "
                            "shingle against its original (nearest %s), inside the stops that "
                            "are supposed to catch reworded prose" % (top[0], top_sh, top[2]))
        worst = max(Corpus(docs).compare(name, text)[0][0] for name, text in docs.items())
        if worst > COS_CEILING:
            failures.append("corpus metric: two accepted instructions scored %.3f, above the "
                            "%.2f ceiling" % (worst, COS_CEILING))
    else:
        failures.append("corpus metric: fewer than four bundles in tasks/ to measure against")

    print("Self-test: 1 complete fixture, %d seeded defects, 2 corpus cases" % len(cases))
    for name, _, expect in cases:
        print("   seeded  %-42s -> %s" % (name, expect[0]))
    if failures:
        print()
        for f in failures:
            print("   FAIL %s" % f)
        return 1
    print("   every stop and axis fired on its own defect; the fixture scores 100")
    return 0


def main(argv: list[str]) -> int:
    args, extra_dirs = [], []
    i = 1
    while i < len(argv):
        if argv[i] == "--corpus" and i + 1 < len(argv):
            extra_dirs.append(Path(argv[i + 1]))
            i += 2
            continue
        args.append(argv[i])
        i += 1
    if not args:
        print(__doc__)
        return 2
    if args[0] == "--calibrate":
        return calibrate(extra_dirs)
    if args[0] == "--selftest":
        return selftest()
    if args[0] == "--nearest":
        if len(args) < 2:
            print("--nearest needs a path to a text file")
            return 2
        return nearest(Path(args[1]), extra_dirs)
    if args[0] == "--all":
        worst, seen = 0, 0
        for d in sorted((ROOT / "authoring").iterdir()):
            if (d / "originality.toml").is_file():
                seen += 1
                worst = max(worst, run_one(d.name, extra_dirs, verbose=False))
                print()
        if not seen:
            print("no originality record under authoring/ - a task whose distinctness was never "
                  "scored is one the similarity screen scores instead (docs/ORIGINALITY.md)")
            return 2
        if worst == 0:
            print("all %d originality records under authoring/ are at or above the floor" % seen)
        return worst
    return run_one(args[0], extra_dirs)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
