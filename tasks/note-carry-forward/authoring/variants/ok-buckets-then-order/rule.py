"""What a revision keeps, what its change covers, and when to say so.

`kept` and `inside` both answer off the script the tool itself settled, which
is the only reason they agree with the rest of the tool on a file that repeats
its lines: several scripts of the same length exist for almost any pair of
revisions of one, and they disagree about which copy of a repeated line
survived.

`should_raise` is the one that is not a question about this revision at all. A
note is raised when its line becomes part of a change. While it stays part of
one the reviewer has already been asked, so raising again says nothing, and
the answer therefore depends on where the note stood at the revision before -
which only a board that walks the store one revision at a time can supply.
"""

from scr import grp, pin


def kept(before, after):
    out = {}
    for kind, i, j in pin.reading(before, after, pin.script(before, after)):
        if kind == "K":
            out[i] = j
    return out


def inside(line, before, after):
    for chunk in grp.spans(before, after):
        if line in chunk:
            return True
    return False


def should_raise(inside_now, inside_before):
    return inside_now and not inside_before
