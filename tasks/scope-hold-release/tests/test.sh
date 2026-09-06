#!/bin/bash
set -Eeuo pipefail

mkdir -p /logs/verifier
chown root:root /logs/verifier
chmod 700 /logs/verifier
echo 0 > /logs/verifier/reward.txt

# Keep the answer model and grader unreadable to submitted code.
chown root:root /tests/gt.json /tests/oracle.py /tests/test_outputs.py
chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py

# Overlay only declared artifacts on a pristine executable tree.
WORK=/work
rm -rf "${WORK}"
mkdir -p "${WORK}/app" "${WORK}/run"
cp -a /pristine/. "${WORK}/app"

for rel in wire/own.py wire/pin.py wire/hold.py wire/gate.py wire/tear.py wire/shut.py wire/plan.py; do
  if [ -f "/app/${rel}" ]; then
    cp "/app/${rel}" "${WORK}/app/${rel}"
  fi
done

id -u sandbox >/dev/null 2>&1 || useradd -u 1002 -M -s /usr/sbin/nologin sandbox
chown -R 1002:1002 "${WORK}/app"
chmod 755 "${WORK}"
install -d -o sandbox -g sandbox -m 700 "${WORK}/scratch"

: > "${WORK}/run/out.json"
chown root:root "${WORK}/run" "${WORK}/run/out.json"
chmod 700 "${WORK}/run"
chmod 600 "${WORK}/run/out.json"

# Give the sandbox an inherited write descriptor, not a writable report path.
SHR_NONCE="$(head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \n')"
export SHR_NONCE

run_rc=0
set +e
exec 7>"${WORK}/run/out.json"
setsid --wait env APPDIR="${WORK}/app" TMPDIR="${WORK}/scratch" HOME="${WORK}/scratch" \
    SHR_NONCE="${SHR_NONCE}" PYTHONDONTWRITEBYTECODE=1 \
  setpriv --reuid=1002 --regid=1002 --clear-groups \
  timeout --signal=KILL 600 python /tests/runner.py fd:7
run_rc=$?
exec 7>&-
python /tests/reap.py 1002
reap_rc=$?
set -e

# Trust the report only after both the runner and survivor reaper succeed.
if [ "${run_rc}" -eq 0 ] && [ "${reap_rc}" -eq 0 ]; then
  RUNNER_OK=1
else
  RUNNER_OK=0
fi

if RUNNER_OK="${RUNNER_OK}" WORKAPP="${WORK}/app" python -m pytest \
      /tests/test_outputs.py -q --ctrf /logs/verifier/ctrf.json ; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
