"""The enumerated pages: one per graded decision, and the must-still-work side of each fence.

Each page is small enough to read the whole log by hand. The name of a page is the rule it pins,
so a failure says which rule broke rather than "a generated page was wrong".

  tiny-example           the page quoted in the brief: equal words in another node are spoken again
  plain-once             spaced-out updates: one utterance per change, nothing repeated
  timing-words           an utterance of w words started at t finishes at t + w
  tie-node-id            equal ages go to the lower text node id, not to document order
  assertive-first        when the reader is free, an assertive change goes before an older polite one
  edit-keeps-age         a waiting change edited again keeps its place in line
  stale-in-line          a waiting change is spoken with the text it has when its turn comes
  undone-in-line         a change undone before its turn is never spoken
  cut-hands-back         a polite utterance cut by an assertive change is spoken again later
  cut-keeps-age          what a cut hands back keeps its age, ahead of newer polite changes
  alert-waits            an assertive change never cuts assertive speech
  finish-before-cut      an utterance whose time is up at a tick finishes before the cut check
  held-alert-no-cut      a held assertive change cuts nothing until its hold is released
  late-case              an atomic status cut by an alert and edited during it is read anew
  off-stops              an off region inside a polite one is silent: off stops the search
  off-absorbs            a change made while its region is off is never spoken later
  hidden-false-stays     aria-hidden false does not expose what a hidden ancestor hides
  hidden-any-value       the hidden attribute hides whatever its value, false included
  hide-removes           hiding content is a removal and showing it again an addition
  region-hidden-silent   removals from a region that is itself hidden are absorbed
  relevant-region-only   aria-relevant on an inner element means nothing
  relevant-bogus         unknown aria-relevant tokens leave the default in force
  relevance-absorbs      an irrelevant change is absorbed, not kept for later
  atomic-inner           an inner container with aria-atomic true is read whole
  atomic-false-stops     an explicit aria-atomic false stops the walk below an atomic region
  empty-unit             a unit with no exposed text says nothing and the next change is chosen
  unit-leaves-held       a unit reads held text but leaves the held change waiting
  busy-inner             aria-busy on a container holds the changes beneath it only
  busy-false-releases    aria-busy false holds nothing
  busy-above-ignored     aria-busy above the region element holds nothing
  removal-last-believed  a removal is placed under the parent it was last believed under
  removal-held-anchor    a removal is held by a busy element above its anchor
  anchor-stale-hold      a move inside a region does not refresh the anchor a removal is held by
  move-across            a node moved between regions is a removal in one and an addition in the other
  absorb-carried         absorbing a change releases it from the utterance that carries it
"""

CASES = {
    # --- the ordinary side, and time ------------------------------------------------
    "tiny-example": """
page 12
@0
add 1 0 end el div
set 1 aria-live polite
add 2 1 end tx online
add 3 1 end tx idle
@1
text 2 offline
@4
text 3 offline
@8
text 2 online
""",
    "plain-once": """
page 14
@0
add 1 0 end el div
set 1 aria-live polite
add 2 1 end tx ready
@1
text 2 saving draft
@5
add 3 1 end tx draft saved
@10
text 2 all done
""",
    "timing-words": """
page 12
@0
add 1 0 end el div
set 1 aria-live polite
add 2 1 end tx a
add 3 1 end tx b
@1
text 2 one two three
text 3 four
""",
    "tie-node-id": """
page 8
@0
add 1 0 end el div
set 1 aria-live polite
add 2 1 end tx zero
@1
add 3 1 end tx last
add 4 1 0 tx first
""",
    "assertive-first": """
page 10
@0
add 1 0 end el div
set 1 aria-live polite
add 2 1 end tx idle
add 3 0 end el div
set 3 aria-live assertive
add 4 3 end tx ok
add 5 3 end tx fine
@1
text 4 power low
@2
text 2 saved
@3
text 5 retry now
""",
    "edit-keeps-age": """
page 14
@0
add 1 0 end el div
set 1 aria-live polite
add 2 1 end tx a
add 3 1 end tx b
add 4 1 end tx c
@1
text 2 long text of five words
@2
text 3 alpha
@3
text 4 beta
@4
text 3 gamma
""",
    "stale-in-line": """
page 12
@0
add 1 0 end el div
set 1 aria-live polite
add 2 1 end tx inbox
add 3 1 end tx cart
@1
text 2 five new messages in inbox
text 3 cart has one item
@3
text 3 cart has two items
""",
    "undone-in-line": """
page 12
@0
add 1 0 end el div
set 1 aria-live polite
add 2 1 end tx inbox
add 3 1 end tx cart
@1
text 2 five new messages in inbox
text 3 cart has one item
@3
text 3 cart
""",

    # --- cuts -----------------------------------------------------------------------------
    "cut-hands-back": """
page 12
@0
add 1 0 end el div
set 1 aria-live polite
add 2 1 end tx idle
add 3 0 end el div
set 3 aria-live assertive
add 4 3 end tx ok
@1
text 2 loading three new messages
@2
text 4 connection lost
""",
    "cut-keeps-age": """
page 16
@0
add 1 0 end el div
set 1 aria-live polite
add 2 1 end tx a
add 3 1 end tx b
add 4 0 end el div
set 4 aria-live assertive
add 5 4 end tx ok
@1
text 2 sync failed for four files
@2
text 3 new mail
@3
text 5 disk full
""",
    "alert-waits": """
page 10
@0
add 1 0 end el div
set 1 aria-live assertive
add 2 1 end tx ok
add 3 1 end tx fine
@1
text 2 battery low now
@2
text 3 saving work
""",
    "finish-before-cut": """
page 10
@0
add 1 0 end el div
set 1 aria-live polite
add 2 1 end tx idle
add 3 0 end el div
set 3 aria-live assertive
add 4 3 end tx ok
@1
text 2 upload done
@3
text 4 low battery
""",
    "held-alert-no-cut": """
page 16
@0
add 1 0 end el div
set 1 aria-live polite
add 2 1 end tx idle
add 3 0 end el div
set 3 aria-live assertive
set 3 aria-busy true
add 4 3 end tx ok
@1
text 2 reading a long line here
@2
text 4 alert
@4
unset 3 aria-busy
""",
    "late-case": """
page 12
@0
add 1 0 end el div
set 1 aria-live polite
add 2 1 end el div
set 2 aria-atomic true
add 3 2 end tx upload
add 4 2 end tx 40 percent
add 5 0 end el div
set 5 aria-live assertive
add 6 5 end tx ok
@1
text 4 60 percent
@2
text 6 network lost
@3
text 4 80 percent
""",

    # --- exposure and regions ------------------------------------------------------------
    "off-stops": """
page 8
@0
add 1 0 end el div
set 1 aria-live polite
add 2 1 end el div
set 2 aria-live off
add 3 2 end tx hidden count
add 4 1 end tx visible
@1
text 3 count 5
@3
text 4 shown
""",
    "off-absorbs": """
page 8
@0
add 1 0 end el div
set 1 aria-live off
add 2 1 end tx a
@1
text 2 b
@3
set 1 aria-live polite
@5
text 2 c
""",
    "hidden-false-stays": """
page 8
@0
add 1 0 end el div
set 1 aria-live polite
add 2 1 end el div
set 2 hidden hidden
add 3 2 end el span
set 3 aria-hidden false
add 4 3 end tx secret
add 5 1 end tx shown
@1
text 4 still secret
@3
text 5 visible
""",
    "hidden-any-value": """
page 6
@0
add 1 0 end el div
set 1 aria-live polite
add 2 1 end el div
set 2 hidden false
add 3 2 end tx quiet
add 4 1 end tx loud
@1
text 3 still quiet
@2
text 4 louder
""",
    "hide-removes": """
page 10
@0
add 1 0 end el div
set 1 aria-live polite
set 1 aria-relevant all
add 2 1 end el div
add 3 2 end tx promo
@1
set 2 hidden hidden
@5
unset 2 hidden
""",
    "region-hidden-silent": """
page 10
@0
add 1 0 end el div
set 1 aria-live polite
set 1 aria-relevant all
add 2 1 end tx a
@1
set 1 hidden hidden
@2
text 2 b
@4
unset 1 hidden
""",

    # --- relevance ------------------------------------------------------------------------
    "relevant-region-only": """
page 8
@0
add 1 0 end el div
set 1 aria-live polite
add 2 1 end el ul
set 2 aria-relevant removals
add 3 2 end tx first
add 4 2 end tx second
@1
drop 3
@3
add 5 2 end tx third
""",
    "relevant-bogus": """
page 6
@0
add 1 0 end el div
set 1 aria-live polite
set 1 aria-relevant bogus
add 2 1 end tx a
@1
text 2 x
""",
    "relevance-absorbs": """
page 8
@0
add 1 0 end el div
set 1 aria-live polite
set 1 aria-relevant additions
add 2 1 end tx v1
@1
text 2 v2
@3
set 1 aria-relevant all
@5
add 3 1 end tx new
""",

    # --- units ----------------------------------------------------------------------------
    "atomic-inner": """
page 12
@0
add 1 0 end el div
set 1 aria-live polite
add 2 1 end el p
set 2 aria-atomic true
add 3 2 end tx score
add 4 2 end tx 3 to 1
add 5 1 end tx other
@1
text 4 3 to 2
@8
text 5 other stuff
""",
    "atomic-false-stops": """
page 10
@0
add 1 0 end el div
set 1 aria-live polite
set 1 aria-atomic true
add 2 1 end tx header
add 3 1 end el span
set 3 aria-atomic false
add 4 3 end tx a
@1
text 4 b
@4
text 2 top
""",
    "empty-unit": """
page 6
@0
add 1 0 end el div
set 1 aria-live polite
set 1 aria-relevant all
add 2 1 end el div
set 2 aria-atomic true
add 3 2 end tx item
add 4 1 end tx tail
@1
drop 3
text 4 end
""",
    "unit-leaves-held": """
page 10
@0
add 1 0 end el div
set 1 aria-live polite
add 2 1 end el div
set 2 aria-atomic true
add 3 2 end tx score
add 4 2 end el span
set 4 aria-busy true
add 5 4 end tx 0
@1
text 5 1
@2
text 3 goal
@6
unset 4 aria-busy
""",

    # --- holds ----------------------------------------------------------------------------
    "busy-inner": """
page 8
@0
add 1 0 end el div
set 1 aria-live polite
add 2 1 end el ul
set 2 aria-busy true
add 3 1 end tx loading
@1
add 4 2 end tx first row
@2
add 5 1 end tx status ok
@5
unset 2 aria-busy
""",
    "busy-false-releases": """
page 4
@0
add 1 0 end el div
set 1 aria-live polite
set 1 aria-busy false
add 2 1 end tx a
@1
text 2 x
""",
    "busy-above-ignored": """
page 4
@0
add 1 0 end el div
set 1 aria-busy true
add 2 1 end el div
set 2 aria-live polite
add 3 2 end tx a
@1
text 3 b
""",

    # --- removals and moves ---------------------------------------------------------------
    "removal-last-believed": """
page 8
@0
add 1 0 end el div
set 1 aria-live polite
set 1 aria-relevant all
add 2 1 end el div
set 2 aria-atomic true
add 3 2 end tx north
add 4 2 end tx gate
add 5 1 end el div
add 6 5 end tx misc
@1
move 4 5 end
@2
drop 4
""",
    "removal-held-anchor": """
page 10
@0
add 1 0 end el div
set 1 aria-live polite
set 1 aria-relevant all
add 2 1 end el ul
set 2 aria-busy true
add 3 2 end tx row one
@1
drop 3
@3
add 4 1 end tx other
@5
unset 2 aria-busy
""",
    "anchor-stale-hold": """
page 8
@0
add 1 0 end el div
set 1 aria-live polite
set 1 aria-relevant all
add 2 1 end el ul
set 2 aria-busy true
add 3 2 end tx row
add 4 1 end el div
@1
move 3 4 end
@2
drop 3
@4
unset 2 aria-busy
""",
    "move-across": """
page 8
@0
add 1 0 end el div
set 1 aria-live polite
set 1 aria-relevant all
add 2 1 end tx draft one
add 3 0 end el div
set 3 aria-live polite
add 4 3 end tx outbox
@1
move 2 3 end
""",
    "absorb-carried": """
page 12
@0
add 1 0 end el div
set 1 aria-live polite
add 2 1 end tx one
@1
text 2 uploading five large files now
@2
set 1 aria-live off
@3
text 2 upload done
@4
set 1 aria-live polite
@8
text 2 upload done
""",
}

ORDER = list(CASES)


def prog(name):
    return [ln for ln in CASES[name].strip("\n").split("\n")]
