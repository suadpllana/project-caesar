#!/bin/bash
# Reference solution. Proves the task is solvable.
#
# This runs in the agent's environment and must produce every artifact the verifier reads,
# scoring 1 via:  harbor run -p . -a oracle -e docker
#
# It should reflect how a competent expert would actually do this work. Do not shortcut
# straight to writing the expected output: a solution that games the verifier hides the
# fact that the verifier can be gamed, and the anti-cheat probe will find it later.
#
# If this script finishes in seconds, treat that as evidence the task is too easy.

set -euo pipefail

# TODO: implement the reference solution.

echo "TODO: solution not implemented" >&2
exit 1
