#!/bin/bash
# Reference solution: install the three decision modules of the debugger.
#
# frames.py  scope chains, caller frames at the call instruction, hidden depth
# marks.py   breakpoint locations: lowest statement row per function body or instance
# steps.py   run control that drives the target by planted addresses: the exits of the
#            current row, the return address over a call (checked against the frame on
#            every stop), and the exit of an inline instance for next and finish
#
# The engine never single-steps: every command is a handful of link round trips however
# long the loops it crosses run, which is what the stated limit requires.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for f in frames.py marks.py steps.py; do
    cp "$here/$f" "/app/dbg/$f"
done
