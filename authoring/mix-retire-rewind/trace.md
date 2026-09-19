# Instruction trace: mix-retire-rewind

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Every graded
assertion, enumerated plan, model rule, collected file and limit has a row, and every row cites
the words in `instruction.md` that tell the agent about it. Checked with
`python tools/tracecheck.py mix-retire-rewind`.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:117` test_frozen_truth_matches_the_model | the sealed model still reproduces the frozen traces, so a drifted model cannot redefine correct; it grades nothing the agent wrote | this is the sealed side checking itself, and what it checks is the union of the rules cited below, chief among them "One sample fills each slot" |
| `tests/test_outputs.py:127` test_hand_case | every enumerated plan prints exactly the frozen trace, line for line | "A plan is a text file of ops" and "`/app/run_feed.py` takes a plan and prints a line for each thing that happens" |
| `tests/test_outputs.py:136` test_every_nonce_plan_matches | plans generated after the container is gone print exactly what the model says | "The graded set is three plans of each of those two shapes and four hundred and forty-two small ones" |
| `tests/test_outputs.py:155` test_every_family_is_represented | the generated population covers every family, so a thin exam cannot pass as a full one | "The graded set is three plans of each of those two shapes and four hundred and forty-two small ones" |
| artifact `/app/feed/mix.py` | collected from the agent and laid over the pristine tree | "You may change six files" naming "`/app/feed/mix.py`" |
| artifact `/app/feed/deck.py` | collected from the agent | "You may change six files" naming "`/app/feed/deck.py`" |
| artifact `/app/feed/draw.py` | collected from the agent | "You may change six files" naming "`/app/feed/draw.py`" |
| artifact `/app/feed/spot.py` | collected from the agent | "You may change six files" naming "`/app/feed/spot.py`" |
| artifact `/app/feed/deal.py` | collected from the agent | "You may change six files" naming "`/app/feed/deal.py`" |
| artifact `/app/feed/keep.py` | collected from the agent | "You may change six files" naming "`/app/feed/keep.py`" |
| nothing else is collected | a change anywhere else in the tree, and any file added beside the six, is not carried into grading | "a file you add beside them is not collected either" and "are taken from our copy of the tree, not from yours" |
| `tests/Dockerfile` has no third-party install beyond pytest | the six files are imported with the standard library only | "Those six files are imported on Python 3.12 with the standard library" |
| `tests/test.sh:27` a 60 s clock on the process that runs the submitted files | a feeder right in every rule and too slow scores 0 | "All of it has to get through inside 60 seconds on one CPU with 2048 MB" |
| `tests/test.sh:38` reward 1 needs both stages clean | a crash, a hang or an unreadable record is a failure | "All of it has to get through inside 60 seconds on one CPU with 2048 MB" |
| `tests/seal/model.py:26-39` hand | the hand-over order of one epoch of one source is the frozen one | "in the order `/app/feed/shuf.py` gives for that source and the epoch it is in" |
| `tests/seal/model.py:41-44` tally | the count of a source over a stretch is periodic in the length of the pattern | "Over a stretch of the stream the pattern repeats" |
| `tests/seal/model.py:67-72` fits | a sample is delivered when its length is at most the cap, so the count inside the cap is what an epoch delivers | "delivered into the slot when its token length is at most the cap" |
| `tests/seal/model.py:83-93` nth | the r-th sample inside the cap of an epoch, in hand-over order, is the one that delivery hands over | "One longer than the cap is passed over: it fills no slot, the cursor moves past it, and the same source is asked again" |
| `tests/seal/model.py:95-98` gives | which sample fills a slot, from the delivered count of its source | "One sample fills each slot" |
| `tests/seal/model.py:100-104` stands (epoch) | the epoch a delivered count falls in, and the cursor just past the sample that ended it | "A cursor that runs off the end of an epoch goes to the first sample of the next one, under a different order" |
| `tests/seal/model.py:105-108` stands (tail) | a cursor left in front of the samples above the cap that trail an epoch | "Nothing is passed over in advance" and "where samples above the cap sit at the end of an epoch, a source stands in front of them until it is asked again" |
| `tests/seal/model.py:110-112` spent | a source is retired once it has delivered what its allowance covers, and never when the allowance is zero | "Zero is an allowance that never runs out" |
| `tests/seal/model.py:122-137` grow (the breakpoint) | the slot of the delivery that spends an allowance, solved inside the pattern that was live before it | "retires the moment it delivers the last sample that allowance covers, which is the last one inside the cap of the final epoch allowed to it" |
| `tests/seal/model.py:138-149` grow (the next stretch) | the retired source leaves the pattern, the rest keep their order, and the next stretch starts at the following slot | "The entries of the retired source leave the pattern, the entries that remain keep the order they were written in, and the slot after the one it last delivered into opens a stretch whose offsets are counted from there" |
| `tests/seal/model.py:151-158` stretch, owner | which source owns a slot, by its offset from the start of the stretch it lies in | "the source of a slot is the entry at the offset of that slot from the first slot of the stretch it lies in" |
| `tests/seal/model.py:160-165` delivered | every delivered count at a slot, before that slot is filled | "how many samples have been delivered since the plan began" |
| `tests/seal/model.py:171-182` where | the state of every source at a slot, with a retired one marked | "A retired source is written `<name>:gone`" |
| `tests/seal/model.py:184-191` stand_text | the three numbers of a source in a record, and their order | "the epoch being handed over now, how far into the order of that epoch the cursor has reached, and how many samples have been delivered since the plan began" |
| `tests/seal/model.py:204-217` ex (corpus ops) | the corpus, the cap and the mix as the plan declares them | "`seed`, `cap` and `src <name> <allowance> <token lengths>` set up the corpus" |
| `tests/seal/model.py:218-220` ex (open) | a fresh run starts at slot zero with the geometry it names | "step 0 is the slots beginning where the base of that run points" and "a fresh run has base zero" |
| `tests/seal/model.py:221-226` ex (feed, take) | the feeder runs ahead of the trainer, and taking produces what it must | "`feed <run> <k>` has the feeder produce k more steps and run that far ahead of the trainer" |
| `tests/seal/model.py:227-238` ex (show) | which slots a micro-batch holds, and how a sample is written | "the slot at offset o goes to rank `o % world`" and "each sample written as the name of its source, a dot, and the position it holds in the list of token lengths given for that source, counted from zero" |
| `tests/seal/model.py:239-247` ex (save) | the record fields, and that the state is taken at the position the feeder reached | "that position is slot `base + produced * world * micro * accum` under the geometry the saved run was using" |
| `tests/seal/model.py:248-253` ex (load) | the slot a load begins at, and the state it prints there | "The base of the run it starts is slot `base + completed * world * micro * accum`" |
| `tests/seal/model.py:254-255` ex (unknown op) | a plan op the model does not know is an error, never a silent skip | "A plan is a text file of ops, and `/app/plans` holds four of them" |
| case cap-all-but-one | a source whose samples are nearly all above the cap still fills every slot it owns | "One longer than the cap is passed over: it fills no slot, the cursor moves past it, and the same source is asked again" |
| case cap-exactly-at-cap | a sample whose length equals the cap is delivered, and one above it is not | "delivered into the slot when its token length is at most the cap" |
| case cap-none-over | the ordinary side: with nothing above the cap the cursor moves one sample per delivery | "delivered into the slot when its token length is at most the cap" |
| case cap-pass-by | one sample above the cap, passed over, and the same source asked again | "the same source is asked again, as many times as that takes" |
| case cap-pass-by-two | two above the cap in a row | "the same source is asked again, as many times as that takes" |
| case cap-same-source-again | the slot is filled by the source the pattern named, never by the next one | "One sample fills each slot" |
| case deal-both | both axes of the deal at once, every rank and every micro-batch | "the slot at offset o goes to rank `o % world`" and "The slots a rank is given fill its `accum` micro-batches of `micro` samples each in the order they arrive" |
| case deal-ranks | the rank a slot offset belongs to | "the slot at offset o goes to rank `o % world`" |
| case deal-seats | the micro-batch a rank slot belongs to | "so the first `micro` of them make up micro-batch 0" |
| case deal-steps-follow | consecutive steps take consecutive slots | "step 1 the slots after those" |
| case deal-wide-geometry | the deal at the geometry the scale plans use | "the slot at offset o goes to rank `o % world`" |
| case edge-rewind-on-retire | a rewind that lands on the slot a source retired at | "A load picks a run up where the trainer left off, not where the feeder had reached" |
| case edge-rewind-over-retire | a feeder position past a retirement the trainer has not reached | "The base of the run it starts is slot `base + completed * world * micro * accum`" |
| case edge-save-past-retire | the record state taken at the position the feeder reached, beyond a retirement | "that position is slot `base + produced * world * micro * accum` under the geometry the saved run was using" |
| case epoch-cursor-rolls | a cursor at the end of an epoch reads as the start of the next | "A cursor that runs off the end of an epoch goes to the first sample of the next one, under a different order" |
| case epoch-fresh-order | the second epoch of a source hands its samples over in another order | "A cursor that runs off the end of an epoch goes to the first sample of the next one, under a different order" |
| case epoch-own-counter | each source counts its own epochs, and a short source wraps while a long one has not | "in the order `/app/feed/shuf.py` gives for that source and the epoch it is in" |
| case epoch-tail-over-cap | the samples above the cap at the end of an epoch are not passed over until the source is asked | "Nothing is passed over in advance" |
| case epoch-wrap | a source crossing its own epoch boundary mid-plan | "A cursor that runs off the end of an epoch goes to the first sample of the next one, under a different order" |
| case hold-counts-deliveries | the allowance is spent in deliveries and not in cursor moves | "retires the moment it delivers the last sample that allowance covers, which is the last one inside the cap of the final epoch allowed to it" |
| case hold-gone-in-record | a retired source in a record | "A retired source is written `<name>:gone`" |
| case hold-last-delivery | retirement on the last sample inside the cap of the final allowed epoch, with samples above it still ahead of the cursor | "retires the moment it delivers the last sample that allowance covers, which is the last one inside the cap of the final epoch allowed to it" |
| case hold-one-epoch | an allowance of one epoch | "An allowance is a number of epochs" |
| case hold-two-epochs | an allowance of two epochs | "An allowance is a number of epochs" |
| case hold-zero-runs-on | the ordinary side: an allowance of zero keeps delivering past many epochs | "Zero is an allowance that never runs out" |
| case keep-chain-base | a load of a run that was itself loaded | "a checkpoint taken from a resumed run carries the base it was resumed at, and a load of that checkpoint begins there" |
| case keep-chain-three-deep | three loads composed | "a checkpoint taken from a resumed run carries the base it was resumed at, and a load of that checkpoint begins there" |
| case keep-nothing-to-rewind | the ordinary side: with the feeder level with the trainer a load begins where the feeder stood | "A load picks a run up where the trainer left off, not where the feeder had reached" |
| case keep-record-geometry | the rewind uses the geometry of the saved run, not the geometry the load asks for | "reading the base, the completed count and the geometry from that record" |
| case keep-rewind-to-done | a feeder run five steps ahead, rewound to the completed step | "A load picks a run up where the trainer left off, not where the feeder had reached" |
| case mix-entries-leave | the pattern after a retirement | "The entries of the retired source leave the pattern" |
| case mix-named-twice | a source named twice in the mix loses both entries | "The entries of the retired source leave the pattern" |
| case mix-offset-from-stretch | offsets in the new stretch counted from its first slot | "opens a stretch whose offsets are counted from there" |
| case mix-retire-inside-step | a retirement inside a printed step changes who owns the slots after it | "opens a stretch whose offsets are counted from there" |
| case mix-survivors-keep-order | the surviving entries keep the order they were written in | "the entries that remain keep the order they were written in" |
| case mix-two-retire | the first retirement moves where the second one lands | "Every plan gives at least one source in the mix an allowance of zero" |
| case state-before-the-slot | the state in a record is the one before the slot it names is filled | "All three are as the feeder stands before the slot at its own position is filled" |

## Readings

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| cap-strict | "delivered into the slot when its token length is at most the cap" | cap-exactly-at-cap |
| cursor-is-count | "One longer than the cap is passed over: it fills no slot, the cursor moves past it, and the same source is asked again" | cap-all-but-one |
| cursor-stays-at-end | "A cursor that runs off the end of an epoch goes to the first sample of the next one, under a different order" | cap-exactly-at-cap |
| deal-contiguous | "the slot at offset o goes to rank `o % world`" | deal-both |
| deal-seats-round-robin | "The slots a rank is given fill its `accum` micro-batches of `micro` samples each in the order they arrive" | deal-both |
| draw-ignores-retire | "opens a stretch whose offsets are counted from there" | mix-retire-inside-step |
| epoch-by-length | "A cursor that runs off the end of an epoch goes to the first sample of the next one, under a different order" | cap-all-but-one |
| hold-by-epoch-counter | "retires the moment it delivers the last sample that allowance covers, which is the last one inside the cap of the final epoch allowed to it" | hold-counts-deliveries |
| hold-counts-samples | "An allowance is a number of epochs" | hold-counts-deliveries |
| hold-one-delivery-early | "retires the moment it delivers the last sample that allowance covers" | edge-rewind-on-retire |
| keep-from-made | "A load picks a run up where the trainer left off, not where the feeder had reached" | edge-rewind-on-retire |
| keep-new-geometry | "reading the base, the completed count and the geometry from that record" | edge-save-past-retire |
| keep-no-chain | "a checkpoint taken from a resumed run carries the base it was resumed at, and a load of that checkpoint begins there" | keep-chain-base |
| keep-state-at-done | "that position is slot `base + produced * world * micro * accum` under the geometry the saved run was using" | cap-all-but-one |
| no-retire-at-all | "A source holding one retires the moment it delivers the last sample that allowance covers" | edge-rewind-on-retire |
| order-once | "in the order `/app/feed/shuf.py` gives for that source and the epoch it is in" | cap-all-but-one |
| pattern-absolute | "opens a stretch whose offsets are counted from there" | edge-rewind-over-retire |
| pattern-sorted | "the entries that remain keep the order they were written in" | mix-offset-from-stretch |
| refill-next-source | "the same source is asked again, as many times as that takes" | cap-all-but-one |
| retire-keeps-slots | "The entries of the retired source leave the pattern" | edge-rewind-on-retire |
| skip-leaves-slot-empty | "One sample fills each slot" | cap-all-but-one |
| state-after-slot | "All three are as the feeder stands before the slot at its own position is filled" | cap-all-but-one |
| state-never-gone | "A retired source is written `<name>:gone`" | edge-rewind-on-retire |
| tail-passed-early | "Nothing is passed over in advance" | epoch-tail-over-cap, and cap-all-but-one is the first to fail it |

Enumerated from the four clusters applied to every rule, from the shipped feeder (whatever it
does is a reading someone will keep), and from the two readings only a walking feeder can hold.
`python tools/readingcheck.py mix-retire-rewind 90` reports all 24 separated by an enumerated
plan, none equivalent. Measured against the generated population, each moves between 29 and 354
of 411 plans (`authoring/mix-retire-rewind/cheat_report.py`).

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (the nop) | reward 0. The worker is killed by the 60 s clock on the wide plans, so no record is graded at all; on the small plans its trace differs on every line of tiny.txt and mixed.txt |
| a constant: one sample for every slot and a zero state for every source (`cheat-shortcut-constant.sh`) | reward 0, caught by cap-all-but-one and cap-exactly-at-cap, and 408 of 411 generated plans |
| positional: always the first sample of the source the pattern names (`cheat-shortcut-first.sh`) | reward 0, caught by cap-exactly-at-cap and cap-none-over, and 403 of 411 generated plans |
| the line the brief quotes, replayed for every request (`cheat-shortcut-example.sh`) | reward 0, caught by cap-all-but-one and cap-exactly-at-cap, and all 411 generated plans |
| the forgery carrying every frozen answer, keyed by the plan config (`cheat-forge-from-truth.sh`) | reward 0. All 37 enumerated plans pass from the table alone and all 411 generated plans fail, which is the measurement that the graded set is not the shipped set |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:27` a 60 s clock on the graded set | `authoring/mix-retire-rewind/slow/walk`, `authoring/mix-retire-rewind/slow/stream` and `authoring/mix-retire-rewind/slow/fold` are three correct feeders written apart from the reference, and `authoring/mix-retire-rewind/variants/bisect` and `authoring/mix-retire-rewind/variants/backscan` are two more | the reference settles all 448 plans in 0.19 s, and both variants score 1 through the real verifier. The walker does the first 2000 of 780000 steps of one wide plan in 0.96 s, which is 373 s for that plan alone; all three slow feeders are killed by the clock with no record to grade. Headroom for a correct derivation is about 300x |
| `task.toml` memory 2048 MB, cpus 1 | `tests/seal/model.py` answers every graded plan inside the same budget, and the same five directories above run under it | peak resident set of the reference feeder over the whole graded set is 19 MB; a feeder holding every epoch order of one wide plan would need about 3.7 GB, which is why walking is bounded by the clock rather than by memory |
| exact comparison, no numeric tolerance | `tests/seal/model.py` against `tasks/mix-retire-rewind/solution` and `authoring/mix-retire-rewind/slow/walk` | 1644 generated plans and 37 enumerated plans, three implementations, zero disagreements (`authoring/mix-retire-rewind/agree.py`) |
