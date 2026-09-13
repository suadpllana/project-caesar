`/app` is the settings service of a deployment tool, cut down to the part that composes a plan
and answers questions about it. A plan is a text file of ops. `/app/plans` holds six of them.
`lay` opens a layer, and layers are numbered 0, 1, 2 and so on in the order they are opened.
Every entry belongs to the layer most recently opened. `put p e` gives the path `p` the
definition `e`. `cut p` takes away the one standing there. `mix s d` copies one subtree over
another. `map s d` installs a copy with its path references moved to the destination. `tie s d`
makes the destination show the source as it stands, from then on. Of the two questions, `ask p`
asks what a path says, while `tot p` asks how many paths at or under it hold a definition; either
may name a layer count after the path. No entry follows a question. A path is one to twenty-four
segments joined by dots, each segment a lowercase letter and up to seven more lowercase letters
or digits. Integers are decimal and may be negative. `/app/run_plan.py` takes a plan and prints
one line per question, in the order the questions were written, and nothing else.

An expression is written in prefix form. `lit n` is the integer `n`. `now p` and `old p` name
a path. `sum` and `top` take two expressions, giving the sum and the larger of them. `pick p a
b` gives `a` where the path holds a definition and `b` where it does not. An entry may end
with one guard, written either `if p n` or `un p`.

We rewrote this half last cycle and it has been wrong since. Run `/app/run_plan.py` on
`/app/plans/one.txt`. It prints `num site 2`. That line should read `num site 1`, since one
path under `site` holds a definition once the plan has been composed. The files you may change
are `/app/cfg/pile.py`, `/app/cfg/past.py`, `/app/cfg/made.py`, `/app/cfg/roll.py`,
`/app/cfg/work.py` and `/app/cfg/ans.py`. Nothing else is taken. `/app/run_plan.py`,
`/app/cfg/lex.py` and `/app/cfg/say.py` are put back as they were before your files are run.

A `put` creates a definition with its expression and the layer that wrote it. A path holds at
most one of them at a time. The entries of a layer are taken in the order they were written,
each against what the earlier ones of that layer have left, so a later `put` replaces an
earlier one. A guard is not taken that way. It is a question about the plan as it stood before
the whole layer, which the earlier entries of its own layer do not move. `if` holds when the
path answers exactly that integer. `un` holds when it answers absent. A path that answers
circular satisfies neither. An entry whose guard does not hold is skipped.

A `cut` takes the definition at the path it names and every definition under it. A `mix` does
that to its destination first. Then it gives the destination, and each path under it, the
definition standing at the matching path at or under the source. Those source paths are the
ones left standing once the clearing has happened, and they are fixed before any of them is
written. What a `mix` gives over is the definitions themselves and not the values they have.
So a path that took one goes on following that expression, and moves when what the expression
names moves. The definition still belongs to the layer that wrote it.

A `map` takes its source after clearing its destination, as `mix` does. In each definition it
carries, it changes every path operand of `now`, `old` and `pick` that equals the source path
or is under it: the source prefix becomes the destination prefix, and the remaining segments
stay in order. Other path operands and all integers stay as they are. This applies to both
arms of `pick`. If the source already came through a `map`, these changes act on its current
path operands. `mix` does not change any path operands.

Each definition installed by `map` also gets a new view for `old`: the complete store
immediately before that entry, before its destination was cleared. Earlier entries of the same
layer are included. An `old` in the copied definition asks for its changed path in that view,
even when its path was outside the source and therefore did not change. This replaces any
earlier view for `old`. Definitions created by `put` use the view before their whole layer
instead; `mix` preserves the view its source definition already has. The layer printed for a
definition remains the layer of its original `put` in all three operations.

Within one `map`, each distinct source definition becomes one new definition. If several
source paths hold the same definition, their mapped paths hold the same new definition.
Separate `map` entries create separate definitions. A later `put` below a mapped subtree is a
fresh definition: it does not inherit earlier path changes or captured views. Unchanged
definitions elsewhere below that subtree keep both.

A `tie` takes away what stands at its destination, as `mix` does. From then on the
destination and every path under it show what the source and the matching path under it show
in the view being read. A definition written under the source later shows at once; one taken
away stops showing. A path under a tie holds the definition it shows. The definitions shown are
moved as `map` moves them, path operands under the source becoming the destination prefix,
acting on their current operands, so a tie whose source is itself tied moves them twice. What
is written at or under the destination afterwards stands in front of what shows there. A `put`
gives its own path a definition and changes nothing else. A `cut`, or a `mix`, `map` or `tie`
whose destination lies under the tie, leaves nothing from the source showing at or under that
path until it is written again. A later `put` beneath such a path shows, for its own path
only. A `cut` at the tied path itself takes the tie away with everything under it.

A tie shows definitions, not values, and changes nothing a definition already carries: the
layer printed is the layer of the original `put`, and `old` keeps the view the source
definition has. Within one tie, each distinct source definition becomes one definition, the
same wherever and whenever it shows; a later `put` under the source is a new one. A `mix` or
`map` whose source shows definitions through a tie carries the definitions shown at that
entry and nothing of the tie, so the copy stays as it was when the tie's source moves on; a
tie placed under such a copy afterwards is live like any other. A tie whose source and
destination overlap is a bad plan, and `/app/run_plan.py` rejects it.

A lookup that reaches a path at or under a tied path continues at the matching path under the
source, in the same view, and may continue again from there. Where it comes back to a path it
has already been through, it finds nothing. Nothing shows at a path of more than twenty-four
segments, and `tot` counts no path longer than that.

Every question counts some number of layers. It is the number a question names, or the whole
plan where a question names none, or its own layer number in the case of a guard. That count
selects the view in which the question starts: both the standing definition and its value come
from that view. `now` reads in the current view. `old` uses the view attached to the
definition it sits in. When a reference enters that view, any `now` or `pick` reached there
uses that view too; an `old` reached there follows the view attached to its own definition.
`sum` and `top` ask for their left side and then for their right. `pick` looks at whether the
path holds a definition in the current view, not at what it answers, and asks for only the
side it takes.

A path with no definition answers absent, and so does an expression whose first failing side
is absent. A definition asked for its value in a view while it is already being worked out in
that same view answers circular. Captured entry views and the views at layer counts are
distinct when their stores differ. An expression whose first failing side is circular answers
circular too. A definition naming its own path through `old` is naming an earlier definition,
and is not circular for that.

`ask` prints `val p v L`. It spells the path as the question spelled it, then the integer it
answered, then the layer that wrote the definition that answered. Where the answer is absent
it prints `val p gone`, and where it is circular, `val p loop`. `tot` prints `num p c`, where
`c` counts the paths at or under `p` that hold a definition.

`/app/plans/wide.txt` puts twenty thousand paths under two prefixes, ties a third prefix to
one of them, chains five hundred more layers of definitions over them with a write or a
removal under the tied prefix in each, and asks about all three at forty different counts.
`/app/plans/deep.txt` takes a copy that sits beside its own source, twenty-one times over.
The graded batch includes three plans of each size, three with twenty-one such copies using
`map` and sparse edits within those copies, three that copy what a tie shows back under the
tie's own source twenty-one times over with sparse writes and removals inside the copies, and
hundreds of smaller plans. All of the batch must finish inside 60 seconds.
`/app/plans/mapped.txt` and `/app/plans/tied.txt` are small inputs using the two newer
operations. Run and time the service before calling the repair done.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
