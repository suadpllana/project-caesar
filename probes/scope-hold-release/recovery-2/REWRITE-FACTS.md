# Facts the contributor must put into their own words

The previously accepted instruction prose is restored in the task folder. Its incident, paths,
record schema, refusal timing and factory scenario can stay. The following corrections are needed
before another archive can be built. They must replace the conflicting passages in the
contributor's own natural wording.

1. Teardown uses reverse instance-allocation order. The core assigns an instance number before it
   recursively builds dependencies or a wrapped registration. This means the later allocated
   dependency or wrapped registration is torn first. Do not describe this as reverse completion
   order, and do not promise that a wrapper is torn before what it wraps.
2. Ordinary new instances belong to the scope used for that build. Singleton ancestry is special:
   the singleton and every new instance underneath it belong to root, even when a descendant has a
   mark. A mark outside such a chain changes only the marked instance's owner. Its unmarked
   dependencies do not inherit that marked owner. Reusing an existing instance does not change its
   owner or cause. Scoped reuse is keyed by the registration and build scope.
3. Admission is evaluated for the name explicitly requested by resolve, invoke or parting call.
   A requested singleton is refused when its graph reaches a scoped registration. A requested
   marked registration is refused when its mark is unavailable. Those two checks are not repeated
   for every dependency. Cycle detection does inspect the dependency/wrapping graph. All stream
   names are registered, and factory declarations are not dependency edges.
4. A successful explicit holder resolution creates or replaces its factory tokens using that
   resolution's build scope. This also happens when the holder is cached, transient, or assigned a
   different teardown owner. The latest token for a factory name wins. Closing the captured scope
   does not revoke the token; invoking it still uses that stored build scope, whose ancestor chain
   is empty once it is no longer live.
5. The grader compares the entire ordered dump. It does not ignore relative ordering between
   different scopes. Internal instance numbers are not printed, but their allocation order affects
   teardown. A refused invoke reports the scope where invocation was attempted; a refused parting
   call reports its landing scope. Each parting call runs immediately after its instance's torn
   record.

The new `crossing.txt` fixture can remain mentioned only as another runnable case. Its expected
output must not be included in the instruction or environment.
