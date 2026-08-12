"""The meter, moved out of the process it measures.

Everything the earlier builds graded lived inside the run: a counter on the tokenizer, a
record the tokenizer appended to, a report the runner assembled from pinned objects. All
of it is honest right up until the loop starts, and after that it belongs to the
submission. An adversarial probe used exactly that. It left the resume logic alone,
handed the shipped tokenizer every render whole, searched for the last position a resume
would have been legal from by asking that same tokenizer, and then rewrote the record and
the counters to describe the run it wished it had done. The record it wrote satisfied
every structural check in tests/audit.py, because the entries were real tails with real
ids - they simply were not what the loop did. Reward 1, no merge table read anywhere.

So the meter is not in that process any more. This is a service, started by test.sh as
root before privileges are dropped, listening on a socket the run may connect to and
nothing else. It does the byte-pair encoding itself - with tests/oracle.py's encoder, the
sealed one - and it writes down what it was asked to do, in order, on the privileged side.
The run gets ids back. It does not get to say what it asked for.

Three requests are served:

  enc   a string; the ids it encodes to come back, and the string and the ids are
        written to the tape as one event.  This is the only way to turn text into ids
        without writing a byte-pair encoder, and every call is on the record.
  fwd   one step of the network; the new state comes back and the tape gets one event,
        which is where the forward count is measured.
  pick  the sampler's choice for a state.  Served, not recorded: it costs the run
        nothing and it is not a graded quantity.

What that buys, and it is the whole point: evidence of work now has to be produced by
doing the work. The old record could be rewritten because it was a list in the run's own
memory. This one can only be appended to, only by asking, and asking is what is being
counted. The expensive-then-rewrite attack now leaves every one of its exploratory
encodes on the tape, where tests/audit.py sees a run that encoded eleven times for four
renders and refuses it.

The residual is smaller and stated in STATE.md: a submission that writes its own
byte-pair encoder, encodes each render whole with it, searches for the cheapest legal
resume and asks the meter only for that tail. It gets the floor and it passes, because
what it recorded is true. Shipping the merge table is what the task is about, so that
route cannot be closed - but it is now the only one, it costs a full encode of every
render plus an encoder of its own, and it lands on an answer the task is happy to accept.
"""

import json
import os
import socket
import sys
import threading

import oracle

NULL = oracle.Counter()


class Tape:
    """The record, on the privileged side of the socket."""

    def __init__(self, path):
        self.fh = open(path, "a")
        self.lock = threading.Lock()

    def write(self, row):
        with self.lock:
            self.fh.write(json.dumps(row) + "\n")
            self.fh.flush()


def answer(req, tape):
    """Serve one request, recording what it cost."""
    if not isinstance(req, dict):
        tape.write(["bad", "request was not an object"])
        return {"err": "bad request"}
    op = req.get("op")
    if op == "enc":
        text = req.get("text")
        if not isinstance(text, str):
            tape.write(["bad", "enc without a string"])
            return {"err": "enc takes a string"}
        ids = oracle.encode(text)
        tape.write(["enc", text, ids])
        return {"ids": ids}
    if op == "fwd":
        h = req.get("h")
        t = req.get("t")
        if not _state(h) or not isinstance(t, int) or not 0 <= t < oracle.NV:
            tape.write(["bad", "fwd with a malformed state"])
            return {"err": "fwd takes a state and a token"}
        tape.write(["fwd"])
        return {"h": list(oracle.advance(NULL, tuple(h), t))}
    if op == "pick":
        h = req.get("h")
        salt = req.get("salt")
        k = req.get("k")
        if not _state(h) or not isinstance(salt, int) or not isinstance(k, int):
            tape.write(["bad", "pick with a malformed state"])
            return {"err": "pick takes a state, a salt and a position"}
        return {"t": oracle.choose(tuple(h), salt, k)}
    tape.write(["bad", str(op)[:40]])
    return {"err": "unknown request"}


def _state(h):
    return (isinstance(h, list) and len(h) == oracle.DIM
            and all(isinstance(x, int) and not isinstance(x, bool) for x in h))


def talk(conn, tape):
    """One client, for as long as it keeps asking."""
    try:
        stream = conn.makefile("rwb")
        for line in stream:
            try:
                req = json.loads(line.decode("utf-8"))
            except ValueError:
                tape.write(["bad", "unparsable line"])
                req = None
            rsp = answer(req, tape)
            stream.write(json.dumps(rsp).encode("utf-8") + b"\n")
            stream.flush()
    except OSError:
        pass
    finally:
        try:
            conn.close()
        except OSError:
            pass


def main(argv):
    if len(argv) != 3:
        print("usage: meter.py <socket> <tape>", file=sys.stderr)
        return 2
    path, tape_path = argv[1], argv[2]
    tape = Tape(tape_path)
    os.chmod(tape_path, 0o600)
    if os.path.exists(path):
        os.unlink(path)
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(path)
    # The run connects as an unprivileged uid. It may speak; it may not read the tape,
    # which lives in a directory it cannot open at all.
    os.chmod(path, 0o666)
    srv.listen(16)
    while True:
        try:
            conn, _ = srv.accept()
        except OSError:
            break
        threading.Thread(target=talk, args=(conn, tape), daemon=True).start()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
