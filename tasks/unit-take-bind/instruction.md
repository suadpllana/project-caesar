`/app` is the binder we put module programs through before a change goes near the compiler. A program is a text file, one declaration to a line, and every line opens with the unit it belongs to. `own` declares a name in that unit. `als` gives a name to a unit. `pull` takes one name, or every name, out of a source. `shut` and `hide` hold a name back from other units. `ask` asks what a name means where it stands. `/app/progs` holds a few. `/app/run_prog.py` runs one and prints a line per `ask`.

Run it on `/app/progs/flat.txt`. The middle line comes out `top log own mid 1`. It should not: `top` reaches `log` in `mid`, which declares it, and in `base`, which declares it too, by routes of the same length. `/app/res/step.py`, `/app/res/show.py`, `/app/res/pick.py` and `/app/res/turn.py` are the four you may change. Nothing else in `/app` is taken from you, so whatever the rest of the tree calls into those four has to go on working.

A line is what makes a unit. A name that turns up only as the source of a pull, or only as what an `als` points at, is not one, and an `als` pointing at one of those binds nothing.

Everything a unit could mean by a name carries a rank. Its own declarations sit at rank 0, `own` and `als` alike. What arrives by a pull costs one more than the larger of two numbers: the rank of the reading that chose the source unit, and the rank the name already holds inside it.

The source of a pull is written as a name, and a name can denote more than one unit. The unit called that in the program is one reading. It is free. Any unit the name is bound to inside the pulling unit is another, costing whatever that binding cost, and both readings put candidates on the table. A name bound to something that is not a unit offers no reading of its own.

`pull <src> *` takes every name the source lets out. `pull <src> <name>` takes the one named. `shut` holds a name back from the first form. `hide` holds it back from both. Neither touches the unit doing the holding. A unit can still `ask` for a name it hides.

A name is settled from its cheapest candidates and from nothing else. A dearer candidate from some other origin is not a second opinion. Where every cheapest candidate carries one origin the name binds to it, and an origin that arrives twice, by two routes or on two identical lines, is still the one origin. Two origins at that price clash instead, and `own x` in unit `u` and `als x u` count as two: an item declared where it stands and a name for a unit are different origins even when the unit they name is the same one, so they clash like any other pair. Nothing survives a clash. It binds no name, neither form of pull carries it, and further out the name is simply absent.

Each binding is settled once. It rests on facts that cost strictly less than it does, which is why neither the order the lines are written in nor the order the units happen to be walked in may move so much as one character of what a program prints.

An `ask` prints its unit and its name, then `own <unit> <rank>` where the name was declared in that unit, `unit <unit> <rank>` where it denotes a unit, `clash <rank>` where it is contested, and a bare `none` where nothing binds it. Nothing else goes to the output.

`/app/progs/wide.txt` is one of the big ones. The graded set is a few hundred programs of this shape, none of them larger, and the whole of it has to be through inside ten minutes.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
