"""Which entries a call can mean, and what their slots ask for once the open kind is known.

Candidates are the entries that carry the call's name and take exactly as many slots as the
call has arguments. Nothing here judges them: the arity filter is the whole of it, and an
entry that cannot take its arguments is dropped later, by the trial that tries it.
"""
from res import kind


def cands(prog, name, count):
    """Entries named `name` taking `count` slots, in declaration order."""
    return [ent for ent in prog.entries
            if ent.name == name and len(ent.params) == count]


def opens(ent):
    """The positions of the entry's open slots."""
    return [i for i, p in enumerate(ent.params) if p == "*"]


def slots(ent, settled):
    """The kinds the entry's slots ask for, with the open kind put in."""
    return [settled if p == "*" else p for p in ent.params]


def result(ent, settled):
    """The kind the entry gives back, with the open kind put in."""
    return settled if ent.ret == "*" else ent.ret


def in_bound(prog, ent, settled):
    """An open entry may only be settled at a kind that rises to its bound."""
    return kind.steps(prog, settled, ent.bound) is not None
