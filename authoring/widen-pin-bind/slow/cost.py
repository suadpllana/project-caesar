"""The numbers a trial is judged on.

A slot costs the steps from the kind its argument stands at to the kind the slot asks for.
The last number of the vector is the same measure taken on the way out: from the kind the
entry gives back to the kind the call was asked for, and nothing when it was asked for
nothing. Every language keeps the result out of this comparison; here it is the last
component of the same vector and decides calls that tie on every argument.
"""
from res import kind


def slot(prog, stands, asked):
    """What an argument standing at `stands` costs in a slot asking for `asked`."""
    return kind.steps(prog, stands, asked)


def result(prog, gives, expected):
    """What the entry's result costs against the kind the call was asked for."""
    if expected is None:
        return 0
    return kind.steps(prog, gives, expected)
