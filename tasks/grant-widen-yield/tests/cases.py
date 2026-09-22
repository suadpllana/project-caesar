"""The enumerated programs: one per graded decision, plus the side of each fence that must
still work.

Each name says which rule it pins. A submission that gets that rule wrong fails the case named
for it, so a failure report names the rule rather than a line number. The order is fixed and
`gt.json` is keyed by these names.

The groups, in the order the rules are stated in the brief:

  plain-*   ordinary traffic: nobody gives way, nothing narrows, nothing widens
  mode-*    the two places the lattice is not the obvious one
  cover-*   an ancestor's mode is the supremum of the asked mode and the live covers below
  take-*    level by level from the store inward, with no look-ahead
  give-*    the cascade, its order, and what it leaves behind
  sweep-*   which claims are tried, in what order, and what a retake may do
  wide-*    the widen rule and both sides of its fences
  free-*    release and finish
  say-*     the printed vocabulary and the closing report
"""

PROG = {}

# --- ordinary traffic: an overcautious service fails here ----------------------------

PROG["plain-share"] = """
lim 6
open t0
open t1
take t0 s0.b0.k1 S
take t1 s0.b0.k2 S
take t1 s0.b0.k1 S
take t0 s0.b0.k2 S
"""

PROG["plain-intent"] = """
lim 6
open t0
open t1
take t0 s0.b0.k1 X
take t1 s0.b0.k2 X
take t0 s0.b0.k3 IS
take t1 s0.b1.k1 IX
"""

PROG["plain-again"] = """
lim 6
open t0
take t0 s0.b0.k1 X
take t0 s0.b0.k1 X
take t0 s0.b0.k1 S
take t0 s0.b0.k1 IS
"""

PROG["plain-stores"] = """
lim 6
open t0
open t1
take t0 s0.b0.k1 X
take t1 s1.b0.k1 X
take t1 s0.b1.k1 S
take t0 s1.b1.k1 S
"""

# --- the mode lattice ----------------------------------------------------------------

PROG["mode-sup-mixed"] = """
lim 6
open t0
take t0 s0.b0 S
take t0 s0.b0.k1 X
drop t0 s0.b0.k1
"""

PROG["mode-cover-six"] = """
lim 6
open t0
open t1
take t0 s0.b0 S
take t0 s0.b0.k1 X
take t1 s0.b1.k1 X
take t1 s0 IS
"""

PROG["mode-cover-read"] = """
lim 6
open t0
open t1
take t0 s0.b0.k1 S
take t1 s0.b1.k1 IS
take t1 s0 S
"""

# --- the derived cover ---------------------------------------------------------------

PROG["cover-asked-stays"] = """
lim 6
open t0
take t0 s0.b0.k1 X
take t0 s0.b0 IX
drop t0 s0.b0.k1
"""

PROG["cover-plain-goes"] = """
lim 6
open t0
take t0 s0.b0.k1 X
drop t0 s0.b0.k1
"""

PROG["cover-thins"] = """
lim 6
open t0
take t0 s0.b0.k1 S
take t0 s0.b0.k2 X
drop t0 s0.b0.k2
"""

PROG["cover-holds-up"] = """
lim 6
open t0
take t0 s0.b0.k1 S
take t0 s0.b0.k2 X
take t0 s0.b0.k3 X
drop t0 s0.b0.k2
"""

PROG["cover-unblocks"] = """
lim 6
open t0
open t1
take t0 s0.b0.k1 X
take t1 s0.b0 S
take t0 s0.b0.k2 IS
drop t0 s0.b0.k1
"""

# --- the take ------------------------------------------------------------------------

PROG["take-outward"] = """
lim 6
open t0
take t0 s0.b0.k1 X
"""

PROG["take-no-lookahead"] = """
lim 6
open t0
open t1
open t2
take t0 s0.b0.k1 S
take t2 s0 S
take t1 s0.b0.k1 X
"""

PROG["take-keeps-grant"] = """
lim 6
open t0
open t1
take t0 s0.b0.k1 S
take t1 s0.b0.k1 S
take t1 s0.b0.k1 X
take t1 s0.b0.k2 S
"""

PROG["take-older-refused"] = """
lim 6
open t0
open t1
take t0 s0 X
take t1 s0.b0.k1 S
take t1 s1.b0.k1 S
"""

# --- giving way ----------------------------------------------------------------------

PROG["give-younger"] = """
lim 6
open t0
open t1
take t1 s0.b0.k1 X
take t0 s0.b0.k1 X
"""

PROG["give-cascade"] = """
lim 6
open t0
open t1
take t1 s0.b0 IX
take t1 s0.b0.k1 X
take t1 s0.b0.k2 S
take t0 s0.b0 S
"""

PROG["give-asked-only"] = """
lim 6
open t0
open t1
take t1 s0.b0.k1 X
take t1 s0.b0.k2 S
take t0 s0 S
"""

PROG["give-claim-asked"] = """
lim 5
open t0
open t1
take t1 s0.b2.k2 SIX
take t1 s0.b2 IS
take t0 s0.b2 SIX
"""

PROG["give-age-order"] = """
lim 6
open t0
open t1
open t2
take t1 s0.b0.k1 IX
take t2 s0.b0.k2 IX
take t0 s0.b0 S
"""

PROG["give-at-level"] = """
lim 6
open t0
open t1
take t1 s0.b0.k1 X
take t1 s0.b1.k1 X
take t0 s0.b0.k1 X
"""

# --- claims and the sweep ------------------------------------------------------------

PROG["sweep-age-first"] = """
lim 6
open t0
open t1
open t2
take t0 s0.b0.k1 X
take t2 s0.b0.k1 X
take t1 s0.b0.k1 X
drop t0 s0.b0.k1
"""

PROG["sweep-outermost"] = """
lim 6
open t0
open t1
take t0 s0 X
take t1 s0.b0 S
take t1 s0.b0.k1 S
drop t0 s0
"""

PROG["sweep-narrower"] = """
lim 6
open t0
open t1
take t1 s0.b0 IX
take t1 s0.b0.k1 X
take t1 s0.b0.k2 S
take t0 s0.b0 S
"""

PROG["sweep-preempts"] = """
lim 6
open t0
open t1
open t2
take t1 s0 S
take t0 s0.b0.k1 X
take t2 s0.b1.k1 X
take t2 s0.b1.k2 S
shut t0
"""

PROG["sweep-next-line"] = """
lim 6
open t0
open t1
open t2
take t1 s0 S
take t0 s0.b0.k1 X
take t2 s0.b1.k1 S
shut t0
take t2 s0.b2.k1 IS
"""

PROG["sweep-parked"] = """
lim 6
open t0
open t1
open t2
take t0 s0.b0.k1 S
take t1 s0.b0.k1 X
take t2 s0.b0 S
take t0 s0.b1.k1 S
take t2 s0.b0.k4 S
"""

# --- the widen rule ------------------------------------------------------------------

PROG["wide-keys"] = """
lim 2
open t0
take t0 s0.b0.k1 S
take t0 s0.b0.k2 S
take t0 s0.b0.k3 X
"""

PROG["wide-chain"] = """
lim 1
open t0
take t0 s0.b0.k1 S
take t0 s0.b0.k2 S
take t0 s0.b1.k1 S
take t0 s0.b1.k2 S
"""

PROG["wide-grants-only"] = """
lim 3
open t0
open t1
take t1 s0.b0.k1 X
take t1 s0.b0.k2 X
take t0 s0.b0.k1 X
take t0 s0.b0.k2 X
take t0 s0.b0.k3 X
"""

PROG["wide-claims-idle"] = """
lim 1
open t0
open t1
take t1 s0.b0.k0 X
take t1 s0.b0.k4 SIX
take t0 s0.b0 IX
take t1 s0.b1.k4 IS
"""

PROG["wide-passive"] = """
lim 2
open t0
open t1
take t1 s0.b0 IS
take t1 s0.b0.k9 S
take t0 s0.b0.k1 X
take t0 s0.b0.k2 X
take t0 s0.b0.k3 X
"""

PROG["wide-deep-first"] = """
lim 2
open t9
open t0
take t9 s0.b0.k2 X
take t9 s0.b1.k1 X
take t0 s0.b0.k1 S
take t0 s0.b0.k3 S
take t0 s0.b2.k1 S
take t0 s0.b0.k2 S
take t0 s0.b1.k1 S
shut t9
"""

PROG["wide-twice"] = """
lim 2
open t0
open t1
take t1 s0.b0.k0 IS
take t1 s0.b1.k3 IX
take t0 s0.b1.k1 IX
take t0 s0.b1.k2 X
take t0 s0.b1.k0 X
take t1 s0.b2 IX
"""

PROG["wide-sup"] = """
lim 2
open t0
take t0 s0.b0 IS
take t0 s0.b0.k1 IS
take t0 s0.b0.k2 S
take t0 s0.b0.k3 IX
"""

PROG["wide-after-sweep"] = """
lim 2
open t0
open t1
take t1 s0.b0.k1 X
take t1 s0.b0.k2 X
take t1 s0.b0.k3 X
take t0 s0.b0.k2 X
drop t0 s0.b0.k2
"""

PROG["wide-last"] = """
lim 1
open t0
open t1
take t1 s0.b0.k4 IX
take t0 s0.b0.k4 S
take t0 s0.b1.k2 SIX
"""

PROG["wide-under-limit"] = """
lim 3
open t0
take t0 s0.b0.k1 S
take t0 s0.b0.k2 S
take t0 s0.b0.k3 S
"""

# --- release and finish --------------------------------------------------------------

PROG["free-subtree"] = """
lim 6
open t0
open t1
take t0 s0.b0.k1 X
take t1 s0.b0.k1 S
take t1 s0.b0.k2 S
drop t1 s0.b0
"""

PROG["free-narrows"] = """
lim 6
open t0
take t0 s0.b0.k1 X
take t0 s0.b1.k1 S
drop t0 s0.b0
"""

PROG["free-nothing"] = """
lim 6
open t0
take t0 s0.b0.k1 X
drop t0 s0.b1
drop t0 s1
"""

PROG["shut-clears"] = """
lim 6
open t0
open t1
take t0 s0.b0.k1 X
take t1 s0.b0.k1 S
take t1 s0.b1.k1 S
shut t1
shut t0
"""

# --- what is printed -----------------------------------------------------------------

PROG["say-report-order"] = """
lim 9
open t1
open t0
take t1 s1.b1.k1 S
take t1 s0.b2.k3 S
take t0 s0.b0.k1 X
take t1 s0.b0.k1 S
"""

ORDER = tuple(sorted(PROG))


def prog(name):
    """One enumerated program as a list of lines."""
    return [row for row in PROG[name].strip().splitlines()]
