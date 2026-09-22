# Instruction trace: grant-widen-yield

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md).
Written by authoring/grant-widen-yield/make_trace.py, which refuses to write a
trace whose quotes are no longer in instruction.md. Checked with
`python tools/tracecheck.py grant-widen-yield`.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:118` test_frozen_truth_matches_the_model | nothing the submission controls: the frozen answers and the sealed model must still agree before either is used to judge, so a drifted model cannot redefine correct | "must return the trace followed by the closing report" |
| `tests/test_outputs.py:128` test_hand_case | every enumerated program's trace and report, line for line, against answers frozen before the grading file was written | "must return the trace followed by the closing report" |
| `tests/test_outputs.py:137` test_every_nonce_program_matches | every generated program's trace and report, line for line, against the sealed model | "Your service is graded on programs you have not seen" |
| `tests/test_outputs.py:153` test_the_nonce_population_is_large_enough | that the population actually generated is the size the task claims, so a shrunken generator cannot make the exam smaller | "Your service is graded on programs you have not seen" |
| `tests/test_outputs.py:157` test_every_family_is_represented | that every shaped family, including the two that carry the execution limit, is present | "around twenty thousand lines in which three transactions hold up to nine thousand keys each under a single block" |
| `tests/cases.py case cover-asked-stays` | an asked mode outlives the grants that were covering it | "the supremum of two things: the mode the program asked for there, if it ever asked, and the cover its own live grants below that resource require" |
| `tests/cases.py case cover-holds-up` | the cover stays while another grant still requires it | "a mode falls when the grants beneath it go and rises when they come back" |
| `tests/cases.py case cover-plain-goes` | a cover with nothing left to cover disappears | "when one is released or when a cover with nothing left to cover disappears" |
| `tests/cases.py case cover-thins` | the cover falls when the exclusive grant under it goes | "a mode falls when the grants beneath it go and rises when they come back" |
| `tests/cases.py case cover-unblocks` | a fallen cover makes the resource compatible for somebody else | "a mode falls when the grants beneath it go and rises when they come back" |
| `tests/cases.py case free-narrows` | a release lets the levels above fall to what is left | "removes every grant and every claim that transaction has at that resource or below it, and then lets the levels above fall to what is left" |
| `tests/cases.py case free-nothing` | a release of something neither held nor claimed prints nothing | "something it neither holds nor claims does nothing at all" |
| `tests/cases.py case free-subtree` | a release takes the subtree and the claims under it | "removes every grant and every claim that transaction has at that resource or below it, and then lets the levels above fall to what is left" |
| `tests/cases.py case give-age-order` | two younger holders give way oldest of them first | "If every incompatible holder is younger, each gives way, oldest of them first" |
| `tests/cases.py case give-asked-only` | a grant that was only a cover leaves no claim | "only to cover something beneath it leaves nothing" |
| `tests/cases.py case give-at-level` | only the subtree under the contested resource is given up | "A holder that gives way loses that resource and every grant it holds below it" |
| `tests/cases.py case give-cascade` | giving way takes every grant below the resource with it | "A holder that gives way loses that resource and every grant it holds below it" |
| `tests/cases.py case give-claim-asked` | the claim is left at the asked mode, not the printed one | "Only a resource the program asked for leaves a claim, at the asked mode, not at the effective mode that was printed" |
| `tests/cases.py case give-younger` | the younger holder gives way instead of the requester waiting | "If every incompatible holder is younger, each gives way, oldest of them first" |
| `tests/cases.py case mode-cover-read` | a shared grant needs only a shared intention above it | "A grant at IS or S requires IS above it; a grant at IX, SIX or X requires IX" |
| `tests/cases.py case mode-cover-six` | a shared-intent-exclusive grant needs an exclusive intention above it | "A grant at IS or S requires IS above it; a grant at IX, SIX or X requires IX" |
| `tests/cases.py case mode-sup-mixed` | the supremum of an intent-exclusive and a shared hold | "the supremum of IX and S is SIX" |
| `tests/cases.py case plain-again` | an asked mode only ever rises, and a take of a mode already held prints nothing | "the requested mode joins whatever the transaction had already asked for there" |
| `tests/cases.py case plain-intent` | two exclusive keys under one block share an IX cover | "A grant at IS or S requires IS above it; a grant at IX, SIX or X requires IX" |
| `tests/cases.py case plain-share` | compatible holders are left alone and nothing is claimed | "IS is compatible with every mode but X, IX with IS and IX, S with IS and S, SIX with IS alone, X with nothing" |
| `tests/cases.py case plain-stores` | stores are independent; a conflict in one does not reach the other | "A take is settled one level at a time from the store inward, and the service does not look ahead" |
| `tests/cases.py case say-report-order` | the closing report, transactions in age order then resource order | "The report comes after the last line, transactions in age order" |
| `tests/cases.py case shut-clears` | a finish removes everything the transaction holds or claims | "removes everything that transaction holds or claims" |
| `tests/cases.py case sweep-age-first` | two claims on one resource are tried oldest transaction first | "oldest transaction first, and within a transaction outermost resource first, then by resource name" |
| `tests/cases.py case sweep-narrower` | a retake rebuilds the cover from what actually came back, and clears the claim when it succeeds | "any claim it had on that resource is gone" |
| `tests/cases.py case sweep-next-line` | what a sweep disturbs is not tried again inside that sweep | "Whatever the sweep itself disturbs, including the claims its own give-ups create, falls due for the next line" |
| `tests/cases.py case sweep-outermost` | a transaction's claims are tried outermost resource first | "oldest transaction first, and within a transaction outermost resource first, then by resource name" |
| `tests/cases.py case sweep-parked` | a claim is not tried while the level that refused it has not moved | "A claim is due when it is made, and again whenever the service moves what is held at the level that last refused it" |
| `tests/cases.py case sweep-preempts` | a retake makes a younger holder give way | "Each is tried once, as an ordinary take that can make younger holders give way and can be refused by an older one" |
| `tests/cases.py case take-keeps-grant` | a refused upgrade keeps the mode the transaction already held | "the requester keeps whatever it held there already" |
| `tests/cases.py case take-no-lookahead` | a give-up forced at an outer level stands when the take is refused deeper | "If any incompatible holder is older than the requester, the take is refused: nothing the requester asked for is granted, at any level, and the give-ups already forced at outer levels stand" |
| `tests/cases.py case take-older-refused` | an older holder refuses, and the refusal leaves a claim at the mode that was asked for | "A refused take leaves a claim on the resource it named, at the mode it asked for" |
| `tests/cases.py case take-outward` | a take and its covers are granted and printed outermost first | "The grants of a successful take are printed outermost first" |
| `tests/cases.py case wide-after-sweep` | the rule runs after the sweep, on what the sweep left | "It does not run again after the changes it makes" |
| `tests/cases.py case wide-chain` | widening keys can take the store over the threshold in the same pass, and what sat under the replaced children goes with them | "Whatever it held under those children goes as well" |
| `tests/cases.py case wide-claims-idle` | a standing claim does not push a transaction over the threshold | "Claims are not grants and do not count" |
| `tests/cases.py case wide-deep-first` | keys are widened before blocks when both cross in one line | "It is applied to keys before blocks, in transaction age order and then by resource name, and repeated until a full pass changes nothing" |
| `tests/cases.py case wide-grants-only` | the threshold is read against grants | "Claims are not grants and do not count" |
| `tests/cases.py case wide-keys` | keys over the threshold are replaced by a grant at the block | "children of one resource has them replaced by a grant at that resource" |
| `tests/cases.py case wide-last` | a retake on this line is counted by the rule on this line | "It does not run again after the changes it makes" |
| `tests/cases.py case wide-passive` | a resource another transaction sits on stays fragmented | "The rule never makes anyone give way" |
| `tests/cases.py case wide-sup` | the widened mode is the supremum of the children and the asked mode | "asked for at the supremum of those children's effective modes and of anything it had already asked for there" |
| `tests/cases.py case wide-twice` | the rule repeats until a full pass changes nothing | "It is applied to keys before blocks, in transaction age order and then by resource name, and repeated until a full pass changes nothing" |
| `tests/cases.py case wide-under-limit` | exactly the threshold is not over it | "children of one resource has them replaced by a grant at that resource" |
| artifact `/app/lk/mode.py` | only the declared files are collected, and only these six | "The files you may change are"; "a new file put beside those six included" |
| artifact `/app/lk/hold.py` | only the declared files are collected, and only these six | "The files you may change are"; "a new file put beside those six included" |
| artifact `/app/lk/give.py` | only the declared files are collected, and only these six | "The files you may change are"; "a new file put beside those six included" |
| artifact `/app/lk/keep.py` | only the declared files are collected, and only these six | "The files you may change are"; "a new file put beside those six included" |
| artifact `/app/lk/wide.py` | only the declared files are collected, and only these six | "The files you may change are"; "a new file put beside those six included" |
| artifact `/app/lk/step.py` | only the declared files are collected, and only these six | "The files you may change are"; "a new file put beside those six included" |
| `tests/test.sh:35` a 60 s clock | the whole graded set must finish inside it | "it has 60 seconds of wall clock for the whole graded set" |
| `tests/seal/model.py:54-61` | the supremum of two modes | "Their supremum is the weakest mode at least as strong as both" |
| `tests/seal/model.py:64-65` | the cover a mode requires of the resource above it | "A grant at IS or S requires IS above it; a grant at IX, SIX or X requires IX" |
| `tests/seal/model.py:68-69` | whether two modes may share a resource | "IS is compatible with every mode but X, IX with IS and IX, S with IS and S, SIX with IS alone, X with nothing" |
| `tests/seal/model.py:72-74` | the resource above a given one | "A take is settled one level at a time from the store inward, and the service does not look ahead" |
| `tests/seal/model.py:77-78` | how deep a resource is, which orders the sweep | "oldest transaction first, and within a transaction outermost resource first, then by resource name" |
| `tests/seal/model.py:81-82` | resource order: store, then block, then key, lower numbers first | "a store before its blocks, a block before its keys, and lower numbers first" |
| `tests/seal/model.py:85-86` | deepest-first order, which the give-up and release walks use | "Giving way prints the deepest resource first, then equal depths in resource order, and then the levels above as they fall" |
| `tests/seal/model.py:115-122` | an ancestor's cover is the supremum over its live children | "the supremum of two things: the mode the program asked for there, if it ever asked, and the cover its own live grants below that resource require" |
| `tests/seal/model.py:124-136` | which other transactions are incompatible at a resource | "IS is compatible with every mode but X, IX with IS and IX, S with IS and S, SIX with IS alone, X with nothing" |
| `tests/seal/model.py:141-151` | the subtree a give-up or a release takes, deepest first | "A holder that gives way loses that resource and every grant it holds below it" |
| `tests/seal/model.py:166-186` | a grant appearing, rising, falling or disappearing, and the verb printed for each | "when a grant appears or rises to that mode" |
| `tests/seal/model.py:188-199` | a child appearing or leaving changes what the level above requires | "a mode falls when the grants beneath it go and rises when they come back" |
| `tests/seal/model.py:201-202` | a resource is brought to the supremum of its asked mode and its cover | "the supremum of two things: the mode the program asked for there, if it ever asked, and the cover its own live grants below that resource require" |
| `tests/seal/model.py:232-247` | a claim is recorded at the asked mode and falls due | "Only a resource the program asked for leaves a claim, at the asked mode, not at the effective mode that was printed" |
| `tests/seal/model.py:257-264` | a claim falls due again when the level that refused it moves | "A claim is due when it is made, and again whenever the service moves what is held at the level that last refused it" |
| `tests/seal/model.py:268-283` | the effective mode each level of a take's chain must reach | "the supremum of two things: the mode the program asked for there, if it ever asked, and the cover its own live grants below that resource require" |
| `tests/seal/model.py:285-312` | the level-by-level take: older refuses, younger gives way, and the grants are printed outermost first | "A take is settled one level at a time from the store inward, and the service does not look ahead" |
| `tests/seal/model.py:314-328` | giving way, its order, and the claim it leaves | "Only a resource the program asked for leaves a claim, at the asked mode, not at the effective mode that was printed" |
| `tests/seal/model.py:332-347` | a release takes the subtree and the claims under it | "removes every grant and every claim that transaction has at that resource or below it, and then lets the levels above fall to what is left" |
| `tests/seal/model.py:349-360` | a finish removes everything and prints its own line | "removes everything that transaction holds or claims" |
| `tests/seal/model.py:364-374` | the sweep: the claims due when it starts, in order, once each | "oldest transaction first, and within a transaction outermost resource first, then by resource name" |
| `tests/seal/model.py:376-415` | the widen rule, its threshold, its mode, its order and its repetition | "It is applied to keys before blocks, in transaction age order and then by resource name, and repeated until a full pass changes nothing" |
| `tests/seal/model.py:419-446` | the line procedure and the closing report | "The report comes after the last line, transactions in age order" |
| `tests/seal/model.py:449-450` | the whole program, as a trace followed by the report | "must return the trace followed by the closing report" |

## Readings

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| mode-sup-top | "the supremum of IX and S is SIX" | mode-cover-six |
| mode-cov-six | "A grant at IS or S requires IS above it; a grant at IX, SIX or X requires IX" | give-claim-asked |
| mode-cov-write | "A grant at IS or S requires IS above it; a grant at IX, SIX or X requires IX" | cover-holds-up |
| hold-never-falls | "a mode falls when the grants beneath it go and rises when they come back" | cover-plain-goes |
| hold-forgets-ask | "the supremum of two things: the mode the program asked for there, if it ever asked, and the cover its own live grants below that resource require" | cover-asked-stays |
| hold-ask-wins | "the supremum of two things: the mode the program asked for there, if it ever asked, and the cover its own live grants below that resource require" | give-claim-asked |
| hold-shallow-walk | "Giving way prints the deepest resource first, then equal depths in resource order, and then the levels above as they fall" | give-age-order |
| give-node-only | "A holder that gives way loses that resource and every grant it holds below it" | give-age-order |
| give-claim-eff | "Only a resource the program asked for leaves a claim, at the asked mode, not at the effective mode that was printed" | give-claim-asked |
| give-claim-all | "only to cover something beneath it leaves nothing" | give-age-order |
| keep-order-made | "oldest transaction first, and within a transaction outermost resource first, then by resource name" | cover-asked-stays |
| keep-order-deep | "oldest transaction first, and within a transaction outermost resource first, then by resource name" | sweep-outermost |
| keep-try-all | "A claim is due when it is made, and again whenever the service moves what is held at the level that last refused it" | sweep-parked |
| keep-fixpoint | "Whatever the sweep itself disturbs, including the claims its own give-ups create, falls due for the next line" | sweep-preempts |
| wide-counts-claims | "Claims are not grants and do not count" | wide-claims-idle |
| wide-once | "It is applied to keys before blocks, in transaction age order and then by resource name, and repeated until a full pass changes nothing" | wide-twice |
| wide-at-limit | "children of one resource has them replaced by a grant at that resource" | wide-after-sweep |
| wide-blocks-first | "It is applied to keys before blocks, in transaction age order and then by resource name, and repeated until a full pass changes nothing" | wide-deep-first |
| wide-preempts | "The rule never makes anyone give way" | wide-passive |
| step-lookahead | "A take is settled one level at a time from the store inward, and the service does not look ahead" | take-no-lookahead |
| step-grants-walked | "If any incompatible holder is older than the requester, the take is refused: nothing the requester asked for is granted, at any level, and the give-ups already forced at outer levels stand" | cover-unblocks |
| step-inner-first | "The grants of a successful take are printed outermost first" | cover-asked-stays |
| step-young-first | "If every incompatible holder is younger, each gives way, oldest of them first" | give-age-order |
| step-refuse-any | "If every incompatible holder is younger, each gives way, oldest of them first" | give-age-order |
| step-give-any | "If any incompatible holder is older than the requester, the take is refused: nothing the requester asked for is granted, at any level, and the give-ups already forced at outer levels stand" | cover-unblocks |
| step-no-sweep | "A claim is due when it is made, and again whenever the service moves what is held at the level that last refused it" | cover-unblocks |
| step-wide-first | "It does not run again after the changes it makes" | wide-last |
| step-drop-keeps | "removes every grant and every claim that transaction has at that resource or below it, and then lets the levels above fall to what is left" | free-subtree |
| step-shut-silent | "removes everything that transaction holds or claims" | shut-clears |

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (nop) | reward 0; it fails 45 of the 48 graded assertions and never finishes the two scale families inside the clock |
| constant: one fixed output for every program (cheat-flat-constant) | reward 0; it matches 0 of 414 graded programs |
| positional: every take granted at the resource it names, nothing else (cheat-pos-grant-all) | reward 0; it matches 0 of 414 graded programs, because no program's first line is a take |
| the worked example's output replayed for every program (cheat-replay-sample) | reward 0; it matches 1 of 414 - runs/one.txt itself is not in the graded set, so it matches nothing |
| an answer key carrying the 44 frozen enumerated answers (cheat-forge-hand) | reward 0; it passes all 44 enumerated programs and fails all 370 it could not have seen |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| tests/test.sh:35 a 60 s clock on the whole graded set | `authoring/grant-widen-yield/variants/walk` and `authoring/grant-widen-yield/variants/multiset`, two correct services written to the same contract with different internals, and `authoring/grant-widen-yield/timing.py`, which re-measures every row below | 2026-09-22: reference 0.22 s on one wide program and 1.45 s on one crowded one, and all 414 graded programs in 7.89 s of the 60; walk 0.22 s and 1.94 s; multiset 1.44 s and 2.65 s. The correct-but-naive readings on the same two programs: 14.97 s with the cover rescanned, 20.96 s with every standing claim looked at, and 26.27 s and over 200 s with the widen threshold tested everywhere - each shipped as a cheat and each scoring 0 |
