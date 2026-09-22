"""The enumerated trails: one per graded decision, and the side of each fence that must still work.

A generated population tells you a submission is wrong; these tell you which rule it broke. Each
name below is the rule it pins, and every wrong reading in the authoring set is separated by the
case named for it, so a failure reads as "this rule" rather than "six of three hundred".

The four groups, in the order an observation applies them: when an observation happens at all,
what may be credited there, what a violation takes away, and what the budget and the close do to
the records around it.
"""

PROGRAMS = {

    # --- when an observation happens -------------------------------------------------

    # A goal satisfied only in the middle of a step is never observed satisfied.
    "obs-step-end": [
        "cfg 100",
        "ep a",
        "goal 0 1 0 at 1 7",
        "step", "put 1 7", "put 1 9", "ok",
        "step", "put 2 1", "ok",
    ],

    # A step that ends err is rolled back and observes nothing, however good its records were.
    "obs-ok-only": [
        "cfg 100",
        "ep a",
        "goal 0 1 0 at 1 7",
        "step", "put 1 7", "err",
        "step", "put 2 1", "ok",
    ],

    # A goal the seeded records already satisfy is credited at the first observation and not
    # before it, so its dependant is still a whole observation behind: were the baseline to
    # credit, goal 1 would be in before the firing instead of never.
    "obs-base-silent": [
        "cfg 100",
        "rec 1 7",
        "ep a",
        "goal 0 2 0 at 1 7",
        "goal 1 3 1 0 at 3 1",
        "bar 0 0 gain 9",
        "step", "put 9 1", "put 3 1", "ok",
        "step", "put 5 1", "ok",
        "step", "put 3 1", "ok",
    ],

    # The baseline fires no bar: it only records what the next observation is compared against.
    "obs-base-no-fire": [
        "cfg 100",
        "rec 1 7",
        "ep a",
        "goal 0 1 0 at 9 1",
        "bar 0 0 gain 1",
        "step", "put 5 1", "ok",
    ],

    # --- what may be credited there ---------------------------------------------------

    # A prerequisite credited at this observation does not let its dependant in.
    "pre-strict-later": [
        "cfg 100",
        "ep a",
        "goal 0 1 0 at 1 1",
        "goal 1 2 1 0 at 2 2",
        "step", "put 1 1", "put 2 2", "ok",
        "step", "put 7 1", "ok",
    ],

    # A chain satisfied all at once is credited one link per observation.
    "pre-chain-layers": [
        "cfg 100",
        "ep a",
        "goal 0 1 0 at 1 1",
        "goal 1 1 1 0 at 2 1",
        "goal 2 1 1 1 at 3 1",
        "step", "put 1 1", "put 2 1", "put 3 1", "ok",
        "step", "put 7 1", "ok",
        "step", "put 7 2", "ok",
    ],

    # A goal standing on two prerequisites waits for the later of them.
    "pre-many-parents": [
        "cfg 100",
        "ep a",
        "goal 0 1 0 at 1 1",
        "goal 1 1 0 at 2 1",
        "goal 2 3 2 0 1 at 3 1",
        "step", "put 1 1", "put 3 1", "ok",
        "step", "put 2 1", "ok",
        "step", "put 7 1", "ok",
    ],

    # A goal whose predicate held long before its prerequisite is credited the observation after it.
    "pre-open-waits": [
        "cfg 100",
        "rec 2 1",
        "ep a",
        "goal 0 1 0 at 1 1",
        "goal 1 2 1 0 at 2 1",
        "step", "put 7 1", "ok",
        "step", "put 7 2", "ok",
        "step", "put 1 1", "ok",
        "step", "put 7 3", "ok",
    ],

    # --- credit settles ----------------------------------------------------------------

    # Credit survives the predicate going false, with no violation anywhere.
    "settle-keeps": [
        "cfg 100",
        "ep a",
        "goal 0 3 0 at 1 1",
        "step", "put 1 1", "ok",
        "step", "cut 1", "ok",
    ],

    # A goal already credited is not marked again when its predicate returns.
    "settle-no-recredit": [
        "cfg 100",
        "ep a",
        "goal 0 1 0 at 1 1",
        "step", "put 1 1", "ok",
        "step", "cut 1", "ok",
        "step", "put 1 1", "ok",
    ],

    # --- what a violation is ------------------------------------------------------------

    # lost needs a value at the previous observation and none now.
    "bar-lost": [
        "cfg 100",
        "ep a",
        "goal 0 1 0 at 9 1",
        "bar 0 0 lost 1",
        "step", "put 1 4", "ok",
        "step", "put 1 5", "ok",
        "step", "cut 1", "ok",
        "step", "cut 1", "ok",
    ],

    # gain needs no value at the previous observation and one now.
    "bar-gain": [
        "cfg 100",
        "rec 1 4",
        "ep a",
        "goal 0 1 0 at 9 1",
        "bar 0 0 gain 1",
        "step", "put 1 5", "ok",
        "step", "cut 1", "ok",
        "step", "put 1 2", "ok",
    ],

    # back needs a strictly lower value; equal is not lower, and higher is not lower.
    "bar-back": [
        "cfg 100",
        "rec 1 5",
        "ep a",
        "goal 0 1 0 at 9 1",
        "bar 0 0 back 1",
        "step", "put 1 5", "ok",
        "step", "put 1 6", "ok",
        "step", "put 1 5", "ok",
    ],

    # A value that dips and comes back inside one step is not a fall between observations.
    "bar-prev-obs": [
        "cfg 100",
        "rec 1 5",
        "ep a",
        "goal 0 1 0 at 9 1",
        "bar 0 0 back 1",
        "step", "put 1 2", "put 1 5", "ok",
        "step", "put 7 1", "ok",
    ],

    # A loss inside a step that ends err is undone and never seen.
    "bar-err-invisible": [
        "cfg 100",
        "rec 1 5",
        "ep a",
        "goal 0 1 0 at 9 1",
        "bar 0 0 lost 1",
        "step", "cut 1", "err",
        "step", "put 7 1", "ok",
    ],

    # --- what a violation takes -----------------------------------------------------------

    # Firing strips the goal named and everything standing on it, directly or through others.
    "void-cone": [
        "cfg 100",
        "ep a",
        "goal 0 1 0 at 1 1",
        "goal 1 2 1 0 at 2 1",
        "goal 2 4 1 1 at 3 1",
        "bar 0 0 lost 1",
        "step", "put 1 1", "ok",
        "step", "put 2 1", "ok",
        "step", "put 3 1", "ok",
        "step", "cut 1", "ok",
    ],

    # The named goal is shut and has to be earned again; a dependant is only opened, so it
    # comes back one observation after its prerequisite does.
    "void-shut-named": [
        "cfg 100",
        "ep a",
        "goal 0 1 0 at 1 1",
        "goal 1 2 1 0 at 2 1",
        "bar 0 0 back 1",
        "step", "put 1 1", "ok",
        "step", "put 2 1", "ok",
        "step", "put 1 0", "ok",
        "step", "cut 1", "ok",
        "step", "put 1 1", "ok",
        "step", "put 7 1", "ok",
    ],

    # A goal shut while its predicate already fails opens at the next observation, whatever
    # that observation touched.
    "void-rearm-false": [
        "cfg 100",
        "ep a",
        "goal 0 2 0 at 1 5",
        "bar 0 0 lost 1",
        "step", "put 1 5", "ok",
        "step", "cut 1", "ok",
        "step", "put 8 1", "ok",
        "step", "put 1 5", "ok",
    ],

    # A goal shut while its predicate still holds stays shut until the predicate fails.
    "void-rearm-holds": [
        "cfg 100",
        "rec 2 9",
        "ep a",
        "goal 0 2 0 up 1 4",
        "bar 0 0 back 2",
        "step", "put 1 6", "ok",
        "step", "put 2 3", "ok",
        "step", "put 8 1", "ok",
        "step", "put 1 9", "ok",
        "step", "cut 1", "ok",
        "step", "put 1 6", "ok",
    ],

    # Credit is applied first and bars fire after it, so a goal can be credited and stripped
    # at the same observation.
    "void-order": [
        "cfg 100",
        "rec 1 9",
        "ep a",
        "goal 0 3 0 up 1 4",
        "bar 0 0 back 1",
        "step", "put 1 5", "ok",
    ],

    # A bar naming a goal that holds no credit prints its firing and shuts the goal anyway.
    "void-uncredited": [
        "cfg 100",
        "rec 1 9",
        "ep a",
        "goal 0 1 0 at 2 3",
        "bar 0 0 back 1",
        "step", "put 1 4", "ok",
        "step", "put 2 3", "ok",
        "step", "put 9 1", "ok",
    ],

    # Voids print in ascending goal id, which here is not the order a walk down from the
    # named goal reaches them.
    "void-ascending": [
        "cfg 100",
        "ep a",
        "goal 0 1 0 at 1 1",
        "goal 1 1 1 0 at 2 1",
        "goal 2 1 1 1 at 3 1",
        "goal 3 1 1 0 at 4 1",
        "bar 0 0 lost 1",
        "step", "put 1 1", "ok",
        "step", "put 2 1", "put 4 1", "ok",
        "step", "put 3 1", "ok",
        "step", "cut 1", "ok",
    ],

    # --- steps and the records ------------------------------------------------------------

    # A step that ends err leaves the records exactly as it found them.
    "step-err-undo": [
        "cfg 100",
        "rec 1 2",
        "ep a",
        "goal 0 1 0 at 1 2",
        "step", "put 1 8", "cut 1", "err",
        "step", "put 7 1", "ok",
    ],

    # A step that ends ok keeps what it wrote: the must-still-work side of the same fence.
    "step-ok-keeps": [
        "cfg 100",
        "rec 1 2",
        "ep a",
        "goal 0 1 0 at 1 8",
        "step", "put 1 8", "ok",
        "step", "put 7 1", "ok",
    ],

    # --- the budget --------------------------------------------------------------------

    # The budget counts actions, not steps.
    "bud-per-action": [
        "cfg 3",
        "ep a",
        "goal 0 1 0 at 4 1",
        "step", "put 1 1", "put 2 1", "ok",
        "step", "put 3 1", "put 4 1", "ok",
    ],

    # The actions of a step that ended err are charged all the same.
    "bud-counts-failed": [
        "cfg 3",
        "ep a",
        "goal 0 1 0 at 3 1",
        "step", "put 1 1", "put 2 1", "err",
        "step", "put 3 1", "put 4 1", "ok",
    ],

    # The action that would cross the budget is not performed, and its step is rolled back.
    "bud-cut-step": [
        "cfg 2",
        "ep a",
        "goal 0 1 0 at 1 1",
        "step", "put 1 1", "ok",
        "step", "put 2 1", "put 3 1", "ok",
        "step", "put 4 1", "ok",
    ],

    # A budget spent exactly by the last action of the last step closes nothing: the episode
    # ends normally and keeps its records.
    "bud-exact-end": [
        "cfg 2",
        "ep a",
        "goal 0 1 0 at 2 1",
        "step", "put 1 1", "put 2 1", "ok",
        "ep b",
        "goal 0 1 0 at 2 1",
        "step", "put 9 1", "ok",
    ],

    # --- closing an episode ---------------------------------------------------------------

    # An episode closed short loses its records and keeps its credit.
    "close-undo-keeps-credit": [
        "cfg 2",
        "ep a",
        "goal 0 5 0 at 1 1",
        "step", "put 1 1", "ok",
        "step", "put 2 1", "put 3 1", "ok",
    ],

    # The next episode starts from the records the close left behind, which are the ones the
    # episode opened with: were they kept, goal 1 would be credited here and goal 0 would not.
    "close-next-baseline": [
        "cfg 2",
        "ep a",
        "goal 0 1 0 at 1 1",
        "step", "put 1 1", "ok",
        "step", "put 5 5", "put 6 6", "ok",
        "ep b",
        "goal 0 1 0 off 5",
        "goal 1 1 0 at 1 1",
        "step", "put 9 1", "ok",
    ],

    # An episode that ran to the end leaves its records for the next one.
    "carry-normal": [
        "cfg 100",
        "ep a",
        "goal 0 1 0 at 1 1",
        "step", "put 1 1", "put 5 5", "ok",
        "ep b",
        "goal 0 1 0 at 5 5",
        "goal 1 1 0 off 6",
        "step", "put 9 1", "ok",
    ],

    # --- the predicates -----------------------------------------------------------------------

    # A value sitting exactly on an `up` threshold is at least that much.
    "pred-up-equal": [
        "cfg 100",
        "ep a",
        "goal 0 2 0 up 1 4",
        "step", "put 1 4", "ok",
    ],

    # A record standing at zero is a record with a value, so `off` does not hold for it.
    "pred-off-zero": [
        "cfg 100",
        "rec 1 0",
        "ep a",
        "goal 0 1 0 off 1",
        "goal 1 2 0 at 1 0",
        "step", "put 7 1", "ok",
        "step", "cut 1", "ok",
    ],

    # --- the report -------------------------------------------------------------------------

    # An episode's credit adds up the weights of what it holds, not the number of goals.
    "rep-weights": [
        "cfg 100",
        "ep a",
        "goal 0 4 0 at 1 1",
        "goal 1 7 0 at 2 1",
        "step", "put 1 1", "ok",
        "step", "put 2 1", "ok",
    ],

    # An episode counts as full only when it holds every goal.
    "rep-full": [
        "cfg 100",
        "ep a",
        "goal 0 1 0 at 1 1",
        "goal 1 1 0 at 2 1",
        "step", "put 1 1", "ok",
        "ep b",
        "goal 0 1 0 at 3 1",
        "step", "put 3 1", "ok",
    ],

    # --- the trail the brief prints the answer for ---------------------------------------------

    # `trails/tiny.txt`, byte for byte. The brief prints its five correct lines, so those lines
    # are a promise and are graded like any other rule.
    "worked-tiny": [
        "cfg 100",
        "rec 0 0",
        "rec 1 5",
        "rec 2 3",
        "ep a1",
        "goal 0 1 0 off 1",
        "goal 1 2 0 at 1 4",
        "goal 2 2 1 1 off 1",
        "bar 0 0 back 2",
        "step", "cut 2", "put 2 3", "ok",
        "step", "cut 1", "put 0 2", "ok",
        "step", "put 2 0", "cut 1", "ok",
    ],

    # --- the ordinary run ---------------------------------------------------------------------

    # No violation, room in the budget, one goal reached per step: the whole rubric is credited
    # and the episode is full.
    "plain-all": [
        "cfg 100",
        "rec 1 0",
        "ep a",
        "goal 0 2 0 up 1 3",
        "goal 1 3 1 0 at 2 4",
        "goal 2 1 1 1 off 3",
        "step", "put 1 5", "ok",
        "step", "put 2 4", "ok",
        "step", "put 8 1", "ok",
    ],
}

ORDER = sorted(PROGRAMS)


def prog(name):
    return list(PROGRAMS[name])
