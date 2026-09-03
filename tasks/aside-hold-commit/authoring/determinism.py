"""The generated set must be the same in every process, whatever PYTHONHASHSEED is."""
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.join(os.path.dirname(HERE), "tests")

SNIP = (
    "import sys, json, hashlib; sys.path.insert(0, %r); import gen; "
    "print(hashlib.sha256(json.dumps([[n, {'stops':[s.decode('latin1') for s in j['stops']], "
    "'scripts':{k:[t.decode('latin1') for t in v] for k,v in sorted(j['scripts'].items())}, "
    "'turns':dict(sorted(j['turns'].items()))}] for n, j in gen.jobs('probe', 120)], "
    "sort_keys=True).encode()).hexdigest())" % TESTS
)


def main():
    seen = []
    for seed in ("0", "1", "17", "4242"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        out = subprocess.run([sys.executable, "-c", SNIP], env=env,
                             capture_output=True, text=True, check=True)
        seen.append(out.stdout.strip())
    ok = len(set(seen)) == 1
    print("digests:", *seen, sep="\n  ")
    print("determinism", "OK" if ok else "BROKEN")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
