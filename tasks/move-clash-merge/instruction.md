`/app` is the reconciler of our sync client. It keeps the record of what the workstation and the
server last agreed on. It is handed each copy of that tree once both have been worked on, and it
settles what the record should now be, and what each side has to do to get there. A scenario
file gives a record and then a run of rounds. `/app/rounds` holds three. `/app/run_sync.py`
replays one and prints what the engine did with it.

Run it on `/app/rounds/plain.txt`. In the second round the server has made `/doc/new` and put
`plan.txt` into it, and the engine hands the workstation `mv /doc/old/plan.txt
/doc/new/plan.txt` before `mkd /doc/new`. There is no `/doc/new` on the workstation when the
move arrives. The move is passed over, and the round ends with the two sides holding different
trees: the file sits in `/doc/old` on one and in `/doc/new` on the other. `/app/rounds/tidy.txt`
comes out wrong as well. `/app/rounds/away.txt` comes out right, and has to go on doing so.

`/app/mrg/live.py`, `/app/mrg/spot.py`, `/app/mrg/name.py`, `/app/mrg/book.py` and
`/app/mrg/step.py` are the five files you may change. The rest of `/app` stays as it is.

A scenario declares the record first, one line to a node, parents before children: `d <number>
<path>` for a folder, `f <number> <path> <content>` for a file. Then `L <op>` and `R <op>` lines
say, in order, what the workstation and the server each did to the copy it holds, and `sync`
runs a round. Rounds are numbered from one. Both sides start the first one holding the record.
The operations are `mkd <path>`, `mkf <path> <content>`, `ed <path> <content>`, `mv <path>
<path>` and `rm <path>`. A move names the whole destination path. A removal names a file, or a
folder with nothing left in it. An operation a side cannot carry out is passed over. The
workstation compares names exactly. On the server they are compared without regard to case, and
so they are in the record, which cannot hold two names in one folder that differ only in case.

Each round prints the operations the engine gave each side, one to a line and in the order it
gave them, as `<round> L <op>` and `<round> R <op>`, with the operation written the way a
scenario writes it. Then it prints the tree each side holds afterwards, `<round> l <path>
<content>` and `<round> r <path> <content>`, in ascending path order, with `-` standing in for
the content of a folder. The record is not printed. It carries forward: what one round settles
is what the next round is handed.

A node both sides still hold stays. A node neither side holds is gone. A node one side removed
stays if the other side changed it at all. Content, name, the folder it sits in: any of the
three counts. It goes if the other side left it exactly as the record had it. A folder that
would otherwise go stays open for the nodes the record put inside it and only for those, and it
stays as long as one of them stays and still settles inside it. So a node that has moved out
will not hold it, and a node moved in from elsewhere will not either. That pull carries on up
the chain of folders the record gives.

The folder a node sits in and the name it carries are settled apart from each other. For each of
the two: a part one side changed and the other did not takes the change; a part both sides
changed the same way takes that; a part both sides changed differently takes what the server
has. Count a settled part as the server's whenever it is what the server holds, and as the
workstation's only when it is not.

A node whose settled folder did not stay goes into the nearest folder above that one in the
record that did, under the name it settled on. The settling can leave nodes sitting inside each
other. Take one such loop and put back the node in it whose folder came from the workstation,
smallest number first, into the folder the record gives it, and above that again if that folder
did not stay, and where no node in the loop took its folder from the workstation put back the
smallest number. Repeat until nothing sits inside itself.

A file only one side still holds keeps the bytes that side has. A file both sides hold keeps the
bytes in the record when neither wrote it, the bytes of whichever side wrote it when only one
did, and those bytes when both wrote the same. When both wrote it and the bytes differ, the
bytes from the workstation stay with the node, and a second file appears beside it in the same
folder, wanting the same name and carrying the bytes from the server.

Nodes new to the record are numbered once the round has settled: the server first, in ascending
order of the paths those nodes have there, then the workstation in ascending order of the paths
they have there, then the second files, in ascending order of the numbers of the files they came
from.

Several nodes in one folder can want one name. Names differing only in case are one name. The
node that keeps it is the one the record already had in that folder under that name, or failing
that the one the server holds under that name, or failing that the one the workstation holds
under that name, or failing all three the smallest number. A second file never keeps the name.
Each of the rest is marked. The mark goes in before the last dot of the name when that dot is
neither the first character nor the last and at the end of the name otherwise, and the number it
carries is the smallest free in that folder, counted without regard to case, against the names
settled there already. The marked nodes take theirs in ascending order of the numbers they hold.

Each side is then given the operations that bring it to the record. Nothing is emitted before it
can be carried out. A destination folder counts only when that path is, at that moment, the node
the record puts the child under, and not whatever else happens to be standing there under that
name. The name has to be free. A folder is removed only once nothing is left in it. Bytes are
written only once the file sits where the record puts it. Where more than one operation can be
carried out, removals go before moves, moves before creations, creations before writes, and
within a kind the operation whose first path sorts earliest goes first. Where none can be
carried out and the side has still not reached the record, take the smallest-numbered node whose
folder is ready but whose name is held by something else, and move that something aside within
the folder it is in, to `~t1`, or to the smallest `~t<number>` free there. Then carry on. A node
can be standing on the name it wants itself, which is what a change of case comes to on a side
that compares names without regard to it.

Every printed line of every round is graded, exactly, on the scenarios in the tree and on
scenarios you have not seen. Those run to four rounds over records of up to thirty nodes,
and they do all of it: removals set against changes, folders emptied and refilled, moves that
cross, one name wanted by more than two nodes at once, and rounds in which nothing happened.
Nothing outside the five files is read.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
