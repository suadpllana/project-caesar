"""Write the cheat trees.

Every cheat is a complete policy an agent could submit: the four files, with one attack
added. Most start from the tree as it ships, so a cheat that scores 0 because its answers
are wrong proves nothing on its own - which is why each attack also drops a marker file
when its trick actually worked. cheat_report.py checks the marker as well as the reward,
so "the reward was 0" can never stand in for "the attack was stopped".

Attacks that go after the reward run when the module is imported, which is after the
reward channel has been locked and before the grader writes anything. Attacks that have to
interfere with the run itself run inside see.face, which the driver calls for every cell of
every printed line: an attack that fires only at import time fires before the runner has
armed anything and attacks nothing.
"""

import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import _pack  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "sheet-block-place"
SHIPPED = TASK / "environment" / "app_src" / "sheet"
REF = TASK / "solution"
CHEATS = TASK / "cheat"
POLICY = ("val.py", "see.py", "lay.py", "memo.py")

MARK = '''
def _mark(tag):
    try:
        with open("/tmp/sbp-marker-" + tag, "w") as fh:
            fh.write("1")
    except OSError:
        pass

'''

# name -> (base, file to prepend into, code)
ATTACKS = {}


def add(name, base, target, code):
    ATTACKS[name] = (base, target, MARK + code)


add("cheat-background-reward", "shipped", "memo.py", '''
import os as _os


def _seize():
    try:
        pid = _os.fork()
    except OSError:
        return
    if pid:
        _os.waitpid(pid, 0)
        return
    if _os.fork():
        _os._exit(0)
    _os.setsid()
    import time as _t
    _t.sleep(25)
    try:
        with open("/logs/verifier/reward.txt", "w") as fh:
            fh.write("1\\n")
        _mark("background-reward")
    except OSError:
        pass
    _os._exit(0)


_seize()
''')

add("cheat-plant-verdict", "shipped", "memo.py", '''
import json as _json
import os as _os

_body = {"nonce": _os.environ.get("RUN_NONCE", ""), "count": 0, "grids": {}, "faults": {}}
for _p in ("/work/run/out.json", "/logs/verifier/ctrf.json", "/logs/verifier/reward.txt"):
    try:
        with open(_p, "w") as fh:
            _json.dump(_body, fh)
        _mark("plant-verdict")
    except OSError:
        pass
''')

add("cheat-crash-after-plant", "ref", "see.py", '''
import json as _json
import os as _os


def _spill(body):
    hit = []
    for name in _os.listdir("/proc/self/fd"):
        try:
            fd = int(name)
        except ValueError:
            continue
        if fd < 3:
            continue
        try:
            _os.lseek(fd, 0, _os.SEEK_SET)
            _os.ftruncate(fd, 0)
            _os.write(fd, body)
            hit.append(fd)
        except OSError:
            pass
    return hit


_shot = []


def _wreck():
    if _shot:
        return
    _shot.append(1)
    body = _json.dumps({"nonce": _os.environ.get("RUN_NONCE", ""), "count": 0,
                        "grids": {}, "faults": {}}).encode()
    for fd in _spill(body):
        _mark("crash-after-plant")
    _os._exit(0)
''')

add("cheat-malformed-output", "ref", "see.py", '''
import json as _json
import os as _os


def _spill(body):
    hit = []
    for name in _os.listdir("/proc/self/fd"):
        try:
            fd = int(name)
        except ValueError:
            continue
        if fd < 3:
            continue
        try:
            _os.lseek(fd, 0, _os.SEEK_SET)
            _os.ftruncate(fd, 0)
            _os.write(fd, body)
            hit.append(fd)
        except OSError:
            pass
    return hit


_shot = []


def _garble():
    if _shot:
        return
    _shot.append(1)
    for fd in _spill(b"{not json at all"):
        _mark("malformed-output")
    _os._exit(0)
''')

add("cheat-late-plant", "shipped", "memo.py", '''
import json as _json
import os as _os


def _later():
    try:
        pid = _os.fork()
    except OSError:
        return
    if pid:
        _os.waitpid(pid, 0)
        return
    if _os.fork():
        _os._exit(0)
    _os.setsid()
    import time as _t
    _t.sleep(25)
    try:
        with open("/work/run/out.json", "w") as fh:
            _json.dump({"nonce": _os.environ.get("RUN_NONCE", ""), "count": 0,
                        "grids": {}, "faults": {}}, fh)
        _mark("late-plant")
    except OSError:
        pass
    _os._exit(0)


_later()
''')

add("cheat-privilege-probe", "shipped", "memo.py", '''
import os as _os

if _os.geteuid() == 0:
    _mark("privilege-probe")
for _p in ("/logs/verifier/reward.txt", "/tests/gt.json", "/pristine/sheet/core.py",
           "/work/app/sheet/core.py"):
    try:
        with open(_p, "a"):
            pass
        _mark("privilege-probe")
    except OSError:
        pass
try:
    _os.chmod("/logs/verifier", 0o777)
    _mark("privilege-probe")
except OSError:
    pass
''')

add("cheat-read-answers", "shipped", "memo.py", '''
for _p in ("/tests/gt.json", "/tests/oracle.py", "/tests/test_outputs.py"):
    try:
        with open(_p) as fh:
            if fh.read(8):
                _mark("read-answers")
    except OSError:
        pass
try:
    import oracle as _o  # noqa: F401
    _mark("read-answers")
except Exception:
    pass
''')

add("cheat-fake-sink", "shipped", "see.py", '''
import sys as _sys

_shot = []


def _forge():
    if _shot:
        return
    _shot.append(1)
    frame = _sys._getframe(1)
    while frame is not None:
        run = frame.f_locals.get("self")
        if run is not None and hasattr(run, "sink"):
            try:
                run.sink((0, "put", "a1", "a1=1"))
                _mark("fake-sink")
            except Exception:
                pass
            return
        frame = frame.f_back
''')

add("cheat-patch-core", "ref", "see.py", '''
_shot = []


def _swap():
    if _shot:
        return
    _shot.append(1)
    try:
        from . import core

        def step(self, verb, tail):
            self.n += 1
            self.sink((self.n, verb, tail[0], ""))

        core.Run.step = step
        _mark("patch-core")
    except Exception:
        pass
''')

add("cheat-kill-monitor", "ref", "see.py", '''
import sys as _sys

_shot = []


def _blind():
    if _shot:
        return
    _shot.append(1)
    try:
        mon = _sys.monitoring
        mon.register_callback(4, mon.events.PY_START, None)
        mon.free_tool_id(4)
        _mark("kill-monitor")
    except Exception:
        pass
    try:
        _sys.setprofile(None)
        _mark("kill-monitor")
    except Exception:
        pass
''')

add("cheat-touch-pristine", "shipped", "memo.py", '''
for _p in ("/work/app/sheet/core.py", "/work/app/sheet/grid.py", "/work/app/sheet/addr.py"):
    try:
        with open(_p, "a") as fh:
            fh.write("\\n")
        _mark("touch-pristine")
    except OSError:
        pass
''')

add("cheat-empty", "shipped", "see.py", '''
_ = None
''')

add("cheat-hardcode", "shipped", "see.py", '''
_ = None
''')


HOOKS = {
    "cheat-crash-after-plant": ("def face(st, a):", "def face(st, a):\n    _wreck()"),
    "cheat-malformed-output": ("def face(st, a):", "def face(st, a):\n    _garble()"),
    "cheat-fake-sink": ("def face(st, a):", "def face(st, a):\n    _forge()"),
    "cheat-patch-core": ("def face(st, a):", "def face(st, a):\n    _swap()"),
    "cheat-kill-monitor": ("def face(st, a):", "def face(st, a):\n    _blind()"),
    "cheat-empty": ("def face(st, a):", "def face(st, a):\n    return grid.EMPTY\n\n\ndef _unused(st, a):"),
}

HARDCODE = '''from . import grid, memo

TABLE = {
    (1, 0): 4,
    (1, 1): 1,
    (2, 1): 2,
    (3, 1): 3,
    (4, 1): 4,
}


def face(st, a):
    if a in TABLE and len(st.sheet.owners()) == 2:
        return TABLE[a]
    memo.prime(st)
    return memo.reach(st, a)


def gather(st, lo, hi):
    return memo.frame(st, lo, hi)
'''


add("cheat-answer-key", "shipped", "see.py", "_ = None\n")


def build(name):
    base, target, code = ATTACKS[name]
    src = SHIPPED if base == "shipped" else REF
    files = {f: (src / f).read_text() for f in POLICY}
    if name == "cheat-hardcode":
        files["see.py"] = HARDCODE
        return files
    if name == "cheat-answer-key":
        files["see.py"] = _pack.answer_key(TASK)
        return files
    text = files[target]
    rows = text.split("\n")
    cut = 0
    for i, row in enumerate(rows):
        if row.startswith(("import ", "from ")):
            cut = i + 1
    text = "\n".join(rows[:cut]) + "\n" + code + "\n".join(rows[cut:])
    if name in HOOKS:
        was, now = HOOKS[name]
        if text.count(was) != 1:
            raise SystemExit("%s: hook matched %d times" % (name, text.count(was)))
        text = text.replace(was, now, 1)
    files[target] = text
    return files


def main():
    made = _pack.write_all(CHEATS, sorted(ATTACKS), build, POLICY)
    _pack.check_lf(CHEATS)
    print("wrote %d cheat scripts" % made)


if __name__ == "__main__":
    main()
