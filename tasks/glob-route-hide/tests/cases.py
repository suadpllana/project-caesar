"""The enumerated programs: one per graded decision, and both sides of every fence.

Each is small enough to resolve by hand. The name of a case is the rule it pins, so a failure
says which rule broke rather than "a generated program was wrong". Expected lines live in
seal/gt.json, frozen from the sealed model and checked by hand before the grading file existed.

  ordinary-tree          everyday program: parent helpers, public items, all references resolve
  vis-child-sees         a child reading its parent through a glob sees the parent's private item
  vis-outsider-denied    a module outside the parent reading the same glob sees nothing
  vis-grandchild         private lines are seen from every module inside, however deep
  vis-parent-denied      a parent does not see its child's private item
  vis-no-inherit         a module sees its parent's names only through its own lines
  vis-sibling-prefix     `ab` is not inside `a`: nesting follows whole names between the dots
  narrow-private-glob    a private glob passes things on only to modules inside the reader
  narrow-pub-keeps       a public glob passes them on as widely as they came
  narrow-explicit        a private explicit import narrows what it gives in the same way
  narrow-keeps-item      a public re-export cannot make a private item wider than its line
  widen-two-routes       a narrow route and a wide route to one item: the wide one counts
  widen-late-cycle       the wide route closes only through a cycle of globs
  widen-gated-arm        the arm that carried the wide route is gated off
  hide-own-private       a private own import hides the public glob's name from outsiders
  hide-descendant-sees   a module inside the hider sees the hider's own private binding
  hide-broken            an own import that finds nothing still hides the globs
  hide-gated-off         an own import whose flag is off hides nothing
  hide-gated-on          the same import with its flag on hides
  gate-negated           `if !F` lines exist only while F is off
  glob-unbound-name      a module binding one name still gets every other name from its globs
  amb-two-globs          two globs offering different items: ambiguous
  amb-file-order         candidates follow their item lines, not the order they were reached
  amb-carried            an ambiguous name travels on through a glob as all its candidates
  amb-filtered           ambiguous in one module, resolved in a reader that sees one candidate
  amb-explicit           an explicit import of an ambiguous name gives every candidate
  route-same-item        one item reached through two globs is one candidate
  own-two-lines          an item line and an import line for one name: both are candidates
  dup-item-lines         two present item lines with one name are two items
  cycle-alone            a cycle of globs with no item behind it gives nothing
  cycle-fed              a cycle fed at one member reaches every member
  cycle-cut              a member binding a name that flows round the cycle cuts it there
  rename-chain           an import with a rename gives under the new name only
  rename-hides-bound     a rename binds the new name, which the globs then no longer give
  explicit-denied        an explicit import of something the importer cannot see is broken
  explicit-ancestor      an explicit import sees an enclosing module's private item
  missing-module         an import from a module the program does not declare finds nothing
  self-import            importing a name from the module itself binds it and gives nothing
  self-glob              a module reading itself through a glob gains nothing
  unresolved-plain       a name nothing offers
"""

CASES = {
    "ordinary-tree": """
flags
mod core
pub item run
pub item stop
item help
mod core.io
use core::*
pub item read
ref help
mod app
use core::*
use core.io::*
ref run
ref read
ref stop
""",
    "vis-child-sees": """
flags
mod a
item h
mod a.b
use a::*
ref h
""",
    "vis-outsider-denied": """
flags
mod a
item h
mod c
use a::*
ref h
""",
    "vis-grandchild": """
flags
mod a
item h
mod a.b
use a::*
mod a.b.c
use a.b::*
ref h
""",
    "vis-parent-denied": """
flags
mod a
use a.b::*
ref h
mod a.b
item h
""",
    "vis-no-inherit": """
flags
mod a
pub item h
mod a.b
ref h
""",
    "vis-sibling-prefix": """
flags
mod a
item h
mod ab
use a::*
ref h
mod a.b
use a::*
ref h
""",
    "narrow-private-glob": """
flags
mod c
pub item x
mod m
use c::*
ref x
mod o
use m::*
ref x
""",
    "narrow-pub-keeps": """
flags
mod c
pub item x
mod m
pub use c::*
mod o
use m::*
ref x
""",
    "narrow-explicit": """
flags
mod c
pub item x
mod m
use c::x
mod m.k
use m::*
ref x
mod o
use m::*
ref x
""",
    "narrow-keeps-item": """
flags
mod a
item x
mod a.b
pub use a::*
mod a.c
use a.b::*
ref x
mod d
use a.b::*
ref x
""",
    "widen-two-routes": """
flags
mod c
pub item x
mod m
use c::*
pub use p::*
mod p
pub use c::*
mod o
use m::*
ref x
""",
    "widen-late-cycle": """
flags
mod c
pub item x
mod m
use c::*
pub use r1::*
mod r1
pub use r2::*
mod r2
pub use m::*
pub use c::*
mod o
use m::*
ref x
""",
    "widen-gated-arm": """
flags
mod c
pub item x
mod m
use c::*
pub use p::* if fast
ref x
mod p
pub use c::*
mod o
use m::*
ref x
""",
    "hide-own-private": """
flags
mod q
pub item x
mod r
pub item x
mod m
pub use q::*
use r::x
ref x
mod o
use m::*
ref x
""",
    "hide-descendant-sees": """
flags
mod q
pub item x
mod r
pub item x
mod m
pub use q::*
use r::x
mod m.k
use m::*
ref x
""",
    "hide-broken": """
flags
mod q
pub item y
mod r
pub item x
mod m
use q::x
use r::*
ref x
""",
    "hide-gated-off": """
flags
mod q
pub item x
mod r
pub item x
mod m
use q::x if dbg
use r::*
ref x
""",
    "hide-gated-on": """
flags dbg
mod q
pub item x
mod r
pub item x
mod m
use q::x if dbg
use r::*
ref x
""",
    "gate-negated": """
flags dbg
mod a
pub item x if !dbg
pub item y if dbg
pub item z if !lite
mod b
use a::*
ref x
ref y
ref z
""",
    "glob-unbound-name": """
flags
mod a
pub item x
pub item y
mod b
item x
use a::*
ref x
ref y
""",
    "amb-two-globs": """
flags
mod p
pub item x
mod q
pub item x
mod m
use q::*
use p::*
ref x
""",
    "amb-file-order": """
flags
mod z
pub item x
mod m
use y::*
use z::*
ref x
mod y
pub item x
""",
    "amb-carried": """
flags
mod p
pub item x
mod q
pub item x
mod m
pub use p::*
pub use q::*
mod n
use m::*
ref x
""",
    "amb-filtered": """
flags
mod m
pub use p::*
use q::*
ref x
mod p
pub item x
mod q
pub item x
mod n
use m::*
ref x
""",
    "amb-explicit": """
flags
mod p
pub item x
mod q
pub item x
mod m
pub use p::*
pub use q::*
mod n
use m::x
ref x
""",
    "route-same-item": """
flags
mod c
pub item x
mod a
pub use c::*
mod b
pub use c::*
mod m
use a::*
use b::*
ref x
""",
    "own-two-lines": """
flags
mod a
pub item x
mod m
item x
use a::x
ref x
""",
    "dup-item-lines": """
flags
mod m
pub item x
pub item x
pub item y if dbg
pub item y if !dbg
ref x
ref y
""",
    "cycle-alone": """
flags
mod a
pub use b::*
ref x
mod b
pub use c::*
mod c
pub use a::*
""",
    "cycle-fed": """
flags
mod r0
pub use r1::*
pub use s::*
ref x
mod r1
pub use r2::*
ref x
mod r2
pub use r0::*
ref x
mod s
pub item x
""",
    "cycle-cut": """
flags
mod r0
pub use r1::*
ref x
mod r1
pub use r2::*
pub item x
ref x
mod r2
pub use r3::*
ref x
mod r3
pub use r0::*
pub use s::*
ref x
mod s
pub item x
""",
    "rename-chain": """
flags
mod a
pub item x
mod b
pub use a::x as y
mod c
use b::*
ref y
ref x
""",
    "rename-hides-bound": """
flags
mod a
pub item x
pub item y
mod m
use a::x as y
use a::*
ref y
ref x
""",
    "explicit-denied": """
flags
mod a
item x
mod b
use a::x
ref x
""",
    "explicit-ancestor": """
flags
mod a
item x
mod a.b
use a::x
ref x
""",
    "missing-module": """
flags
mod a
pub item x
mod m
use nowhere::x
use a::*
ref x
""",
    "self-import": """
flags
mod a
pub item x
mod m
use m::x
use a::*
ref x
""",
    "self-glob": """
flags
mod m
use m::*
pub item x
ref x
ref y
""",
    "unresolved-plain": """
flags
mod a
ref x
""",
}

ORDER = list(CASES)


def prog(name):
    """The case's program as a list of lines, without the leading and trailing blank lines."""
    return CASES[name].strip("\n").split("\n")
