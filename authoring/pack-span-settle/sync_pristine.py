"""Keep tests/pristine in step with the shipped tree.

The verifier lays the six submitted modules over its own copy of the tree, so that copy has to
be the tree the agent was given. It is a copy, and copies go stale: rebuilding the environment
without re-syncing makes the oracle fail with an ImportError inside the worker, which reads
like a broken task rather than a stale mirror.

The shards are left out: the worker writes the shard it is replaying, and shipping a megabyte
of them into the verifier image buys nothing.

    python3 sync_pristine.py            copy environment/app_src into tests/pristine
    python3 sync_pristine.py --check    exit 1 if they differ
"""
import filecmp
import pathlib
import shutil
import sys

TASK = pathlib.Path(__file__).resolve().parents[2] / "tasks" / "pack-span-settle"
SRC = TASK / "environment" / "app_src"
DST = TASK / "tests" / "pristine"
KEEP = ("run_shard.py", "pipe")


def wanted():
    out = []
    for name in KEEP:
        one = SRC / name
        if one.is_file():
            out.append(pathlib.Path(name))
        else:
            for p in sorted(one.rglob("*.py")):
                out.append(p.relative_to(SRC))
    return out


def main(argv):
    check = "--check" in argv
    bad = []
    for rel in wanted():
        src, dst = SRC / rel, DST / rel
        if check:
            if not dst.is_file() or not filecmp.cmp(src, dst, shallow=False):
                bad.append(str(rel))
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)
    if check:
        extra = [str(p.relative_to(DST)) for p in sorted(DST.rglob("*.py"))
                 if p.relative_to(DST) not in wanted()]
        for name in extra:
            bad.append(name + " (not in the shipped tree)")
        if bad:
            print("pristine is stale: %s" % ", ".join(bad))
            return 1
        print("pristine matches the shipped tree (%d files)" % len(wanted()))
        return 0
    print("synced %d files into tests/pristine" % len(wanted()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
