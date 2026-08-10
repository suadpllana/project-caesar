"""Child process. The only thing anywhere that imports the submitted module.

It takes a job on stdin, performs the calls, and writes down what came back.
It holds no expected answer, reads no clock and decides nothing, so patching a
timer or bending a comparison in here moves no number the grade depends on.
"""

import json
import sys

TAMPER = []


class _Block:
    """Deny the submitted module a route into the grading framework, and keep
    the attempt, which a grading case later reads."""

    BLOCKED = ("pytest", "_pytest", "py", "unittest", "oracle")

    def find_module(self, fullname, path=None):
        return self.find_spec(fullname, path)

    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in self.BLOCKED:
            TAMPER.append("attempted to import %r" % fullname)
            raise ImportError("blocked")
        return None


sys.meta_path.insert(0, _Block())
sys.path.insert(0, "/app")
sys.path.insert(0, "/tmp/sbx")

import casegen  # noqa: E402


def clean(value):
    """Whatever came back, reduced to something comparable, without trusting
    it to be a list of integers in the first place."""
    if isinstance(value, dict):
        return value
    try:
        return [int(x) for x in value]
    except Exception as exc:
        return {"error": "not a list of integers: %s: %s"
                         % (type(exc).__name__, exc)}


def main():
    job = json.loads(sys.stdin.read())
    out = {"tamper": TAMPER}
    try:
        import file_reads
    except Exception as exc:
        out["error"] = "importing file_reads raised %s: %s" % (
            type(exc).__name__, exc)
        out["tamper"] = TAMPER
        sys.stdout.write(json.dumps(out))
        return

    try:
        if job["mode"] == "cases":
            manifest = job["manifest"]
            filters = job["filters"]
            plain, held = [], []
            for f in filters:
                try:
                    plain.append(clean(file_reads.files_to_read(manifest, f)))
                except Exception as exc:
                    plain.append({"error": "%s: %s" % (type(exc).__name__, exc)})
            try:
                reader = file_reads.Reader(manifest)
            except Exception as exc:
                held = {"error": "Reader(manifest) raised %s: %s"
                                 % (type(exc).__name__, exc)}
            else:
                for f in filters:
                    try:
                        held.append(clean(reader.files_to_read(f)))
                    except Exception as exc:
                        held.append({"error": "%s: %s"
                                              % (type(exc).__name__, exc)})
            out["plain"] = plain
            out["held"] = held
        else:
            # The workload is built here, from the seed, so nothing that size
            # ever crosses the pipe and no answer can be prepared in advance.
            seed = int(job["seed"])
            manifest = casegen.timed_manifest(seed)
            filters = casegen.timed_filters(seed)
            reader = file_reads.Reader(manifest)
            answers = []
            for f in filters:
                answers.append(sorted(int(x) for x in reader.files_to_read(f)))
            out["digest"] = casegen.digest(seed, answers)
            out["queries"] = len(answers)
            out["files"] = len(manifest)
    except Exception as exc:
        out["error"] = "%s: %s" % (type(exc).__name__, exc)
    out["tamper"] = TAMPER
    sys.stdout.write(json.dumps(out))


if __name__ == "__main__":
    main()
