# Instruction trace: stale-cover-serve

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md).
Written by authoring/stale-cover-serve/make_trace.py from a hand-written mapping, so a
renamed case or a reworded sentence fails there rather than leaving a stale quote here.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:85` test_record_is_complete | that every graded program was run, on the text the grader set, so a run that skipped or shortened programs fails on the record | "Every graded program is compared line for line against the answer it should give" "The graded artifact is these seven files and nothing else: `/app/rng/seg.py`, `/app/rng/pick.py`, `/app/rng/hole.py`, `/app/rng/mend.py`, `/app/rng/knit.py`, `/app/rng/age.py` and `/app/rng/ask.py`" "a new file anywhere is never collected" |
| `tests/test_outputs.py:97` test_nothing_raised | that no graded program raised | "one wrong line anywhere fails the whole run" |
| `tests/test_outputs.py:105` test_enumerated_programs | the whole trace of each of the 37 named programs against the frozen answers | "Every graded program is compared line for line against the answer it should give" "one wrong line anywhere fails the whole run" |
| `tests/test_outputs.py:123` test_model_still_matches_the_frozen_answers | that the sealed model still reproduces the frozen answers before it judges anything | "Every graded program is compared line for line against the answer it should give" |
| `tests/test_outputs.py:130` test_generated_programs | the whole trace of each of the 364 generated programs against the sealed model | "Every graded program is compared line for line against the answer it should give" "one wrong line anywhere fails the whole run" "A cache that answers every program correctly and does not get through the set inside the limit scores the same as one that answers them wrongly" |
| `tests/cases.py` case cold-miss | a read with nothing cached fetches and answers at the present version | "the read goes to the store instead and is answered at N" "Each remaining run is one fetch, issued in increasing key order" |
| `tests/cases.py` case fresh-cover | a range wholly inside current content is answered without a fetch | "the read is answered from the cache at the largest such version and no fetch is issued" |
| `tests/cases.py` case serve-back-one | one version back is a whole cover, so an allowance of one avoids the fetch | "The version a read is answered at is at most N and at least N - s, and never below 0" "the read is answered from the cache at the largest such version and no fetch is issued" |
| `tests/cases.py` case zero-forces-fetch | the same read with no allowance goes to the store | "The version a read is answered at is at most N and at least N - s, and never below 0" "the read goes to the store instead and is answered at N" |
| `tests/cases.py` case no-torn-cover | two halves never correct at the same version are not an answer | "every part of the answer must be content the cache still accounts for at that same version" |
| `tests/cases.py` case newest-wins | covers at two versions, and the newer one is served | "the read is answered from the cache at the largest such version and no fetch is issued" |
| `tests/cases.py` case gap-at-now | the holes are the ones open at the present version, not at the best partial one | "Start from the maximal runs of keys within lo to hi that no content the cache accounts for at N covers" |
| `tests/cases.py` case learn-the-past | a fetch answers reads aimed before it happened | "The store also reports the newest version at which it wrote any key in that range" "the content just fetched was the store's content over that range at every version in between" |
| `tests/cases.py` case empty-not-old | a fetch that comes back empty is correct from the delete | "The store also reports the newest version at which it wrote any key in that range" "or version 0 when it has never written one of them" |
| `tests/cases.py` case close-before | a commit ends a run at the version before it | "the fetched content was the store's up to the version before that commit and no further" |
| `tests/cases.py` case same-value-write | storing the value a key already holds is still a write | "A staged write or delete writes its key whether or not it changes what is there" |
| `tests/cases.py` case absent-delete | deleting a key that is not there is still a write | "A staged write or delete writes its key whether or not it changes what is there" |
| `tests/cases.py` case keep-closed | content the present has left behind keeps answering its own versions | "the fetched content was the store's up to the version before that commit and no further" "the read is answered from the cache at the largest such version and no fetch is issued" |
| `tests/cases.py` case horizon-drops | past the horizon the older version is gone | "Content whose last correct version is below N - H is discarded and can answer nothing further" |
| `tests/cases.py` case horizon-edge | a run ending exactly on the horizon is kept | "Content whose last correct version is below N - H is discarded and can answer nothing further" |
| `tests/cases.py` case horizon-open | a run still open is never discarded | "Content whose run is still open is never discarded, however long ago it was fetched" |
| `tests/cases.py` case horizon-zero | a horizon of zero drops a run on the commit that closed it | "Content whose last correct version is below N - H is discarded and can answer nothing further" |
| `tests/cases.py` case dupe-keys | two pieces of one cover share keys and the answer lists each once | "Every key appears at most once on an answer line" |
| `tests/cases.py` case row-order | the cover was built right half first and the answer is still in key order | "the live rows of lo to hi as of that version in increasing key order, each written `k=v`, all separated by single spaces" |
| `tests/cases.py` case floor-edge | the only cover sits exactly at the oldest allowed version | "The version a read is answered at is at most N and at least N - s, and never below 0" |
| `tests/cases.py` case two-holes | two holes, one fetch each, in increasing key order | "Each remaining run is one fetch, issued in increasing key order" "Each fetch prints `f lo hi` with the first and last key of the run fetched" |
| `tests/cases.py` case single-hole | a hole of one key is one fetch and an empty range prints a dash | "Each remaining run is one fetch, issued in increasing key order" "A read whose range holds no rows at that version prints `a` and the version followed by a single `-`" |
| `tests/cases.py` case empty-commit | a commit that stages nothing still makes a version | "every `c` raises the version by one, whether or not anything was staged" |
| `tests/cases.py` case dup-staged | two writes of one key in a batch leave the later value | "two staged operations on one key leave the later one and count as a single write of that key" |
| `tests/cases.py` case read-at-zero | a read before any commit is answered at version zero | "The store starts empty at version 0" |
| `tests/cases.py` case wide-allowance | an allowance past the whole history stops at version zero | "The version a read is answered at is at most N and at least N - s, and never below 0" |
| `tests/cases.py` case nested-cover | content inside the range leaves a hole on each side | "Start from the maximal runs of keys within lo to hi that no content the cache accounts for at N covers" |
| `tests/cases.py` case cascade-close | one commit ends two runs and the pair still covers the older version together | "the fetched content was the store's up to the version before that commit and no further" "A commit that writes nothing inside a range leaves its run open" |
| `tests/cases.py` case delete-visible | a key deleted since is absent now and present at the allowed version | "the live rows of lo to hi as of that version in increasing key order, each written `k=v`, all separated by single spaces" |
| `tests/cases.py` case zero-hit | no allowance at all still takes a current cover | "the read is answered from the cache at the largest such version and no fetch is issued" |
| `tests/cases.py` case no-cover-any | part of the range was never cached, so no version has a whole cover | "the read goes to the store instead and is answered at N" |
| `tests/cases.py` case combine-two | two holes one cached key apart are one round trip when the slack allows | "a run that begins no more than G keys after the previous one ends is taken together with it as a single run spanning both and the ground between them" |
| `tests/cases.py` case combine-edge | one key further apart and the same slack leaves them as two | "a run that begins no more than G keys after the previous one ends is taken together with it as a single run spanning both and the ground between them" |
| `tests/cases.py` case cap-whole | past the cap it is the whole requested range, not the span of the runs | "If more than F runs are left after that, all of them are dropped and the whole of lo to hi is fetched as one run instead" |
| `tests/cases.py` case cap-edge | exactly as many runs as the cap allows is not past it | "If more than F runs are left after that, all of them are dropped and the whole of lo to hi is fetched as one run instead" "F is never below 1" |
| `tests/cases.py` case combine-then-cap | the cap counts what combining left, not the holes before it | "a run that begins no more than G keys after the previous one ends is taken together with it as a single run spanning both and the ground between them" "If more than F runs are left after that, all of them are dropped and the whole of lo to hi is fetched as one run instead" |
| `tests/cases.py` case install-run-whole | a combined run is kept as the run it was fetched in | "what comes back is kept as the run it was fetched in" "it is not folded into anything the cache already holds even where it covers the same keys" "The store also reports the newest version at which it wrote any key in that range" |
| artifact `/app/rng/seg.py` | only the declared files are collected | "The graded artifact is these seven files and nothing else: `/app/rng/seg.py`, `/app/rng/pick.py`, `/app/rng/hole.py`, `/app/rng/mend.py`, `/app/rng/knit.py`, `/app/rng/age.py` and `/app/rng/ask.py`" "a new file anywhere is never collected" "so those three names and their arguments have to stay as they are" |
| artifact `/app/rng/pick.py` | only the declared files are collected | "The graded artifact is these seven files and nothing else: `/app/rng/seg.py`, `/app/rng/pick.py`, `/app/rng/hole.py`, `/app/rng/mend.py`, `/app/rng/knit.py`, `/app/rng/age.py` and `/app/rng/ask.py`" "a new file anywhere is never collected" "so those three names and their arguments have to stay as they are" |
| artifact `/app/rng/hole.py` | only the declared files are collected | "The graded artifact is these seven files and nothing else: `/app/rng/seg.py`, `/app/rng/pick.py`, `/app/rng/hole.py`, `/app/rng/mend.py`, `/app/rng/knit.py`, `/app/rng/age.py` and `/app/rng/ask.py`" "a new file anywhere is never collected" "so those three names and their arguments have to stay as they are" |
| artifact `/app/rng/mend.py` | only the declared files are collected | "The graded artifact is these seven files and nothing else: `/app/rng/seg.py`, `/app/rng/pick.py`, `/app/rng/hole.py`, `/app/rng/mend.py`, `/app/rng/knit.py`, `/app/rng/age.py` and `/app/rng/ask.py`" "a new file anywhere is never collected" "so those three names and their arguments have to stay as they are" |
| artifact `/app/rng/knit.py` | only the declared files are collected | "The graded artifact is these seven files and nothing else: `/app/rng/seg.py`, `/app/rng/pick.py`, `/app/rng/hole.py`, `/app/rng/mend.py`, `/app/rng/knit.py`, `/app/rng/age.py` and `/app/rng/ask.py`" "a new file anywhere is never collected" "so those three names and their arguments have to stay as they are" |
| artifact `/app/rng/age.py` | only the declared files are collected | "The graded artifact is these seven files and nothing else: `/app/rng/seg.py`, `/app/rng/pick.py`, `/app/rng/hole.py`, `/app/rng/mend.py`, `/app/rng/knit.py`, `/app/rng/age.py` and `/app/rng/ask.py`" "a new file anywhere is never collected" "so those three names and their arguments have to stay as they are" |
| artifact `/app/rng/ask.py` | only the declared files are collected | "The graded artifact is these seven files and nothing else: `/app/rng/seg.py`, `/app/rng/pick.py`, `/app/rng/hole.py`, `/app/rng/mend.py`, `/app/rng/knit.py`, `/app/rng/age.py` and `/app/rng/ask.py`" "a new file anywhere is never collected" "so those three names and their arguments have to stay as they are" |
| `tests/test.sh:34` a 60 s clock | the wall clock on the stage that runs submitted code | "gives that stage 60 seconds of wall clock for the whole set" "A cache that answers every program correctly and does not get through the set inside the limit scores the same as one that answers them wrongly" |
| `tests/seal/model.py:37-46` | Hist.commit applies the staged batch as one version | "every `c` raises the version by one, whether or not anything was staged" "two staged operations on one key leave the later one and count as a single write of that key" "A staged write or delete writes its key whether or not it changes what is there" |
| `tests/seal/model.py:48-53` | Hist.value reads one key back at a past version | "the live rows of lo to hi as of that version in increasing key order, each written `k=v`, all separated by single spaces" |
| `tests/seal/model.py:55-61` | Hist.rows builds the answer rows at the served version | "the live rows of lo to hi as of that version in increasing key order, each written `k=v`, all separated by single spaces" "Every key appears at most once on an answer line" |
| `tests/seal/model.py:63-68` | Hist.mark is the newest write across a fetched run | "The store also reports the newest version at which it wrote any key in that range" "or version 0 when it has never written one of them" |
| `tests/seal/model.py:71-79` | Part is one cached run with the versions it is correct for | "the content just fetched was the store's content over that range at every version in between" |
| `tests/seal/model.py:93-98` | Cache.add keeps a fetched run as it was fetched | "what comes back is kept as the run it was fetched in" "it is not folded into anything the cache already holds even where it covers the same keys" |
| `tests/seal/model.py:109-115` | Cache.close ends a run at the version before the commit | "the fetched content was the store's up to the version before that commit and no further" "A commit that writes nothing inside a range leaves its run open" |
| `tests/seal/model.py:117-119` | Cache.drop applies the horizon to closed runs only | "Content whose last correct version is below N - H is discarded and can answer nothing further" "Content whose run is still open is never discarded, however long ago it was fetched" |
| `tests/seal/model.py:122-131` | _union merges one key's runs before they are counted | "every part of the answer must be content the cache still accounts for at that same version" |
| `tests/seal/model.py:136-139` | served clamps the band the answer may come from | "The version a read is answered at is at most N and at least N - s, and never below 0" |
| `tests/seal/model.py:141-158` | served requires every key of the range to be covered at the same version | "every part of the answer must be content the cache still accounts for at that same version" |
| `tests/seal/model.py:159-175` | served takes the newest version at which that holds | "the read is answered from the cache at the largest such version and no fetch is issued" |
| `tests/seal/model.py:184-208` | gaps is the maximal runs uncovered at the present version | "Start from the maximal runs of keys within lo to hi that no content the cache accounts for at N covers" |
| `tests/seal/model.py:211-216` | gaps combines runs within the slack | "a run that begins no more than G keys after the previous one ends is taken together with it as a single run spanning both and the ground between them" |
| `tests/seal/model.py:217-219` | gaps replaces them with the whole range past the cap | "If more than F runs are left after that, all of them are dropped and the whole of lo to hi is fetched as one run instead" |
| `tests/seal/model.py:222-225` | render is the answer line and the empty answer | "the live rows of lo to hi as of that version in increasing key order, each written `k=v`, all separated by single spaces" "A read whose range holds no rows at that version prints `a` and the version followed by a single `-`" |
| `tests/seal/model.py:269-277` | trace prints the version a commit created and settles the cache | "A commit prints `v N` with the version it created" "the fetched content was the store's up to the version before that commit and no further" "Content whose last correct version is below N - H is discarded and can answer nothing further" |
| `tests/seal/model.py:278-286` | trace serves a read or fetches for it | "the read is answered from the cache at the largest such version and no fetch is issued" "the read goes to the store instead and is answered at N" "Each fetch prints `f lo hi` with the first and last key of the run fetched" |

## Readings

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| born-now - a fetch is correct only from the version it happened at | "The store also reports the newest version at which it wrote any key in that range" | `learn-the-past` |
| born-zero-empty - a fetch that comes back empty is correct from the beginning | "or version 0 when it has never written one of them" | `empty-not-old` |
| cap-at-cap - the cap fires at the cap rather than past it | "If more than F runs are left after that, all of them are dropped and the whole of lo to hi is fetched as one run instead" | `cap-edge` |
| cap-before-combine - the cap counts the holes before combining | "If more than F runs are left after that, all of them are dropped and the whole of lo to hi is fetched as one run instead" "a run that begins no more than G keys after the previous one ends is taken together with it as a single run spanning both and the ground between them" | `combine-then-cap` |
| cap-span - past the cap it is the span of the runs rather than the requested range | "If more than F runs are left after that, all of them are dropped and the whole of lo to hi is fetched as one run instead" | `cap-whole` |
| close-at-commit - a commit ends a run at its own version | "the fetched content was the store's up to the version before that commit and no further" | `serve-back-one` |
| const-empty - every read answers at version zero with no rows | "the live rows of lo to hi as of that version in increasing key order, each written `k=v`, all separated by single spaces" "The version a read is answered at is at most N and at least N - s, and never below 0" | `cold-miss` |
| const-now - every read answers at the present version with no rows | "the live rows of lo to hi as of that version in increasing key order, each written `k=v`, all separated by single spaces" | `cold-miss` |
| drop-on-close - a run a commit overtook is discarded rather than closed | "the fetched content was the store's up to the version before that commit and no further" "the read is answered from the cache at the largest such version and no fetch is issued" | `serve-back-one` |
| fetch-when-stale - anything but the present version is refetched | "the read is answered from the cache at the largest such version and no fetch is issued" | `serve-back-one` |
| floor-high - the band stops one version short | "The version a read is answered at is at most N and at least N - s, and never below 0" | `serve-back-one` |
| floor-low - the band reaches one version further back | "The version a read is answered at is at most N and at least N - s, and never below 0" | `zero-forces-fetch` |
| holes-count-closed - closed runs count as covering when the holes are worked out | "Start from the maximal runs of keys within lo to hi that no content the cache accounts for at N covers" | `zero-forces-fetch` |
| holes-desc - the fetches go in decreasing key order | "Each remaining run is one fetch, issued in increasing key order" | `two-holes` |
| holes-per-key - one run per uncovered key rather than maximal runs | "Start from the maximal runs of keys within lo to hi that no content the cache accounts for at N covers" | `two-holes` |
| holes-unsorted - the holes are walked in the order the runs were installed | "Start from the maximal runs of keys within lo to hi that no content the cache accounts for at N covers" "Each remaining run is one fetch, issued in increasing key order" | `row-order` |
| horizon-drops-open - the horizon also discards runs that are still open | "Content whose run is still open is never discarded, however long ago it was fetched" | `horizon-open` |
| horizon-keeps-count - the horizon is a count of closed runs rather than a version | "Content whose last correct version is below N - H is discarded and can answer nothing further" | `horizon-drops` |
| horizon-strict - a run ending exactly on the horizon is discarded | "Content whose last correct version is below N - H is discarded and can answer nothing further" | `horizon-edge` |
| install-per-hole - a combined run is carved back into the holes it was made of | "what comes back is kept as the run it was fetched in" "it is not folded into anything the cache already holds even where it covers the same keys" | `install-run-whole` |
| now-only - the allowance is ignored and every read is answered at the present version | "The version a read is answered at is at most N and at least N - s, and never below 0" | `serve-back-one` |
| oldest-version - the oldest allowed covered version is served | "the read is answered from the cache at the largest such version and no fetch is issued" | `newest-wins` |
| per-entry - each piece of the cover need only be recent enough on its own | "every part of the answer must be content the cache still accounts for at that same version" | `serve-back-one` |
| pos-always-fetch - every read fetches the whole range | "the read is answered from the cache at the largest such version and no fetch is issued" | `fresh-cover` |
| rows-at-now - the rows are taken from whatever is current rather than at the served version | "the live rows of lo to hi as of that version in increasing key order, each written `k=v`, all separated by single spaces" "every part of the answer must be content the cache still accounts for at that same version" | `serve-back-one` |
| rows-concat - the pieces of the cover are concatenated | "Every key appears at most once on an answer line" "the live rows of lo to hi as of that version in increasing key order, each written `k=v`, all separated by single spaces" | `no-torn-cover` |
| rows-unsorted - the rows come out in the order the pieces were read | "the live rows of lo to hi as of that version in increasing key order, each written `k=v`, all separated by single spaces" | `no-torn-cover` |
| slack-gap - the slack is measured from the first key of the next run | "a run that begins no more than G keys after the previous one ends is taken together with it as a single run spanning both and the ground between them" | `combine-two` |
| slack-strict - the slack is exclusive | "a run that begins no more than G keys after the previous one ends is taken together with it as a single run spanning both and the ground between them" | `combine-two` |
| warm-fetch - the holes are fetched even when the cache could serve the read | "the read is answered from the cache at the largest such version and no fetch is issued" | `serve-back-one` |

`holes-per-key` is the one reading nothing separates, and that is a fact about the contract rather than a gap: combining puts adjacent per-key runs back together whatever the slack is, so the maximality of the holes is unobservable. It is a correct variant that must score 1, not a cheat.

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (nop) | 0. Two of the five test functions fail; the shipped service ignores the version an answer is at, treats the allowance as an age on a cache entry, and concatenates the pieces of a cover. |
| constant: one fixed answer for every read (`cheat-const-empty`, `cheat-const-now`) | 0 each. `const-empty` matches no enumerated program and no generated one; `const-now` matches none either, since every program in the set has at least one read over a range holding rows. |
| positional: always fetch the whole range and answer at the present version (`cheat-pos-always-fetch`) | 0. It is right on a cold miss and wrong on every read a cover could have served; it fails `fresh-cover`, the first enumerated program with two reads. |
| the frozen answers replayed (`cheat-forge-hand`) | 0. It carries the answers for all 37 enumerated programs, narrows by the op sequence as the run proceeds and reproduces every one of them, then falls back to the shipped engine and fails the generated population. |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:34` a 60 s clock on the stage that runs submitted code | three correct engines written apart from the reference: `authoring/stale-cover-serve/variants/ok-perkey-cover` answers the serving question by unioning each key's runs and counting events, `authoring/stale-cover-serve/variants/ok-no-index` carries no key index at all, and `authoring/stale-cover-serve/variants/ok-holes-per-key` splits the holes per key | 4.95 s, 5.10 s and 8.40 s over the whole graded set of 401 programs against the 60 s limit, 7 to 12 times the headroom; the reference is 5.11 s. The two naive serving searches are 387.70 s and 82.64 s on the four scale programs alone. |

There is no numeric tolerance anywhere: traces are compared as strings.
