#!/bin/bash
set -u

mkdir -p /logs/verifier
chmod 700 /logs/verifier
echo 0 > /logs/verifier/reward.txt

WORK=/work
rm -rf "${WORK}"
mkdir -p "${WORK}"
cp -a /pristine/. "${WORK}/app"

for rel in wire/own.py wire/pin.py wire/hold.py wire/gate.py wire/tear.py wire/shut.py wire/plan.py; do
  if [ -f "/app/${rel}" ]; then
    cp "/app/${rel}" "${WORK}/app/${rel}"
  fi
done

SHR_NONCE="$(head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \n')"
export SHR_NONCE

id -u sandbox >/dev/null 2>&1 || useradd -u 1002 -M -s /usr/sbin/nologin sandbox
chown -R 1002:1002 "${WORK}"

setsid --wait env APPDIR="${WORK}/app" SHR_NONCE="${SHR_NONCE}" \
  setpriv --reuid=1002 --regid=1002 --clear-groups \
  timeout --signal=KILL 600 python /tests/runner.py "${WORK}/out.json"

python /tests/reap.py 1002 || true

if WORKAPP="${WORK}/app" python -m pytest /tests/test_outputs.py -q \
      --ctrf /logs/verifier/ctrf.json ; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
