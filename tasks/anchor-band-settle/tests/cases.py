"""The enumerated programs: one per graded decision, and both sides of every fence.

Each program is small enough to trace by hand, and its name is the name of the rule it pins, so
a failure says which rule broke rather than "a generated program was wrong". The expected lines
are in seal/gt.json, frozen from the model after the model and a plain full-relayout oracle both
produced them; the hand traces behind them are written out in the authoring trace.

  hold-ordinary   content above resolves: the offset moves by exactly the growth
  hold-still      a frame with no edits, and one whose edits all lie below the view
  hold-band       the holder under a stuck header keeps its distance below the band, and
                  keeps it when the header is unpinned and the band drops to nothing
  top-held        a view at offset zero is held like any other
  flow-shut       a shut row's children take no space; opening it pushes the holder down
  flow-lift       a lifted box takes no space; lifting it pulls the holder up
  stick-strict    a stick line exactly on the header's top does not stick it
  stick-push      the end of its section pushes a stuck header up, and the band with it
  stick-none      a header of no height, one under a shut row and one lifted never stick
  band-lowest     overlapping stuck headers: the band is the lowest edge, not a sum
  band-floor      a header pushed wholly above the view adds nothing to the band
  pick-below      the first box showing lies under the band and is passed over
  pick-edges      a box ending on the band line is skipped; one starting on it is whole
  pick-partial    a partly showing box with nothing inside it is taken, and holds when it grows
  pick-first      a partly showing box comes before a wholly showing one after it
  pick-skips      live, lifted and zero-height boxes are never taken
  pick-empty      a band as tall as the view leaves nothing to take
  fall-dropped    a dropped holder hands over to its container at the container's own distance
  fall-hidden     a holder under a row that was shut hands over to that row
  fall-lifted     a lifted holder hands over to its container
  fall-empty      a holder resized to nothing hands over
  fall-two        holder and container both gone: the next box up takes over
  fall-none       the whole chain gone: no holder, offset clamped
  none-late       nothing qualifies at the second pass: the offset that pass began from
  stuck-inside    a box inside a stuck header cannot hold, nor can the header
  turn-back       the holder sticks at the old offset, its container holds a pass, it returns
  turn-late       the band falls as the view rises, the holder sticks at the fourth pass and
                  the section the frame resized holds instead
  settle-cycle    two offsets alternate: the smallest, held by the first pass to reach it
  settle-stick    the old offset unsticks the header, the first pass overshoots, it re-sticks
  settle-fourth   three moves and a fourth pass that stands still
  settle-drift    a section end pushing the band every pass: the smallest of four
  settle-holder   the holder and its container alternate; the smallest offset is the container's
  clamp-pass      a target past the end of the range is clamped before the next pass reads it
  clamp-start     the first pass begins at the old offset, not at the clamped one
  off-scroll      an explicit scroll wins; the last one counts and is clamped to the new tree
  off-live        an edit inside a live box switches holding off for the frame
  off-live-add    adding a live box counts as an edit inside one
  off-both        an explicit scroll and a live edit together: the scroll's line
  none-before     nothing showing to take before the edits
"""

CASES = {
    "hold-ordinary": """
view 100
box r1 - 40
box r2 - 30
box r3 - 30
box r4 - 30
box r5 - 30
box r6 - 30
at 50
frame
size r1 70
frame
size r1 40
""",
    "hold-still": """
view 100
box r1 - 40
box r2 - 30
box r3 - 30
box r4 - 30
box r5 - 30
box r6 - 30
at 50
frame
frame
size r5 90
add r7 - 6 40
""",
    "hold-band": """
view 100
box g1 - 30
box s1 - 0
box h1 s1 20 pin=0
box r1 s1 40
box r2 s1 40
box r3 s1 40
box r4 s1 40
at 80
frame
size g1 55
frame
unpin h1
""",
    "top-held": """
view 100
box r1 - 40
box r2 - 40
box r3 - 40
box r4 - 40
at 0
frame
add r5 - 0 25
""",
    "flow-shut": """
view 100
box r1 - 20
box r2 - 20 shut
box k1 r2 30
box k2 r2 30
box r3 - 40
box r4 - 40
box r5 - 40
box r6 - 40
at 50
frame
open r2
frame
shut r2
""",
    "flow-lift": """
view 100
box r1 - 30
box r2 - 30
box r3 - 40
box r4 - 40
box r5 - 40
box r6 - 40
at 70
frame
lift r2
frame
sink r2
""",
    "stick-strict": """
view 100
box s1 - 20
box h1 s1 20 pin=10
box r1 s1 40
box r2 s1 40
box r3 s1 40
box r4 s1 40
at 10
frame
size r4 60
frame
to 11
frame
size r4 40
""",
    "stick-push": """
view 100
box s1 - 0
box h1 s1 20 pin=0
box r1 s1 40
box r2 s1 40
box s2 - 0
box r3 s2 10
box r4 s2 40
box r5 s2 40
box r6 s2 40
at 90
frame
size r6 50
frame
size r2 20
""",
    "stick-none": """
view 100
box s1 - 0
box h1 s1 0 pin=15
box r1 s1 10
box r2 s1 30
box r3 s1 40
box r4 - 10 shut
box h2 r4 20 pin=0
box r5 - 10
box h3 r5 20 pin=0 lift
box r6 r5 40
box r7 - 40
at 30
frame
size r7 50
""",
    "band-lowest": """
view 100
box s1 - 0
box h1 s1 30 pin=0
box p1 s1 0
box h2 p1 20 pin=15
box r1 p1 40
box r2 p1 10
box r3 p1 40
box r4 p1 40
box r5 p1 40
at 60
frame
size r5 60
""",
    "band-floor": """
view 100
box s1 - 0
box h1 s1 20 pin=0
box r1 s1 40
box s2 - 0
box r2 s2 3
box r3 s2 40
box r4 s2 40
box r5 s2 40
at 65
frame
size r5 50
""",
    "pick-below": """
view 100
box g1 - 20
box s1 - 0
box h1 s1 30 pin=0
box r1 s1 20
box r2 s1 40
box r3 s1 40
box r4 s1 40
at 40
frame
size g1 30
""",
    "pick-edges": """
view 100
box g1 - 20
box s1 - 0
box h1 s1 20 pin=0
box r1 s1 30
box r2 s1 30
box r3 s1 40
box r4 s1 40
at 50
frame
size g1 35
frame
to 49
frame
size g1 20
""",
    "pick-partial": """
view 100
box r1 - 50
box r2 - 40
box r3 - 40
box r4 - 40
at 30
frame
size r1 70
""",
    "pick-first": """
view 100
box g1 - 20
box p1 - 0
box k1 p1 30
box k2 p1 20
box r1 - 40
box r2 - 40
at 30
frame
size g1 35
""",
    "pick-skips": """
view 100
box g1 - 20
box v1 - 20 live
box k1 v1 10
box z1 - 0
box l1 - 30 lift
box r2 - 40
box r3 - 40
box r4 - 40
at 25
frame
size g1 45
""",
    "pick-empty": """
view 60
box s1 - 0
box h1 s1 70 pin=0
box r1 s1 40
box r2 s1 40
box r3 s1 40
at 20
frame
size r3 60
""",
    "fall-dropped": """
view 100
box g1 - 30
box s1 - 20
box r1 s1 30
box r2 s1 30
box r3 s1 30
box r4 - 40
box r5 - 40
at 90
frame
drop r2
size g1 50
""",
    "fall-hidden": """
view 100
box g1 - 30
box p1 - 20
box k1 p1 30
box k2 p1 30
box r1 - 40
box r2 - 40
box r3 - 40
at 60
frame
shut p1
""",
    "fall-lifted": """
view 100
box g1 - 30
box p1 - 20
box k1 p1 30
box k2 p1 30
box k3 p1 30
box r1 - 40
box r2 - 40
at 60
frame
lift k1
size g1 40
""",
    "fall-empty": """
view 100
box g1 - 30
box p1 - 20
box k1 p1 30
box k2 p1 30
box r1 - 40
box r2 - 40
at 60
frame
size k1 0
""",
    "fall-two": """
view 100
box g1 - 30
box c1 - 10
box p1 c1 20
box k1 p1 30
box k2 p1 30
box r1 c1 40
box r2 - 40
box r3 - 40
at 70
frame
drop p1
size g1 45
""",
    "fall-none": """
view 100
box g1 - 30
box p1 - 20
box k1 p1 40
box k2 p1 40
box r1 - 30
at 40
frame
drop p1
""",
    "none-late": """
view 100
box r1 - 10
box s1 - 10
box r2 s1 30
box r3 s1 30
box r4 s1 30
box r5 - 40
box r6 - 40
at 20
frame
size r1 60
pin s1 10
""",
    "stuck-inside": """
view 60
box s1 - 0
box r0 s1 40
box p1 s1 0 pin=0
box t1 p1 25
box t2 p1 25
box t3 p1 25
box r1 s1 40
box r2 s1 40
box r3 - 40
at 40
frame
size p1 10
""",
    "turn-back": """
view 100
box g1 - 50
box s1 - 10
box h1 s1 20 pin=0
box r1 s1 40
box r2 s1 40
box r3 s1 40
box s2 - 10
box h2 s2 20 pin=0
box r4 s2 40
box r5 s2 40
at 60
frame
size g1 80
frame
frame
size g1 50
""",
    "turn-late": """
view 60
box s1 - 0
box h2 s1 20 pin=50
box r3 s1 30
box s4 - 0
box h5 s4 20 pin=10
box r6 s4 10
box p7 s4 10
box r8 p7 30
at 13
frame
size s4 20
""",
    "settle-cycle": """
view 100
box g1 - 100
box s1 - 0
box r1 s1 40
box r2 s1 40
box s2 - 0
box h2 s2 20 pin=50
box r3 s2 40
box r4 s2 40
box r5 s2 40
at 100
frame
size r2 5
""",
    "settle-stick": """
view 80
box s1 - 10
box h2 s1 30 pin=10
box r3 s1 60
at 9
frame
size s1 20
""",
    "settle-fourth": """
view 100
box s1 - 0
box r2 s1 40
box p3 s1 0
box h4 p3 10 pin=10
box r5 p3 20
box r6 s1 60
box s7 - 0
box r8 s7 60
at 78
frame
size s1 20
""",
    "settle-drift": """
view 60
box s1 - 0
box h2 s1 30 pin=20
box r3 s1 30
box r4 s1 30
box r5 s1 30
box s6 - 0
box h7 s6 20 pin=0
box r8 s6 20
at 65
frame
size r3 5
""",
    "settle-holder": """
view 80
box s1 - 10
box r2 s1 60
box r3 s1 40
at 14
frame
pin r2 0
""",
    "clamp-pass": """
view 60
box s1 - 10
box h2 s1 10 pin=20
box p3 s1 10
box h4 p3 10 pin=20
box r5 p3 10
at 0
frame
drop h2
""",
    "clamp-start": """
view 60
box s1 - 0
box h2 s1 10 pin=50
box r3 s1 20
box r4 s1 20
box s5 - 0
box h6 s5 30 pin=20
box r7 s5 10
at 16
frame
size r3 5
""",
    "off-scroll": """
view 100
box r1 - 40
box r2 - 40
box r3 - 40
box r4 - 40
box r5 - 40
at 30
frame
size r1 60
to 20
to 300
frame
size r1 40
to 25
drop r5
""",
    "off-live": """
view 100
box v1 - 30 live
box k1 v1 10
box r1 - 40
box r2 - 40
box r3 - 40
box r4 - 40
at 50
frame
size k1 40
frame
size r1 50
""",
    "off-live-add": """
view 100
box r1 - 40
box r2 - 40
box r3 - 40
box r4 - 40
at 50
frame
add v1 - 0 30 live
frame
add r5 - 0 30
""",
    "off-both": """
view 100
box v1 - 30 live
box r1 - 40
box r2 - 40
box r3 - 40
at 20
frame
size v1 60
to 45
""",
    "none-before": """
view 100
box r1 - 0
box l1 - 50 lift
box v1 - 60 live
at 0
frame
size v1 10
add r2 - 3 40
frame
size r2 60
""",
}

ORDER = list(CASES)


def prog(name):
    """The program for one case, as the list of its lines."""
    return CASES[name].strip("\n").split("\n")
