import hashlib
import json
import os
import sys
import traceback

WORK = os.environ.get("APPDIR", "/work/app")
sys.path.insert(0, WORK)
sys.path.insert(0, "/tests")

import cases  # noqa: E402
import gen  # noqa: E402


def digest(mod, names):
    h = hashlib.sha256()
    for n in sorted(names):
        f = getattr(mod, n, None)
        code = getattr(f, "__code__", None)
        if code is None:
            h.update(b"?")
            continue
        h.update(code.co_code)
        h.update(repr(code.co_consts).encode())
    return h.hexdigest()


def blocks(nonce):
    out = [("fixed", nm, rows, ops) for nm, rows, ops in cases.FIXED]
    for i in range(300):
        rows, ops = gen.stream("%s-%d" % (nonce, i), i % 2 == 0)
        out.append(("gen", "g%04d" % i, rows, ops))
    return out


def main(dest):
    nonce = os.environ.get("SHR_NONCE", "0")
    rec = {"nonce": nonce, "runs": {}, "fault": None}
    try:
        from wire import core, plan, reg, scope
        rec["seal"] = {
            "core": digest(core.Core, ["build", "fire", "mint", "forget", "since", "mark"]),
            "reg": digest(reg, ["load", "reach"]),
            "scope": digest(scope.Stack, ["open", "close", "top", "under", "holds"]),
        }
        for kind, name, rows, ops in blocks(nonce):
            try:
                got = plan.run(reg.load(rows), ops)
                rec["runs"][name] = [[str(x) for x in r] for r in got]
            except Exception:
                rec["runs"][name] = {"error": traceback.format_exc()[-400:]}
    except Exception:
        rec["fault"] = traceback.format_exc()[-800:]
    with open(dest, "w") as fh:
        json.dump(rec, fh)


main(sys.argv[1])
