"""Child process. The only thing anywhere that imports the submitted module.

It reads a job on standard input, calls the submitted function once per case,
writes back what came out, and stops. It holds no expected answer, takes no
measurement and decides nothing, so patching a clock or an equality test in
here changes no number that is ever looked at.
"""

import json
import sys

TAMPER = []


class _Block:
    """The grading framework is not importable from in here. An attempt to
    reach it is denied and recorded, and the record is asserted on later."""

    BLOCKED = ("pytest", "_pytest", "py.test")

    def find_module(self, fullname, path=None):
        return self.find_spec(fullname, path)

    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in self.BLOCKED:
            TAMPER.append("tried to import %r" % fullname)
            raise ImportError("blocked")
        return None


sys.meta_path.insert(0, _Block())
sys.path.insert(0, "/app")


def normalise(value):
    """Whatever came back, turned into pairs or into a complaint. Tuples and
    lists are both fine; anything else is a wrong answer, not a crash."""
    if not isinstance(value, (list, tuple)):
        return {"bad": "returned %s, not a sequence" % type(value).__name__}
    out = []
    for item in value:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            kind, index = item[0], item[1]
            if isinstance(kind, str) and isinstance(index, int) \
                    and not isinstance(index, bool):
                out.append([kind, index])
                continue
        return {"bad": "an entry was %r" % (item,)}
    return out


def run(mod, cases):
    answers = []
    for before, after in cases:
        try:
            answers.append(normalise(mod.changes(before, after)))
        except Exception as exc:
            answers.append({"bad": "%s: %s" % (type(exc).__name__, exc)})
    return answers


def main():
    job = json.loads(sys.stdin.read())
    # Anything the submitted module prints goes to stderr, where it cannot
    # damage the report. A stray print is a bad habit, not a wrong answer.
    channel = sys.stdout
    sys.stdout = sys.stderr
    out = {}
    try:
        import change_script
        out["answers"] = run(change_script, job["cases"])
    except Exception as exc:
        out["error"] = "%s: %s" % (type(exc).__name__, exc)
    out["tamper"] = TAMPER
    channel.write(json.dumps(out))
    channel.flush()


if __name__ == "__main__":
    main()
