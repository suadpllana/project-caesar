# Instruction trace: line-step-stop

Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Written
by authoring/line-step-stop/write_trace.py, which refuses a quote that is not in
instruction.md. Check with `python tools/tracecheck.py line-step-stop`.

## Graded assertions

| Verifier site | What it grades | Instruction sentence |
|---|---|---|
| `tests/test_outputs.py:21` test_judge_finished | the judge reached a verdict; a crash or an unfinished run is a 0 | "Every line `/app/dbg/sess.py` prints in every session must match ours exactly" |
| `tests/test_outputs.py:26` test_sealed_model_reproduces_frozen_lines | the model re-derives every small frozen session's lines before anything is graded (a guard on the verifier, not on the agent) | "must match ours exactly" |
| `tests/test_outputs.py:31` test_declared_files_present | all three declared files were handed in | "Only those three files are collected" |
| `tests/test_outputs.py:41` test_samples | the four shipped sessions, graded like the rest | "Four of them are the samples, and you have not seen the other 365" |
| `tests/test_outputs.py:46` test_enumerated_cases | one session per wrong reading (rows below) | "Four of them are the samples, and you have not seen the other 365" |
| `tests/test_outputs.py:52` test_plain_fences | ordinary sessions an over-cautious engine gets wrong | "Four of them are the samples, and you have not seen the other 365" |
| `tests/test_outputs.py:58` test_heavy_sessions | long loops crossed by single commands | "Their loops run up to 700,000 times inside one row, inside called functions and inside inlined instances" |
| `tests/test_outputs.py:64` test_generated_sessions | the nonce population, every family, against the sealed model | "Four of them are the samples, and you have not seen the other 365" |
| `tests/test_outputs.py:70` test_whole_set_within_limit | the one clock for the whole graded set | "The debugger has 300 seconds for all of them together, counted from the start of each session to its end" |
| `tests/test_outputs.py:75` test_verdict | every session passed and the clock held | "Every line `/app/dbg/sess.py` prints in every session must match ours exactly" |
| artifact `/app/dbg/marks.py` | only the declared files are collected | "You may change `/app/dbg/marks.py`, `/app/dbg/frames.py` and `/app/dbg/steps.py`" |
| artifact `/app/dbg/frames.py` | only the declared files are collected | "You may change `/app/dbg/marks.py`, `/app/dbg/frames.py` and `/app/dbg/steps.py`" |
| artifact `/app/dbg/steps.py` | only the declared files are collected | "You may change `/app/dbg/marks.py`, `/app/dbg/frames.py` and `/app/dbg/steps.py`" |
| `tests/judge.py:93-111` stage_tree | a pristine tree with the three files laid over it; every other module is the shipped one | "Everything else stays as it is" |
| `tests/probe.py:17-25` the worker | the driver calls resolve, show and Engine; a file that drops one crashes the session | "They must keep `resolve`, `show` and `Engine`, with its `hid` and its `run`, `cont`, `step`, `next` and `finish`, as `/app/dbg/sess.py` uses them" |
| `tests/judge.py:128-143` play: target and worker | target under its own uid with the tape on stdin; debugger as another uid, fresh process per session, read-only tree | "When we grade, each session runs in a fresh process as an unprivileged user, in a copy of `/app` it cannot write, and the debugger has no way to read the tape" |
| `tests/judge.py:45` LIMIT = 300.0 | the wall clock shared by the whole graded set, from each debugger process's start to its end | "The debugger has 300 seconds for all of them together, counted from the start of each session to its end" |
| `tests/judge.py:145-203` the lines pipe | only the lines the driver writes to its pipe are compared; the debugger's own stdout is discarded | "Nothing else the debugger prints is read" |
| `tests/seal/forge.py:594` MAX_ADDRESSES | no graded program is longer | "Their programs have up to 400 addresses" |
| `tests/seal/forge.py` check_image | every image obeys the stated guarantees | "Execution enters an instance only at LO from outside it and leaves only by running from HI to HI+1"; "An instance holds no `ret`"; "Its first address LO starts a statement row whose line is not 0"; "Address HI+1 starts a row"; "Every row carries a line of the innermost function or instance holding its address, or 0" |
| `tests/seal/forge.py` script | commands are issued only where the brief allows | "It comes once, before any `cont`, `step`, `next` or `finish`"; "No script issues `finish` in the outermost frame while its deepest visible scope is its function"; "Every `break` names a line that has a statement row" |
| `tests/seal/model.py:34-38` fn lines | function ranges, source lines, the entry | "An image starts with its functions"; "The program starts at address 0" |
| `tests/seal/model.py:43-51` code lines | one instruction per address | "Each address holds one instruction, written `ADDRESS OP ARGS`" |
| `tests/seal/model.py:160-188` exec1 | the machine: what each instruction does, per-call registers, the end | "`in R` (the next number on the tape)"; "`jnz R A` (jump to A if R is not 0)"; "`call A` (A is the first address of a function)"; "Registers `a` to `d` belong to each call"; "They start at 0"; "ends when a `ret` has no call to return to" |
| `tests/seal/model.py:39-40` row lines | the statement flag | "A trailing `x` marks a row that is not a statement" |
| `tests/seal/model.py:60-77` row coverage | which row holds an address | "A row covers the addresses up to the next row of its function or the end of the function"; "A function declared without lines has no rows" |
| `tests/seal/model.py:79-97` instances | instance records and their nesting | "says addresses LO to HI hold the body of function F inlined into P"; "An instance lies inside its parent and never overlaps a sibling" |
| `tests/seal/model.py:107-109` chain | the scopes of a frame at an address | "at that address the scopes of a frame are its function and then every instance holding the address, outermost first" |
| `tests/seal/model.py:111-112` name | what a scope prints | "An instance prints the name of the function it inlines" |
| `tests/seal/model.py:122-124` line | the deepest scope's line | "the deepest shows the line of the row holding the address, or 0" |
| `tests/seal/model.py:199-208` frames | callers at the call instruction; call lines; hidden scopes | "The innermost frame is read at the program counter and each caller at its return address minus one, its `call`"; "A scope shows the call line of the scope below it"; "The scope above them still shows the call line of the first hidden one" |
| `tests/seal/model.py:212-224` do_break | breakpoint numbering, grouping and order | "The command `break L` numbers breakpoints from 1 and prints `bN` followed by its addresses in ascending order"; "A statement row belongs to the innermost function body or instance holding its address"; "gives the breakpoint one address, the lowest of them" |
| `tests/seal/model.py:190-195` tick | the hit test after every instruction, in every frame, nothing hidden | "A hit happens whenever execution arrives at a breakpoint address, in any frame"; "It ends the command there"; "A stop hides nothing unless a rule below says so" |
| `tests/seal/model.py:228-232` do_run | run stops at once on a breakpoint at address 0 | "except that `run` stops at once when address 0 is a breakpoint" |
| `tests/seal/model.py:234-237` do_cont | cont | "The command `cont` runs until a hit or the end"; "The instruction a command starts at runs without that check" |
| `tests/seal/model.py:244-260` do_finish | finish out of an instance or a function, and what it hides | "When the deepest visible scope of the innermost frame is an instance, `finish` runs until the frame leaves that instance"; "Otherwise it runs until the innermost frame returns"; "It stops where it lands, hiding the instances that start there" |
| `tests/seal/model.py:262-267` do_step setup | the stepping frame, scope and line | "Its deepest visible scope is the stepping scope"; "The line that scope shows is the stepping line" |
| `tests/seal/model.py:268-276` hidden scopes | reveal one level; next over the outermost hidden instance | "`step` makes the outermost hidden one visible and stops without running anything"; "`next` runs until the frame leaves that instance and then judges where it lands" |
| `tests/seal/model.py:283-296` calls | next runs calls; step stops in callees with lines, hiding what starts there | "`next` runs it until it returns"; "`step` stops at the first address of the called function if that function has lines, hiding the instances that start there"; "A call that returns counts as a move from the `call` to its return address" |
| `tests/seal/model.py:297-303` returns | the caller becomes the stepping frame; the stepping line is kept | "When the stepping frame returns, its caller becomes the stepping frame"; "not counting instances that start exactly there, becomes the stepping scope"; "The stepping line is kept and the arrival is judged" |
| `tests/seal/model.py:304-305` row changes | which moves are judged | "Execution arriving in a different row of the stepping frame is judged" |
| `tests/seal/model.py:321-323` leaving the scope | rule 14 | "the enclosing scope that holds the new address becomes the stepping scope first" |
| `tests/seal/model.py:324-337` instance entries | rule 13: into, over or at the call site, by call line | "If the address is the first of instances below the stepping scope, the outermost of them decides"; "when its call line equals the stepping line, `step` stops with it visible and the deeper ones hidden"; "`next` runs until the frame leaves it and then judges where it lands"; "when it does not, both stop there with all of them hidden" |
| `tests/seal/model.py:307-313` over_instance | leaving an instance is judged in the stepping frame only | "`next` runs until the frame leaves it and then judges where it lands" |
| `tests/seal/model.py:338-349` rows | rule 12: statement row starts stop, part-way arrivals adopt, nothing else | "a statement row whose line is not 0 and differs from the stepping line stops the command"; "Part-way into a row, a line that is not 0 becomes the stepping line"; "No other arrival stops them or changes the stepping line" |
| `tests/seal/model.py:131-139` Stop, Ended | the stop kinds and the end | "The kind is `hit` at a breakpoint, `step` at the end of a `step` or `next`, and `done` at the end of a `finish`"; "When the program ends, the command prints `exit` and no command follows" |
| `tests/seal/model.py:352-375` play | one line per command in the stated format | "Every command prints one line"; "Any other stop prints its kind, the program counter and the frames innermost first, each as `NAME:LINE`" |
| `tests/cases.py` case sample-calls | shipped sample: ordinary calls, loops and breakpoints; the brief quotes its first six lines | "The one called `long` is as heavy as the heaviest one we grade" |
| `tests/cases.py` case sample-inline | shipped sample: nested inlined calls, call sites and reveals | "The one called `long` is as heavy as the heaviest one we grade" |
| `tests/cases.py` case sample-long | shipped sample: loops crossed inside one row, as heavy as the heaviest frozen session | "The one called `long` is as heavy as the heaviest one we grade" |
| `tests/cases.py` case sample-rows | shipped sample: non-statement rows of the next line, split lines, calls in them | "The one called `long` is as heavy as the heaviest one we grade" |
| `tests/cases.py` case break-every-row | separates the reading that a breakpoint gets every statement row of its line | "each body or instance with statement rows of line L gives the breakpoint one address, the lowest of them" |
| `tests/cases.py` case break-ns-rows | separates the reading that non-statement rows are breakpoint locations too | "each body or instance with statement rows of line L gives the breakpoint one address" |
| `tests/cases.py` case break-per-function | separates the reading that a breakpoint gets one location per function, ignoring inline instances | "each body or instance with statement rows of line L gives the breakpoint one address, the lowest of them" |
| `tests/cases.py` case call-return-always-judged | separates the reading that a call stepped over always counts as arriving part-way into its row | "A call that returns counts as a move from the `call` to its return address" |
| `tests/cases.py` case call-return-unjudged | separates the reading that a call stepped over never counts as passing into another row | "A call that returns counts as a move from the `call` to its return address" |
| `tests/cases.py` case cont-rechecks | separates the reading that cont stops again at once when it starts on a location | "The instruction a command starts at runs without that check" |
| `tests/cases.py` case entry-always-in | separates the reading that an instance entry is always stepped into (step) or over (next), whatever its call line | "when its call line equals the stepping line, `step` stops with it visible and the deeper ones hidden" |
| `tests/cases.py` case entry-never-in | separates the reading that an instance entry always stops at the call site with everything hidden | "when its call line equals the stepping line, `step` stops with it visible and the deeper ones hidden" |
| `tests/cases.py` case finish-real | separates the reading that finish from an inlined frame runs until the real frame returns | "When the deepest visible scope of the innermost frame is an instance, `finish` runs until the frame leaves that instance" |
| `tests/cases.py` case finish-shows-all | separates the reading that finish leaves the instances starting where it lands visible | "It stops where it lands, hiding the instances that start there" |
| `tests/cases.py` case hidden-shows-pc-line | separates the reading that a visible scope above a hidden instance shows the line at the pc, not the call line | "The scope above them still shows the call line of the first hidden one" |
| `tests/cases.py` case hit-hides | separates the reading that a hit hides the instances starting at its address, like a step stop | "A stop hides nothing unless a rule below says so" |
| `tests/cases.py` case inrow-call-unplanted | separates the reading that a call whose target lies inside the current row needs no planted address | "`step` stops at the first address of the called function if that function has lines" |
| `tests/cases.py` case leave-takes-call-line | separates the reading that leaving an inlined instance makes its call line the line being stepped | "the enclosing scope that holds the new address becomes the stepping scope first" |
| `tests/cases.py` case never-hide | separates the reading that inline frames are read off the program counter and never hidden | "The innermost frame may have its deepest scopes hidden" |
| `tests/cases.py` case next-reveals | separates the reading that next at a call site reveals the hidden instance like step | "`next` runs until the frame leaves that instance and then judges where it lands" |
| `tests/cases.py` case no-adopt | separates the reading that a part-way landing keeps the line being stepped | "Part-way into a row, a line that is not 0 becomes the stepping line" |
| `tests/cases.py` case ns-adopts | separates the reading that a non-statement row start makes its line the line being stepped | "No other arrival stops them or changes the stepping line" |
| `tests/cases.py` case ns-stops | separates the reading that a non-statement row start of another line stops the step | "a statement row whose line is not 0 and differs from the stepping line stops the command" |
| `tests/cases.py` case ret-address | separates the reading that caller frames are shown at the return address instead of the call instruction | "The innermost frame is read at the program counter and each caller at its return address minus one, its `call`" |
| `tests/cases.py` case ret-unplanted | separates the reading that a row that returns needs no planted return address | "When the stepping frame returns, its caller becomes the stepping frame" |
| `tests/cases.py` case return-keeps-line | separates the reading that after the stepping frame returns, a part-way landing keeps the callee's line | "The stepping line is kept and the arrival is judged" |
| `tests/cases.py` case reveal-all | separates the reading that step at a call site reveals every hidden instance at once | "`step` makes the outermost hidden one visible and stops without running anything" |
| `tests/cases.py` case rowless-stops | separates the reading that step stops at the entry of a function that has no lines | "`step` stops at the first address of the called function if that function has lines, hiding the instances that start there, and otherwise runs it until it returns" |
| `tests/cases.py` case run-skips-entry | separates the reading that run does not stop on a location at the first address | "except that `run` stops at once when address 0 is a breakpoint" |
| `tests/cases.py` case same-line-stops | separates the reading that any statement row start stops, even of the line being stepped | "a statement row whose line is not 0 and differs from the stepping line stops the command" |
| `tests/cases.py` case step-callee-shows-all | separates the reading that stepping into a function leaves the instances starting at its entry visible | "`step` stops at the first address of the called function if that function has lines, hiding the instances that start there" |
| `tests/cases.py` case trust-first-hit | separates the reading that a planted return address or instance exit is trusted on its first hit, at any depth | "`next` runs it until it returns" |
| `tests/cases.py` case zero-stops | separates the reading that a line-0 statement row start stops the step | "a statement row whose line is not 0 and differs from the stepping line stops the command" |
| `tests/cases.py` case fence-0 | ordinary calls and loops, 12 commands | "a statement row whose line is not 0 and differs from the stepping line stops the command" |
| `tests/cases.py` case fence-1 | ordinary calls and loops, 8 commands | "a statement row whose line is not 0 and differs from the stepping line stops the command" |
| `tests/cases.py` case fence-2 | ordinary calls and loops, 8 commands | "a statement row whose line is not 0 and differs from the stepping line stops the command" |
| `tests/cases.py` case fence-3 | ordinary calls and loops, 9 commands | "a statement row whose line is not 0 and differs from the stepping line stops the command" |
| `tests/cases.py` case fence-4 | ordinary calls and loops, 8 commands | "a statement row whose line is not 0 and differs from the stepping line stops the command" |
| `tests/cases.py` case fence-5 | ordinary calls and loops, 11 commands | "a statement row whose line is not 0 and differs from the stepping line stops the command" |
| `tests/cases.py` case heavy-00 | 13104853 instructions, 13104849 of them inside a stepping frame | "Their loops run up to 700,000 times inside one row, inside called functions and inside inlined instances" |
| `tests/cases.py` case heavy-01 | 4848888 instructions, 3459797 of them inside a stepping frame | "Their loops run up to 700,000 times inside one row, inside called functions and inside inlined instances" |
| `tests/cases.py` case heavy-02 | 10612322 instructions, 3988303 of them inside a stepping frame | "Their loops run up to 700,000 times inside one row, inside called functions and inside inlined instances" |
| `tests/cases.py` case heavy-03 | 7679613 instructions, 5694689 of them inside a stepping frame | "Their loops run up to 700,000 times inside one row, inside called functions and inside inlined instances" |
| `tests/cases.py` case heavy-04 | 4486551 instructions, 3231829 of them inside a stepping frame | "Their loops run up to 700,000 times inside one row, inside called functions and inside inlined instances" |
| `tests/cases.py` case heavy-05 | 4773600 instructions, 4073348 of them inside a stepping frame | "Their loops run up to 700,000 times inside one row, inside called functions and inside inlined instances" |
| `tests/cases.py` case heavy-06 | 6925803 instructions, 6082459 of them inside a stepping frame | "Their loops run up to 700,000 times inside one row, inside called functions and inside inlined instances" |
| `tests/cases.py` case heavy-07 | 4246866 instructions, 4246844 of them inside a stepping frame | "Their loops run up to 700,000 times inside one row, inside called functions and inside inlined instances" |
| `tests/cases.py` case heavy-08 | 5456409 instructions, 5456403 of them inside a stepping frame | "Their loops run up to 700,000 times inside one row, inside called functions and inside inlined instances" |
| `tests/cases.py` case heavy-09 | 7247509 instructions, 3026545 of them inside a stepping frame | "Their loops run up to 700,000 times inside one row, inside called functions and inside inlined instances" |
| `tests/cases.py` case heavy-10 | 5208600 instructions, 5208587 of them inside a stepping frame | "Their loops run up to 700,000 times inside one row, inside called functions and inside inlined instances" |
| `tests/cases.py` case heavy-11 | 8399629 instructions, 4446119 of them inside a stepping frame | "Their loops run up to 700,000 times inside one row, inside called functions and inside inlined instances" |
| `tests/cases.py` case heavy-12 | 3254584 instructions, 3254555 of them inside a stepping frame | "Their loops run up to 700,000 times inside one row, inside called functions and inside inlined instances" |
| `tests/cases.py` case heavy-13 | 6057882 instructions, 4790960 of them inside a stepping frame | "Their loops run up to 700,000 times inside one row, inside called functions and inside inlined instances" |
| `tests/cases.py` case heavy-14 | 9109283 instructions, 9109183 of them inside a stepping frame | "Their loops run up to 700,000 times inside one row, inside called functions and inside inlined instances" |
| `tests/cases.py` case heavy-15 | 3015665 instructions, 3015635 of them inside a stepping frame | "Their loops run up to 700,000 times inside one row, inside called functions and inside inlined instances" |
| `tests/cases.py` case heavy-16 | 6464572 instructions, 6464562 of them inside a stepping frame | "Their loops run up to 700,000 times inside one row, inside called functions and inside inlined instances" |
| `tests/cases.py` case heavy-17 | 11935893 instructions, 3488087 of them inside a stepping frame | "Their loops run up to 700,000 times inside one row, inside called functions and inside inlined instances" |
| `tests/cases.py` case heavy-18 | 5084647 instructions, 5084632 of them inside a stepping frame | "Their loops run up to 700,000 times inside one row, inside called functions and inside inlined instances" |
| `tests/cases.py` case heavy-19 | 6622913 instructions, 6622897 of them inside a stepping frame | "Their loops run up to 700,000 times inside one row, inside called functions and inside inlined instances" |
| `tests/cases.py` case heavy-20 | 6494726 instructions, 5643154 of them inside a stepping frame | "Their loops run up to 700,000 times inside one row, inside called functions and inside inlined instances" |
| `tests/cases.py` case heavy-21 | 6868690 instructions, 3603378 of them inside a stepping frame | "Their loops run up to 700,000 times inside one row, inside called functions and inside inlined instances" |
| `tests/cases.py` case heavy-22 | 3347337 instructions, 3347315 of them inside a stepping frame | "Their loops run up to 700,000 times inside one row, inside called functions and inside inlined instances" |
| `tests/cases.py` case heavy-23 | 3500848 instructions, 3500836 of them inside a stepping frame | "Their loops run up to 700,000 times inside one row, inside called functions and inside inlined instances" |

## Readings

| Reading | Sentence or published example that rules it out | Case that separates it |
|---|---|---|
| ret-address: caller frames are shown at the return address instead of the call instruction | "The innermost frame is read at the program counter and each caller at its return address minus one, its `call`" | case ret-address |
| no-adopt: a part-way landing keeps the line being stepped | "Part-way into a row, a line that is not 0 becomes the stepping line" | case no-adopt |
| ns-stops: a non-statement row start of another line stops the step | "a statement row whose line is not 0 and differs from the stepping line stops the command" | case ns-stops |
| ns-adopts: a non-statement row start makes its line the line being stepped | "No other arrival stops them or changes the stepping line" | case ns-adopts |
| zero-stops: a line-0 statement row start stops the step | "a statement row whose line is not 0 and differs from the stepping line stops the command" | case zero-stops |
| same-line-stops: any statement row start stops, even of the line being stepped | "a statement row whose line is not 0 and differs from the stepping line stops the command" | case same-line-stops |
| entry-always-in: an instance entry is always stepped into (step) or over (next), whatever its call line | "when its call line equals the stepping line, `step` stops with it visible and the deeper ones hidden" | case entry-always-in |
| entry-never-in: an instance entry always stops at the call site with everything hidden | "when its call line equals the stepping line, `step` stops with it visible and the deeper ones hidden" | case entry-never-in |
| reveal-all: step at a call site reveals every hidden instance at once | "`step` makes the outermost hidden one visible and stops without running anything" | case reveal-all |
| never-hide: inline frames are read off the program counter and never hidden | "The innermost frame may have its deepest scopes hidden" | case never-hide |
| finish-real: finish from an inlined frame runs until the real frame returns | "When the deepest visible scope of the innermost frame is an instance, `finish` runs until the frame leaves that instance" | case finish-real |
| trust-first-hit: a planted return address or instance exit is trusted on its first hit, at any depth | "`next` runs it until it returns" | case trust-first-hit |
| rowless-stops: step stops at the entry of a function that has no lines | "`step` stops at the first address of the called function if that function has lines, hiding the instances that start there, and otherwise runs it until it returns" | case rowless-stops |
| break-per-function: a breakpoint gets one location per function, ignoring inline instances | "each body or instance with statement rows of line L gives the breakpoint one address, the lowest of them" | case break-per-function |
| break-every-row: a breakpoint gets every statement row of its line | "each body or instance with statement rows of line L gives the breakpoint one address, the lowest of them" | case break-every-row |
| break-ns-rows: non-statement rows are breakpoint locations too | "each body or instance with statement rows of line L gives the breakpoint one address" | case break-ns-rows |
| cont-rechecks: cont stops again at once when it starts on a location | "The instruction a command starts at runs without that check" | case cont-rechecks |
| return-keeps-line: after the stepping frame returns, a part-way landing keeps the callee's line | "The stepping line is kept and the arrival is judged" | case return-keeps-line |
| finish-shows-all: finish leaves the instances starting where it lands visible | "It stops where it lands, hiding the instances that start there" | case finish-shows-all |
| hit-hides: a hit hides the instances starting at its address, like a step stop | "A stop hides nothing unless a rule below says so" | case hit-hides |
| call-return-unjudged: a call stepped over never counts as passing into another row | "A call that returns counts as a move from the `call` to its return address" | case call-return-unjudged |
| call-return-always-judged: a call stepped over always counts as arriving part-way into its row | "A call that returns counts as a move from the `call` to its return address" | case call-return-always-judged |
| leave-takes-call-line: leaving an inlined instance makes its call line the line being stepped | "the enclosing scope that holds the new address becomes the stepping scope first" | case leave-takes-call-line |
| next-reveals: next at a call site reveals the hidden instance like step | "`next` runs until the frame leaves that instance and then judges where it lands" | case next-reveals |
| hidden-shows-pc-line: a visible scope above a hidden instance shows the line at the pc, not the call line | "The scope above them still shows the call line of the first hidden one" | case hidden-shows-pc-line |
| run-skips-entry: run does not stop on a location at the first address | "except that `run` stops at once when address 0 is a breakpoint" | case run-skips-entry |
| inrow-call-unplanted: a call whose target lies inside the current row needs no planted address | "`step` stops at the first address of the called function if that function has lines" | case inrow-call-unplanted |
| ret-unplanted: a row that returns needs no planted return address | "When the stepping frame returns, its caller becomes the stepping frame" | case ret-unplanted |
| step-callee-shows-all: stepping into a function leaves the instances starting at its entry visible | "`step` stops at the first address of the called function if that function has lines, hiding the instances that start there" | case step-callee-shows-all |

## Shortcuts

| Strategy | Result |
|---|---|
| the shipped tree unchanged (nop) | reward 0 in the host trial (first failing session: sample-calls); matches 130 of 344 sessions exactly (37.8%) |
| constant: every command prints exit and every breakpoint resolves to nothing | reward 0 in the host trial (first failing session: sample-calls); matches 0 of 344 sessions exactly (0.0%) |
| positional: every breakpoint takes only its first statement row | reward 0 in the host trial (first failing session: sample-inline); matches 191 of 344 sessions exactly (55.5%) |
| positional: every step, next and finish moves exactly one instruction | reward 0 in the host trial (first failing session: sample-calls); matches 61 of 344 sessions exactly (17.7%) |
| positional: a stop prints only the innermost real frame | reward 0 in the host trial (first failing session: sample-calls); matches 135 of 344 sessions exactly (39.2%) |
| the worked example's output replayed for every session | reward 0 in the host trial (first failing session: sample-calls); matches 4 of 344 sessions exactly (1.2%) |
| the previous revision of a correct engine (V2 before its in-row call fix) | reward 0 in the host trial (first failing session: case-inrow-call-unplanted); matches 343 of 344 sessions exactly (99.7%) |

## Tolerances

| Tolerance or limit | Independent implementation | Measured |
|---|---|---|
| 300 seconds for the whole graded set (`tests/judge.py` LIMIT, stated as the debugger's 300 seconds) | `authoring/line-step-stop/variants/v2/steps.py`, a second engine written apart from the reference (plants every decision address of the stepping function) | V2 used 24.3 s (reward 1) and the reference 24.4 s (reward 1) of debugger time for the whole set in the host trial; the exactly correct single-stepping `authoring/line-step-stop/variants/slow/steps.py`: reward 0, stopped by the clock on sample-long after 300 s of debugger time; the half-way `authoring/line-step-stop/variants/half/steps.py`: reward 0, stopped by the clock on sample-long after 300 s of debugger time |
| programs of up to 400 addresses (`tests/seal/forge.py` MAX_ADDRESSES) | `tests/seal/forge.py` rejects any longer program before a session is built; `tests/seal/model.py` parses every graded image | largest program over the 63 frozen sessions and 900 freshly generated ones: 399 addresses |
| loops of up to 700,000 iterations (`authoring/line-step-stop/make_heavy.py` draws heavy counts from 250,000 to 700,000) | `tests/seal/model.py` executes every frozen session one instruction at a time | largest value on any frozen tape: 699958; largest on 900 freshly generated tapes: 3 |
