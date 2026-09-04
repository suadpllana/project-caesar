My first plan, written before opening the tree.

The relay charges each arrival twice and hands permit back as an absolute ceiling. So I
keep, per level, the total the level has drained and the total it has been charged. The
ceiling is drained plus the window. I publish it when the raise is at least twenty, and
I publish it below twenty when the producer would otherwise be stuck with less than its
smallest batch of room. An arrival is refused when it would carry either level past its
ceiling. A teardown throws away what is parked and the producer keeps sending for three
more ticks, so I let those through and throw them away too.

What I would have written first, and where it is wrong.

I would have taken the ceiling from what the consumer drew. That is what the shipped code
does and it is what every account of a windowed receiver says. The strand run would have
pushed me off it, because thirty-nine rows go away three times and the fourth feed then
cannot send: the only place that permit can come back from is the discard. So I think I
get that one, though not on the first write.

The one I would have missed is the stuck test. I would have compared the ceiling I am
holding against what the producer has spent, because that is the number in front of me
and it reads like the right one. It is not: the producer is acting on a ceiling from
three ticks ago and those two numbers are only the same while nothing is in flight. I
would not have noticed, because on any stream without a teardown they agree, and my own
harness would have gone green.

Where I got confirmation, and what I had to guess.

Confirmation: the case files run, so I can see the trace change as I edit, and the strand
run tells me plainly that something is being lost. That is a symptom, not a check - it
does not tell me what the right rows are. There is no producer in the tree, so I cannot
run the thing and watch it wedge or not wedge; I would have to write a producer myself,
and writing one correctly is the same problem as the stuck test.

Guesses: whether a refused arrival counts as activity for the idle fallback, whether a
draw against a torn-down feed does anything, whether the link's totals restart when a
feed is reopened, and whether the smallest-batch test is about the ceiling I hold or the
one the producer knows about. Four coin flips.
