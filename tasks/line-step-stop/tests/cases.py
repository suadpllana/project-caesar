"""The frozen graded sessions, by name, and what each one pins.

The sessions themselves (image, tape, script, expected lines) are sealed in
tests/seal/gt.json; this table is what a reader of the verifier needs to see which
behaviour each one exists to check. judge.py refuses to grade if the names here and in
gt.json ever disagree.
"""

# The four sessions shipped in /app/samples, graded with the rest.
SAMPLES = {
    'sample-calls': 'shipped sample: ordinary calls, loops and breakpoints; the brief quotes its first six lines',
    'sample-inline': 'shipped sample: nested inlined calls, call sites and reveals',
    'sample-long': 'shipped sample: loops crossed inside one row, as heavy as the heaviest frozen session',
    'sample-rows': 'shipped sample: non-statement rows of the next line, split lines, calls in them',
}

# One per wrong reading of the stop rules: under that reading, and only reading it
# the other way, the session prints a different line. Keyed by the reading's name.
CASES = {
    'break-every-row': 'separates the reading that a breakpoint gets every statement row of its line',
    'break-ns-rows': 'separates the reading that non-statement rows are breakpoint locations too',
    'break-per-function': 'separates the reading that a breakpoint gets one location per function, ignoring inline instances',
    'call-return-always-judged': 'separates the reading that a call stepped over always counts as arriving part-way into its row',
    'call-return-unjudged': 'separates the reading that a call stepped over never counts as passing into another row',
    'cont-rechecks': 'separates the reading that cont stops again at once when it starts on a location',
    'entry-always-in': 'separates the reading that an instance entry is always stepped into (step) or over (next), whatever its call line',
    'entry-never-in': 'separates the reading that an instance entry always stops at the call site with everything hidden',
    'finish-real': 'separates the reading that finish from an inlined frame runs until the real frame returns',
    'finish-shows-all': 'separates the reading that finish leaves the instances starting where it lands visible',
    'hidden-shows-pc-line': 'separates the reading that a visible scope above a hidden instance shows the line at the pc, not the call line',
    'hit-hides': 'separates the reading that a hit hides the instances starting at its address, like a step stop',
    'inrow-call-unplanted': 'separates the reading that a call whose target lies inside the current row needs no planted address',
    'leave-takes-call-line': 'separates the reading that leaving an inlined instance makes its call line the line being stepped',
    'never-hide': 'separates the reading that inline frames are read off the program counter and never hidden',
    'next-reveals': 'separates the reading that next at a call site reveals the hidden instance like step',
    'no-adopt': 'separates the reading that a part-way landing keeps the line being stepped',
    'ns-adopts': 'separates the reading that a non-statement row start makes its line the line being stepped',
    'ns-stops': 'separates the reading that a non-statement row start of another line stops the step',
    'ret-address': 'separates the reading that caller frames are shown at the return address instead of the call instruction',
    'ret-unplanted': 'separates the reading that a row that returns needs no planted return address',
    'return-keeps-line': "separates the reading that after the stepping frame returns, a part-way landing keeps the callee's line",
    'reveal-all': 'separates the reading that step at a call site reveals every hidden instance at once',
    'rowless-stops': 'separates the reading that step stops at the entry of a function that has no lines',
    'run-skips-entry': 'separates the reading that run does not stop on a location at the first address',
    'same-line-stops': 'separates the reading that any statement row start stops, even of the line being stepped',
    'step-callee-shows-all': 'separates the reading that stepping into a function leaves the instances starting at its entry visible',
    'trust-first-hit': 'separates the reading that a planted return address or instance exit is trusted on its first hit, at any depth',
    'zero-stops': 'separates the reading that a line-0 statement row start stops the step',
}

# Ordinary sessions - no inlining, no special rows - that an engine which hides,
# reveals or stops more than the rules say prints wrongly.
FENCES = {
    'fence-0': 'ordinary calls and loops, 12 commands',
    'fence-1': 'ordinary calls and loops, 8 commands',
    'fence-2': 'ordinary calls and loops, 8 commands',
    'fence-3': 'ordinary calls and loops, 9 commands',
    'fence-4': 'ordinary calls and loops, 8 commands',
    'fence-5': 'ordinary calls and loops, 11 commands',
}

# Loops of up to 700,000 iterations crossed by single commands, in one row, in called
# functions and in inlined instances: what the stated limit is measured on.
HEAVY = {
    'heavy-00': '13104853 instructions, 13104849 of them inside a stepping frame',
    'heavy-01': '4848888 instructions, 3459797 of them inside a stepping frame',
    'heavy-02': '10612322 instructions, 3988303 of them inside a stepping frame',
    'heavy-03': '7679613 instructions, 5694689 of them inside a stepping frame',
    'heavy-04': '4486551 instructions, 3231829 of them inside a stepping frame',
    'heavy-05': '4773600 instructions, 4073348 of them inside a stepping frame',
    'heavy-06': '6925803 instructions, 6082459 of them inside a stepping frame',
    'heavy-07': '4246866 instructions, 4246844 of them inside a stepping frame',
    'heavy-08': '5456409 instructions, 5456403 of them inside a stepping frame',
    'heavy-09': '7247509 instructions, 3026545 of them inside a stepping frame',
    'heavy-10': '5208600 instructions, 5208587 of them inside a stepping frame',
    'heavy-11': '8399629 instructions, 4446119 of them inside a stepping frame',
    'heavy-12': '3254584 instructions, 3254555 of them inside a stepping frame',
    'heavy-13': '6057882 instructions, 4790960 of them inside a stepping frame',
    'heavy-14': '9109283 instructions, 9109183 of them inside a stepping frame',
    'heavy-15': '3015665 instructions, 3015635 of them inside a stepping frame',
    'heavy-16': '6464572 instructions, 6464562 of them inside a stepping frame',
    'heavy-17': '11935893 instructions, 3488087 of them inside a stepping frame',
    'heavy-18': '5084647 instructions, 5084632 of them inside a stepping frame',
    'heavy-19': '6622913 instructions, 6622897 of them inside a stepping frame',
    'heavy-20': '6494726 instructions, 5643154 of them inside a stepping frame',
    'heavy-21': '6868690 instructions, 3603378 of them inside a stepping frame',
    'heavy-22': '3347337 instructions, 3347315 of them inside a stepping frame',
    'heavy-23': '3500848 instructions, 3500836 of them inside a stepping frame',
}
