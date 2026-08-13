We keep a set of grouped aggregates up to date against a change stream, and the thing is
costing us orders of magnitude more than it should. The engine is in /app. Rows arrive against a keyed
store as inserts, as deletes, as updates that carry a new value or a new group, each one
stamped with a timestamp, and a watermark trailing the highest timestamp we have seen
decides when a group's current values get published. Your job is to make the maintenance incremental without moving a single
published number.

/app/run_view.py takes a scenario file and prints what the engine did with it. Feed it
eight deltas against one group, five rows in and three of them retracted, and the view
comes back sum 16, cnt 2, min 7, max 9, top 16, which is right: c and e survive at 9 and
7. It got there with 120 folds and 40 scans. The same eight deltas want 55 folds and 11
scans. Every delta throws the whole group away and rebuilds it from the row store, for every
aggregate, whether or not anything that cell holds could have moved. On a real stream
that is most of a machine.

Some ground rules, because several of them are not what you would do elsewhere.

The published numbers are not negotiable. Whatever you do to the work, every value this
engine emits at a watermark advance and the view it ends on have to stay exactly what
they are now, and we grade the emitted values in their order as well as the final view,
so a submission that repairs lazily and settles up at the end has still failed every
number it published on the way there even when the last one it prints is right.

The accumulator in /app/store/agg.py does not hold everything its group holds. It keeps a
bounded set of candidates and drops the rest on the floor, silently, with no counter and
no flag, so two cells carrying identical candidate sets can be answerable for entirely
different rows. Nothing records the loss. Read what fold does at the cap. What an accumulator can recover from
changes with the aggregate, and for one aggregate it changes over the life of the cell.

Retraction is where this turns. A running total takes a negative edit as happily as
a positive one. It needs no history to do it. An order-sensitive aggregate can take one too,
right up until the candidate set stops being able to answer for the group, and after that
point folding a retraction in produces a number the group does not have. Both halves are
measured. Rebuild a cell that could have absorbed the edit and the values come out right
and the work comes out wrong; absorb an edit the cell could not answer for and the values
themselves go. The cheap test is that the multiplicity folded exceeds the candidates
kept. It is not the line. A group of duplicates trips it having lost nothing at all.

An update is two edits. The row leaves the group it was in and joins the group it now
belongs to, and where the update carries a new group those are two different cells, each
of them judged on its own state at that moment, so one side can absorb what the other has
to rebuild for. A delete for a key nobody inserted is not an edit. Neither is a second
delete for a key already retracted. Those must not touch a cell at all.

Deltas arrive behind the watermark. That changes nothing about how a cell is repaired.
Late is a property of when we heard about a row, never of what the row does to its group.

Leave the rest of the engine where it is. When the watermark advances, which cells get
published and in what order, how the row store lands a delta, what the driver counts as
late: none of that is what we are after. A run whose publications come out in a different
order from the engine you were handed is a different engine.

One file is yours. It is /app/view/route.py, and that path is the only thing we take out
of your container, which means anything else you touch is not read, and that covers new
modules of your own, helper scripts, edits to the files around it, whatever you leave
lying about in /app; the rest of the tree goes back to a clean copy of what you started
with before any of this is measured, and your one file has to keep working against that
copy, not against a tree you reshaped around it.

The arithmetic is integer the whole way and the engine is deterministic, so two runs of
one scenario agree exactly. Put whatever you like through /app/run_view.py, any sequence
of insertions and retractions and updates at whatever timestamps, and check it against a
rebuild you write yourself.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
