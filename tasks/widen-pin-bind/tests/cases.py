"""The enumerated programs: one for every graded decision, and both sides of every fence.

Each name says which rule its program pins down, and a failure on one of them names the rule
that was read the wrong way. The generated families cover combinations and keep a submission
from being fitted to these; these decide the rules one at a time.

  one-only      a single survivor is the winner, with nothing to beat
  plain-best    one entry no worse everywhere and better somewhere is the winner
  cross-sum     two entries that cross, with different totals: ambiguous, not the cheaper total
  cross-even    two entries that cross with equal totals: ambiguous from the other side
  ret-decides   entries alike at the slot and apart at the result, under a slot that asks
  ret-free      the same two entries asked for nothing: ambiguous, the result costing nothing
  nest-expect   a call in a slot binds by the kind that slot asks for, not on its own
  nest-dead     a slot whose call has no binding drops the entry, and another may still take it
  nest-amb      an ambiguous call in an open slot drops that entry, and a plain one survives
  path-short    the shorter of two chains between two kinds is the number of steps
  path-tally    the same, read off the tally rather than the winner
  open-lub      two slots standing at kinds that meet at one kind settle the entry there
  open-none     two slots whose common kinds have no least: the entry is dropped
  open-first    the first open slot's kind is not the settled kind
  bound-under   an entry settled below its bound is taken
  bound-over    an entry settled above its bound is dropped
  bound-none    a settled kind that does not reach the bound at all
  open-free     an open slot holding a call binds it asking for nothing
  open-noslot   an open entry with no open slot is never taken
  arity         entries of the same name and a different slot count are not candidates
  no-entry      a name with no entry of that slot count has no binding
  val-norise    an argument that does not rise to its slot drops the entry
  pin-drop      an entry settled by a trial that loses is not pinned
  pin-inside    a pin made at one slot is in force at the slots after it
  pin-holds     a pinned entry is not settled again, and the kind it holds costs
  pin-order     the pins of the arguments come before the entry's own
  pin-slots     the open slots are bound before the others, and pin in that order
  amb-quiet     an expression with no binding prints one line and leaves no pin behind
  memo-pins     one call reached twice under different pins gives two different answers
  memo-asks     the same site number in two expressions is not the same call
  order-pre     the bind lines run outermost first, left to right
  tally-ret     the tally carries the result costs as well as the slot costs
"""

PROGS = {
    "one-only": """
        kind a
        kind b
        rise a b
        entry f b a
        val x a
        ask f(x)
    """,
    "plain-best": """
        kind a
        kind b
        kind c
        rise a b
        rise b c
        entry f c a
        entry f c b
        val x a
        ask f(x)
    """,
    "cross-sum": """
        kind a
        kind b
        kind c
        kind d
        rise a b
        rise b c
        rise c d
        entry f d a d
        entry f d b b
        val x a
        val y a
        ask f(x,y)
    """,
    "cross-even": """
        kind a
        kind b
        kind c
        rise a b
        rise b c
        entry f c a c
        entry f c c a
        val x a
        val y a
        ask f(x,y)
    """,
    "ret-decides": """
        kind a
        kind b
        kind c
        rise a b
        rise b c
        entry g b a
        entry g a a
        entry h c b
        val x a
        ask h(g(x))
    """,
    "ret-free": """
        kind a
        kind b
        kind c
        rise a b
        rise b c
        entry g b a
        entry g a a
        val x a
        ask g(x)
    """,
    "nest-expect": """
        kind a
        kind b
        kind c
        rise a b
        rise b c
        entry g b b
        entry g c a
        entry f c b a
        entry f c c b
        val x a
        val y a
        ask f(g(x),y)
    """,
    "nest-dead": """
        kind a
        kind b
        kind c
        rise a b
        rise b c
        entry g b b
        entry f c b a
        entry f c a a
        val x a
        val y a
        ask f(g(x),y)
    """,
    "nest-amb": """
        kind a
        kind b
        kind t
        rise a b
        rise b t
        entry g a a
        entry g b a
        open f t * *
        entry f t a
        val x a
        ask f(g(x))
    """,
    "path-short": """
        kind a
        kind b
        kind c
        rise a b
        rise b c
        rise a c
        entry f c c
        entry f c b
        val x a
        ask f(x)
    """,
    "path-tally": """
        kind a
        kind b
        kind c
        rise a b
        rise b c
        rise a c
        entry f c c
        val x a
        ask f(x)
    """,
    "open-lub": """
        kind a
        kind b
        kind c
        kind t
        rise a c
        rise b c
        rise c t
        open f t * * *
        val p a
        val q b
        ask f(p,q)
    """,
    "open-none": """
        kind a
        kind b
        kind c
        kind d
        kind t
        rise a c
        rise b c
        rise a d
        rise b d
        rise c t
        rise d t
        open f t * * *
        val p a
        val q b
        ask f(p,q)
    """,
    "open-first": """
        kind a
        kind b
        kind t
        rise a b
        rise b t
        open f t * * *
        val p a
        val q b
        ask f(p,q)
    """,
    "bound-under": """
        kind a
        kind b
        kind t
        rise a b
        rise b t
        open f t * *
        val x a
        ask f(x)
    """,
    "bound-over": """
        kind a
        kind b
        kind t
        rise a b
        rise b t
        open f a * *
        entry f t b
        val x b
        ask f(x)
    """,
    "bound-none": """
        kind a
        kind b
        kind t
        rise a t
        rise b t
        open f a * *
        val x b
        ask f(x)
    """,
    "open-free": """
        kind a
        kind b
        kind t
        rise a b
        rise b t
        entry g b b
        entry g a a
        open f t * *
        val x a
        ask f(g(x))
    """,
    "open-noslot": """
        kind a
        kind b
        rise a b
        open f b b a
        entry f a a
        val x a
        ask f(x)
    """,
    "arity": """
        kind a
        kind b
        rise a b
        entry f b a a
        entry f a a
        val x a
        ask f(x)
    """,
    "no-entry": """
        kind a
        kind b
        rise a b
        entry f b a a
        val x a
        ask f(x)
    """,
    "val-norise": """
        kind a
        kind b
        kind c
        rise a b
        entry f b b
        val x c
        ask f(x)
    """,
    "pin-drop": """
        kind a
        kind b
        kind t
        rise a b
        rise b t
        open f t * * *
        entry f b a b
        val p a
        val q b
        ask f(p,q)
        ask f(p,p)
    """,
    "pin-inside": """
        kind a
        kind b
        kind t
        rise a b
        rise b t
        open w t * *
        entry f t b b
        val x a
        val q b
        ask f(w(x),w(q))
    """,
    "pin-holds": """
        kind a
        kind b
        kind t
        rise a b
        rise b t
        open w t * *
        val q b
        val x a
        ask w(q)
        ask w(x)
    """,
    "pin-order": """
        kind a
        kind b
        kind t
        rise a b
        rise b t
        open w t * *
        open f t * *
        val x a
        ask f(w(x))
    """,
    "pin-slots": """
        kind a
        kind b
        kind t
        rise a b
        rise b t
        open w t * *
        open g t * *
        open f t t b *
        val x a
        ask f(w(x),g(x))
    """,
    "amb-quiet": """
        kind a
        kind b
        kind c
        kind d
        rise a b
        rise b c
        rise c d
        open w d * *
        entry f d a d
        entry f d b b
        val x a
        val y b
        ask f(w(x),y)
        ask w(y)
    """,
    "memo-pins": """
        kind a
        kind b
        kind t
        rise a b
        rise b t
        open w t * *
        entry w b a
        entry f t a b
        entry f t b b
        val x a
        val q b
        ask f(w(x),w(q))
    """,
    "memo-asks": """
        kind a
        kind b
        kind t
        rise a b
        rise b t
        entry f b a
        entry f t b
        val x a
        val y b
        ask f(x)
        ask f(y)
    """,
    "order-pre": """
        kind a
        kind b
        kind c
        rise a b
        rise b c
        entry g a a
        entry h a a a
        entry f c b
        val x a
        val y a
        ask f(h(g(x),g(y)))
    """,
    "tally-ret": """
        kind a
        kind b
        kind c
        rise a b
        rise b c
        entry g a a
        entry f c b
        val x a
        ask f(g(x))
    """,
}

ORDER = tuple(sorted(PROGS))


def prog(name):
    """The program named, as the lines a run is given."""
    return [row.strip() for row in PROGS[name].strip().splitlines()]
