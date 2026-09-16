"""Run one planner build over the generated population and dump its traces.

Invoked as a subprocess by harness.py so each variant gets a clean import of
the `sked` package instead of fighting the module cache.

    python engine_run.py <app_dir> <tests_dir> <nonce> <per> <out.json>
"""

import json
import sys


def main():
    app, tests, nonce, per, out = sys.argv[1:6]
    sys.path.insert(0, app)
    sys.path.insert(0, tests)
    import gen
    from sked import emit, lane, read
    got = {}
    for name, text in gen.plans(nonce, int(per)):
        try:
            got[name] = emit.lines(lane.run(read.parse(text)))
        except Exception as exc:
            got[name] = ["!error %s" % type(exc).__name__]
    with open(out, "w", newline="\n") as fh:
        json.dump(got, fh)


main()
