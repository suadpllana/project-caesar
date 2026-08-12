#!/bin/bash
# Verifier entry point.
#
# The reward channel is locked and defaulted to 0 before anything the agent wrote is
# executed. Nothing the agent wrote is executed by this process or by the supervisor it
# starts: /tests/runner.py spawns one unprivileged child process per trainer life, in its
# own session, and talks to it over a pipe. The supervisor owns the corpus, the arithmetic
# kernels, the counters and the checkpoint channel, so what lands in the work file is its
# measurement rather than the trainer's account of itself, and the work file itself is
# root-owned and outside anything the trainer can write.
#
# The trainer's uid is given no writable directory anywhere on the filesystem. That is
# deliberate: a kill in a scenario has to be a kill, and a file, a cache or a socket left
# behind by one life would be a way around the bounded channel the task is built on.
#
# Grading happens afterwards, as root, in pytest, which never runs agent code and reads
# the ground truth, the graded corpus and the sealed trainer from root-only files.
set -Eeuo pipefail

mkdir -p /logs/verifier
chown root:root /logs/verifier
chmod 700 /logs/verifier
echo 0 > /logs/verifier/reward.txt

chown root:root /tests/gt.json /tests/oracle.py /tests/corpus.json
chmod 600 /tests/gt.json /tests/oracle.py /tests/corpus.json
chmod 700 /pristine

rm -rf /work
mkdir -p /work/app
cp -a /pristine/. /work/app/

# Overlay only the declared editable files. A file the agent never produced simply is
# not there, and the pristine copy stands.
for f in train/ckpt.py data/feed.py train/noise.py train/sched.py; do
  if [ -f "/app/$f" ]; then
    cp -f "/app/$f" "/work/app/$f"
  fi
done
find /work/app -name '__pycache__' -type d -prune -exec rm -rf {} +

# The trainer reads its tree and writes nothing: the tree is root-owned, and so is the
# work file the supervisor reports into.
chown -R root:root /work
chmod -R a-w,a+rX /work
chmod 755 /work /work/app

# Every place the trainer's uid could write is closed to it, so no life can leave
# anything on disk for the life that follows it. The scan covers the whole root
# filesystem; the mounted-over directories that -xdev skips are named as well, and
# test_outputs.py re-checks the result from the privileged side after the run.
for d in /tmp /var/tmp /dev/shm /run /run/lock /home/sandbox /var/lock; do
  if [ -d "$d" ]; then chown root:root "$d"; chmod 700 "$d"; fi
done
find / -xdev \( -perm -0002 -o -uid 1002 -o -gid 1002 \) -print0 2>/dev/null \
  | xargs -0 -r chown root:root 2>/dev/null || true
find / -xdev -perm -0002 -print0 2>/dev/null \
  | xargs -0 -r chmod o-w 2>/dev/null || true

set +e
setsid --wait env APPDIR=/work/app SUPDIR=/pristine LIFE_UID=1002 \
  PYTHONDONTWRITEBYTECODE=1 \
  timeout --signal=KILL 720 python /tests/runner.py /work/out.json
python /tests/reap.py 1002
set -e

if pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
