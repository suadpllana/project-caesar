"""The enumerated programs: one per graded decision, and both sides of every fence.

Each program is small enough to settle by hand. The comment above each says which decision it
pins and what a wrong reading of that decision prints instead. `gt.json` holds the expected
output, frozen from a definitional settling of the contract before the verifier was written; the
sealed model has to reproduce every line of it before any submission is graded.
"""

PROGS = {

    # 1 - a peg keeps what its volume held when it was made, so overwriting a block does not
    # release it. An implementation that frees on overwrite prints b1 at the first trim.
    "keep-after-write": """
        vol v1
        set v1 1
        peg p1 v1
        set v1 1
        trim
        shed p1
        trim
    """,

    # 1, both sides - a block overwritten with no peg standing must come back at the very next
    # trim. An implementation that holds everything prints nothing.
    "no-peg-free": """
        vol v1
        set v1 1
        set v1 1
        trim
        trim
    """,

    # 1 - a peg made after the block left keeps nothing of it. Comparing the peg's stamp with the
    # block's birth alone keeps b1 and prints nothing.
    "late-peg": """
        vol v1
        set v1 1
        set v1 1
        peg p1 v1
        trim
    """,

    # 2 - one block at two slots. The volume lets go only when the last slot does, so the peg
    # made between the two releases keeps it. Ending the hold at the first release prints b1.
    "two-slots": """
        vol v1
        set v1 1
        dup v1 2 1
        clr v1 1
        peg p1 v1
        clr v1 2
        trim
        tally p1
        shed p1
        trim
    """,

    # 2 - the same shape with the peg after both releases: now nothing keeps b1 and it comes back.
    "two-slots-late": """
        vol v1
        set v1 1
        dup v1 2 1
        clr v1 1
        clr v1 2
        peg p1 v1
        trim
    """,

    # 3 - a peg made while the block was away keeps nothing of it. Reading the hold as one stretch
    # from first taken to last let go makes p2 a keeper, so nothing is printed at the last trim.
    "gap-peg": """
        vol v1
        set v1 1
        peg p1 v1
        clr v1 1
        peg p2 v1
        back v1 1 p1 1
        clr v1 1
        shed p1
        trim
    """,

    # 3, 9 - pegs on both sides of a gap keep the block; the one inside it does not, so its tally
    # is zero and shedding it changes nothing.
    "gap-both-sides": """
        vol v1
        set v1 1
        peg p1 v1
        clr v1 1
        peg p2 v1
        back v1 1 p1 1
        peg p3 v1
        clr v1 1
        tally p1
        tally p2
        tally p3
        shed p2
        trim
        shed p1
        trim
        tally p3
        shed p3
        trim
    """,

    # 4, 6 - a fork holds what the peg holds. Shedding that peg releases nothing the fork still
    # holds. Treating a fork as a view of the peg prints b1 at the second trim.
    "fork-keeps": """
        vol v1
        set v1 1
        peg p1 v1
        fork v2 p1
        set v1 1
        trim
        shed p1
        trim
    """,

    # 4 - a peg of the fork keeps a block written in the origin volume. Looking only at the pegs
    # of the volume that wrote the block prints b1.
    "fork-peg-keeps": """
        vol v1
        set v1 1
        peg p1 v1
        fork v2 p1
        set v1 1
        peg p2 v2
        clr v2 1
        shed p1
        trim
        tally p2
    """,

    # 5 - writing in the fork changes the fork only; the origin still holds b1 and nothing is
    # reclaimed.
    "fork-apart": """
        vol v1
        set v1 1
        peg p1 v1
        fork v2 p1
        set v2 1
        shed p1
        trim
        set v1 1
        trim
    """,

    # 4 - a fork of a fork's peg keeps a block written two volumes back.
    "fork-of-fork": """
        vol v1
        set v1 1
        peg p1 v1
        fork v2 p1
        peg p2 v2
        fork v3 p2
        set v1 1
        set v2 1
        shed p1
        shed p2
        trim
        clr v3 1
        trim
    """,

    # 8 - the reclaim list is in the order blocks stopped being kept. b1 stops when p1 is shed,
    # after b2 was overwritten, so b2 comes first. Sorting by allocation order swaps them.
    "order-by-stop": """
        vol v1
        set v1 1
        peg p1 v1
        set v1 2
        set v1 1
        clr v1 2
        shed p1
        trim
    """,

    # 8 - blocks that stop being kept during one op are printed in allocation order.
    "order-tie": """
        vol v1
        set v1 1
        set v1 2
        peg p1 v1
        clr v1 1
        clr v1 2
        shed p1
        trim
    """,

    # 8 - a block already printed is never printed again.
    "printed-once": """
        vol v1
        set v1 1
        clr v1 1
        trim
        trim
        set v1 2
        clr v1 2
        trim
        trim
    """,

    # 7 - reclaim waits for a trim: the block stops being kept at the shed but appears at the
    # trim after it, not at the one before.
    "deferred": """
        vol v1
        set v1 1
        peg p1 v1
        clr v1 1
        trim
        tally p1
        shed p1
        trim
    """,

    # 9 - a block a volume still holds counts for no peg, even when that peg is the only one that
    # keeps it. Counting every block the peg keeps prints 2 for the first tally.
    "tally-live": """
        vol v1
        set v1 1
        set v1 2
        peg p1 v1
        tally p1
        clr v1 1
        tally p1
        clr v1 2
        tally p1
    """,

    # 9 - two pegs keeping one block leave it counted by neither; shedding one hands it to the
    # other.
    "tally-two-pegs": """
        vol v1
        set v1 1
        peg p1 v1
        peg p2 v1
        clr v1 1
        tally p1
        tally p2
        shed p2
        tally p1
        shed p1
        trim
    """,

    # 9, 4 - the two pegs are in different volumes: the fork's peg and the origin's peg both keep
    # b1, so both tallies are zero until one is shed.
    "tally-fork": """
        vol v1
        set v1 1
        peg p1 v1
        fork v2 p1
        set v1 1
        clr v2 1
        tally p1
        peg p2 v2
        tally p1
        shed p1
        tally p2
        trim
    """,

    # 9 - a peg of a volume holding nothing keeps nothing.
    "tally-empty": """
        vol v1
        peg p1 v1
        tally p1
        set v1 1
        tally p1
        clr v1 1
        tally p1
    """,

    # 2, 3 - taking a block back into a slot while another slot still holds it does not open a
    # second episode, so p2 keeps it and shedding p1 alone frees nothing.
    "back-while-held": """
        vol v1
        set v1 1
        peg p1 v1
        dup v1 2 1
        clr v1 1
        back v1 3 p1 1
        peg p2 v1
        clr v1 2
        clr v1 3
        shed p1
        trim
        shed p2
        trim
    """,

    # 3 - a block taken back into a different volume gets an episode there, and a peg of that
    # volume keeps it.
    "back-other-volume": """
        vol v1
        vol v2
        set v1 1
        peg p1 v1
        clr v1 1
        back v2 5 p1 1
        peg p2 v2
        clr v2 5
        shed p1
        trim
        tally p2
        shed p2
        trim
    """,

    # 2 - a slot given the block it already holds is unchanged, so no episode ends and the peg
    # made afterwards still keeps the block.
    "same-block": """
        vol v1
        set v1 1
        dup v1 2 1
        dup v1 2 1
        clr v1 1
        peg p1 v1
        clr v1 2
        shed p1
        trim
    """,

    # 6 - shedding a peg ends its keeping and nothing else: the other peg still keeps b1.
    "shed-one-of-two": """
        vol v1
        set v1 1
        peg p1 v1
        peg p2 v1
        set v1 1
        shed p1
        trim
        shed p2
        trim
    """,

    # 7, 8 - the late case: a block held at two slots, kept across a gap, and released only when
    # the earlier peg is shed, printed after a block that stopped being kept later in the program
    # but earlier in time than the shed.
    "late-case": """
        vol v1
        set v1 1
        dup v1 2 1
        peg p1 v1
        clr v1 1
        clr v1 2
        peg p2 v1
        back v1 1 p1 1
        peg p3 v1
        set v1 4
        clr v1 1
        tally p1
        tally p2
        tally p3
        shed p3
        clr v1 4
        trim
        shed p1
        trim
        shed p2
        trim
    """,

    # 1, 4 - two volumes side by side, each with its own pegs, neither keeping the other's blocks.
    "two-volumes": """
        vol v1
        vol v2
        set v1 1
        set v2 1
        peg p1 v1
        set v1 1
        set v2 1
        trim
        tally p1
        shed p1
        trim
    """,

    # 6, 9 - a peg made, forked from, and shed while the fork still keeps everything.
    "shed-fork-origin": """
        vol v1
        set v1 1
        set v1 2
        peg p1 v1
        fork v2 p1
        clr v1 1
        clr v1 2
        tally p1
        shed p1
        trim
        clr v2 1
        trim
        peg p2 v2
        clr v2 2
        tally p2
        shed p2
        trim
    """,

    # 7 - a trim with nothing to give back prints nothing at all.
    "trim-quiet": """
        vol v1
        trim
        set v1 1
        trim
        peg p1 v1
        trim
    """,

    # 3, 9 - a block taken back after the peg that keeps it was shed cannot be, so the only route
    # back into a volume is a peg that still keeps it; here p2 is that peg.
    "back-after-shed": """
        vol v1
        set v1 1
        peg p1 v1
        peg p2 v1
        clr v1 1
        shed p1
        back v1 2 p2 1
        tally p2
        shed p2
        trim
        clr v1 2
        trim
    """,

    # 2 - a slot that holds nothing may still be read: clearing it changes nothing, and a dup or a
    # back that reads it leaves the slot it writes holding nothing, which lets go of what was there.
    "empty-reads": """
        vol v1
        set v1 1
        peg p1 v1
        clr v1 4
        dup v1 1 4
        trim
        set v1 2
        back v1 2 p1 3
        trim
        shed p1
        trim
    """,

    # 2, 8 - several blocks at several slots, released in an order that is not their allocation
    # order, with no peg standing.
    "loose-order": """
        vol v1
        set v1 1
        set v1 2
        set v1 3
        clr v1 2
        clr v1 3
        clr v1 1
        trim
    """,
}

ORDER = sorted(PROGS)


def ops(name):
    """The program as a list of op lines."""
    return [line.strip() for line in PROGS[name].strip().splitlines()]
