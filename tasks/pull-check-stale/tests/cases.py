"""Enumerated programs, one per graded decision plus the side of each fence that must
still work. A failure here names the rule that broke, which a generated program cannot do.

The names group by rule: `ord-` the ordered walk and its stop, `stuck-` a step that has
already run, `cut-` early cutoff, `look-` presence observations, `miss-` and `dead-`
failure and revival, `bare-` reading a produced path with no pull to order it, `out-` the
output observation, `loop-` cycles, `rec-` what a re-run does to the old record, `twin-`
one program not leaning on the one before it.
"""

CASES = {

# --- the ordered walk, and the stop at the first failure ---------------------------

# The walk stops at the read that no longer holds, so the pull after it is never walked
# and `mk` is not brought up to date; the re-run dies before reaching the pull as well.
"ord-stop-short": """
seed g g1
seed f f1
step mk om
op mk read f
op mk emit *
step t ot
op t read g
op t pull mk
op t emit *
round
want t
round
cut g
put f f2
want t
""",

# The first observation is the pull, so walking it runs `mk`, and only then does the
# walk end. The re-run reaches the read that comes after it.
"ord-pull-first": """
seed f f1
seed h h1
step mk om
op mk read f
op mk emit *
step t ot
op t pull mk
op t read h
op t emit *
round
want t
round
put f f2
want t
""",

# The record is walked in the order the run made it. Checking the read before the pull
# would stop on bytes an overwrite has already moved and leave `mk` for the re-run, which
# puts the two run lines the other way round.
"ord-flat-after-pull": """
seed f f1
step mk w
op mk read f
op mk emit *
step t ot
op t pull mk
op t read w
op t emit *
round
want t
round
put w junk
put f f2
want t
""",

# Nothing has moved, so nothing runs.
"ord-nothing-moves": """
seed f f1
seed g g1
step a oa
op a read f
op a emit *
step b ob
op b pull a
op b look g
op b emit *
round
want b
round
want b
want a
""",

# --- a step that has already run this round ----------------------------------------

# `peek` reads a path two steps write. It runs between them, and the second write leaves
# its record behind, so the fourth pull finds a step that has already run and gone stale.
"stuck-second-pull": """
seed a a1
seed b b1
step one shared
op one read a
op one emit *
step two shared
op two read b
op two emit *
step peek op.peek
op peek read shared
op peek emit *
step drive op.drive
op drive pull one
op drive pull peek
op drive pull two
op drive pull peek
op drive emit *
round
want drive
""",

# The same shape with the edit coming from outside the engine instead of from a step.
"stuck-edit-midround": """
seed f f1
step a oa
op a read f
op a emit *
round
want a
want a
put f f2
want a
""",

# The must-still-work side: `a` was only checked before the edit, never run, so it runs.
"stuck-only-checked": """
seed f f1
step a oa
op a read f
op a emit *
round
want a
round
want a
put f f2
want a
""",

# `rd` is checked sound, then `mk2` writes the path it read, then it is pulled again. It
# has not run this round, so it runs.
"stuck-checked-then-undone": """
seed w0 x1
seed b b1
seed spare s0
step rd ord
op rd read w0
op rd emit *
step mk2 w0
op mk2 read b
op mk2 emit *
step drive od
op drive pull rd
op drive pull mk2
op drive pull rd
op drive emit *
round
want rd
round
put spare s9
want drive
""",

# A stuck raised under a running step cuts that run short and leaves it as if it had never
# run, so the next round runs it again.
"stuck-inside-run": """
seed f f1
step a oa
op a read f
op a emit *
step outer oo
op outer pull a
op outer emit *
round
want a
put f f2
want outer
round
want outer
""",

# --- early cutoff -------------------------------------------------------------------

# `p` re-runs and emits the word it emitted before, so `u` is left alone.
"cut-value-holds": """
seed f f1
step p op
op p read f
op p emit fixed
step u ou
op u pull p
op u emit *
round
want u
round
put f f2
want u
""",

# The same shape with a value that does move.
"cut-value-moves": """
seed f f1
step p op
op p read f
op p emit *
step u ou
op u pull p
op u emit *
round
want u
round
put f f2
want u
""",

# --- looks --------------------------------------------------------------------------

# A look observes presence, so rewriting the bytes at that path disturbs nothing.
"look-content-quiet": """
seed f f1
seed s s1
step t ot
op t look f
op t read s
op t emit *
round
want t
round
put f f9
want t
""",

# The path the look did not find arrives.
"look-appear": """
seed s s1
step t ot
op t look ghost
op t read s
op t emit *
round
want t
round
put ghost g1
want t
""",

# The path the look found goes away.
"look-vanish": """
seed f f1
seed s s1
step t ot
op t look f
op t read s
op t emit *
round
want t
round
cut f
want t
""",

# --- dying, staying dead, coming back -------------------------------------------------

"miss-dies": """
seed s s1
step t ot
op t read s
op t read ghost
op t emit *
round
want t
""",

# The dead step is pulled twice in one round and runs once.
"miss-cached-in-round": """
step d od
op d read ghost
op d emit k
step u1 ou1
op u1 pull d
op u1 emit *
step u2 ou2
op u2 pull d
op u2 emit *
round
want u1
want u2
""",

# The absence it died on is what stops holding, so the step comes back to life.
"miss-revives": """
step d od
op d read ghost
op d emit k
step u ou
op u pull d
op u emit *
round
want u
round
put ghost g1
want u
""",

# A pull of a dead step names the step it pulled, not the reason underneath.
"dead-via-name": """
step d od
op d read ghost
op d emit k
step m om
op m pull d
op m emit *
step t ot
op t pull m
op t emit *
round
want t
""",

# The dead observation holds whatever the step died of, so `u` is left alone even though
# `b` re-runs and dies of something else.
"dead-reason-changes": """
seed s s1
step b ob
op b read gb
op b read ga
op b emit kb
step u ou
op u pull b
op u emit *
round
want u
round
put gb z1
want u
""",

# --- reading a produced path with no pull to order it ---------------------------------

# `rd` reads the path `mk` writes without pulling it, so it sees what was left there last
# round; `mk` is brought up to date only when `drive` pulls it, after `rd` has run.
"bare-stale": """
seed f f1
step mk w
op mk read f
op mk emit *
step rd ord
op rd read w
op rd emit *
step drive od
op drive pull rd
op drive pull mk
op drive emit *
round
want mk
round
put f f2
want drive
""",

# The pull comes first, so the read sees this round's bytes.
"bare-fresh": """
seed f f1
step mk w
op mk read f
op mk emit *
step rd ord
op rd pull mk
op rd read w
op rd emit *
round
want rd
round
put f f2
want rd
""",

# --- the output a run wrote ------------------------------------------------------------

"out-clobber": """
seed f f1
step t ot
op t read f
op t emit *
round
want t
round
put ot junk
want t
""",

# The must-still-work side: the write puts back the bytes that were already there.
"out-same-quiet": """
seed f f1
step t ot
op t read f
op t emit kk
round
want t
round
put ot kk
want t
""",

# --- cycles ------------------------------------------------------------------------

# The chain runs from where the repeated step first appears on the stack, not from the
# step the request named.
"loop-inner": """
seed s s1
step p op
op p pull q
op p emit *
step q oq
op q pull r
op q emit *
step r orr
op r pull q
op r emit *
step lead olead
op lead read s
op lead pull p
op lead emit *
round
want lead
""",

"loop-self": """
seed f f1
step z oz
op z pull z
op z emit *
round
want z
""",

# A run cut short by a loop leaves nothing behind, so the next round runs it again, and
# the request that follows in the same round is unaffected.
"loop-leaves-nothing": """
seed f f1
step a oa
op a look f
op a pull b
op a emit *
step b ob
op b pull a
op b emit *
step solo os
op solo read f
op solo emit *
round
want a
want solo
round
want a
""",

# --- what a re-run does to the old record ---------------------------------------------

# Round two leaves a one-observation record. In round three only `f` moves, and `f` is not
# in that record any more, so the dead step is not disturbed.
"rec-replaced": """
seed g g1
seed f f1
step t ot
op t read g
op t read f
op t emit *
round
want t
round
cut g
want t
round
put f f2
want t
""",

# A run that dies writes nothing, so the path it would have written is still not there for
# anyone reading it.
"dead-writes-nothing": """
step d od
op d read ghost
op d emit k
step r orr
op r read od
op r emit *
round
want d
want r
""",

# `pre` finished before the loop cut the run that pulled it, so it stands: asking for it
# afterwards in the same round runs nothing.
"loop-keeps-finished": """
seed f f1
step pre op
op pre read f
op pre emit *
step a oa
op a pull pre
op a pull b
op a emit *
step b ob
op b pull a
op b emit *
round
want a
want pre
""",

# --- values ----------------------------------------------------------------------------

# The value of `emit *` takes what the pulls returned as well as what the reads found.
"emit-mix-pulls": """
seed f f1
step p op
op p read f
op p emit pv
step t ot
op t pull p
op t read f
op t emit *
round
want t
""",

# --- one program does not lean on the one before it -------------------------------------

"twin-a": """
seed f f1
step t ot
op t read f
op t emit *
round
want t
""",

"twin-b": """
seed f f2
step t ot
op t read f
op t emit *
round
want t
""",

# --- a small diamond, the shape the scale family grows ------------------------------------

"diamond-small": """
seed f0 a1
step a0 oa0
op a0 pull b0
op a0 pull c0
op a0 emit *
step b0 ob0
op b0 pull a1
op b0 emit *
step c0 oc0
op c0 pull a1
op c0 emit *
step a1 oa1
op a1 pull b1
op a1 pull c1
op a1 emit *
step b1 ob1
op b1 pull a2
op b1 emit *
step c1 oc1
op c1 pull a2
op c1 emit *
step a2 oa2
op a2 read f0
op a2 emit *
round
want a0
round
want a0
round
put f0 a2
want a0
""",
}

ORDER = sorted(CASES)


def prog(name):
    return CASES[name].strip("\n")


def programs():
    return [(name, prog(name)) for name in ORDER]
