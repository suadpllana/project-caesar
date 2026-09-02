#!/bin/bash
# Verifier entry point, written as five steps that have to happen in this order.
#
# One rule decides the order: nothing the submission executes may be able to reach the
# reward, the answers, or the file it is graded on. So the reward channel is closed and
# set to failure before a line of agent code is loaded; the answers, the sealed model and
# the grader are made root-only; the tree the run executes is a fresh copy of the shipped
# one with only the four declared artifacts laid over it, owned by root and read-only to
# the run; the report is opened here, as root, in a directory the run cannot enter, and
# handed over as an inherited descriptor so the uid that runs agent code never owns the
# file its grade comes from; and grading happens afterwards, as root, in pytest, which
# imports none of it.
#
# The nonce is made here, from /dev/urandom, after the agent has stopped. It picks the
# registers the submission is actually graded on, and both sides are given it so the run
# and the grader are answering about the same registers.
set -Eeuo pipefail

REWARD_DIR=/logs/verifier
VAULT=/tests/out
APP=/work/app
PEN=/work/pen
RUNAS=1002
HOW_MANY=320

deny_first() {
  mkdir -p "$REWARD_DIR"
  chown root:root "$REWARD_DIR"
  chmod 700 "$REWARD_DIR"
  echo 0 > /logs/verifier/reward.txt
}

seal_the_answers() {
  chown root:root /tests/gt.json /tests/oracle.py /tests/test_outputs.py
  chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py
  rm -rf "$VAULT"
  install -d -o root -g root -m 700 "$VAULT"
}

lay_the_tree() {
  rm -rf /work
  mkdir -p "$APP"
  cp -a /pristine/. "$APP/"
  for rel in pol/screen.py pol/voice.py pol/tally.py pol/note.py; do
    [ -f "/app/$rel" ] && cp -f "/app/$rel" "$APP/$rel"
  done
  find "$APP" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
  find "$APP" -name '*.pyc' -delete 2>/dev/null || true
  chown -R root:root /work
  chmod -R u=rwX,go=rX "$APP"
  chmod 755 /work
  install -d -o "$RUNAS" -g "$RUNAS" -m 700 "$PEN"
}

turn_it_over() {
  head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n' > "$VAULT/nonce"
  chmod 600 "$VAULT/nonce"
  : > "$VAULT/report.json"
  chmod 600 "$VAULT/report.json"
  local nonce
  nonce="$(cat "$VAULT/nonce")"
  set +e
  exec 9>"$VAULT/report.json"
  setsid --wait env APPDIR="$APP" TMPDIR="$PEN" HOME="$PEN" \
      PYTHONDONTWRITEBYTECODE=1 SRS_NONCE="$nonce" SRS_COUNT="$HOW_MANY" SRS_FD=9 \
      SRS_REQUIRE_MONITORING=1 \
    setpriv --reuid="$RUNAS" --regid="$RUNAS" --clear-groups \
    timeout --signal=KILL 540 python /tests/runner.py
  exec 9>&-
  python /tests/reap.py "$RUNAS"
  set -e
}

grade() {
  if SRS_REPORT="$VAULT/report.json" SRS_NONCEFILE="$VAULT/nonce" SRS_WORK="$APP" \
     pytest --ctrf "$REWARD_DIR/ctrf.json" /tests/test_outputs.py -rA; then
    echo 1 > /logs/verifier/reward.txt
  else
    echo 0 > /logs/verifier/reward.txt
  fi
}

deny_first
seal_the_answers
lay_the_tree
turn_it_over
grade
