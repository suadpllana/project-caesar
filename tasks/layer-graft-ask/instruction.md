`/app` is the settings service of a deployment tool, cut down to the part that composes a plan
and answers questions about it. A plan is a text file of ops. `/app/plans` holds four of them.
`lay` opens a layer, and layers are numbered 0, 1, 2 and so on in the order they are opened.
Every entry belongs to the layer most recently opened. `put p e` gives the path `p` the
definition `e`. `cut p` takes away the one standing there. `mix s d` copies one subtree over
another. Of the two questions, `ask p` asks what a path says, while `tot p` asks how many paths
at or under it hold a definition; either may name a layer count after the path. No entry
follows a question. A path is one to twenty-four segments joined by dots, each segment a
lowercase letter and up to seven more lowercase letters or digits. Integers are decimal and may
be negative. `/app/run_plan.py` takes a plan and prints one line per question, in the order the
questions were written, and nothing else.

An expression is written in prefix form. `lit n` is the integer `n`. `now p` and `old p` name a
path. `sum` and `top` take two expressions, giving the sum and the larger of them. `pick p a b`
gives `a` where the path holds a definition and `b` where it does not. An entry may end with
one guard, written either `if p n` or `un p`.

We rewrote this half last cycle and it has been wrong since. Run `/app/run_plan.py` on
`/app/plans/one.txt`. It prints `num site 2`. That line should read `num site 1`, since one
path under `site` holds a definition once the plan has been composed. The files you may change
are `/app/cfg/pile.py`, `/app/cfg/past.py`, `/app/cfg/made.py`, `/app/cfg/roll.py`,
`/app/cfg/work.py` and `/app/cfg/ans.py`. Nothing else is taken.
`/app/run_plan.py`, `/app/cfg/lex.py` and `/app/cfg/say.py` are put back as they were before
your files are run.

A definition is the expression a `put` wrote together with the layer that wrote it. A path
holds at most one of them at a time. The entries of a layer are taken in the order they were
written, each against what the earlier ones of that layer have left, so a later `put` replaces
an earlier one. A guard is not taken that way. It is a question about the plan as it stood
before the whole layer, which the earlier entries of its own layer do not move. `if` holds when
the path answers exactly that integer. `un` holds when it answers absent. A path that answers
circular satisfies neither. An entry whose guard does not hold is skipped.

A `cut` takes the definition at the path it names and every definition under it. A `mix` does
that to its destination first. Then it gives the destination, and each path under it, the
definition standing at the matching path at or under the source. Those source paths are the
ones left standing once the clearing has happened, and they are fixed before any of them is
written. What a `mix` gives over is the definitions themselves and not the values they have. So
a path that took one goes on following that expression, and moves when what the expression
names moves. The definition still belongs to the layer that wrote it.

Every question counts some number of layers. It is the number a question names, or the whole
plan where a question names none, or its own layer number in the case of a guard. That count
settles both halves of an answer: which definition is standing at the path, and what that
definition says. `now` counts the plan the way the question counts it. `old` counts it as it
stood before the layer that wrote the definition the `old` sits in. `sum` and `top` ask for
their left side and then for their right. `pick` looks at whether the path holds a definition
where the question counts to, not at what it answers, and asks for only the side it takes.

A path with no definition answers absent, and so does an expression whose first failing side is
absent. A definition asked for its value at a count while it is already being worked out at
that same count answers circular. An expression whose first failing side is circular answers
circular too. A definition naming its own path through `old` is naming an earlier definition,
and is not circular for that.

`ask` prints `val p v L`. It spells the path as the question spelled it, then the integer it
answered, then the layer that wrote the definition that answered. Where the answer is absent it
prints `val p gone`, and where it is circular, `val p loop`. `tot` prints `num p c`, where `c`
counts the paths at or under `p` that hold a definition.

`/app/plans/wide.txt` puts twenty thousand paths under two prefixes, chains five hundred more
layers of definitions over them and asks about them at forty different counts, while
`/app/plans/deep.txt` takes a copy that sits beside its own source, twenty-one times over. The
graded set is three plans of each of those sizes and three hundred and fifty-three smaller
ones, and all of it has to get through inside 60 seconds. Time both. Then call it done.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
