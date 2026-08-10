A colleague spent two days last month proving a report wrong. The report was right. Our file skipping was broken. Beside every data file we keep a summary. A query reads it and decides whether the file is worth opening. Somebody made the summary cleverer. The skipping got keener, and it began passing over files that did hold matching rows. Wrong answers beat slow ones nowhere, so the feature is switched off until we work out what these summaries actually license.

Write `/app/file_reads.py`.

## The data and what gets recorded about it

Every file holds rows, and a row has twelve fields, `a` through `l`. A field holds a code from 0 to 15 -- they came from a dictionary encoding years ago and nobody has needed the strings since -- or it holds nothing at all, because plenty of rows never had a value to put there.

We do not keep the rows. We keep two things about each file. For a pair of fields, which combinations of their codes turned up together in one row. And for each field, whether any row left it unset. Here is a summary:

```python
{"pairs": {"ab": [1, 0, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
           "cl": [0, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]},
 "unset": ["c", "h"]}
```

The pair key is two field names, in order. The list carries one entry per code of the first field, sixteen of them. Each entry is a bitmask over codes of the second. Bit `j` of entry `i` means a row in that file held `i` in the first field and `j` in the second. So `"ab": [1, 0, 6, ...]` says a row existed with `a=0, b=0`, and rows existed with `a=2, b=1` and `a=2, b=2`, and nothing else involving those two fields. A row only ever counted towards a pair when both of those fields held a code, since a field with nothing in it has no entry to go in and no bit to set.

Pairs are keyed in field order, so `"ab"`, `"ac"`, and on to `"kl"`. Not every pair is recorded. A pair missing from `pairs` means nothing was kept about how those two fields sit together, and any combination of them is possible so far as that file says. A file whose `pairs` is empty says nothing about any of them.

`unset` lists the fields that at least one row in that file left with nothing in them. A field not in that list was filled in on every row of that file. The key can be missing, which is the same as an empty list.

## When a file has to be read

Queries arrive as a tree of dictionaries. At the bottom, `{"op": "<", "col": "a", "value": 3}` tests one field's code against a number, and the operator is any of `<`, `<=`, `>`, `>=`, `=`, `!=`. The number is an ordinary integer and is not promised to be a code. Those get combined by `{"op": "and", "args": [...]}` and by `{"op": "or", "args": [...]}`, each taking two or more of them, and inverted by `{"op": "not", "arg": {...}}`. There is no depth limit on the nesting.

Call a choice a code for each of the twelve fields, except that a field the summary lists under `unset` may be given nothing instead. A file has to be read when there is a choice for which both of these hold:

- every recorded pair agrees with it. Take a pair in `pairs`: if the choice gave both of its fields a code, those two codes have to be a combination that pair recorded. If the choice gave either of them nothing, that pair asks nothing at all of the choice.
- the filter comes out true on it.

A condition on a field the choice gave nothing to comes out neither true nor false. It comes out as a third answer, and that answer travels: `and` is false as soon as an arm is false and true only when every arm is true, `or` is true as soon as an arm is true and false only when every arm is false, and `not` turns true into false and false into true and leaves the third answer as it is. Coming out true is what makes a file worth reading. Neither of the other two answers does.

Both conditions are about one choice, made once, covering all twelve fields together. A choice that satisfies the records need not be a row that ever existed, and a field taken as nothing need not have been empty in the company of anything else the choice picks. The summaries are not that precise. Opening a file we did not have to is only wasted work. Skipping one we did have to read is the bug that took the feature offline.

## What to write

Two things need to exist in `/app/file_reads.py`.

One is `files_to_read(manifest, filter_expr)`. Hand it a list of summaries and a query; it hands back where in that list the files worth opening sit, as integers, ascending.

The other is a class, `Reader`, built from a manifest once. `Reader(manifest).files_to_read(filter_expr)` settles the same question for a query. Every case goes through both, and a disagreement between them is a failure like any other.

## Speed

Summaries get loaded once and queried all day, so there is a run against the clock. Fourteen hundred files, twenty-four queries carrying about a dozen conditions apiece, one `Reader` for all of them, thirty seconds of wall time. The stopwatch sits in another process, not yours, and it starts before the manifest exists. Neither the summaries nor the queries are ones you have seen: both come out of a seed drawn when the run starts.

Being right and being quick are graded apart and you want both. That run puts thirty-three thousand file-and-filter questions, and not one of them is a lookup.

## How you're graded

Everything is asked twice, once down each route. First a few dozen queries against a manifest of tiny files, whose summaries and conditions stay inside four of the twelve fields, where the answer is arrived at by trying every choice there is. Then a few hundred queries against several hundred larger files across all twelve. Then the clock.

The expected answers come from the rules written above and not from anybody else's reader, so the rules are the only thing you can check yourself against.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
