"""The enumerated programs: one per graded decision, plus the must-still-work side of each
fence.

Each name says which rule its program pins, and `tests/test_outputs.py` reports the name when
it fails, so a failure says which reading the submission took. The answers are frozen in
`seal/gt.json`; the grader checks the sealed model still reproduces them before it grades
anything.

Entry numbers are counted from 0 over the entry lines only; change numbers are counted from 0
over `open` brackets and bare entries. Both are written in the comment above each program,
because `off` and `once` name them and a miscount is a silently different program.
"""

PROGS = {

    # --- the climb: a value above, a mask that stops it, a section reached twice ------

    # 0 sec 1  1 lnk 0  2 sec 0  3 set 7 42  4 sec 1
    "climb-up": [
        "sec 1", "lnk 0", "sec 0", "set 7 42", "sec 1",
        "get 1 7", "get 0 7", "get 2 7",
    ],

    # a cleared slot lets the climb go on; the value above is still found
    "clr-goes-on": [
        "sec 1", "lnk 0", "sec 0", "set 7 42", "sec 1", "set 7 9", "clr 7",
        "get 1 7",
    ],

    # a masked slot stops the climb where a cleared one would not
    "cut-stops": [
        "sec 1", "lnk 0", "sec 0", "set 7 42", "sec 1", "set 7 9", "cut 7",
        "get 1 7",
    ],

    # a write clears the mask again
    "cut-then-set": [
        "sec 1", "lnk 0", "sec 0", "set 7 42", "sec 1", "cut 7", "set 7 5",
        "get 1 7", "all",
    ],

    # two sections linked to each other: the climb ends when it comes back round
    "climb-loop": [
        "sec 1", "lnk 2", "sec 2", "lnk 1", "set 3 8",
        "get 1 3", "get 1 4", "get 2 4",
    ],

    # a section linked to itself ends the climb at once
    "climb-self": [
        "sec 1", "lnk 1", "set 3 8",
        "get 1 3", "get 1 4",
    ],

    # --- `add`: reads through the climb, writes where the walk is ---------------------

    "add-writes-here": [
        "sec 1", "lnk 0", "sec 0", "set 7 42", "sec 1", "add 7 3",
        "get 1 7", "get 0 7", "all",
    ],

    # nothing found anywhere on the chain: the entry does nothing, it does not write the step
    "add-finds-none": [
        "sec 1", "lnk 0", "sec 1", "add 7 3",
        "get 1 7", "all",
    ],

    # a cleared name is not a zero
    "add-after-clr": [
        "set 7 42", "clr 7", "add 7 3",
        "get 0 7", "all",
    ],

    # a masked name is not a zero either, and the mask is still standing afterwards
    "add-after-cut": [
        "sec 1", "lnk 0", "sec 0", "set 7 42", "sec 1", "cut 7", "add 7 3",
        "get 1 7", "all",
    ],

    # --- the section the walk carries -------------------------------------------------

    # 0 sec 2  1 set 4 11  2 sec 0  3 set 4 22
    "sec-carries": [
        "sec 2", "set 4 11", "sec 0", "set 4 22",
        "get 2 4", "get 0 4",
    ],

    # every pass starts in section 0, so a write before any `sec` entry lands there
    "sec-starts-at-zero": [
        "set 4 11", "sec 3", "set 4 22",
        "get 0 4", "get 3 4",
    ],

    # and the second pass of a settle starts there too, not where the first one ended
    # 0 set 4 1   1 once 4 1 set 9 9   2 sec 3   3 set 4 2
    "sec-resets-each-pass": [
        "set 4 1", "once 4 1 set 9 9", "sec 3", "set 4 2",
        "get 0 9", "get 3 9",
    ],

    # clearing a masked slot takes the mask off, so the climb goes on again
    "cut-then-clr": [
        "sec 1", "lnk 0", "sec 0", "set 7 42", "sec 1", "cut 7", "clr 7",
        "get 1 7", "all",
    ],

    # a question is answered over the entries above it, never over the whole file
    "later-entries-ignored": [
        "get 0 4", "set 4 10", "get 0 4",
    ],

    # --- `if`: a refused condition does nothing at all ---------------------------------

    # 0 if 9 9 sec 4   1 set 1 2      - the walk must still be in section 0
    "gate-blocks-sec": [
        "if 9 9 sec 4", "set 1 2",
        "get 0 1", "get 4 1",
    ],

    # a refused condition on a link entry leaves the chain alone
    "gate-blocks-lnk": [
        "sec 0", "set 7 42", "sec 1", "if 9 9 lnk 0",
        "get 1 7", "all",
    ],

    # the must-still-work side: a condition that is met fires, section entries included
    "gate-passes": [
        "set 9 9", "if 9 9 sec 4", "set 1 2",
        "get 4 1", "get 0 1",
    ],

    # the condition is read in the section the walk carries, climbing from there
    "gate-reads-here": [
        "sec 1", "lnk 0", "sec 0", "set 9 9", "sec 1", "if 9 9 set 1 2",
        "get 1 1",
    ],

    # and in that section rather than in section 0: the same name holds different numbers
    "gate-reads-sec": [
        "sec 2", "set 9 9", "if 9 9 set 1 2", "sec 0", "set 9 5", "if 9 5 set 3 4",
        "get 2 1", "get 0 3", "get 2 3", "get 0 1",
    ],

    # --- `once`: asleep until the board says otherwise ---------------------------------

    # 0 set 1 5   1 once 1 5 set 2 9
    "once-wakes": [
        "set 1 5", "once 1 5 set 2 9",
        "get 0 2",
    ],

    # a woken entry is not tested again, even when its own write ends the condition
    "once-no-retest": [
        "set 1 5", "once 1 5 cut 1",
        "get 0 1", "all",
    ],

    # one wake per pass, lowest number first: waking entry 1 stops entry 2 ever waking
    # 0 set 1 1   1 once 1 1 clr 1   2 once 1 1 set 2 2
    "once-one-per-pass": [
        "set 1 1", "once 1 1 clr 1", "once 1 1 set 2 2",
        "get 0 2", "get 0 1",
    ],

    # both wake, one pass each, so the pass count is three
    "once-two-passes": [
        "set 1 1", "once 1 1 set 2 2", "once 2 2 set 3 3",
        "get 0 3",
    ],

    # the sleeping condition is read in the section its position had, not the last one
    # 0 sec 1   1 once 5 7 set 8 1   2 sec 2   3 set 5 7
    "once-sec-at-pos": [
        "sec 1", "once 5 7 set 8 1", "sec 2", "set 5 7",
        "get 1 8", "get 2 8",
    ],

    # the other way round: read in the section its position had, the condition is met
    "once-sec-mirror": [
        "sec 1", "once 5 7 set 8 1", "set 5 7", "sec 2",
        "get 1 8", "get 2 8",
    ],

    # and over the board that pass left, including writes made after its own position
    "once-reads-final": [
        "once 5 7 set 8 1", "set 5 7",
        "get 0 8",
    ],

    # every settle starts them asleep again: lifting the reason un-wakes it
    # 0 set 1 5   1 once 1 5 set 2 9     changes: 0 and 1
    "once-resleeps": [
        "set 1 5", "once 1 5 set 2 9",
        "get 0 2", "off 0", "get 0 2", "back 0", "get 0 2",
    ],

    # a lifted sleeping entry can never wake
    "once-lifted": [
        "set 1 5", "once 1 5 set 2 9",
        "off 1", "get 0 2", "get 0 1",
    ],

    # --- withdrawal: a walk of what survives, not an undo ------------------------------

    # 0 set 4 10 (chg 0)   1 set 4 20 (chg 1)   - lifting chg 0 must change nothing
    "off-overwritten": [
        "set 4 10", "set 4 20",
        "get 0 4", "off 0", "get 0 4", "back 0", "get 0 4",
    ],

    # lifting the only write leaves the name standing at what is above it
    # 0 sec 1 (chg 0)  1 lnk 0 (chg 1)  2 sec 0 (chg 2)  3 set 7 42 (chg 3)
    # 4 sec 1 (chg 4)  5 set 7 9 (chg 5)
    "off-uncovers": [
        "sec 1", "lnk 0", "sec 0", "set 7 42", "sec 1", "set 7 9",
        "get 1 7", "off 5", "get 1 7", "back 5", "get 1 7",
    ],

    # the late one: a lookup that found nothing where a mask stood has to be worked out
    # again once the change carrying that mask is withdrawn, and the sleeper it decides
    # wakes on the pass after. chg 4 is the masking change.
    "mask-lifted": [
        "open", "sec 1", "lnk 0", "shut",
        "open", "sec 2", "lnk 1", "shut",
        "sec 0", "set 7 42",
        "open", "sec 1", "cut 7", "shut",
        "sec 2", "once 7 42 set 8 1",
        "get 2 7", "get 2 8",
        "off 4", "get 2 7", "get 2 8",
        "back 4", "get 2 7", "get 2 8",
    ],

    # a lifted change holding a section entry moves everything written after it
    # chg 0: open/sec 2/shut    chg 1: set 4 11    chg 2: set 5 12
    "off-moves-writes": [
        "open", "sec 2", "shut", "set 4 11", "set 5 12",
        "get 2 4", "off 0", "get 2 4", "get 0 4", "get 0 5",
    ],

    # a lifted change holding a link entry takes the chain with it
    # 0 sec 1 (chg 0)  1 lnk 0 (chg 1)  2 sec 0 (chg 2)  3 set 7 42 (chg 3)
    "off-unlinks": [
        "sec 1", "lnk 0", "sec 0", "set 7 42",
        "get 1 7", "off 1", "get 1 7", "back 1", "get 1 7",
    ],

    # lifting a change that is already lifted, and reinstating a live one, change nothing
    "off-twice": [
        "set 4 10",
        "get 0 4", "off 0", "off 0", "get 0 4", "back 0", "back 0", "get 0 4",
    ],

    # --- what the board summary prints -------------------------------------------------

    # the three runs in order of section and then of name, which is not the order of name
    # and then of section: (1,5) sits above (0,7) under one and below it under the other
    "all-shape": [
        "sec 1", "lnk 0",
        "sec 0", "set 7 42", "set 8 1", "cut 6",
        "sec 1", "cut 7", "set 9 3", "set 5 4", "cut 2",
        "all",
    ],

    "all-empty": [
        "set 1 1", "clr 1",
        "all", "get 0 1",
    ],

    # --- the ordinary case an overconservative resolver has to keep working -------------

    "plain-run": [
        "open", "set 1 10", "set 2 20", "shut", "set 3 30", "add 1 5", "clr 2",
        "get 0 1", "get 0 2", "get 0 3", "get 0 4", "all",
    ],
}

ORDER = sorted(PROGS)


def prog(name):
    return list(PROGS[name])
