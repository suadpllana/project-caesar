"""Run the enumerated hand cases through a staged tree and compare with gt.json."""
import json
import sys

from stage import TASK, TESTS, stage

sys.path.insert(0, str(TESTS))

import cases  # noqa: E402
import readings  # noqa: E402

gt = json.loads((TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
where = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else None
tree = stage(where)
bad = []
for name in cases.ORDER:
    if readings.run(where or TASK / "environment" / "app_src" / "keep",
                    "\n".join(cases.ops(name))) != gt[name]:
        bad.append(name)
print("%d of %d hand cases wrong%s" % (len(bad), len(cases.ORDER),
                                       (": " + ", ".join(bad)) if bad else ""))
