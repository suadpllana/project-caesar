`/app` is the replay half of the durable runtime we try workflow changes on before they go near the shipped one. A run file is a text file of lines. `/app/progs` holds four of them. Blank lines are ignored. A `b` line is one op of the workflow body, in the order the body runs them. An `e` line is one line of the history an earlier attempt recorded, in the order it happened. An `r` line is one value that work run for real gives back. Values are integers, and names, tags and keys are single words. `/app/run_dur.py` takes a run file and prints what happened, a line per event.

A body runs as branches. Branch 0 starts at the first op. `fork` starts another branch at a label and keeps going itself; branches are numbered from 0 in the order they are forked. Each branch has its own accumulator, starting at zero, and every result, signal and marker it takes goes into it. `add` and `set` work that accumulator, `jz` jumps when it is zero and `jnz` when it is not, `jmp` and `lab` are the rest of the jumps, and `end` ends the branch.

Four ops issue a command. `call` and `fire` issue one of kind `call`, `spawn` one of kind `child`, and `nap` one of kind `timer`; the word after the op is the command's name. `call`, `spawn` and `nap` then wait for that command's own result. `fire` does not wait, and a later `take` waits for the earliest command the branch has issued and not yet taken the result of. A `take` with nothing untaken changes nothing. `wait` waits for a signal with the tag it names, and `mark` reads a version marker without waiting for anything.

The recorded lines are four as well. A `go` is a command that was issued, with its kind and its name. An `ok` is a result, with the kind and name of the command it answers and its value. A `sig` is a signal that arrived, with its tag and value. A `ch` is a marker choice that was recorded, with its key and value.

We rewrote this half last cycle and it has been wrong since. Run `/app/run_dur.py` on `/app/progs/tiny.txt`. The second line comes out `0 ok call 0 7` and it should read `0 ok call 0 5`, because the two commands were answered in the opposite order from the one they were issued in and each one takes the result recorded under its own name.

Every count and every position here starts at zero. Commands are counted by kind, and the count of one kind is not moved by commands of any other. The command at count `i` of its kind matches the `go` at position `i` among the `go` lines of that kind, taken in the order they appear in the history. If that `go` carries another name the run stops there and prints `drift <kind> <i> <recorded name> <name asked for>`.

The result of a matched command is recorded under its kind and its name together: the command at count `j` among the commands of that kind and name takes the `ok` at position `j` among the `ok` lines carrying that same kind and name.

A branch that waits goes down with a mark, and the mark is the position in the history of the line that will release it. For a command that is the line carrying its result. For a `wait` it is the line of the signal the branch claims as it goes down, which is the earliest `sig` of that tag nobody has claimed yet. A branch waiting for something the history never recorded goes down with no mark at all.

Which branch runs next follows from that. A branch able to run without waiting for anything goes first, and among those the lowest numbered. Otherwise the waiting branch whose mark is smallest goes, whatever its number and whatever order the branches started waiting in. A branch runs until it waits or ends.

When no branch can run and no waiting branch has a mark, the run has nothing left to replay. It prints `live`, once, before anything else it does. Every waiting branch can run again from that point, nothing waits again, and no command is matched against the history again however much of it is left. A result the history does not carry, then or earlier, comes off the `r` lines in the order the branches take them, and is zero once those run out.

`mark` takes the earliest `ch` of its own key that has not been taken. With none of that key left the value is zero while the run still has something to replay, and the marker's own second word once `live` has been printed. Either way the branch prints `ver <key> <value>`.

Every line of the printout but the last names the branch it belongs to. A fork prints `<b> fork <new branch>`, a command issued prints `<b> go <kind> <i> <name>`, a result taken prints `<b> ok <kind> <i> <value>`, a signal taken prints `<b> sig <tag> <value>`, a marker prints `<b> ver <key> <value>`, and a branch ending prints `<b> end <accumulator>`.

Branch 0 ending ends the run, whatever the other branches are doing. The run then prints `fin` and branch 0's accumulator, unless the history still holds a `go` that no command matched: then it prints `drift left <kind> <i>` for the earliest such `go` in the history instead, `i` being its position among the `go` lines of its kind. Only `go` lines count for that. An `ok`, a `sig` or a `ch` that nobody took is not a failure. A body that executes more than 200000 ops prints `over` and nothing else.

The files you may change are `/app/dur/tab.py`, `/app/dur/edge.py`, `/app/dur/pair.py`, `/app/dur/hold.py`, `/app/dur/sched.py`, `/app/dur/wake.py` and `/app/dur/ver.py`. Nothing else. Every other file under `/app` is restored from a clean copy before yours are run. A change anywhere else has no effect, and a new file put beside those seven is never read. The rest of the tree imports the seven under the names they already use. The functions they define have to keep those names and their arguments.

Your engine is graded on run files you have not seen. Six of them are large: three carry twenty-four thousand commands on one branch against a history of forty-eight thousand lines, and three carry eight thousand branches of eight commands each against a history of a hundred and twenty-eight thousand lines. All of the graded run files together have to finish inside 60 seconds of wall clock.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
