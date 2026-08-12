We run a post-training loop with a rollout worker that stays up across a batch of
episodes, and the sequences it hands the trainer do not match the policy that produced
them. The worker is in /app. An episode is a conversation. An operator question goes in,
the policy samples a reply token by token, a tool result comes back and is appended to
the conversation, the policy replies again, and at some point the episode ends and the
whole thing goes over. What goes over is the token sequence of the rendered conversation,
together with the run of positions inside that sequence each surviving reply is
answerable for. Two things about it are wrong. The positions are wrong on a fraction of
the replies, and the tokenizer is costing us more than the network is.

/app/run_rollout.py runs the short version: a question, a reply, one tool result, a
second reply. The sampler produced 178, 34, 183, 44, 3 for the first reply. The finished
sequence carries 178, 34, 183, 44, 67 across those same five positions. Token 3 is the
character that closes a block. Token 67 is that character glued to the one that opens the
tool block, which is what the tokenizer makes of the pair once a tool result sits behind
the reply. So the last of those five positions holds a symbol no sampler ever emitted, and a
gradient goes through it. That token is not ours. The bill is the other half of it: the
same run hands the tokenizer 246 characters for a conversation of 135, because every turn
goes back to the first character of the render, and on the episodes we care about, the
ones that run for twenty turns against a tool that answers in paragraphs, that arithmetic
is most of what the worker spends its afternoon doing.

Some ground rules, because a few of them are not what you would do elsewhere.

The sequence we send has to be what the template's render of the finished conversation
encodes to, character for character.

A reply owns the run of positions that begins where it began generating and stops at the
first position where the finished sequence stops agreeing with the sequence the sampler
ran against, which is the prompt it was handed followed by what it put out. Where those
two agree the whole way, every position the reply generated is trainable, the one that
closed it included. Where they part company early, the rest of that reply goes, however
many positions that turns out to be. Both halves are measured. Keeping a position the
policy did not choose is wrong. Dropping one it did choose is wrong too. A reply still
standing in the conversation keeps its place in the list even when the count comes out at
nothing. Its run then starts and ends where it began generating.

A reply that a retry threw away is not in the conversation any longer, and it goes out of
that list with it. A retry here drops the last reply, drops whatever the tool sent back
after it, and puts a note in their place. That is all it does.

The tokenizer is metered. It takes a string and counts the characters that go into the
merge loop, and one render is one call. The way to spend less is to hand it less. Handing
it the same characters a second time to check the first answer costs exactly what never
caching anything costs, so that route is closed. You may pick an encode up again only at a
position that is a token boundary whatever text sits either side of it. Working out which
positions those are is the job. Every id you hand back comes out of /app/tok. The worker
checks that before it uses one, and a sequence goes through only when it is a prefix of a
sequence already accepted followed by exactly what the tokenizer returned this time, so an
encoder of your own built off the same table and run alongside the meter buys you nothing,
and the tokens the sampler emitted are not an encode of anything either. The tokenizer
notes down what it was actually given and what it gave back, every call, and after the run
the bill is added up again off those notes, against the renders we already know the worker
had to encode. Counters are cheap. A number that disagrees with the notes is the number we
drop. The floor under the count is what the cheapest legal resume
costs. Above it the count has a ceiling, and there is room in between, so we are not going
to split hairs over the very last protected position; walking back only as far as the
nearest character the table takes no interest in at all leaves you over the ceiling, and
going back to the first character of the render leaves you nowhere near it. The network is
on the same meter, so a reply that gets walked twice shows up there.

Leave the rest of the worker's behaviour where it is. Which episode does what and when,
the order the loop opens and finishes them in, what the sampler picks: none of that is
what we are after, and a run whose lifecycle comes out different from the worker you were
handed, in what it raises or in the order it raises it, is a different worker.

Four files are yours. They are /app/tok/inc.py, /app/tok/store.py, /app/loop/ep.py and
/app/loop/rec.py, and those four paths are the only ones we take out of your container,
which means that anything else you touch is not read, and that covers new modules of your
own, helper scripts, edits to the files around them, whatever you leave lying about in
/app; the rest of the tree goes back to a clean copy of what you started with before any
of this is measured, and your four have to keep working against that copy, not against a
tree you reshaped around them.

/app/run_rollout.py takes a scenario file as its argument and prints what the worker did
with it, so put whatever sequences of questions, replies, tool results and retries you
like through it. The arithmetic is integer the whole way and the worker is deterministic.
Two runs of one scenario agree exactly.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
