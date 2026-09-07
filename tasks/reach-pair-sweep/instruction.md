`/app` is the runtime we try collector changes on before they go near the real one. A program is a text file of ops and `/app/progs` holds a few. `new` allocates an object in the nursery and may give it a finalizer. `set` stores a reference into a field, `slot` stores one into a named slot of the innermost open frame, `glob` stores one in the global table, and `push` and `pop` open and close a frame. `hold` pushes an object on the handle stack and `drop` pops it. `pin` and `unpin` count pins on an object. `weak` registers a weak reference under a name and `pair` puts a key and a value in the pair table. `collect` runs a minor collection and `collectfull` a full one. `runfin` runs whichever finalizer has been queued longest.

`/app/run_prog.py` takes a program and prints what happened, a line per event.

We rewrote the collector last cycle and it has been wrong since. Run `/app/run_prog.py` on `/app/progs/tiny.txt`. It prints `fin 3`, then `pro 1`, `pro 2` and `pro 3`, and that last line should not be there: object 3 is unreachable and is only still around because its finalizer has not run, which is not the same as having survived. The five files under `/app/col` are the ones you may change. Nothing else.

An object survives a collection when the walk reaches it. A full collection walks from every root. That means the frame slots, the global table and the handle stack. A minor collection walks the nursery only, so it never traces an old object and never releases one, and the roots it starts from are the nursery objects those same three name plus the nursery objects reachable from old space. The remembered set is how it finds the second kind, and `/app/mem/rset.py` is where it comes from.

The pair table is weaker than a field. The value of a pair is reached only while that pair's key is reached, and a value that arrives can be some other pair's key. It makes no difference how that key is being kept. During a minor collection an old key is reached for as long as the collection lasts, because nothing that collection did could show otherwise.

An object that the walk did not reach, and that was allocated with a finalizer that has not run, is kept anyway, along with everything it reaches, and its finalizer joins the queue. It stays kept until that finalizer has run. The first collection after that releases it, unless something live points at it again. Which finalizers join the queue is settled from what the walk reached, before any of this keeping is granted. A finalizer runs at most once for an object, whatever happens to it afterwards.

An object the walk reached gets a year older, and at two it moves to old space. Being kept so a finalizer can run is not surviving, so those do not age. A pinned object still gets a year older when the walk reaches it, but it stays where it is until the pin comes off. If its age is already two then, it moves to old space the next time it survives.

A weak reference is cleared when the walk did not reach its referent. Being kept so a finalizer can run is not being reached. A minor collection leaves a reference alone when its referent is in old space, having no grounds to say anything about it. Once cleared it stays cleared.

Each collection prints `clr <name>` for every weak reference it cleared, then `fin <id>` for every finalizer it queued, then `rel <id>` for every object it released, then `pro <id>` for every object it promoted, ascending within each of the four. `runfin` prints `ran <id>`. Nothing else is printed.

`/app/progs/wide.txt` is one of the big ones. It has about seven thousand objects and a pair table written back to front. The graded set has 338 programs: 26 fixed programs and 312 generated after you finish, including 12 with 10,000 to 16,000 linked pair keys and another 3,000 to 5,000 unrelated pairs. The whole set must finish inside 60 seconds, so time it on `/app/progs/wide.txt` before you call it done.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
