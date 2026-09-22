`/app` is the replay half of the durable runtime we try workflow changes on before they go near the shipped one. A run file is a text file of lines. `/app/runs` holds four of them. Blank lines are ignored. A `b` line is one op of the workflow body, in the order the body runs them. An `e` line is one event of the history an earlier attempt recorded, in the order it happened. An `r` line is one value that work run for real gives back. Values are integers. Names, tags and keys are single words. `/app/run_dur.py` takes a run file and prints what happened, a line per event.

The body ops are these. `call`, `spawn` and `nap` each issue a command and take its result. `fire` and `open` issue one and leave it outstanding. `join` and `race` take the result of an outstanding command. `wait` takes a signal and `mark` reads a version marker. `add` and `set` work the accumulator. `jz`, `jnz` and `jmp` are the jumps. `lab` marks a place and does nothing else. `fin` ends the body. The accumulator starts at zero, every result taken and every marker and signal goes into it, `jz` jumps when it is zero and `jnz` when it is not. `call` and `fire` issue a command of kind `call`, `spawn` and `open` of kind `child`, `nap` of kind `timer`. The word after the op is the command's name.

Four things are recorded. A `go` is a command that was issued, with its kind and name. An `ok` is an answer, with the kind and name of the command it answers and its value. A `sig` is a signal that arrived, with its tag and value. A `ch` is a marker choice, with its key and value.

We rewrote this half last cycle and it has been wrong since.

Run `/app/run_dur.py` on `/app/runs/tiny.txt`. The third line comes out `ok call 0 7` and it should read `ok call 0 5`. The two commands were answered in the opposite order from the one they were issued in, and each one takes the answer recorded under its own name.

Every count and every position here starts at zero. Commands are counted by kind, from zero, and the count of one kind is not moved by commands of any other. The command at count `i` of its kind matches the `go` at position `i` among the `go` lines of that kind, taken in the order they appear in the history. If that `go` carries another name the run stops there and prints `drift <kind> <i> <recorded name> <name asked for>`.

A command whose kind has no `go` left at its count opens the live side. `live` is printed once for the whole run, before that command's own line, and no command issued after it looks at the history for a `go`, whatever its kind.

A command that matched a `go` takes the answer recorded under its kind and its name together. Counted that way, the command at count `j` among the commands of that kind and name takes the `ok` at position `j` among the `ok` lines carrying that same kind and name, in the order those lines appear.

A command on the live side takes the next `r` value instead, in the order the live commands were issued, and zero once the `r` lines run out. Its answer counts as having arrived after every recorded answer.

`call`, `spawn` and `nap` take the answer of the command they issue. `join` takes the result of the outstanding command that was issued earliest. `race` takes the result of the outstanding command whose answer arrives earliest. A recorded answer arrives at the position of its `ok` line, and an outstanding command with no answer at all is never taken by a race. A command whose result is taken is no longer outstanding.

A result that is needed and has no answer stops the run: it prints `hold <kind> <i>` naming that command. A `join`, or a `race` where no outstanding command has an answer, names the outstanding command issued earliest. With nothing outstanding at all it prints `hold none` instead.

`wait` takes the earliest `sig` of its own tag that has not been taken, wherever that line sits in the history and whichever side of the boundary the run is on. It prints `sig <tag> <value>`. With none of that tag left it stops the run and prints `hold sig <tag>`.

`mark` takes the earliest `ch` of its own key that has not been taken. With none of that key left the value is zero while the run is still replaying, and the marker's own second word once the run has gone live. Either way it prints `ver <key> <value>`.

Every command issued prints `go <kind> <i> <name>` and every result taken prints `ok <kind> <i> <value>`, with `i` the command's own count within its kind. A body that reaches `fin` while the history still holds a `go` that no command matched prints `drift left <kind> <i>` for the earliest such `go` in the history. Here `i` is its position among the `go` lines of its kind, and nothing else is printed.

Only `go` lines count for that: an `ok`, a `sig` or a `ch` that nobody took is not a failure. A run that stopped short never makes the check. A body that reaches `fin`, or runs off its last op, with nothing left over prints `fin <accumulator>`.

A body that executes more than 200000 ops prints `over` and nothing else.

The files you may change are `/app/dur/tab.py`, `/app/dur/edge.py`, `/app/dur/pair.py`, `/app/dur/pend.py`, `/app/dur/sigq.py` and `/app/dur/ver.py`. Nothing else. Every other file under `/app` is restored from a clean copy before yours are run. A change anywhere else has no effect, and a new file put beside those six is never read. The rest of the tree imports the six under the names they already use. The functions they define have to keep those names and their arguments.

Your engine is graded on run files you have not seen. Six of them are large: three carry thirty thousand commands against a history of sixty thousand lines, and three carry twenty-two thousand commands against forty-four thousand lines. All of the graded run files together have to finish inside 60 seconds of wall clock.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
