"""The scenario set the rebuilt trainer is driven through.

Each entry is aimed at one reading of the resume rule.  The op list is deliberately
readable: knowing which sequences run does not produce the parameter vectors they end on,
because those come out of the arithmetic of the whole run.

  micro   run n microbatch fills
  save    write the checkpoint into the bounded channel
  kill    throw the trainer away
  load    build a fresh trainer and restore it from the channel
  amend   patch the live configuration, as a relaunch with new settings would
"""


def _sc(name, ops, over=None, aim=""):
    return {"name": name, "ops": ops, "over": over or {}, "aim": aim}


M = lambda n: {"op": "micro", "n": n}
SAVE = {"op": "save"}
KILL = {"op": "kill"}
LOAD = {"op": "load"}


def AMEND(sched=None, top=None):
    op = {"op": "amend"}
    if sched:
        op["sched"] = sched
    if top:
        op["top"] = top
    return op


SCENARIOS = [
    _sc("straight", [M(18)],
        aim="ordinary training with no checkpoint anywhere; nothing about the loop may "
            "have moved"),

    _sc("empty-carry", [SAVE, KILL, LOAD, M(9)],
        aim="a checkpoint taken before any work: the packer holds nothing and the cursor "
            "is at zero, and an encoding that cannot say 'nothing held' fails here"),

    _sc("boundary", [M(4), SAVE, KILL, LOAD, M(8)],
        aim="a save at a window boundary with an item held whose bound matches the bound "
            "in force; the easy resume"),

    _sc("midwindow", [M(11), SAVE, KILL, LOAD, M(7)],
        aim="a save with an accumulation window open: the partial gradient, the token "
            "count and the window length latched when it opened all have to come back"),

    _sc("carry-bump", [M(12), SAVE, M(2), KILL, LOAD, M(6)],
        aim="the curriculum bound rises at the step after the one that drew the held "
            "item, so the item has to come back truncated to the bound it was drawn "
            "under, not to the one in force at the load"),

    _sc("rollback", [M(6), SAVE, M(5), KILL, LOAD, M(8)],
        aim="five microbatches of real work are rolled back by the load; the reads and "
            "positions they cost still happened and are still counted"),

    _sc("epoch", [M(10), SAVE, M(3), KILL, LOAD, M(9)],
        aim="the cursor crosses the end of an epoch after the load, so the order for the "
            "next epoch has to be rebuilt rather than carried"),

    _sc("amend-lr", [M(7), SAVE, KILL, AMEND(sched={"base": 60}), LOAD, M(6)],
        aim="the trainer comes back under an amended learning rate while a window is "
            "open; the step that closes that window has to use the amended value"),

    _sc("amend-bound", [M(5), SAVE, KILL, AMEND(sched={"bounds": [[0, 14]]}), LOAD, M(7)],
        aim="an amended curriculum reaches every item drawn after the load and none of "
            "the item already held, which was fixed before the save"),

    _sc("amend-window", [M(19), SAVE, KILL, AMEND(sched={"window": [[0, 2], [9, 2]]}),
                         LOAD, M(7)],
        aim="an amended window length must not shorten the window that was already open "
            "when the save was taken, and must apply to every window after it"),

    _sc("amend-ema", [M(9), SAVE, KILL, AMEND(sched={"ema": [[0, 4]]}), LOAD, M(6)],
        aim="an amended averaging shift reaches the update that closes the open window"),

    _sc("twice", [M(6), SAVE, M(3), KILL, LOAD, M(4), SAVE, M(2), KILL, LOAD, M(5)],
        aim="two cycles, the second restoring a checkpoint written after the first "
            "resume"),

    _sc("wide", [M(9), SAVE, M(2), KILL, LOAD, M(8)],
        over={"binw": 34, "budget": 70},
        aim="the same lifecycle against a different packing shape, so nothing may depend "
            "on the numbers the default configuration happens to produce"),

    _sc("long", [M(5), SAVE, M(4), KILL, LOAD, M(6),
                 AMEND(sched={"bounds": [[0, 9], [6, 16], [14, 11]]}), M(3),
                 SAVE, M(2), KILL, AMEND(sched={"base": 72}, top={"budget": 62}),
                 LOAD, M(7), SAVE, KILL, LOAD, M(4)],
        aim="everything at once over a long op list, including an amendment taken while "
            "the trainer is up and another taken while it is down"),
]

BY_NAME = {s["name"]: s for s in SCENARIOS}


def by_name(name):
    return BY_NAME[name]
