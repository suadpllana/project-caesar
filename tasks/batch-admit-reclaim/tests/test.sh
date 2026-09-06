#!/bin/bash
# Verifier entry point. The order below is the argument rather than a convenience.
set -Eeuo pipefail

SAND=1002
BOX=/box
KEEP="$BOX/say/out.json"

seal_reward() {
  # Nothing derived from agent code may reach this directory, so it is closed
  # and defaulted to a loss before any of that code is loaded.
  mkdir -p /logs/verifier
  chown root:root /logs/verifier
  chmod 700 /logs/verifier
  echo 0 > /logs/verifier/reward.txt
  chown root:root /tests/gt.json /tests/oracle.py /tests/test_outputs.py
  chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py
}

lay_tree() {
  # The executed tree is built root-owned and read-only from the untouched copy,
  # with only the four declared artifacts laid over it. An edit anywhere else is
  # impossible rather than merely detectable.
  rm -rf "$BOX"
  mkdir -p "$BOX/app" "$BOX/say"
  cp -a /pristine/. "$BOX/app/"
  for rel in eng/fit.py eng/room.py eng/back.py eng/pick.py; do
    [ -f "/app/$rel" ] && cp -f "/app/$rel" "$BOX/app/$rel"
  done
  find "$BOX/app" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
  find "$BOX/app" -name '*.pyc' -delete 2>/dev/null || true
  chown -R root:root "$BOX"
  chmod -R u=rwX,go=rX "$BOX/app"
  chmod 755 "$BOX" "$BOX/say"
  install -d -o runner -g runner -m 700 "$BOX/tmp"
  : > "$KEEP"
  chown root:root "$KEEP"
  chmod 600 "$KEEP"
}

seal_reward
lay_tree

# Drawn here, once the agent has stopped, and handed to both the run and the
# grader so the two are talking about the same three hundred traces.
RUN_NONCE="$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')"
RUN_COUNT=300
export RUN_NONCE RUN_COUNT

# The run publishes into a descriptor root opened before the privilege drop, so
# the account executing agent code does not own the file it is graded from. It
# gets its own session and a wall clock, and whatever it leaves behind is reaped.
set +e
exec 9>"$KEEP"
setsid --wait env APPDIR="$BOX/app" TMPDIR="$BOX/tmp" HOME="$BOX/tmp" \
    PYTHONDONTWRITEBYTECODE=1 RUN_NONCE="$RUN_NONCE" RUN_COUNT="$RUN_COUNT" \
  setpriv --reuid=$SAND --regid=$SAND --clear-groups \
  timeout --signal=KILL 600 python /tests/runner.py fd:9
exec 9>&-
python /tests/reap.py "$SAND"
set -e

# pytest grades as root and imports nothing the submission wrote.
if RUN_OUT="$KEEP" APP_DIR="$BOX/app" PRISTINE_DIR=/pristine \
   RUN_NONCE="$RUN_NONCE" RUN_COUNT="$RUN_COUNT" \
   pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
