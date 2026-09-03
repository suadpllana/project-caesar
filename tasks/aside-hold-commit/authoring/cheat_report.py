"""Which test catches each cheat, and is it the one that should have.

A sweep that only reads the reward cannot tell a probe that was rejected from a probe that never
ran, and a probe rejected by the wrong layer says nothing about the layer it was aimed at. So this
asserts an expectation per cheat rather than a reward per cheat.

  a value cheat        has to be caught by a test that reads the trace
  an attestation probe has to be caught by ITS OWN attestation and by nothing else. Each of the
                       four is built on the reference, so every answer it gives is correct and the
                       only thing left to reject it is the layer it was aimed at
  a reward probe       has to score 0 and to have reached the tree at all
"""
import os
import subprocess
import sys

import stage
import trial

VALUE = {"test_named_job", "test_the_generated_jobs",
         "test_no_job_faulted_or_took_a_release_back"}
# Caught by this and by nothing else. Both probes are the reference with one attestation
# interfered with, so their answers are all correct and there is nothing else left to reject them.
OWN = {
    "patch-driver": {"test_the_sealed_driver_is_the_one_we_shipped"},
    "rewrite-kernel": {"test_the_executed_tree_was_the_one_we_shipped"},
}

# These two cannot be value-clean by construction, so the expectation is that their own layer
# fires rather than that it fires alone. Switching the instrumentation off stops both tallies,
# which are one attestation with two readings; pushing a row into the trace is a change to the
# trace, which is the thing being compared.
MUST_FIRE = {
    "kill-monitor": {"test_every_job_was_driven",
                     "test_the_dispatches_in_the_trace_really_happened",
                     "test_the_instrumentation_was_still_on_at_the_end"},
    "forge-dispatch": {"test_the_dispatches_in_the_trace_really_happened"},
}


def failing(work_report, tests, app, pristine, nonce, count):
    env = dict(os.environ, RUN_OUT=work_report, APP_DIR=app, PRISTINE_DIR=pristine,
               RUN_NONCE=nonce, RUN_COUNT=str(count), PYTHONPATH=tests,
               PYTHONDONTWRITEBYTECODE="1")
    out = subprocess.run([sys.executable, "-m", "pytest", "-q", "--no-header", "-rf",
                          os.path.join(tests, "test_outputs.py")],
                         env=env, capture_output=True, text=True)
    names = set()
    for line in out.stdout.splitlines():
        if line.startswith("FAILED "):
            node = line.split()[1]
            names.add(node.split("::")[-1].split("[")[0])
    return names, out.returncode


def main():
    trial.check_host()
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    import shutil
    import tempfile
    bad = 0
    for name in sorted(os.listdir(trial.CHEATS)):
        if not name.endswith(".sh"):
            continue
        slug = name[3:-3] if name.startswith("che") else name[:-3]
        slug = name[len("cheat-"):-len(".sh")]
        work = tempfile.mkdtemp(prefix="ahc-report-")
        try:
            app, tests, pristine = trial.lay(work, None)
            trial.play(app, os.path.join(trial.CHEATS, name))
            report = os.path.join(work, "out.json")
            nonce = "report-%s" % slug
            env = dict(os.environ, APPDIR=app, RUN_NONCE=nonce, RUN_COUNT=str(count),
                       PYTHONPATH=os.pathsep.join([app, tests]), PYTHONDONTWRITEBYTECODE="1")
            run = subprocess.run([sys.executable, os.path.join(tests, "runner.py"), report],
                                 env=env, capture_output=True, text=True, cwd=work)
            if not os.path.exists(report):
                print("BAD  %-22s wrote no report, so no layer rejected it: %s"
                      % (slug, run.stderr.strip().splitlines()[-1:] or ""))
                bad += 1
                continue
            names, rc = failing(report, tests, app, pristine, nonce, count)
            if rc == 0:
                print("BAD  %-22s reward 1" % slug)
                bad += 1
                continue
            must = MUST_FIRE.get(slug)
            if must is not None:
                if names & must:
                    print("ok   %-22s its own attestation fired: %s"
                          % (slug, sorted(names & must)))
                else:
                    print("BAD  %-22s caught by %s, its own attestation never fired"
                          % (slug, sorted(names)))
                    bad += 1
                continue
            want = OWN.get(slug)
            if want is not None:
                if not (names & want):
                    print("BAD  %-22s caught by %s, not by its own attestation %s"
                          % (slug, sorted(names), sorted(want)))
                    bad += 1
                elif names - want:
                    print("BAD  %-22s caught by its own attestation AND by %s, so the probe is "
                          "wrong on values too" % (slug, sorted(names - want)))
                    bad += 1
                else:
                    print("ok   %-22s caught by %s and nothing else" % (slug, sorted(names)))
            else:
                if not (names & VALUE):
                    print("BAD  %-22s caught by %s, none of which reads the trace"
                          % (slug, sorted(names)))
                    bad += 1
                else:
                    print("ok   %-22s caught by %s" % (slug, sorted(names & VALUE)))
        finally:
            shutil.rmtree(work, ignore_errors=True)
    print("%d unexpected" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
