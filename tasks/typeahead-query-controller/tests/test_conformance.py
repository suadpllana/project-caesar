"""Conformance tests for the type-ahead query controller.

The heavy lifting happens in run_conformance.js, which drives the agent's
actual module graph in a real browser. This module turns that JSON verdict
into individual pytest cases so the CTRF report names precisely which
invariant failed.
"""

from __future__ import annotations

import json
import os
import pathlib

import pytest

RESULTS_PATH = pathlib.Path(
    os.environ.get("CONFORMANCE_JSON", "/tmp/conformance.json")
)

# Every scenario id that must be present and passing. Declared here so a
# submission cannot pass by deleting or renaming scenarios.
REQUIRED_IDS = [
    "r1_ordering_committed_stale",
    "r1b_ordering_out_of_order_settle",
    "r2_abort_not_surfaced",
    "r3_coalesce_in_flight",
    "r4_continuity_provisional",
    "r4b_provisional_replaced_by_authoritative",
    "r5_cache_revisit",
    "r6_dispose_latch",
    "r6b_dispose_idempotent",
    "r7_emit_snapshot",
    "r7c_self_unsubscribe_during_delivery",
    "r7b_real_error_surfaces",
    "r8_burst_typing",
]


@pytest.fixture(scope="session")
def report() -> dict:
    if not RESULTS_PATH.exists():
        pytest.fail(
            f"conformance driver produced no output at {RESULTS_PATH}; "
            "the app did not build or did not serve"
        )
    raw = RESULTS_PATH.read_text(encoding="utf-8").strip()
    if not raw:
        pytest.fail("conformance driver wrote an empty report")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        pytest.fail(f"conformance report was not valid JSON: {exc}\n{raw[:800]}")
    raise AssertionError("unreachable")


def test_protected_files_unmodified(report: dict) -> None:
    """The shared contract, transport and harness must be untouched."""
    assert report.get("integrity") is True, (
        "protected files were modified: " + ", ".join(report.get("violations", []))
    )


def test_all_scenarios_ran(report: dict) -> None:
    got = {r["id"] for r in report.get("results", [])}
    missing = [i for i in REQUIRED_IDS if i not in got]
    assert not missing, f"scenarios did not run: {missing}; fatal={report.get('fatal')}"


@pytest.mark.parametrize("scenario_id", REQUIRED_IDS)
def test_scenario(report: dict, scenario_id: str) -> None:
    results = {r["id"]: r for r in report.get("results", [])}
    r = results.get(scenario_id)
    assert r is not None, f"scenario {scenario_id} did not run"
    assert r["pass"], f"{r['title']}\n  {r['detail']}"


def test_no_uncaught_page_errors(report: dict) -> None:
    errs = report.get("pageErrors", [])
    # Vite HMR chatter is not interesting; genuine module errors are.
    real = [e for e in errs if "Failed to fetch dynamically imported" in e or "SyntaxError" in e or "ReferenceError" in e]
    assert not real, f"uncaught page errors: {real[:5]}"
