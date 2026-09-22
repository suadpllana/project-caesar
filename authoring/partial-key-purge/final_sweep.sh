#!/bin/bash
# The container gates, in one pass, on freshly built images. Authoring only.
A=/home/user/project-caesar/authoring/partial-key-purge
T=/home/user/project-caesar/tasks/partial-key-purge
set -u
python3 $A/sync_pristine.py --check || exit 1
python3 $A/build_gt.py | tail -1
echo "== oracle"; timeout 2400 python3 $A/local_trial.py --cpus 1 --memory 2g oracle 2>&1 | tail -3
echo "== nop"; timeout 1200 python3 $A/local_trial.py --cpus 1 --memory 2g nop 2>&1 | tail -3
echo "== timings"
for d in $T/solution $A/variants/chk $A/variants/walk; do timeout 1200 bash $A/time_container.sh $d; done
echo "== variants through docker_trial"
for d in $A/variants/chk $A/variants/walk; do timeout 1200 python3 $A/local_trial.py --cpus 1 --memory 2g --dir $d 2>&1 | tail -3; done
echo "== forgecheck (runs every cheat through cheat_report.py)"
cd /home/user/project-caesar && timeout 5400 python3 tools/forgecheck.py partial-key-purge
echo "== done"
