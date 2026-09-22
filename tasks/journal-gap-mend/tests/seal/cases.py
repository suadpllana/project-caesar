"""Hand journals, one per graded decision plus the ordinary side of each fence.

Root-only (tests/seal is 0700 before any submitted code runs). Every journal here
was found by search over small generated journals, not written from memory; the
comment above each says what it pins. Frozen answers are in gt.json.
"""

JOURNALS = {}

# the brief's worked example: a restored entry, then two candidates in text order
JOURNALS['small'] = """\
cfg 1 2 3
acq 0 0 grant
rel 0 0 free
gap
aud 2 4 1 0 92e4c90eb2d3
back
beat 0
aud 2 4 1 1 92e4c90eb2d3
"""

# only a session holding a lock can send the heartbeat the totals count
JOURNALS['beat-needs-lock'] = """\
cfg 1 4 3
acq 0 0 grant
rel 0 0 free
acq 0 1 grant
gap
aud 2 2 1 1 acb80112efcf
back
beat 1
acq 0 2 wait
aud 2 3 1 2 2f1ff8c3e53c
"""

# a candidate is an entry some complete account holds, not any request the table accepts
JOURNALS['live-candidates'] = """\
cfg 2 3 3
acq 0 2 grant
acq 1 1 grant
gap
aud 2 4 0 0 2697654ec57c
back
acq 1 0 wait
aud 2 5 0 0 7f2bcef64ed7
"""

# a digest sits right after the grant that triggers it, which forces the release before it
JOURNALS['digest-anchored'] = """\
cfg 3 2 2
acq 0 0 grant
beat 0
gap
dig 2 26bc32a8ff82
back
acq 1 1 grant
rel 1 1 free
aud 3 3 2 1 b920d82cb9fc
"""

# only an entry that raises the grant total to a multiple of K writes a digest
JOURNALS['digest-on-grant'] = """\
cfg 1 3 3
acq 0 1 grant
rel 0 1 free
gap
dig 3 6b86b273ff34
back
acq 0 0 wait
aud 3 4 2 0 fea1d7ff7365
"""

# a span with no markers of its own, settled by a digest after it (also the shipped plan)
JOURNALS['later-evidence'] = """\
cfg 3 2 3
acq 2 0 grant
beat 0
gap
back
acq 1 0 grant
rel 1 0 free
acq 0 0 grant
dig 3 26bc32a8ff82
aud 3 3 2 1 b920d82cb9fc
"""

# a pass hands the lock to the first session in its queue
JOURNALS['pass-first-waiter'] = """\
cfg 1 4 3
acq 0 0 grant
aud 1 1 0 0 798af9f668bf
acq 0 2 wait
aud 1 2 0 0 f1900605d633
rel 0 0 pass
acq 0 1 wait
acq 0 3 wait
acq 0 0 wait
gap
dig 3 6b86b273ff34
aud 3 5 2 0 61eae9422c3f
back
rel 0 1 pass
aud 4 5 3 0 1c44c16b24e0
"""

# three lost requests whose order only the queues in the final audit fix
JOURNALS['queue-order'] = """\
cfg 3 3 3
acq 2 1 grant
gap
back
acq 2 0 wait
aud 2 5 0 0 cdbd2410815c
"""

# a reentry deepens the lock, which the audit's whole-table fingerprint shows
JOURNALS['reentry-depth'] = """\
cfg 1 2 2
acq 0 1 grant
beat 1
acq 0 0 wait
beat 1
gap
aud 1 3 0 2 afe33a9e346d
back
acq 0 1 again
aud 1 4 0 2 c0e364e71ae5
"""

# one account ends the first span where another adds a release: the dash is a candidate
JOURNALS['end-of-span'] = """\
cfg 3 3 3
acq 1 1 grant
aud 1 1 0 0 371206488273
beat 1
gap
back
acq 2 0 grant
gap
aud 2 2 2 1 3ce7d894f784
back
acq 2 2 grant
dig 3 649489c96db5
aud 3 3 2 1 c69762e3977e
"""

# a pass counts as a grant and writes the digest right after the release
JOURNALS['pass-is-grant'] = """\
cfg 2 2 2
acq 1 0 grant
acq 1 1 wait
gap
aud 1 2 0 1 6018808dce80
back
beat 0
rel 1 0 pass
dig 2 416c970e7550
aud 2 2 1 2 ac7abaaa9962
acq 0 1 grant
beat 1
aud 3 3 1 3 b5e2519463ae
"""

# one heartbeat either span may hold: the second span inherits every table the first leaves
JOURNALS['two-spans-one-beat'] = """\
cfg 1 4 3
acq 0 0 grant
gap
back
acq 0 0 grant
gap
back
acq 0 0 grant
dig 3 5feceb66ffc8
aud 3 3 2 1 798af9f668bf
"""

# only the final audit shows the first span held nothing
JOURNALS['empty-then-grant'] = """\
cfg 2 4 3
acq 1 0 grant
acq 0 1 grant
gap
back
rel 0 1 free
gap
dig 3 b0e4f9bb7b55
back
rel 1 0 free
rel 0 1 free
aud 3 3 3 0 f0b6737b73fa
"""

# a waiting session sends nothing, which orders the two lost requests
JOURNALS['waiter-silent'] = """\
cfg 2 2 2
acq 1 1 grant
gap
dig 2 83b97b859aa5
aud 2 3 0 0 ca1aecdafc16
back
acq 0 1 wait
aud 2 4 0 0 ded6a3318fdb
"""

# an audit listed inside a span was taken before its first lost entry
JOURNALS['audit-before-loss'] = """\
cfg 2 3 2
acq 0 0 grant
rel 0 0 free
gap
aud 1 1 1 0 f0b6737b73fa
dig 2 044bc233cf50
back
acq 0 2 grant
beat 2
acq 1 2 wait
acq 0 0 wait
acq 1 1 wait
aud 3 6 1 1 acd14d5601c9
"""

# two audits inside one span, each standing where its totals fit
JOURNALS['audits-inside'] = """\
cfg 2 3 3
acq 0 1 grant
rel 0 1 free
gap
dig 3 044bc233cf50
aud 3 3 2 0 b23ed3d1539b
aud 4 4 2 0 d989a2909c09
back
rel 1 0 free
aud 4 4 3 0 5384a078621f
"""

# a digest right after the surviving entry that triggered it, then the span
JOURNALS['digest-before-gap'] = """\
cfg 2 3 2
acq 0 1 grant
acq 1 0 grant
dig 2 b0e4f9bb7b55
gap
back
acq 0 0 wait
aud 2 5 0 0 0a9fed251803
"""

# two spans every account leaves empty: the header alone, for each
JOURNALS['both-empty'] = """\
cfg 2 2 3
acq 0 1 grant
gap
back
acq 1 0 grant
gap
back
acq 0 0 wait
acq 1 1 wait
aud 2 4 0 0 889de78585d7
"""

# accounts part at the very first entry of the span
JOURNALS['choices-first'] = """\
cfg 2 2 3
acq 1 0 grant
gap
back
acq 1 0 again
aud 2 4 0 2 bcaee0a87a5a
"""

# the end of a span as a candidate, sorted before every entry
JOURNALS['dash-first'] = """\
cfg 2 3 2
acq 1 0 grant
gap
back
acq 1 0 again
gap
back
rel 1 0 keep
aud 1 4 2 0 f56131a8338b
"""

# an entry every account agrees on, then a choice
JOURNALS['restored-then-choice'] = """\
cfg 1 2 3
acq 0 0 grant
gap
aud 1 4 1 0 ecfc2875abf3
back
beat 0
aud 1 4 1 1 ecfc2875abf3
"""

# an entry every account agrees on, then a choice that includes the end
JOURNALS['restored-then-dash'] = """\
cfg 2 3 3
acq 1 2 grant
gap
back
beat 1
gap
back
acq 1 1 wait
aud 2 5 0 1 c12daa42ff7e
"""

# candidates of three kinds, sorted as text
JOURNALS['kinds-in-order'] = """\
cfg 3 2 3
acq 0 1 grant
gap
back
acq 0 0 again
aud 2 4 1 1 97ce49245634
"""

# spans numbered from 1: one restored, one empty, one restored
JOURNALS['three-spans'] = """\
cfg 1 3 3
acq 0 1 grant
gap
back
acq 0 0 grant
gap
back
acq 0 2 wait
gap
back
beat 0
aud 2 4 1 1 df21d539b072
"""

ORDER = tuple(JOURNALS)


def text(name):
    return JOURNALS[name]
