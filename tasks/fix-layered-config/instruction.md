`/app` is the settings service of a deployment tool, cut down to composing a plan and answering
questions about it. A plan is a text file of ops. `/app/plans` holds six of them. `lay` opens a
layer. Layers are numbered from 0 in the order they are opened. Every entry belongs to the layer
most recently opened. `put p e` gives the path `p` the definition `e`. `cut p` takes away the one
standing there. `mix s d`, `map s d`, `tie s d` and `veil s d` each take a source and a
destination. `ask p` asks what a path says. `tot p` asks how many paths at or under it hold a
definition. Either may name a layer count after the path. No entry follows a question. A path is
one to twenty-four dot-joined segments, each a lowercase letter and up to seven more lowercase
letters or digits. Integers are decimal and may be negative. `/app/run_plan.py` takes a plan and
prints one line per question, in the order they were written, and nothing else.

An expression is written in prefix form. `lit n` is the integer `n`. `now p` and `old p` name a
path. `sum` and `top` take two expressions, giving the sum and the larger of them. `pick p a b`
gives `a` where the path holds a definition and `b` where it does not. An entry may end with one
guard, written either `if p n` or `un p`.

We rewrote this half last cycle and it has been wrong since. Run `/app/run_plan.py` on
`/app/plans/one.txt`. It prints `num site 2`. That line should read `num site 1`, since one path
under `site` holds a definition once the plan has been composed. The files you may change are
`pile.py`, `past.py`, `made.py`, `roll.py`, `work.py` and `ans.py`, all in `/app/cfg`. Nothing
else is taken. `/app/run_plan.py`, `/app/cfg/lex.py` and `/app/cfg/say.py` are put back as they
were before your files run.

A `put` creates a definition from its expression, the layer that wrote it, and the view its `old`
operands read in, which is the store before that whole layer. The layer and the view stay with
the definition wherever it is later copied or shown. The layer is what `ask` prints. Only a `map`
replaces the view. A path holds at most one definition at a time. The entries of a layer are
taken in the order they were written, each against what the earlier ones of that layer have left,
so a later `put` replaces an earlier one. A guard is not taken that way. It is a question about
the plan as it stood before the whole layer, which the earlier entries of its own layer do not
move. `if` holds when the path answers exactly that integer. `un` holds when it answers absent. A
path that answers circular satisfies neither. An entry whose guard does not hold is skipped.

A `cut` takes the definition at the path it names and every definition under it; `mix`, `map`,
`tie` and `veil` each do that to their destination first. A `mix` then gives the destination, and
each path under it, the definition standing at the matching path at or under the source. Those
source paths are the ones left standing after the clearing, fixed before any of them is written.
A `mix` gives over the definitions themselves, not their values. A path that took one goes on
following that expression, and moves when what the expression names moves.

A `map` carries its source the same way. In each definition it carries, it changes every path
operand of `now`, `old` and `pick` that equals the source path or is under it: the source prefix
becomes the destination prefix, and the remaining segments stay in order. Other path operands and
all integers stay as they are. The rewriting reaches into both arms of `pick`. If the source
already came through a `map`, these changes act on its current path operands. `mix` does not
change any path operands.

Each definition installed by `map` gets a new view for `old`: the complete store immediately
before that entry, earlier entries of its own layer included and its destination not yet cleared.
An `old` in the copied definition asks for its changed path in that view, even when its path was
outside the source and therefore did not change. Within one `map`, each distinct source
definition becomes one new definition. Source paths holding the same definition have their mapped
paths holding the same new one. Separate `map` entries create separate definitions. A later `put`
below a mapped subtree is a fresh definition: it does not inherit earlier path changes or
captured views. Unchanged definitions elsewhere below that subtree keep both.

From its entry on, a `tie` makes the destination and every path under it show what the source and
the matching path under it show in the view being read. A definition written under the source
later shows at once; one taken away stops showing. A path under a tie holds the definition it
shows. The definitions shown are moved as `map` moves them, path operands under the source
becoming the destination prefix, acting on their current operands, so a tie whose source is
itself tied moves them twice.

A tie shows definitions, not values. Beyond moving their path operands it changes nothing a
definition carries. Within one tie, each distinct source definition becomes one definition, the
same wherever and whenever it shows; a later `put` under the source is a new one. A `tie` or
`veil` whose source and destination overlap is a bad plan, and `/app/run_plan.py` rejects it.

A `veil` keeps the complete destination store immediately before that entry, clears the
destination, then places a live view of the source above the saved destination. At each path at
or below the destination, a definition written there after the veil wins; otherwise the matching
source definition in the view being read wins if one shows there, and the saved destination
definition wins if none does. A circular source definition still wins over the fallback: the
choice is made by definition presence, not by value. The children of both sides can show even
when neither side has a definition at their parent. `tot` counts a path only once if both sides
define it. Source definitions have their operands moved as in a tie and share one moved identity
per distinct source definition within that veil. Fallback definitions keep their operands and
their identity.

What is written at or under a tie or a veil afterwards stands in front of what shows there. A
`put` gives its own path a definition and changes nothing else. A `cut`, or a `mix`, `map`, `tie`
or `veil` whose destination lies under the tie or the veil, leaves nothing inherited showing at
or under that path until it is written there again, and a later `put` beneath it shows for its
own path only. A `cut` at the tied or veiled path itself takes it away with everything under it.
A `mix` or `map` taking its source from what a tie or a veil shows carries the definitions
visible at that entry and nothing of the tie or veil itself, so the copy stays as it was while
the source moves on; a tie placed under such a copy afterwards is live like any other.

A lookup reaching a path at or under a tied path continues at the matching path under the source,
in the same view, and may continue again from there. A veil follows its source the same way
before consulting its saved fallback. Where a lookup comes back to a path it has already been
through, it finds nothing. Nothing shows at a path of more than twenty-four segments, and `tot`
counts no path longer than that.

Every question counts some number of layers. It is the number it names, the whole plan where it
names none, or its own layer number in the case of a guard. That count selects the view the
question starts in. Both the standing definition and its value come from it. `now` reads in the
current view. `old` uses the view attached to the definition it sits in. When a reference enters
that view, any `now` or `pick` reached there uses that view too; an `old` reached there follows
the view attached to its own definition. `sum` and `top` ask for their left side and then for
their right. `pick` looks at whether the path holds a definition in the current view, not at what
it answers, and asks for only the side it takes.

A path with no definition answers absent. An expression answers whatever its first failing side
answers, absent or circular. A definition asked for its value in a view while it is already being
worked out in that same view answers circular. Captured entry views and the views at layer counts
are distinct when their stores differ. A definition naming its own path through `old` is naming
an earlier definition, and is not circular for that.

`ask` prints `val p v L`: the path as the question spelled it, the integer it answered, and the
layer that wrote the definition that answered. Where the answer is absent it prints `val p gone`,
and where it is circular, `val p loop`. `tot` prints `num p c`, where `c` counts the paths at or
under `p` that hold a definition.

`/app/plans/wide.txt` puts twenty thousand paths under two prefixes, ties a third prefix to one
of them, chains five hundred more layers over them that each write or remove under the tied
prefix, and asks about all three at forty different counts. `/app/plans/deep.txt` takes a copy
that sits beside its own source, twenty-one times over. The graded batch has three plans of each
size, three of twenty-one `map` copies, three that copy what a tie shows back under the tie's own
source twenty-one times over, three that put a live source above a deep frozen copy with
overlapping paths, sparse writes and removals inside all of those copies, and hundreds of smaller
plans. All of it must finish inside 60 seconds. `/app/plans/mapped.txt` and `/app/plans/tied.txt`
are small inputs using the two newer operations. Run and time the service before calling the
repair done.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
