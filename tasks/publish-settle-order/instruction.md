`/app` is the extension host we try loader changes on before they go near the shipped one. A program is a text file of ops and `/app/progs` holds a few. `unit` declares a unit, `dep` gives it a dependency, and `pre` gives it a unit that has to be up first. `pub` is a name the unit publishes and `fall` a name it publishes as a fallback. `boot` is a name its startup calls. `act` brings a unit up, `call` has a unit call a name, and `rel` gives back one hold.

`/app/run_host.py` takes a program and prints what happened, a line per event.

We rewrote the loader last cycle and it has been wrong since. Run `/app/run_host.py` on `/app/progs/tiny.txt`. The last line comes out `run u3 s1 u2`. It should name u1, which published `s1` before u2 did: publishing a name as a fallback does not queue it behind an ordinary publication. The files you may change are `/app/link/walk.py`, `/app/link/pick.py`, `/app/link/site.py`, `/app/link/want.py` and `/app/link/drop.py`. Nothing else.

Bringing up a unit that is already up adds a hold to it and does nothing else. Bringing up one that is not brings up what it names first, dependencies and `pre` units alike, in declaration order, skipping any that is already up or is itself part way up. The unit is published at the back of the publication order. Its startup calls run after that, in declaration order, so a startup call sees the order as far as it has been built and no further.

A name is answered by the first unit in publication order that publishes it and is still up. A fallback publication competes on that footing and no other.

A call from a unit that is not up is not an event. A use is one unit's call of one name. It settles the first time that call is answered, and after that it is never resolved again. While the publication it settled on is still up the call reaches it. Once that publication has gone the call is dead and stays dead, and a unit of the same name coming back up is not that publication and does not repair it. A call that is not answered settles nothing, so the same call can settle later against a unit that came up in between. A unit coming up has settled nothing, whatever it had settled the last time it was up.

`rel` gives back one hold from a unit that is up and holds at least one. Anything else it leaves alone. A unit stays up while it holds a hold of its own, and while any unit that is still up names it as a dependency. A `pre` decides when its unit comes up and keeps it up no longer than that. Once a hold has been given back, the last unit in publication order that is not staying goes down. Then the question is asked again, since the one that went down may have been all that kept the next one, and that repeats until a pass finds nothing to take down.

Every event is one line, printed when it happens and never sorted. `up <unit>` when a unit is published, `down <unit>` when it goes down. `run <caller> <name> <unit that answered>` for a call that reached one, `miss <caller> <name>` for a call that found nothing, and `dead <caller> <name>` for a call whose publication has gone. Nothing else is printed.

`/app/progs/wide.txt` is one of the big ones. Close to nineteen thousand units and seventy-two thousand calls. The graded set is four programs that size and about three hundred and sixty small ones, and all of it has to get through inside 60 seconds. Time `wide.txt` before you call it done.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
