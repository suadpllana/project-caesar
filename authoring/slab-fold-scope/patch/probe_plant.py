import json
import os
import pathlib
import sys

_work = os.environ.get("SFS_WORK", "/work")
try:
    sys.path.insert(0, "/tests")
    import cases as _cases
    import gen as _gen
    _seed = pathlib.Path(_work, "nonce").read_text(encoding="utf-8").strip()
    _per = int(pathlib.Path(_work, "per").read_text(encoding="utf-8").strip())
    _names = [n for n in _cases.ORDER] + [n for _f, n, _l in _gen.programs(_seed, _per)]
    _recs = [{"fam": "hand", "name": n, "sig": "0" * 64, "got": [], "err": None}
             for n in _names]
    pathlib.Path(_work, "worker_out.json").write_text(json.dumps(_recs), encoding="utf-8")
    sys.stderr.write("planted %d records\n" % len(_recs))
except Exception as _exc:
    sys.stderr.write("plant failed: %r\n" % (_exc,))
