"""Trusted shell statuses are required in addition to a correct worker report.

These values are set by the root-owned shell after the unprivileged worker and
cleanup process return. Agent code cannot make a failed process look successful
by writing an otherwise valid report before exiting or leaving live descendants.
"""

import os


def test_worker_exited_cleanly():
    status = os.environ.get("WORKER_EXIT")
    assert status == "0", "worker did not exit cleanly: %r" % status


def test_worker_descendants_were_reaped():
    status = os.environ.get("REAPER_EXIT")
    assert status == "0", "worker cleanup did not finish cleanly: %r" % status
