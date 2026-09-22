# Instruction trace: journal-gap-mend

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Cite the
instruction word for word in double quotes, four words or more. Write NOT STATED where it
says nothing, then write the sentence or stop grading it. Split each model row into one row
per rule it applies, citing its lines. Check with `python tools/tracecheck.py journal-gap-mend`.

The graded output of every journal is the exact list of lines the pristine driver returns,
compared all-or-nothing with the sealed model (`tests/seal/model.py`) and, for hand journals,
with `tests/seal/gt.json`. Since `assert got == want` hides every rule the model applies, the
model is walked below rule by rule.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:113` test_frozen_answers_match_the_model | the hand journals' frozen printouts are the model's (verifier integrity; a drift grades nothing) | "We grade the printout of every journal exactly, with no partial credit" |
| `tests/test_outputs.py:120` test_model_fingerprints_match_the_frozen_code | the model's fingerprints are the frozen `fp.py`'s, the definition the brief points to | "are what `holders` and `whole` in `/app/jl/fp.py` return for the table" |
| `tests/test_outputs.py:139` test_the_set_is_whole | the graded set is every hand journal plus every family at its count | "24 journals written by hand and 334 generated after you finish" |
| `tests/test_outputs.py:159` test_hand_journal | each hand journal's printout, exactly, and that the journal text was not altered | "We grade the printout of every journal exactly, with no partial credit" |
| `tests/test_outputs.py:168` test_every_generated_journal_matches | each generated journal's printout, exactly; a missing or altered record fails | "24 journals written by hand and 334 generated after you finish" |
| `tests/seal/cases.py:11` case small | the worked example itself: one restored entry, then a candidate line | "where it should print three lines: `gap 1`, then `acq 0 0 grant`, then `? acq 0 0 again | acq 0 1 wait`" |
| `tests/seal/cases.py:23` case beat-needs-lock | the heartbeat the totals count can only come from the session that holds a lock | "which a session sends only while it holds at least one lock, and it changes nothing" |
| `tests/seal/cases.py:37` case live-candidates | a candidate is an entry some complete account holds, not any request the table accepts | "followed by every entry some account has at the first place they differ" |
| `tests/seal/cases.py:49` case digest-anchored | the digest sits right after its grant, forcing the release before it | "Right after any entry that brings the grant count to a multiple of K, and at no other time, the service writes a digest" |
| `tests/seal/cases.py:62` case digest-on-grant | only an entry that raises the grant count writes a digest | "Right after any entry that brings the grant count to a multiple of K, and at no other time, the service writes a digest" |
| `tests/seal/cases.py:74` case later-evidence | a span with no markers settled by a digest after it | "An account of a journal fills every lost stretch with entries so that, replaying the whole journal from the start" |
| `tests/seal/cases.py:88` case pass-first-waiter | a pass goes to the first queued session | "the first session in the queue takes the lock at depth 1 (`pass`)" |
| `tests/seal/cases.py:107` case queue-order | three lost requests ordered only by the queues in the final audit | "`holders` covers who holds each lock and nothing else, and `whole` adds depths and queues" |
| `tests/seal/cases.py:117` case reentry-depth | a reentry deepens the lock, visible in the whole-table fingerprint | "a lock the session already holds goes one deeper (`again`)" |
| `tests/seal/cases.py:131` case end-of-span | the end of a span is a candidate | "and `-` if some account's stretch ends there" |
| `tests/seal/cases.py:148` case pass-is-grant | a pass counts as a grant and writes its digest after the release | "grants (every `grant` and every `pass`), requests (every `acq`), releases (every `rel`) and heartbeats" |
| `tests/seal/cases.py:165` case two-spans-one-beat | the second span inherits every table the first can leave | "An account of a journal fills every lost stretch with entries so that, replaying the whole journal from the start" |
| `tests/seal/cases.py:179` case empty-then-grant | only the final audit shows the first span held nothing | "A lost stretch may have held any number of entries, none included" |
| `tests/seal/cases.py:195` case waiter-silent | a waiting session sends nothing, which orders two lost requests | "A session in a queue is waiting, and it sends nothing at all until a `pass` hands it the lock" |
| `tests/seal/cases.py:207` case audit-before-loss | an audit listed in a span may have been taken before its first lost entry | "Nothing says where among its lost entries an audit listed inside it was taken" |
| `tests/seal/cases.py:224` case audits-inside | two audits in one span, each where its totals fit | "every audit taken between the entry before the loss and the entry after it, in the order they were written" |
| `tests/seal/cases.py:238` case digest-before-gap | a digest right after the surviving entry that triggered it, then the span | "with the count and the table as they stand after that entry" |
| `tests/seal/cases.py:250` case both-empty | spans every account leaves empty print their header alone | "When they agree on the whole stretch, that is all." |
| `tests/seal/cases.py:264` case choices-first | accounts part at the first entry of the span | "followed by every entry some account has at the first place they differ" |
| `tests/seal/cases.py:274` case dash-first | the end of a span as a candidate, sorted first | "sorted as plain ASCII text, so `-` comes first" |
| `tests/seal/cases.py:287` case restored-then-choice | an agreed entry, then a choice | "the entries that open that stretch in every account, for as long as all accounts agree" |
| `tests/seal/cases.py:298` case restored-then-dash | an agreed entry, then a choice that includes the end | "and `-` if some account's stretch ends there" |
| `tests/seal/cases.py:311` case kinds-in-order | candidates of three kinds in text order | "sorted as plain ASCII text, so `-` comes first" |
| `tests/seal/cases.py:321` case three-spans | span numbering from 1 across three spans | "print `gap <n>` with n counted from 1" |
| artifact `/app/jl/table.py` | only the declared files are collected | "The files you may change are `/app/jl/table.py`, `/app/jl/tally.py`, `/app/jl/span.py`, `/app/jl/seek.py` and `/app/jl/walk.py`" |
| artifact `/app/jl/tally.py` | only the declared files are collected | "The files you may change are `/app/jl/table.py`, `/app/jl/tally.py`, `/app/jl/span.py`, `/app/jl/seek.py` and `/app/jl/walk.py`" |
| artifact `/app/jl/span.py` | only the declared files are collected | "The files you may change are `/app/jl/table.py`, `/app/jl/tally.py`, `/app/jl/span.py`, `/app/jl/seek.py` and `/app/jl/walk.py`" |
| artifact `/app/jl/seek.py` | only the declared files are collected; `mend(journal)` is the entry point the frozen driver calls | "hands the journal that `/app/jl/read.py` parsed to `mend` in `seek.py` and prints the lines it returns" |
| artifact `/app/jl/walk.py` | only the declared files are collected; a sixth file is never seen | "The verifier lays those five files over its own copy of the rest of the tree, and a new file put beside them is never seen" |
| `tests/test.sh:32` a 120 s clock | the worker running the submission over all 358 journals is killed at 120 s and scores 0 | "All 358 have to finish inside 120 seconds on one CPU with 2 GB of memory. A run that does not finish scores 0" |
| `tests/worker.py:36-40` pristine overlay | the submission runs over the verifier's copy of the tree with only the five files laid on it | "Nothing else is collected" |
| `tests/Dockerfile:4` standard library only | the verifier image holds Python 3.12 and pytest, nothing the submission may import | "Use nothing outside the Python 3.12 standard library" |
| `tests/seal/model.py:25-40` _mark, _who, holders_mark, whole_mark | holder fingerprint over holders, whole fingerprint over holders, depths and queues with each queue from its first waiter, in the frozen format | "return for the table given as one `(holder, depth, queue)` row per lock in lock order, each queue running from its first waiter to its last and a free lock being `(None, 0, ())`" |
| `tests/seal/model.py:199-202` through, audit fields | an audit carries the four totals and the whole-table fingerprint at the moment it is taken | "with the four counts and the table as they stand at that moment" |
| `tests/seal/model.py:45-46` empty | every lock starts free, depth 0, empty queue | "The service starts with every lock free and four counts at zero" |
| `tests/seal/model.py:49-50,61-62` is_waiting, serve | a session in a queue sends nothing | "A session in a queue is waiting, and it sends nothing at all until a `pass` hands it the lock" |
| `tests/seal/model.py:64-65` serve beat | a heartbeat needs a held lock and changes nothing | "which a session sends only while it holds at least one lock, and it changes nothing" |
| `tests/seal/model.py:68-69` serve acq free | a free lock is taken at depth 1, outcome grant | "A free lock is taken at depth 1 (`grant`)" |
| `tests/seal/model.py:70-71` serve acq own | a held lock goes one deeper, outcome again | "a lock the session already holds goes one deeper (`again`)" |
| `tests/seal/model.py:72-73` serve acq other | the session joins the back of the queue, outcome wait | "a lock someone else holds puts the session at the back of its queue (`wait`)" |
| `tests/seal/model.py:75-76` serve rel holder | only the holder releases | "is only ever sent by the holder and takes one off the depth" |
| `tests/seal/model.py:77-78` serve rel keep | depth still above 0 keeps the lock | "If the depth is still above 0 the outcome is `keep`" |
| `tests/seal/model.py:79-80` serve rel pass | the first waiter takes the lock at depth 1 | "the first session in the queue takes the lock at depth 1 (`pass`)" |
| `tests/seal/model.py:81-82` serve rel free | nobody queued: the lock becomes free | "with nobody queued, the lock becomes free (`free`)" |
| `tests/seal/model.py:90-97` bump | grants count grant and pass; requests, releases, heartbeats count their entries | "grants (every `grant` and every `pass`), requests (every `acq`), releases (every `rel`) and heartbeats" |
| `tests/seal/model.py:100-116` offers | any lock, any session, any request the table accepts can be a lost entry | "An account of a journal fills every lost stretch with entries so that, replaying the whole journal from the start, every entry is one the service would accept, with the outcome shown" |
| `tests/seal/model.py:119-123` entry_text | restored entries and candidates are printed in journal form | "one per line and exactly as the journal writes them" |
| `tests/seal/model.py:128-156` parse | `cfg`, entries, `dig`, `aud`, and `gap` ... `back` holding the span's markers | "Where entries were lost, the file has a line `gap`" |
| `tests/seal/model.py:159-177` slack | a span cannot add more than later digests and audits allow once the surviving entries are counted; a consequence of every digest and audit matching, not a separate rule | "every digest and audit is exactly what would have been written where it stands, with no entry triggering a digest the file does not have" |
| `tests/seal/model.py:189-198` through, surviving entry | a surviving entry is legal with its outcome, and one that brings grants to a multiple of K obliges the very next line to be its digest | "Right after any entry that brings the grant count to a multiple of K, and at no other time, the service writes a digest" |
| `tests/seal/model.py:199-202` through, surviving digest and audit | a digest must be the one its entry obliged; an audit matches the counts and whole table where it stands | "every digest and audit is exactly what would have been written where it stands" |
| `tests/seal/model.py:211-213` moves, audit in a span | an audit listed in a span matches at any point between lost entries, in the listed order | "Nothing says where among its lost entries an audit listed inside it was taken" |
| `tests/seal/model.py:219-223` moves, digest in a span | a lost entry that brings grants to a multiple of K must be followed at once by the next listed digest; no digest, no such entry | "with no entry triggering a digest the file does not have" |
| `tests/seal/model.py:225` moves, leaving a span | a span is left only once every marker listed in it is used | "then every digest a lost entry triggered and every audit taken between the entry before the loss and the entry after it" |
| `tests/seal/model.py:227-243` done, inside | an account is judged against the whole journal, spans after included | "An account of a journal fills every lost stretch with entries so that, replaying the whole journal from the start" |
| `tests/seal/model.py:246` expect | every graded journal has an account | "The journal happened, so it has at least one account." |
| `tests/seal/model.py:256` expect | each span prints its header, counted from 1 | "print `gap <n>` with n counted from 1" |
| `tests/seal/model.py:272-292` expect, the walk | print the entries every account agrees on, from the start of the span | "the entries that open that stretch in every account, for as long as all accounts agree" |
| `tests/seal/model.py:283-285` expect, end | a span may end at the point of disagreement: the dash | "and `-` if some account's stretch ends there" |
| `tests/seal/model.py:289-295` expect, candidate line | no line when all agree; otherwise one line of every candidate, sorted | "sorted as plain ASCII text, so `-` comes first" |

## Readings

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| shortest-plan: the shipped search kept, table fixed - per span, from one table, the shortest fillings consistent up to the next span | "An account of a journal fills every lost stretch with entries so that, replaying the whole journal from the start" | `tests/seal/cases.py:74` later-evidence |
| span-local: each span judged with evidence up to the next span only | "An account of a journal fills every lost stretch with entries so that, replaying the whole journal from the start" | `tests/seal/cases.py:179` empty-then-grant |
| forward-only: no pruning from later evidence; candidates from what the span's own markers allow | "An account of a journal fills every lost stretch with entries so that, replaying the whole journal from the start" | `tests/seal/cases.py:74` later-evidence |
| merge-holders: histories merged by the holder fingerprint | "`holders` covers who holds each lock and nothing else, and `whole` adds depths and queues" | `tests/seal/cases.py:107` queue-order |
| single-start: each span starts from the one table the first filling of the span before it leaves | "An account of a journal fills every lost stretch with entries so that, replaying the whole journal from the start" | `tests/seal/cases.py:165` two-spans-one-beat |
| digest-floats: a digest inside a span may be matched anywhere, like an audit | "Right after any entry that brings the grant count to a multiple of K, and at no other time, the service writes a digest" | `tests/seal/cases.py:49` digest-anchored |
| audit-at-end: an audit inside a span checked against the table the span ends with | "Nothing says where among its lost entries an audit listed inside it was taken" | `tests/seal/cases.py:224` audits-inside |
| no-end: the end of a span never offered | "and `-` if some account's stretch ends there" | `tests/seal/cases.py:131` end-of-span |
| candidates-local: candidates by local legality, whether or not an account completes | "followed by every entry some account has at the first place they differ" | `tests/seal/cases.py:37` live-candidates |
| walk-no-closure: the walk forgets an audit may sit before the next entry | "Nothing says where among its lost entries an audit listed inside it was taken" | `tests/seal/cases.py:207` audit-before-loss |
| pass-uncounted: a pass not counted as a grant | "grants (every `grant` and every `pass`), requests (every `acq`), releases (every `rel`) and heartbeats" | `tests/seal/cases.py:148` pass-is-grant |
| digest-on-multiple: a digest after any entry that leaves grants on a multiple | "Right after any entry that brings the grant count to a multiple of K, and at no other time, the service writes a digest" | `tests/seal/cases.py:62` digest-on-grant |
| waiting-sends: a waiting session may still send | "A session in a queue is waiting, and it sends nothing at all until a `pass` hands it the lock" | `tests/seal/cases.py:195` waiter-silent |
| beat-anytime: a heartbeat without a held lock | "which a session sends only while it holds at least one lock, and it changes nothing" | `tests/seal/cases.py:23` beat-needs-lock |
| no-depth: a reentry does not deepen, a release never keeps | "a lock the session already holds goes one deeper (`again`)" | `tests/seal/cases.py:117` reentry-depth |
| last-come-pass: a pass goes to the last waiter | "the first session in the queue takes the lock at depth 1 (`pass`)" | `tests/seal/cases.py:88` pass-first-waiter |

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (nop) | 0: matches 6 of 24 hand journals and 0 of 334 generated (1.7%, seed shortcuts-1, 77 journals past a 5 s alarm); on the graded run the clock stops it (half one exits 124) |
| constant: every span printed as its header alone (the commonest line) | 0: matches 1 of 24 hand journals (`both-empty`) and 0 of 334 generated (0.3%); `cheat-const-headers.sh` scores 0 |
| positional: one account printed in full, always the first candidate | 0: matches 13 of 24 hand journals and 74 of 334 generated (24.3%) - exactly the journals whose every span one filling explains, the C1 ordinary side; `cheat-pos-first-account.sh` scores 0 |
| the worked example's output replayed | 0: matches 1 of 24 hand journals (`small`, the example itself) and 0 of 334 generated (0.3%); `cheat-const-example.sh` scores 0 |
| the shipped search kept, with the table and totals fixed (`shortest-plan`) | 0: matches 12 of 24 hand journals and 18 of 334 generated (8.4%, 14 past a 5 s alarm); `cheat-shortest-plan.sh` scores 0 |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:32` a 120 s clock | `tests/seal/model.py`, `authoring/journal-gap-mend/variants/topdown/seek.py`, `authoring/journal-gap-mend/variants/packed/seek.py` | the whole 358-journal set on four seeds (`timing_full.py resized-r1..r4`, one process each): sealed model 2.0 to 4.3 s, top-down variant 3.4 to 8.3 s, packed variant 2.8 to 6.2 s, reference 1.9 to 5.1 s - at least 14x inside the clock. Under the worker's own limits (`prlimit --as` 2 GB, `timeout 120`) the reference finished seed lim-1 in 2.2 s while stretches bounded by the next audit alone (`slow/loosecap`) were killed at 120 s; enumerating accounts and memo-less search (`slow/enumerate`, `slow/exist`) each run past 40 s on a single busy journal |
