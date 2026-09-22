# Instruction trace: glob-route-hide

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Every citation
is the instruction word for word. The sealed model is walked rule by rule with its lines, since
`assert got == want` hides every rule the model applies. Check with
`python tools/tracecheck.py glob-route-hide`.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:110` test_frozen_truth_matches_the_model | the sealed model reproduces the frozen hand answers before anything is judged; grades nothing the agent wrote | "Every line of every program has to match" |
| `tests/test_outputs.py:119` test_the_worker_ran_the_whole_exam | every graded program has a record, made from the text that was graded | "We grade forty programs written by hand, four hundred small ones generated when grading starts" |
| `tests/test_outputs.py:130` test_hand_case | each hand program's lines equal the frozen answer exactly | "Every line of every program has to match" |
| `tests/test_outputs.py:137` test_every_generated_program_matches | every generated program's lines equal the sealed model's exactly | "four hundred small ones generated when grading starts, and three of each of those two large shapes" |
| `tests/test_outputs.py:152` test_every_family_is_represented | the generated population contains every family, including both large shapes | "three of each of those two large shapes" |
| `tests/cases.py:50` case ordinary-tree | a child reads its parent's private helper through a glob, public items resolve through globs | "Any other line can be seen from its own module and from every module inside it, and nowhere else" |
| `tests/cases.py:67` case vis-child-sees | a module inside the source sees its private item through a glob | "Any other line can be seen from its own module and from every module inside it" |
| `tests/cases.py:75` case vis-outsider-denied | a module outside the source does not | "and from every module inside it, and nowhere else" |
| `tests/cases.py:83` case vis-grandchild | inside is transitive over dots | "so `a.b.c` is inside `a.b` and inside `a`" |
| `tests/cases.py:93` case vis-parent-denied | an enclosing module does not see a nested module's private item | "A module is inside every module whose path is its own cut off at a dot" |
| `tests/cases.py:101` case vis-no-inherit | a nested module gets nothing from its parent without a line | "Enclosing modules lend nothing: a module gets names only through its own lines." |
| `tests/cases.py:108` case vis-sibling-prefix | `ab` is not inside `a` | "while `ab` is inside nothing" |
| `tests/cases.py:119` case narrow-private-glob | a private glob passes candidates on only to modules inside its module | "from then on that candidate is seen only from the modules that can see both it and the `use` line" |
| `tests/cases.py:130` case narrow-pub-keeps | a public glob passes them on as widely as they came | "A `pub` line can be seen from every module." |
| `tests/cases.py:140` case narrow-explicit | a private explicit import narrows the same way; a module inside it still sees | "each candidate that `P` has under `N` and the importing module can see, and from then on that candidate is seen only from the modules that can see both it and the `use` line" |
| `tests/cases.py:153` case narrow-keeps-item | a public re-export of a private item stays inside the item line's reach | "seen only from the modules that can see both it and the `use` line" |
| `tests/cases.py:166` case widen-two-routes | a narrow route and a wide route to one item: seen from where the wide one allows | "it is seen from every module that any one of those chains lets see it" |
| `tests/cases.py:179` case widen-late-cycle | the wide route closes only through a cycle | "When several chains reach the same item it is still one candidate, and it is seen from every module that any one of those chains lets see it." |
| `tests/cases.py:195` case widen-gated-arm | the wide route's glob is gated off, so only the narrow route remains | "A line that is not there does nothing at all." |
| `tests/cases.py:209` case hide-own-private | a private own import hides the public glob's name from an outside reader | "That holds for every module reading it, including one that cannot see the lines that bind." |
| `tests/cases.py:223` case hide-descendant-sees | a module inside the hider sees the hider's private binding | "Any other line can be seen from its own module and from every module inside it" |
| `tests/cases.py:236` case hide-broken | an own import that finds nothing still hides the globs and prints broken | "It then has under that name exactly what those lines give, even if that is nothing, and never anything from its `use P::*` lines." |
| `tests/cases.py:247` case hide-gated-off | an own import whose flag is off hides nothing | "A line that is not there does nothing at all." |
| `tests/cases.py:258` case hide-gated-on | the same import with its flag on hides | "A line ending in `if F` is there only while flag `F` is on." |
| `tests/cases.py:269` case gate-negated | `if !F` lines exist only while F is off; an unlisted flag is off | "One ending in `if !F` is there only while it is off." |
| `tests/cases.py:281` case glob-unbound-name | a module binding one name still gets other names from its globs | "`use P::*` does the same under every name its module does not bind itself." |
| `tests/cases.py:292` case amb-two-globs | two globs giving different items: ambiguous, in item-line order | "More than one prints `<module> N ambiguous` and then every candidate as `<m>.<n>`, in the order their `item` lines appear in the file." |
| `tests/cases.py:303` case amb-file-order | order follows item lines, not the order the module reads them | "in the order their `item` lines appear in the file" |
| `tests/cases.py:314` case amb-carried | an ambiguous name travels on through a glob as every candidate | "`use P::*` does the same under every name its module does not bind itself." |
| `tests/cases.py:327` case amb-filtered | a reader that cannot see one candidate resolves to the other | "each candidate that `P` has under `N` and the importing module can see" |
| `tests/cases.py:341` case amb-explicit | an explicit import of an ambiguous name gives every candidate | "gives its module, under `K`, each candidate that `P` has under `N`" |
| `tests/cases.py:354` case route-same-item | one item through two globs is one candidate | "When several chains reach the same item it is still one candidate" |
| `tests/cases.py:367` case own-two-lines | an item line and an import line for one name both give | "It then has under that name exactly what those lines give" |
| `tests/cases.py:376` case dup-item-lines | two present item lines with one name are two items; exclusive flags leave one | "every `item` line is a separate item" |
| `tests/cases.py:386` case cycle-alone | a cycle of globs with no item behind it gives nothing | "Lines that only lead round a circle give nothing." |
| `tests/cases.py:396` case cycle-fed | a cycle fed at one member reaches every member | "A module has a candidate only when a chain of these lines leads from it to the candidate's `item` line." |
| `tests/cases.py:411` case cycle-cut | a member binding a name that flows round the cycle stops its glob giving it | "It then has under that name exactly what those lines give, even if that is nothing, and never anything from its `use P::*` lines." |
| `tests/cases.py:430` case rename-chain | a rename gives under the new name only | "`use P::N as K` gives its module, under `K`" |
| `tests/cases.py:441` case rename-hides-bound | a rename binds the new name, which the glob then no longer gives; the old name still comes through the glob | "A module binds a name itself when an `item`, `use P::N` or `use Q::M as N` line for that name is there." |
| `tests/cases.py:452` case explicit-denied | an explicit import of something the importer cannot see gives nothing, so broken | "each candidate that `P` has under `N` and the importing module can see" |
| `tests/cases.py:460` case explicit-ancestor | an explicit import sees an enclosing module's private item | "Any other line can be seen from its own module and from every module inside it" |
| `tests/cases.py:468` case missing-module | an import from an undeclared module finds nothing, still binds, so broken | "Neither does a module the program never declares." |
| `tests/cases.py:477` case self-import | importing a name from the module itself binds it and gives nothing | "Lines that only lead round a circle give nothing." |
| `tests/cases.py:486` case self-glob | a module reading itself gains nothing new | "Lines that only lead round a circle give nothing." |
| `tests/cases.py:494` case unresolved-plain | a name nothing gives and nothing binds | "and `<module> N unresolved` if it does not" |
| artifact `/app/fe/vis.py` | only the declared files are collected | "You may change `/app/fe/vis.py`, `/app/fe/own.py`, `/app/fe/glob.py`, `/app/fe/fix.py` and `/app/fe/say.py`, and only those." |
| artifact `/app/fe/own.py` | only the declared files are collected | "You may change `/app/fe/vis.py`, `/app/fe/own.py`, `/app/fe/glob.py`, `/app/fe/fix.py` and `/app/fe/say.py`, and only those." |
| artifact `/app/fe/glob.py` | only the declared files are collected | "You may change `/app/fe/vis.py`, `/app/fe/own.py`, `/app/fe/glob.py`, `/app/fe/fix.py` and `/app/fe/say.py`, and only those." |
| artifact `/app/fe/fix.py` | only the declared files are collected | "You may change `/app/fe/vis.py`, `/app/fe/own.py`, `/app/fe/glob.py`, `/app/fe/fix.py` and `/app/fe/say.py`, and only those." |
| artifact `/app/fe/say.py` | only the declared files are collected | "You may change `/app/fe/vis.py`, `/app/fe/own.py`, `/app/fe/glob.py`, `/app/fe/fix.py` and `/app/fe/say.py`, and only those." |
| `tests/worker.py:33-43` pristine overlay | everything but the five files comes from the verifier's copy; a sixth file is never collected | "everything outside those five files is replaced by our own copy, so a file you add beside them is never picked up" |
| `environment/app_src/run_res.py:6-9` frozen entry points | the driver calls `settle(prog)` once and `line(prog, tab, i)` per reference, index from 0 | "It then calls `line(prog, tab, i)` in `say.py` for the `ref` line with index `i`, counting from 0 in file order, passing whatever `settle` returned as `tab`." |
| `environment/app_src/run_res.py:6-9` frozen entry points, names | both functions keep their names and arguments | "Keep both functions with those names and arguments." |
| `tests/test.sh:36` a 60 s clock | the unprivileged worker must finish the whole exam inside 60 seconds | "The whole set has to run inside 60 seconds on one CPU with 2 GB of memory" |
| `tests/seal/model.py:34-73` _parse, flags line | the first line lists the flags that are on | "A program opens with a line reading `flags` and then the names of the flags that are on." |
| `tests/seal/model.py:34-73` _parse, module blocks | each `mod` starts a module holding the lines up to the next | "`mod P` starts module `P`, and every line up to the next `mod` belongs to it." |
| `tests/seal/model.py:34-73` _parse, line kinds | item, explicit import with and without rename, glob, optional pub and flag suffix, ref | "The lines a module holds are `item N`, `use P::N`, `use P::N as K` and `use P::*`, any of which may begin with `pub` and end with `if F` or `if !F`, and `ref N`, which takes neither." |
| `tests/seal/model.py:76-77` _present | a line is present only when its flag condition holds; unlisted flags are off | "A line ending in `if F` is there only while flag `F` is on." |
| `tests/seal/model.py:76-77` _present, negation | `if !F` present only while F is off | "One ending in `if !F` is there only while it is off." |
| `tests/seal/model.py:80-82` _inside | inside means a dot-prefix of the path | "A module is inside every module whose path is its own cut off at a dot" |
| `tests/seal/model.py:85-87` _sees | a candidate is seen from every module or from its root's subtree | "Each candidate is an item, together with the modules it can be seen from" |
| `tests/seal/model.py:90-100` _narrower | passing through a line keeps only the modules that can see both | "that candidate is seen only from the modules that can see both it and the `use` line" |
| `tests/seal/model.py:103-131` _Bits | a candidate is an item held under a name; a rename carries it to the new name | "`use P::N as K` gives its module, under `K`, each candidate that `P` has under `N`" |
| `tests/seal/model.py:134-137` _merge | the same item from several chains is one candidate | "When several chains reach the same item it is still one candidate" |
| `tests/seal/model.py:140-149` _normalise | a candidate is seen from the widest set any chain allows | "it is seen from every module that any one of those chains lets see it" |
| `tests/seal/model.py:152-158` _through | an import passes only candidates the importing module can see, narrowed | "each candidate that `P` has under `N` and the importing module can see" |
| `tests/seal/model.py:171-173` expect, item lines | a present item line gives its item, seen from where the line is seen | "`item N` gives its module that item under `N`, seen from wherever the line can be seen." |
| `tests/seal/model.py:171-173` expect, pub | a pub line is seen from every module, any other from its module's subtree | "A `pub` line can be seen from every module." |
| `tests/seal/model.py:171-179` expect, binding | a module binds a name through its present item and explicit import lines, whatever they find | "A module binds a name itself when an `item`, `use P::N` or `use Q::M as N` line for that name is there." |
| `tests/seal/model.py:189-213` expect, fixed point | holdings start empty and grow round by round until nothing changes: only chains ending at item lines | "A module has a candidate only when a chain of these lines leads from it to the candidate's `item` line." |
| `tests/seal/model.py:196-203` expect, explicit imports | an explicit import gives what the source has under the name, renamed, whatever else the module binds | "`use P::N` is the same under `N`." |
| `tests/seal/model.py:197-198` expect, undeclared source | an import from an undeclared module gives nothing | "Neither does a module the program never declares." |
| `tests/seal/model.py:204-209` expect, globs | a glob gives every name except those the module binds itself | "`use P::*` does the same under every name its module does not bind itself." |
| `tests/seal/model.py:204-209` expect, hiding for every reader | the own-name mask is applied to the module's holdings, not per reader | "That holds for every module reading it, including one that cannot see the lines that bind." |
| `tests/seal/model.py:216-221` expect, reading a reference | a reference reads everything its module has under the name | "`ref N` asks what its own module has under `N`, all of which that module can see." |
| `tests/seal/model.py:222-223` expect, one candidate | module, name, then the item's module and name joined by a dot | "One candidate prints `<module> N <m>.<n>`, with `m` the module holding the candidate's `item` line and `n` the name on that line." |
| `tests/seal/model.py:224-225` expect, none | broken when the module binds the name itself, unresolved otherwise | "No candidate prints `<module> N broken` if the module binds `N` itself, and `<module> N unresolved` if it does not." |
| `tests/seal/model.py:226-228` expect, several | ambiguous and every candidate in item-line order | "More than one prints `<module> N ambiguous` and then every candidate as `<m>.<n>`, in the order their `item` lines appear in the file." |
| `tests/seal/model.py:215-229` expect, format | single spaces, one line per reference in file order, nothing else | "Fields are separated by single spaces." |
| `tests/seal/model.py:215-229` expect, line order | one line per ref line in file order | "Lines come in the order of the `ref` lines, and nothing else is printed." |

## Readings

Every reading is written as a whole submission by `authoring/glob-route-hide/emit.py`, which
keeps its readings in a table built at run time, so each is cited by hand here.
`tools/readingcheck.py` measured all 30 as separated by the enumerated set, and
`cheat_report.py` asserts each is caught by the case named in the last column.

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| a line passes on only public candidates (pub-only) | "Any other line can be seen from its own module and from every module inside it" | vis-child-sees |
| a module is inside another when its path merely starts with the other's (string-prefix) | "while `ab` is inside nothing" | vis-sibling-prefix |
| an import passes candidates on as widely as they came (no-narrow) | "seen only from the modules that can see both it and the `use` line" | narrow-private-glob |
| a private glob does not narrow (glob-no-narrow) | "`use P::*` does the same under every name its module does not bind itself." | narrow-private-glob |
| a private explicit import does not narrow (explicit-no-narrow) | "seen only from the modules that can see both it and the `use` line" | narrow-explicit |
| a public line makes what it passes on public (pub-widens) | "seen only from the modules that can see both it and the `use` line" | narrow-keeps-item |
| an explicit import takes what the source holds, seen or not (explicit-ignores-vis) | "each candidate that `P` has under `N` and the importing module can see" | explicit-denied |
| a candidate keeps the visibility of its first route (first-route) | "it is seen from every module that any one of those chains lets see it" | widen-two-routes |
| an own binding hides only from readers that can see it (seen-hides) | "That holds for every module reading it, including one that cannot see the lines that bind." | hide-own-private |
| an own import that finds nothing does not hide (broken-falls) | "even if that is nothing, and never anything from its `use P::*` lines" | hide-broken |
| an absent own line still hides (gated-hides) | "A line that is not there does nothing at all." | hide-gated-off |
| globs give every name, own names included (glob-all-names) | "`use P::*` does the same under every name its module does not bind itself." | glob-unbound-name |
| an import from an undeclared module binds nothing (missing-unbound) | "A module binds a name itself when an `item`, `use P::N` or `use Q::M as N` line for that name is there." | missing-module |
| a rename binds the old name too (rename-binds-both) | "A module binds a name itself when an `item`, `use P::N` or `use Q::M as N` line for that name is there." | rename-hides-bound |
| a rename binds and gives under the old name (rename-keeps-name) | "`use P::N as K` gives its module, under `K`" | rename-chain |
| a glob exists whatever its flag says (glob-ignores-flags) | "A line that is not there does nothing at all." | widen-gated-arm |
| an item line exists whatever its flag says (item-ignores-flags) | "A line ending in `if F` is there only while flag `F` is on." | gate-negated |
| `if !F` read as `if F` (negation-ignored) | "One ending in `if !F` is there only while it is off." | gate-negated |
| an item through two globs is two candidates (route-dupes) | "When several chains reach the same item it is still one candidate" | route-same-item |
| a glob drops a name ambiguous at its source (drop-ambiguous) | "`use P::*` does the same under every name its module does not bind itself." | amb-carried |
| an explicit import of an ambiguous name gives nothing (explicit-amb-broken) | "gives its module, under `K`, each candidate that `P` has under `N`" | amb-explicit |
| candidates in the order the module's lines reach them (found-order) | "in the order their `item` lines appear in the file" | amb-two-globs |
| candidates in alphabetical order (alpha-order) | "in the order their `item` lines appear in the file" | amb-file-order |
| two item lines with one module and name are one candidate (dup-items-merged) | "every `item` line is a separate item" | dup-item-lines |
| a bound name that finds nothing prints unresolved (no-broken) | "No candidate prints `<module> N broken` if the module binds `N` itself" | hide-broken |
| a module falls back to its parent's names (inherit) | "Enclosing modules lend nothing: a module gets names only through its own lines." | vis-no-inherit |
| every member of a cycle of globs holds the same candidates (scc-share) | "It then has under that name exactly what those lines give, even if that is nothing, and never anything from its `use P::*` lines." | cycle-cut |
| only item lines hide the globs, explicit imports do not (use-no-hide) | "A module binds a name itself when an `item`, `use P::N` or `use Q::M as N` line for that name is there." | hide-own-private |
| a renamed item printed under the name it is held by (display-held-name) | "with `m` the module holding the candidate's `item` line and `n` the name on that line" | rename-chain |
| memoized recursion, a pair in progress giving nothing (memo-rec) | "A module has a candidate only when a chain of these lines leads from it to the candidate's `item` line." | cycle-fed |

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (nop) | 0 in the host trial: the worker runs out the 60 s clock on the large programs; with the clock set aside it matches 20 of 40 hand programs and gets 326 of 400 generated wrong |
| constant: every reference prints unresolved, the commonest outcome (cheat-const-unresolved) | 0; matches 5 of 40 hand programs, 390 of 400 generated wrong |
| positional: an ambiguity settled on its first candidate (cheat-pos-first) | 0; matches 32 of 40 hand programs, 122 of 400 generated wrong |
| positional: a module reads only its first glob (cheat-pos-first-glob) | 0; matches 30 of 40 hand programs, 190 of 400 generated wrong |
| the worked example's output replayed for every reference (cheat-replay-example) | 0; matches 0 of 40 hand programs and no generated one |
| forgery: every frozen hand answer carried, the shipped resolver for other small programs and unresolved for large ones (cheat-forge-hand) | 0; passes all 40 hand programs, 326 of 400 generated wrong; in the host trial it finishes in 6.4 s and fails only `test_every_generated_program_matches` |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:36` a 60 s clock | `authoring/glob-route-hide/variants/ok-rounds` and `authoring/glob-route-hide/variants/ok-scc`, written apart from the reference; `tests/seal/model.py` also written apart | host trial of the whole verifier: ok-rounds 12.8 s and ok-scc 10.5 s end to end, pytest about 6 s of each, so the worker's share is under 7 s against 60; the reference 9.6 s, 5.4 s of it pytest. On one 4000-module tree program, against 0.8 s for the reference, 1.0 s for ok-rounds and 0.9 s for ok-scc: the exact but slow `authoring/glob-route-hide/slow/pairs` runs out of 2 GB after 34.5 s, `slow/tables` after 20.4 s, the per-name `slow/sweep` takes 94.6 s and the last-in-first-out `slow/lifo` 77.8 s; all four score 0 in the host trial with the worker stopped by the clock |
