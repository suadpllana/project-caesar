import copy

from eng import take


class Void:
    def row(self, *cells):
        pass


def admit(st, o, out):
    shadow = copy.deepcopy(st)
    probe = copy.deepcopy(o)
    take.walk(shadow, probe, Void())
    if probe.rem <= 0:
        take.walk(st, o, out)
    if o.rem > 0:
        out.row("pul", o.oid, "whole")
