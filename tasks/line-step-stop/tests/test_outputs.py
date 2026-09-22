"""Report for line-step-stop, read from the trusted judge's verdict.

The judge (tests/judge.py) has already played every graded session through the submitted
debugger under an unprivileged user, against a target that alone holds each tape, and
compared every printed line with the expected one. Each test below reports one part of that
verdict, so a failing run says which part of the contract it broke.
"""
import json

import pytest

VERDICT = "/var/lib/judge/verdict.json"


@pytest.fixture(scope="module")
def v():
    with open(VERDICT) as f:
        return json.load(f)


def test_judge_finished(v):
    # The judge wrote a final verdict: it neither crashed nor stopped before playing.
    assert v.get("stage") in ("done", "play", "artifacts", "model", "cases"), v


def test_sealed_model_reproduces_frozen_lines(v):
    # The sealed model re-derives every frozen line of the enumerated cases and fences.
    assert v.get("model_drift") == [], v.get("model_drift")


def test_declared_files_present(v):
    # /app/dbg/marks.py, /app/dbg/frames.py and /app/dbg/steps.py were all handed in.
    assert v.get("missing") == [], v.get("missing")


def _group(v, group):
    assert v.get("stage") == "done", v.get("failed")
    assert v["passed"][group] == v["counts"][group], v.get("failed")


def test_samples(v):
    # The four sessions shipped in /app/samples, including the heavy one.
    _group(v, "sample")


def test_enumerated_cases(v):
    # One small session per wrong reading of the stop rules; each prints differently under
    # that reading, so a failure here names the rule that was misread.
    _group(v, "case")


def test_plain_fences(v):
    # Ordinary sessions - no inlining, no special rows - that an over-cautious debugger
    # (one that hides, reveals or stops too often) prints wrongly.
    _group(v, "fence")


def test_heavy_sessions(v):
    # Frozen sessions whose commands cross loops of hundreds of thousands of iterations
    # inside one row, inside called functions and inside inlined instances.
    _group(v, "heavy")


def test_generated_sessions(v):
    # Sessions generated inside the verifier from a fresh seed, every family of the
    # generator, checked line for line against the sealed model.
    _group(v, "nonce")


def test_whole_set_within_limit(v):
    # The stated wall clock for the whole graded set.
    assert v.get("spent") is not None and v["spent"] <= v["limit"], (v.get("spent"), v.get("limit"))


def test_verdict(v):
    assert v.get("ok") is True, v.get("failed")
