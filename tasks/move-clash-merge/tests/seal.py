"""The frozen surface of the engine, and how it is hashed.

The five policy files are the agent's. Everything else in the tree is the verifier's copy,
and a submission that rewrites one of those files - to print its own trace, to change what
the applier accepts, to replace the driver - changes a code object named here. The worker
hashes them as they exist in its interpreter; the grader derives the same hashes by
compiling the pristine sources, executing nothing.

Nested code objects are hashed by recursion rather than by repr, because a code object's
repr carries its filename and its address and would differ on every run.
"""

import hashlib
import types

FROZEN = (
    ("mrg/tree.py", "Nd.__init__"),
    ("mrg/tree.py", "Tr.__init__"),
    ("mrg/tree.py", "Tr.copy"),
    ("mrg/tree.py", "Tr.put"),
    ("mrg/tree.py", "Tr.pop"),
    ("mrg/tree.py", "Tr.mov"),
    ("mrg/tree.py", "Tr.wr"),
    ("mrg/tree.py", "Tr.kids"),
    ("mrg/tree.py", "Tr.path"),
    ("mrg/tree.py", "Tr.at"),
    ("mrg/tree.py", "Tr.free"),
    ("mrg/tree.py", "Tr.under"),
    ("mrg/tree.py", "Tr.paths"),
    ("mrg/tree.py", "mk"),
    ("mrg/lay.py", "split"),
    ("mrg/lay.py", "join"),
    ("mrg/lay.py", "fmt"),
    ("mrg/lay.py", "do"),
    ("mrg/read.py", "parse"),
    ("mrg/drive.py", "Mint.__init__"),
    ("mrg/drive.py", "Mint.__call__"),
    ("mrg/drive.py", "rekey"),
    ("mrg/drive.py", "go"),
)


def digest(code):
    h = hashlib.sha256()
    h.update(code.co_code)
    h.update(repr(code.co_names).encode())
    h.update(repr(code.co_varnames).encode())
    for k in code.co_consts:
        h.update((digest(k) if isinstance(k, types.CodeType) else repr(k)).encode())
    return h.hexdigest()


def stamp(book):
    h = hashlib.sha256()
    for k in sorted(book):
        h.update(("%s:%s|" % (k, book[k])).encode())
    return h.hexdigest()


def find(code, parts):
    for const in code.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == parts[0]:
            return find(const, parts[1:]) if parts[1:] else const
    return None


def from_source(root):
    """The stamp the frozen surface must have, compiled from the untouched sources."""
    book = {}
    cache = {}
    for rel, qual in FROZEN:
        if rel not in cache:
            with open("%s/%s" % (root, rel), encoding="utf-8") as fh:
                cache[rel] = compile(fh.read(), rel, "exec")
        code = find(cache[rel], qual.split("."))
        book["%s#%s" % (rel, qual)] = digest(code) if code is not None else "absent"
    return stamp(book)
