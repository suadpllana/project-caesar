We run the sanctions screen over a corporate registry, and it is telling us two things at
once about the same company. The screen is in /app. It reads a register of filings, replays
them into the state the register stands in now, and then works out, company by company,
whether the programme reaches that company through the parties it has named. Each company
gets one record.

/app/screen_reg.py takes register files and prints those records. Put /app/regs/ring.txt
through it. The first company comes back no, two seats of three, with the programme's mark
standing against two of the three directors, so the company is off the list while the same
row says the list picked its board. That is one company on one file, and it is the only
thing anywhere in the tree that tells you something is wrong.

The screen answers one question about a company. It has to answer it the same way every
time, on a register of two companies and on a register of seven. A company belongs on the
list when the parties already on that list can appoint more than half of its directors.
Nothing the list can appoint the board of may be left off it. Nothing the list cannot may
be put on it. Both cost us. A company we miss keeps moving
money, and a company we name wrongly is a customer we apologise to and a regulator we
answer to.

More than one party of the programme's side holds shares in the same company on most of the
registers we grade, and often several do. The files under /app/regs are a handful of the
shapes a register takes. They are not all of them.

How a board is settled is in /app/reg/poll.py and is not in question. Seats are filled one
at a time, and each one goes to whichever hand at the meeting has the largest holding
divided by one more than the number of seats that hand has already taken. A hand holding
nothing takes nothing. An empty seat stays empty. What a hand is worth is the shares it
holds multiplied by the votes those shares carry, added up over every class the company
has issued. Shares a company holds in itself are silent. Shares standing in the name
of a party that holds them for somebody else are voted by the party they are held for,
through as many names as the arrangement runs through, and an arrangement that has been
ended stops counting from the moment it ends.

Records come out in the order the register incorporated the companies. A record carries five
things: the company, then one if it is on the list and zero if it is not, then how many of
its seats the list took, then how many seats it has, then who took each seat in the order
the seats were filled. A seat that went to the list is written with a star, whoever took it.
A seat nobody could take is written with a dash. Every other seat carries the name the
register knows its taker by.

The registers we grade are ordinary ones. Companies hold shares in each other in whichever
direction the filings happened to run, both directions at once included, and a company
incorporated late in a register holds shares in one incorporated early. Parties hold through
nominees, sometimes through a nominee of a nominee, and a nominee sometimes holds for a
company, the company whose own register it stands on included. Companies buy their own
shares back. No seat on any register we grade comes down to two hands on the same average,
so nothing
turns on how you would settle that.

Four files are yours. They are /app/pol/screen.py, /app/pol/voice.py, /app/pol/tally.py and
/app/pol/note.py, and those four paths are the only ones we take out of your container,
which means anything else you touch is not read, and that covers new modules of your own,
helper scripts, edits to the files around them, and whatever you leave lying about in /app;
the rest of the tree goes back to a clean copy of what you were handed before any of this is
measured, and your four have to keep working against that copy, not against a tree you
reshaped around them. Being yours to edit says nothing about whether a file needs changing.
Leave the rest of the screen where it is. How a filing is parsed, what a share class is
worth, which party a holding is voted by, how a board is filled: none of that is what we are
after, and a screen that reads the register differently from the one you were handed is a
different screen, whatever it decides.

The registers under /app/regs are there to be driven, and so is anything you write yourself.
/app/screen_reg.py prints the whole record for every company in every file you hand it. The
arithmetic is integer the whole way and the screen is deterministic. Two runs over one
register agree exactly. We grade on registers you have not seen, built after you have
stopped.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
