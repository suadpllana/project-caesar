Provisioning a compute sled takes about two minutes. It ought to take seconds.
That is the entire complaint. I have left it alone for a year because nothing
is broken, exactly. Rails land on the settings they were asked for, they always
have, and no part has ever latched a fault out in the field.

Everything you need to change is in `/app/src/driver.c`. The part underneath it
is documented in `/app/README.md`: register map, what settling costs, the frame
the bus can stage, and every refusal the silicon makes. Read it before you read
the driver. `/app/src/sandbox.c` is a bench model of the same part. Run
`make sandbox` in `/app` and the `/app/sandbox` binary it produces drives one
batch through whatever the driver does today, printing each transaction as it
goes.

## How the work arrives

Work comes down from the rack controller in batches. Each one is a flat list of
settings, ordered the way our config layer emitted them. That layer thinks in
whole rails rather than in changes, so it restates a lot that is already true.
One call to `sled_apply()` per batch. `sled_open()` runs first, exactly once,
and is told how many rails this part carries. Both prototypes are in
`/app/include/sled.h`, next to the addresses and the three bus entry points.

By the time `sled_apply()` hands control back, each register named anywhere in
the batch must hold whatever that batch said about it last. How it got there is
nobody's business. Name a rail's voltage three times and you have made a single
promise, about the third one. Registers the batch is silent on stay exactly
where they are. Nothing between one return and the next call is looked at.

## What provisioning costs

Here is what actually matters. This control bus is slow and the sequencing
logic borrows it, so the price of provisioning is a transaction count and
nothing else. `sled_bus_write()` and `sled_bus_read()` bill one apiece —
including the ones that shift the mode, and every look at the status register.
`sled_bus_burst()` bills two. Grading adds up everything an apply path spends
over a full session and weighs it against a ceiling.

I cannot give you the ceiling as a figure, because there is not one. It gets
derived at grading time, from what a competently built apply path spends on the
identical sessions. Landing above it costs you the run, exactly as badly as
parking a rail at the wrong voltage would. I will tell you that the thing which
shipped is nowhere near it and that the gap is not one saving, and leave the
datasheet to say the rest.

The opposite error is caught just as firmly. Where a batch leaves a rail
switched off, it had better be off when you return. Where a batch brings one
up, it had better be up. Ignoring the enable bank altogether fails as hard as
flapping it does. A batch holding nothing is a real batch. A part with exactly
one rail is a real part.

## What you can count on

Out of reset each rail reads voltage 50 and limit 90 and is switched on, with
the part settled and outside program mode. No other master on the sled goes
near it mid-session. You will never be handed a batch whose final word puts a
live rail's limit beneath its voltage. You will be handed batches that leave a
rail switched off and pinned beneath its limit — that is how the rack parks a
domain it has taken out of service — and such a rail is always brought back
limit first. A batch that walks a live rail downwards asks for it the safe way
round, and a batch that raises one asks for that the safe way round too, which
is why applying a batch exactly as it arrives has never faulted.

## How you're graded

Forty-five fixed sessions across one to eight rails. Twelve more short ones,
generated from a seed drawn as the run begins. Then eight long sessions, twenty
rails apiece, ten batches each. For the fixed and generated sessions the
questions are only whether the rails finished where the batch said and whether
the part ever refused anything. The long ones ask both of those and then weigh
the transaction total against the ceiling. A separate pass then repeats the lot
on a seed of its own.

`/app/include/sled.h`, `/app/src/sandbox.c` and `/app/Makefile` are off limits;
all three get fingerprinted ahead of the first graded session. `sled_open()`
and `sled_apply()` keep the names and the parameters they have, and nothing you
add belongs outside them.

The thing worth saying about this job is that the code you are replacing is not
wrong. It has never faulted. It has never stranded a rail at the wrong setting.
All it does is spend, and it has been spending for a year while a good few of
us read it and agreed it looked fine.

You have 10800 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
