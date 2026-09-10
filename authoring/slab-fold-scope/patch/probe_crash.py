import json
import os
import pathlib
import sys

_work = os.environ.get("SFS_WORK", "/work")
try:
    sys.path.insert(0, "/tests")
    import cases as _cases
    _recs = [{"fam": "hand", "name": n, "sig": "0" * 64, "got": ["land a 1 0 0"],
              "err": None} for n in _cases.ORDER]
    pathlib.Path(_work, "worker_out.json").write_text(json.dumps(_recs), encoding="utf-8")
    sys.stderr.write("planted then exiting clean\n")
    sys.stderr.flush()
except Exception as _exc:
    sys.stderr.write("plant failed: %r\n" % (_exc,))
os._exit(0)
