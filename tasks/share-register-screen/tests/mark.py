"""Digests of a function as it exists in a running interpreter, and of one compiled here.

The verifier hashes the executed tree on disk after the run, which answers "is this file
the one we shipped". It does not answer "is this object the one that file built", because
a submission can rebind a name in a frozen module to a quiet copy of its own. These two
functions answer that second question: the runner records what the frozen entry points
actually were while it drove the registers, and the grader derives what they should have
been by compiling the pristine sources, executing nothing.
"""

from __future__ import annotations

import hashlib


def _digest(code):
    h = hashlib.sha256()
    h.update(code.co_code)
    h.update(("|%d|%d|%s" % (code.co_argcount, code.co_nlocals,
                             ",".join(code.co_names))).encode())
    for k in code.co_consts:
        if hasattr(k, "co_code"):
            h.update(_digest(k).encode())
        else:
            h.update(("<%s:%r>" % (type(k).__name__, k)).encode())
    return h.hexdigest()[:32]


def live(pairs):
    """{label: digest} for (label, callable) pairs, as they stand right now."""
    out = {}
    for label, fn in pairs:
        code = getattr(fn, "__code__", None)
        out[label] = _digest(code) if code is not None else "?"
    return out


def compiled(sources):
    """{label: digest} from source text, by compiling and walking the code tree.

    Nothing is executed. `sources` maps a module name to its text; labels come out as
    "module.function" and "module.Class.method".
    """
    out = {}
    for name, text in sorted(sources.items()):
        top = compile(text, "<%s>" % name, "exec")
        stack = [(name, top)]
        while stack:
            prefix, code = stack.pop()
            for k in code.co_consts:
                if not hasattr(k, "co_code"):
                    continue
                label = "%s.%s" % (prefix, k.co_name)
                if k.co_name == "<module>":
                    continue
                out[label] = _digest(k)
                stack.append((label, k))
    return out
