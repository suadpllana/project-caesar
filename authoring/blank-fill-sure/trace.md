# Instruction trace: blank-fill-sure

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Every graded
assertion - a test function, an enumerated case, a collected artifact, the clock, the memory cap,
and each rule the sealed model applies - is tied to the sentence of `instruction.md` that states
it, quoted word for word. Check with `python tools/tracecheck.py blank-fill-sure`.

The grader compares printed lines exactly (`tests/test_outputs.py:119`, `tests/test_outputs.py:138`),
so the model is the test file and is walked rule by rule below.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:105` test_model_reproduces_frozen_answers | the sealed model still reproduces the frozen answers of the hand programs before it judges anything; grades the verifier, not the agent | "thirty-three small programs of our own" |
| `tests/test_outputs.py:115` test_hand_case | each hand program's printed report equals `gt.json` line for line, and the program the worker ran is the one the grader holds | "Every line of every report has to be exactly right." and "thirty-three small programs of our own" |
| `tests/test_outputs.py:124` test_every_generated_program_matches | every generated program (300 small, 3 wide, 3 flags) was run unaltered and printed exactly what the model prints; a missing or raising program fails it | "three hundred small programs generated after you finish" and "three programs built like each of the big two" and "Every line of every report has to be exactly right." |
| `tests/test_outputs.py:144` test_every_family_is_graded | every family, both big shapes included, is present in the record | "three programs built like each of the big two" |
| `tests/cases.py:45` case self-same | two rows sharing `?w` join each other whatever it is | "A label is one value everywhere it appears." and "a variable takes one value everywhere it appears in the rule" |
| `tests/cases.py:51` case two-labels | `?w` and `?v` may differ, so rows 1 and 2 never certainly join | "A filling gives each placeholder one of the values it may take, and nothing else constrains it" |
| `tests/cases.py:57` case one-value | a column allowing only 7 makes its placeholder 7 | "The values a placeholder may take are the values allowed by every column it sits in" and "allows every integer from lo to hi, both included" |
| `tests/cases.py:65` case cover-join | every allowed region maps to ann, so the manager row is returned under every filling | "that the query returns under every filling" |
| `tests/cases.py:74` case cover-gap | region 3 has no manager, so no row is certain | "that the query returns under every filling" |
| `tests/cases.py:82` case cover-split | regions map to two managers, so neither is certain | "that the query returns under every filling" |
| `tests/cases.py:91` case meet-cols | the placeholder sits in a 1..5 and a 1..3 column, so only 1..3, all mapped to ann | "The values a placeholder may take are the values allowed by every column it sits in" |
| `tests/cases.py:103` case union-cover | one rule asks for open and one for shut, and the status allows only those | "A query returns every row that any of its rules derives." and "that the query returns under every filling" |
| `tests/cases.py:110` case union-hold | the shut rule also needs a hold row, so account 5 is certain and 6 is not | "A query returns every row that any of its rules derives." |
| `tests/cases.py:119` case pigeon-spare | two placeholders in 1..3 with 1 and 2 used: both at 3 makes them equal, so a rule fires either way | "two placeholders may take the same value" |
| `tests/cases.py:129` case spare-enough | every used value has a stop row, yet the placeholder may take a value nothing uses | "a value need not appear anywhere else in the program" |
| `tests/cases.py:140` case ne-const | `D != 0` on constants keeps 3 and drops 0 | "holds when the value X takes is not c" |
| `tests/cases.py:146` case ne-wide | `D != 0` on a billion-value placeholder is not certain, since it may be 0 | "holds when the value X takes is not c" and "allows every integer from lo to hi, both included" |
| `tests/cases.py:152` case ne-unallowed | `S != gone` on an open-or-shut placeholder always holds | "holds when the value X takes is not c" and "The values a placeholder may take are the values allowed by every column it sits in" |
| `tests/cases.py:157` case ne-tight | `S != shut` fails when S is shut, and a second rule asking for shut rescues only account 6 | "holds when the value X takes is not c" and "A query returns every row that any of its rules derives." |
| `tests/cases.py:164` case ne-trade | making the distance 0 kills one rule and matches the stop row in the other | "holds when the value X takes is not c" and "that the query returns under every filling" |
| `tests/cases.py:172` case ne-trade-miss | the same with no stop at 0, so the filling 0 removes the row | "holds when the value X takes is not c" and "that the query returns under every filling" |
| `tests/cases.py:182` case data-cover | every value 1..6 is used by the zone rows, all north, so the join is certain with no constant in the query | "that the query returns under every filling" and "allows every integer from lo to hi, both included" |
| `tests/cases.py:196` case head-label | a head bound to a wide placeholder prints no row | "A placeholder never appears in a report." |
| `tests/cases.py:201` case head-few | a head bound to a y-or-n placeholder prints neither value | "A placeholder never appears in a report." and "that the query returns under every filling" |
| `tests/cases.py:206` case repeat-var | `pair(X, X)` holds for a row carrying one label twice, not for two labels; the zero-head query prints its name | "a variable takes one value everywhere it appears in the rule" and "printed as the query name alone" |
| `tests/cases.py:217` case wild | `_` matches a placeholder whatever it is | "equals the row's value in that column, `_` fits anything" |
| `tests/cases.py:222` case const-atom | a constant the placeholder is not allowed to take never matches it | "a constant argument equals the row's value in that column" and "The values a placeholder may take are the values allowed by every column it sits in" |
| `tests/cases.py:229` case bool-yes | a query with no head variables prints one empty row when it always holds | "A query with no head variables reports at most one row, the empty one, printed as the query name alone." |
| `tests/cases.py:235` case bool-no | and no row when some filling makes it fail | "A query with no head variables reports at most one row" and "that the query returns under every filling" |
| `tests/cases.py:240` case order-mixed | rows sort value by value, integers first and by value, then symbols | "Rows are sorted on their first value, then their second, and so on." and "Integers come before symbols, integers compare as numbers" |
| `tests/cases.py:251` case unread-labels | placeholders in a table no query reads change nothing | "holds, once each, the rows of integers and symbols that the query returns under every filling" |
| `tests/cases.py:261` case split-late | one account's conditions hold under every filling among several accounts' that do not | "A query returns every row that any of its rules derives." and "that the query returns under every filling" |
| `tests/cases.py:273` case split-none | no account's conditions hold everywhere, so the row is not reported | "that the query returns under every filling" |
| `tests/cases.py:283` case tight-tight | two x-or-y placeholders meet only when their values agree, and the value 6 is reached either way | "two placeholders may take the same value" and "that the query returns under every filling" |
| `tests/cases.py:292` case int-sym | a symbol-valued placeholder never equals an integer, and `V != 3` on it always holds | "An integer never equals a symbol." |
| `tests/cases.py:300` case dup-row | a row derived twice prints once | "The report of a query holds, once each, the rows of integers and symbols" |
| `tests/cases.py:306` case empty-table | a rule over a table with no rows derives nothing, and its query still prints first | "The queries print in the order of their first rule" |
| artifact `/app/rs/cmp.py` | only the declared files are collected | "The files you may change are `/app/rs/cmp.py`, `/app/rs/join.py` and `/app/rs/keep.py`." |
| artifact `/app/rs/join.py` | only the declared files are collected | "The files you may change are `/app/rs/cmp.py`, `/app/rs/join.py` and `/app/rs/keep.py`." |
| artifact `/app/rs/keep.py` | only the declared files are collected | "Nothing else is collected: we copy those three into a clean copy of the rest of `/app`" |
| `tests/worker.py:41` fresh_tree | the three files are laid over the verifier's pristine tree; a new file or an edit to a frozen file is never seen | "so a change to any other file, or a new file, is never seen" |
| `tests/worker.py:59` import run_ask | every program runs through the frozen entry point, `report(store)` in `keep.py`, in one process | "passes the store it builds to `report` in `/app/rs/keep.py`" and "The whole set runs one program after another in a single Python 3.12 process" |
| `environment/app_src/rs/say.py:5` lines | the printer takes the mapping `report` returns; rows must be hashable tuples, and a missing query prints empty | "each row a tuple holding its integers as ints and its symbols as strs; a query it leaves out prints with no rows" |
| `tests/test.sh:34` a 300 s clock | the worker, running every graded program, is killed at 300 s and the reward stays 0 | "it has to finish inside 300 seconds" |
| `task.toml` memory_mb = 2048, cpus = 1 | the container's caps apply to the whole run | "on one CPU with 2048 MB of memory" |
| `tests/Dockerfile` python:3.12-slim with pytest only | a submission importing a package outside the standard library fails every program | "in a single Python 3.12 process with only the standard library" |
| `tests/seal/model.py:46` konst, `tests/seal/model.py:54` eq | an integer and a symbol are never equal, compared by type then value | "An integer never equals a symbol." |
| `tests/seal/model.py:60` read: tables | one allowed set per column, a range or a symbol list | "declares a table with one allowed set per column" |
| `tests/seal/model.py:78` read: rows | a value is an integer, a symbol or a label written with `?` | "A value is an integer, a symbol or a placeholder, written `?` and its label" |
| `tests/seal/model.py:82` read: rules | a rule is a head of variables, atoms and conditions; queries keep the order of their first rule | "adds a rule to a query" and "The queries print in the order of their first rule" |
| `tests/seal/model.py:122` allowed_of | a label's allowed set is the meet of every column it sits in | "The values a placeholder may take are the values allowed by every column it sits in" |
| `tests/seal/model.py:141` mentioned | the constants a program mentions, which fillings may or may not reuse | "a value need not appear anywhere else in the program" |
| `tests/seal/model.py:178-193` cases_of: spare values | a label with more unused allowed values than labels can take a value nothing else holds, and every filling gives it one, so one such value stands for all of them | "A filling gives each placeholder one of the values it may take, and nothing else constrains it" and "a value need not appear anywhere else in the program" |
| `tests/seal/model.py:194-199` cases_of: compared constants | such a label may still take a constant an inequality compares it with | "holds when the value X takes is not c" |
| `tests/seal/model.py:200-201` cases_of: everything else | any other label ranges over its whole allowed set | "The values a placeholder may take are the values allowed by every column it sits in" |
| `tests/seal/model.py:207` can | a label meets a constant it may take, and two labels meet on a value both may take | "A label is one value everywhere it appears." and "two placeholders may take the same value" |
| `tests/seal/model.py:226` rule_rows: atoms | an atom fits a row on equal constants, `_` for anything, one value per variable | "a constant argument equals the row's value in that column" and "a variable takes one value everywhere it appears in the rule" |
| `tests/seal/model.py:271-283` rule_rows: conditions and head | every condition must hold; the head is the head variables' values in order | "every condition of the rule holds" and "the values of its head variables in the order written" |
| `tests/seal/model.py:286` consistent | one label takes one value in one derivation | "A label is one value everywhere it appears." |
| `tests/seal/model.py:299` reach_rows, `tests/seal/model.py:320` build_index | which rows a constant or a label can fit; an index, it decides nothing beyond `can` | "a constant argument equals the row's value in that column" |
| `tests/seal/model.py:340` labs_in, `tests/seal/model.py:349` truth, `tests/seal/model.py:362` settle | a condition's truth under an assignment | "Under a filling every row holds only integers and symbols." |
| `tests/seal/model.py:380` always | a row is reported when some derivation of it holds under every filling | "that the query returns under every filling" |
| `tests/seal/model.py:427` order | integers before symbols, integers by value, symbols by character code | "Integers come before symbols, integers compare as numbers, and symbols compare character by character in ASCII order, a prefix first." |
| `tests/seal/model.py:431` expect: union and heads | candidate rows are collected across every rule of a query; a head label that can only be a value of its own never yields a row, and one with cases yields one row per case | "A query returns every row that any of its rules derives." and "A placeholder never appears in a report." |
| `tests/seal/model.py:452-460` expect: printing | `ans <query> <n>` then each row, the query name and its values; an empty head prints the name alone | "each as a line `ans <query> <n>`, where n is the number of rows" and "the query name and then its values, separated by single spaces" |

## Readings

Each is the reference with one decision taken the other way, built by
`authoring/blank-fill-sure/make_readings.py`, emitted as a cheat by
`authoring/blank-fill-sure/emit.py`, checked by `python tools/readingcheck.py blank-fill-sure` and
by `authoring/blank-fill-sure/cheat_report.py`, and scored 0 through the two-stage host trial.

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| fresh-all: every placeholder is a value only it holds, the textbook evaluation | "The values a placeholder may take are the values allowed by every column it sits in" and "that the query returns under every filling" | cover-join |
| first-col: allowed values come from the first column a label sits in | "The values a placeholder may take are the values allowed by every column it sits in" | meet-cols |
| per-rule: certainty decided rule by rule, then united | "A query returns every row that any of its rules derives." then "that the query returns under every filling" | union-cover |
| spare-one: a placeholder is fresh as soon as one allowed value is unused | "two placeholders may take the same value" | pigeon-spare |
| ne-fresh: an inequality on a placeholder with spare values always holds | "holds when the value X takes is not c" | ne-wide |
| ne-no-join: taking the compared constant fails the inequality but never opens a join | "A filling gives each placeholder one of the values it may take" and "a constant argument equals the row's value in that column" | ne-trade |
| query-consts: a value counts as used only when a rule names it | "The values a placeholder may take are the values allowed by every column it sits in" and "that the query returns under every filling" | data-cover |
| used-only: a placeholder with spare values ranges over used values only | "a value need not appear anywhere else in the program" | spare-enough |
| head-label: a row carrying a placeholder that every filling returns is printed with the label | "A placeholder never appears in a report." | head-label |
| all-groups: a row is certain only when every group of its conditions holds | "A query returns every row that any of its rules derives." and "that the query returns under every filling" | split-late |
| possible: rows some filling returns | "that the query returns under every filling" | cover-gap |
| no-ban: an inequality on a placeholder is ignored | "holds when the value X takes is not c" | ne-tight |
| ne-unknown: a row needing an inequality on a placeholder is never reported | "holds when the value X takes is not c" and "The values a placeholder may take are the values allowed by every column it sits in" | ne-unallowed |
| labels-apart: two different placeholders never share a value | "two placeholders may take the same value" | pigeon-spare |
| smallest-fill: one filling decides, each placeholder at its smallest value | "that the query returns under every filling" | cover-gap |
| SQL null logic, the shipped engine (a placeholder matches nothing) | "A label is one value everywhere it appears." and the worked example in `environment/app_src/progs/tiny.txt` | self-same |

What the worked example decides, measured by running every reading on `tiny.txt`: the line the
brief states, `ans pair 6`, rules out the shipped engine (`ans pair 1`) and two misreadings of
the definition itself, possible and smallest-fill (`ans pair 10` each). fresh-all, ne-fresh and
no-ban print `ans pair 6` and differ from the reference only on the `far` query, whose correct
output the brief does not give; the other ten readings print the reference's report exactly. So
the example is evidence for label identity and for returning under every filling, both stated in
so many words, and for none of the method's decisions: not the allowed sets, the spare count,
the inequality cases or the split.

## Shortcuts

Measured by `authoring/blank-fill-sure/shortcuts.py` on the 33 hand programs and the 306 programs
of one generated seed, and scored through the host trial where a cheat exists.

| Strategy | Result |
|---|---|
| the shipped tree unchanged (nop) | reward 0; matches 16 of 33 hand and 173 of 306 generated reports |
| constant: every query reports nothing (cheat-const-empty) | reward 0; matches 8 of 33 hand and 75 of 306 generated reports |
| positional: only the first rule of each query counts, evaluated correctly | score 0; matches 25 of 33 hand and 198 of 306 generated reports |
| the worked example's corrected report replayed for every program (cheat-replay-example) | reward 0; matches none |
| the textbook evaluation, each placeholder a value only it holds (cheat-fresh-all) | reward 0; matches 20 of 33 hand and 173 of 306 generated reports |
| every row some filling returns (cheat-possible) | reward 0; matches 23 of 33 hand and 109 of 306 generated reports |
| the frozen hand answers carried in the file (cheat-forge-hand) | reward 0; passes all 33 hand cases and fails the generated programs it could not have seen |

## Tolerances

There is no numeric tolerance: every printed line is compared as a string.

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| `tests/test.sh:34` a 300 s clock on the whole graded set | `authoring/blank-fill-sure/variants/ok-a` (no pruning at all, per-group enumeration of every combination) and `authoring/blank-fill-sure/variants/ok-b`, both written apart from the reference, and `tests/seal/model.py` | whole graded set of 339 programs: ok-a 34.7 s, ok-b 3.5 s, reference 2.3 s; both variants score 1 in the host trial (40.0 s and 9.1 s with grading). The exact readings the clock exists for, `cheat-slow-no-split` and `cheat-slow-no-fresh`: `cheat-slow-no-split` is killed by the clock in the host trial (worker exit 124 at 300 s) and alone ran 1800 s on one flags program without finishing; `cheat-slow-no-fresh` exhausts the 2048 MB cap in 38 s on the first wide program and fails every wide program with MemoryError (90 s for the whole set under the cap) |
| memory, `task.toml` 2048 MB | the same two variants and `tests/seal/model.py` | peak on the three wide and three flags programs under a 2048 MB address-space cap: ok-a 74 MB, ok-b 43 MB, model 50 MB, reference 51 MB; `cheat-slow-no-fresh` exhausts 2048 MB in 38 s on the first wide program |
