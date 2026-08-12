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
# The trainer's uid is given no writable directory that this image owns. That is
# deliberate: a kill in a scenario has to be a kill, and a file, a cache or a socket left
# behind by one life would be a way around the bounded channel the task is built on.
#
# Two rules govern the shape of this script, and they are the ones the earlier version got
# wrong. Hardening the image is best effort: a chown or a chmod that comes back refused
# describes the platform the verifier was handed rather than the submission, so every one
# of them ends in `|| true` and the two conditions that must hold, a locked reward channel
# and root-only answer material, are checked afterwards instead of assumed. Nothing else
# is unguarded: -e is on, and every step that can legitimately fail says what happens
# next, so the script neither dies quietly nor carries on past a real one. And what is
# graded about disk is what the run did, not what the image looked like: premark.py
# surveys the filesystem before the run and test_outputs.py surveys it again afterwards,
# so a writable path the verifier could not close costs the submission nothing unless the
# trainer actually wrote to it.
#
# Grading happens afterwards, as root, in pytest, which never runs agent code and reads
# the ground truth, the graded corpus and the sealed trainer from root-only files.
set -eEuo pipefail

REWARD=/logs/verifier/reward.txt

die() {
  echo "verifier: $*" >&2
  echo 0 > "$REWARD" 2>/dev/null || true
  exit 1
}

# The reward channel first, before anything else happens on this image.
mkdir -p /logs/verifier || die "no reward directory"
chown root:root /logs/verifier 2>/dev/null || true
chmod 700 /logs/verifier 2>/dev/null || true
echo 0 > "$REWARD" || die "the reward channel is not writable"

# Assumed above, checked here: a reward directory the run's uid could reach is a reward
# channel the run could write, and no result from this image would mean anything.
python - <<'PY' || die "the reward channel could not be locked"
import os, sys
sys.path.insert(0, "/tests")
from premark import _perm
st = os.stat("/logs/verifier")
# Write to place a file, search to reach one already there. Neither, and the run cannot
# touch the score however long it lives.
if _perm(st, 0o2) or _perm(st, 0o1):
    sys.exit(1)
PY

# The ground truth, the graded corpus and the sealed trainer are already root-only from
# the image build. Re-applying it costs nothing where /tests is writable and is skipped
# where it is not; either way the modes are checked before the run goes ahead.
chown root:root /tests/gt.json /tests/oracle.py /tests/corpus.json 2>/dev/null || true
chmod 600 /tests/gt.json /tests/oracle.py /tests/corpus.json 2>/dev/null || true
chmod 700 /pristine 2>/dev/null || true

python - <<'PY' || die "the answer material is not closed to the run on this image"
import os, sys
sys.path.insert(0, "/tests")
from premark import _perm
for p in ("/tests/gt.json", "/tests/oracle.py", "/tests/corpus.json", "/pristine"):
    st = os.stat(p)
    if _perm(st, 0o4) or _perm(st, 0o2) or _perm(st, 0o1):
        print("reachable by the run:", p, oct(st.st_mode), file=sys.stderr)
        sys.exit(1)
PY

rm -rf /work || true
mkdir -p /work/app || die "no work directory"
cp -a /pristine/. /work/app/ || die "the pristine tree did not copy"

# Overlay only the declared editable files. A file the agent never produced simply is
# not there, and the pristine copy stands.
for f in train/ckpt.py data/feed.py train/noise.py train/sched.py; do
  if [ -f "/app/$f" ]; then
    cp -f "/app/$f" "/work/app/$f" || die "the declared file $f did not overlay"
  fi
done
find /work/app -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true

# The trainer reads its tree and writes nothing: the tree is root-owned, and so is the
# work file the supervisor reports into.
chown -R root:root /work 2>/dev/null || true
chmod -R a-w,a+rX /work 2>/dev/null || true
chmod 755 /work /work/app 2>/dev/null || true

# Close the directories this image ships writable, so no life can leave anything on disk
# for the life that follows it. /app is in the list because the harness put the declared
# files there and they have served their purpose by now: everything the run reads was
# copied into /work above.
#
# None of this is allowed to stop the run, and none of it is graded. A directory the
# platform holds out of reach belongs to the platform rather than to the submission;
# premark.py records what stayed open and test_outputs.py grades what the trainer did
# with it, which is nothing.
for d in /tmp /var/tmp /dev/shm /run /run/lock /var/lock /home /home/sandbox /app; do
  if [ -e "$d" ]; then
    chown root:root "$d" 2>/dev/null || true
    chmod 700 "$d" 2>/dev/null || true
  fi
done

# The survey the disk check is differenced against: what the image looks like before any
# of the agent's code has run. Bounded in both time and size, and never fatal.
python /tests/premark.py /logs/verifier/premark.json 2>/dev/null || true

# A run that times out, crashes or is killed leaves the work file as it stands and the
# reward at 0; pytest still runs, so the report says which of those happened.
setsid --wait env APPDIR=/work/app SUPDIR=/pristine LIFE_UID=1002 \
  PYTHONDONTWRITEBYTECODE=1 \
  timeout --signal=KILL 720 python /tests/runner.py /work/out.json || true
python /tests/reap.py 1002 2>/dev/null || true

if pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA; then
  echo 1 > "$REWARD"
else
  echo 0 > "$REWARD"
fi
