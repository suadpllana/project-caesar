"""The enumerated programs: one per graded decision, plus the must-still-work side of each fence.

Each program is small enough to trace by hand, and each is named for the rule it pins. Their
correct lines are frozen in seal/gt.json from the sealed model before the grading file was
written; test_outputs.py checks the model still reproduces them before it judges anything.

The schemas reuse a few shapes:

  SHOP     dept <- emp: a deferred noaction key and a deferred min check on pay
  SHOP_IMM the same tables with the check immediate and the key deferrable
  TWO      two deferred keys declared ahead of the check, for declaration order
  a, b, c  small action walks built for the one rule each case pins
"""

SHOP = """
table dept k size
table emp k dept pay
check pay_min emp pay min 1 deferrable deferred
fk emp_dept emp dept dept noaction deferrable deferred
row dept 1 5
row dept 2 3
row emp 10 1 4
row emp 11 1 6
row emp 12 2 2
"""

SHOP_IMM = """
table dept k size
table emp k dept pay
check pay_min emp pay min 1
fk emp_dept emp dept dept noaction deferrable
row dept 1 5
row dept 2 3
row emp 10 1 4
row emp 11 1 6
row emp 12 2 2
"""

TWO = """
table dept k size
table site k cap
table emp k dept site pay
fk emp_site emp site site noaction deferrable deferred
fk emp_dept emp dept dept noaction deferrable deferred
check pay_min emp pay min 1 deferrable deferred
row dept 1 5
row dept 2 3
row site 1 9
row site 2 9
row emp 10 1 1 4
row emp 11 1 2 6
row emp 12 2 2 2
"""

PROGRAMS = {
    # --- keys, missing rows and the two check tests -----------------------------------------
    "key-dup": SHOP + """
begin
insert emp 10 1 -
insert emp 13 1 4
rollback
""",
    "miss-noop": SHOP + """
begin
update emp 99 pay 0
delete dept 77
update emp 10 pay 5
commit
""",
    "min-null": SHOP_IMM + """
begin
update emp 10 pay -
insert emp 13 2 -
commit
""",
    "min-floor": SHOP_IMM + """
begin
update emp 10 pay 1
update emp 11 pay 0
rollback
""",
    "notnull-null": """
table a k u
table b k x v
check vnn b v notnull deferrable deferred
fk bx b x a cascade
row a 1 1
row b 5 1 3
begin
update b 5 v -
update b 5 v 2
update b 5 v -
commit
""",

    # --- checks at the write, restrict at the delete, key checks at the end -------------------
    "row-at-write": """
table a k u
table b k x y
table c k z w
fk cz c z b setnull
check znn c z notnull
fk bx b x a cascade
fk cw c w a cascade
row a 1 0
row b 5 1 -
row c 9 5 1
begin
delete a 1
rollback
""",
    "row-final-state": """
table a k u
table b k x y
table c k z w
fk cz c z b setnull
check znn c z notnull deferrable deferred
fk bx b x a cascade
fk cw c w a cascade
row a 1 0
row b 5 1 -
row c 9 5 1
begin
delete a 1
commit
""",
    "restrict-at-once": """
table a k u
table b k x
table c k y z
fk cy c y a restrict
fk bx b x a cascade
fk cz c z b cascade
row a 1 0
row b 5 1
row c 9 1 5
begin
delete a 1
rollback
""",
    "noaction-at-end": """
table a k u
table b k x
table c k y z
fk cy c y a noaction
fk bx b x a cascade
fk cz c z b cascade
row a 1 0
row b 5 1
row c 9 1 5
begin
delete a 1
commit
""",
    "walk-listed-late": """
table a k u
table b k x y
fk bx b x a cascade
fk by b y a restrict
row a 1 0
row a 2 0
row b 7 1 1
row b 8 2 1
begin
delete a 2
delete a 1
commit
""",
    "walk-touch-order": """
table a k u
table b k x
table c k z
check znn c z notnull deferrable deferred
fk bx b x a cascade
fk cz c z b setnull
row a 1 0
row b 5 1
row b 6 1
row c 2 6
row c 9 5
begin
delete a 1
set all immediate
""",
    "walk-depth-first": """
table a k u
table b k x
table c k z w
check znn c z notnull
check wnn c w notnull
fk bx b x a cascade
fk cw c w a setnull
fk cz c z b setnull
row a 1 0
row a 2 0
row b 5 1
row b 6 2
row c 2 6 1
row c 9 5 2
begin
delete a 1
rollback
""",
    "cascade-clears": """
table a k u
table b k x v
check vmin b v min 1 deferrable deferred
fk bx b x a cascade
row a 1 0
row a 2 0
row b 4 1 3
row b 7 2 3
begin
update b 7 v 0
update b 4 v 0
delete a 2
commit
""",
    "walk-decl-order": """
table a k u
table b k x y
check xnn b x notnull
check ynn b y notnull
fk by b y a setnull
fk bx b x a setnull
row a 1 0
row b 4 1 1
begin
delete a 1
rollback
""",
    "action-deferred": """
table a k u
table b k x
table c k y
fk bx b x a cascade deferrable deferred
fk cy c y a setnull deferrable deferred
check yn c y notnull deferrable deferred
row a 1 0
row a 2 0
row b 5 1
row c 7 1
begin
delete a 1
insert b 6 1
set all immediate
rollback
""",
    "imm-key-end": SHOP_IMM + """
begin
insert emp 13 9 4
delete dept 1
update emp 12 dept 5
rollback
begin
delete dept 1
rollback
""",
    "imm-order": """
table a k u
table b k x
table d k z
table e k w
fk dz d z b noaction
fk ew e w a noaction
fk bx b x a cascade
row a 1 0
row b 1 1
row d 5 1
row e 7 1
begin
delete a 1
rollback
""",

    # --- owing: what records, what clears, and what only looks lazily -------------------------
    "lazy-mend": SHOP + """
begin
insert emp 13 7 3
insert dept 7 1
update emp 11 pay 5
commit
""",
    "lazy-own-write": SHOP + """
begin
insert emp 13 7 3
insert dept 7 1
update emp 13 pay 3
commit
""",
    "rewrite-keeps-place": SHOP + """
begin
update emp 10 pay 0
update emp 11 pay 0
update emp 10 dept 2
set pay_min immediate
rollback
""",
    "side-parent": SHOP + """
begin
delete dept 1
insert emp 13 2 3
rollback
""",
    "side-reinsert": SHOP + """
begin
delete dept 1
insert dept 1 9
commit
""",
    "side-holders-moved": SHOP + """
begin
delete dept 1
update emp 10 dept 2
update emp 11 dept 2
commit
""",
    "side-both": SHOP + """
begin
delete dept 1
update emp 10 pay 7
commit
""",
    "deleted-row-clears": SHOP + """
begin
insert emp 13 8 0
delete emp 13
commit
""",
    "check-and-key": SHOP + """
begin
insert emp 13 8 0
insert dept 8 1
update emp 13 pay 2
commit
""",

    # --- the ledger order ------------------------------------------------------------------------
    "order-decl": SHOP + """
begin
insert emp 13 9 5
update emp 12 pay 0
set all immediate
""",
    "order-within": SHOP + """
begin
update emp 12 pay 0
update emp 10 pay 0
set pay_min immediate
""",
    "order-listing": TWO + """
begin
insert emp 13 9 1 5
insert emp 14 1 8 5
insert dept 9 1
insert site 8 1
set all immediate
commit
""",
    "commit-lists": SHOP + """
begin
insert emp 14 8 3
insert emp 13 7 3
insert dept 7 1
insert dept 8 1
commit
""",

    # --- savepoints ---------------------------------------------------------------------------
    "replace-place": SHOP + """
begin
update emp 10 pay 0
update emp 11 pay 0
savepoint a
update emp 10 pay 3
update emp 10 pay 0
rollback to a
set pay_min immediate
""",
    "rewind-lists": SHOP + """
begin
update emp 10 pay 0
update emp 11 pay 0
savepoint a
update emp 10 pay 4
update emp 12 pay 0
insert emp 13 9 2
rollback to a
commit
""",
    "rewind-cleared-back": SHOP + """
begin
insert emp 13 7 3
insert dept 7 1
savepoint a
set all immediate
insert emp 14 8 3
rollback to a
set emp_dept immediate
commit
""",
    "rewind-mode": SHOP + """
begin
savepoint a
set pay_min immediate
update emp 10 pay 0
rollback to a
update emp 10 pay 0
rollback
""",
    "rewind-keeps": SHOP + """
begin
savepoint a
update emp 10 pay 0
rollback to a
update emp 11 pay 0
rollback to a
commit
""",
    "release-drops-later": SHOP + """
begin
savepoint a
savepoint b
update emp 10 pay 0
release a
rollback to b
rollback
""",
    "release-merges": SHOP + """
begin
savepoint a
update emp 10 pay 0
savepoint b
update emp 11 pay 0
release b
rollback to a
commit
""",
    "shadow": SHOP + """
begin
savepoint a
update emp 10 pay 0
savepoint a
update emp 11 pay 0
release a
rollback to a
commit
""",
    "error-unknown": SHOP + """
begin
savepoint a
release b
update emp 10 pay 0
rollback to a
update emp 11 pay 0
commit
""",

    # --- check points and modes ------------------------------------------------------------------
    "failset-atomic": TWO + """
begin
insert emp 14 1 8 5
insert site 8 1
insert emp 13 9 1 5
savepoint a
set all immediate
update emp 10 pay 5
rollback to a
set emp_site immediate
commit
""",
    "set-named-only": SHOP + """
begin
update emp 12 pay 0
insert emp 13 9 5
set emp_dept deferred
insert dept 9 2
set emp_dept immediate
commit
""",
    "set-nondeferrable": SHOP_IMM + """
begin
set pay_min deferred
rollback
begin
set all deferred
update emp 10 pay 0
insert emp 13 7 3
commit
""",
    "set-immediate-nondeferrable": SHOP_IMM + """
begin
set pay_min immediate
update emp 10 pay 5
rollback
begin
set emp_dept deferred
insert emp 13 7 3
set emp_dept immediate
rollback
""",
    "set-all-deferred": SHOP_IMM + """
begin
set all deferred
insert emp 13 7 3
set all immediate
rollback
""",
    "modes-per-txn": SHOP + """
begin
set emp_dept immediate
commit
begin
insert emp 13 7 3
rollback
""",

    # --- the aborted state, commit and rollback ---------------------------------------------------
    "abort-ignored": SHOP_IMM + """
begin
savepoint a
update emp 10 pay 0
savepoint b
update emp 11 pay 5
set emp_dept deferred
release a
rollback to b
rollback to a
update emp 11 pay 5
commit
""",
    "abort-commit": SHOP_IMM + """
begin
insert emp 13 2 4
update emp 10 pay 0
commit
begin
insert emp 13 2 4
commit
""",
    "commit-fail": SHOP + """
begin
insert emp 13 9 4
commit
begin
insert emp 13 2 4
update emp 11 pay 0
rollback
""",
    "rollback-lists": SHOP + """
begin
update emp 11 pay 0
delete dept 2
rollback
begin
delete emp 12
delete dept 2
commit
""",
    "place-ordinary": SHOP + """
begin
insert dept 3 4
insert emp 13 3 2
update emp 10 dept 3
delete emp 11
commit
""",
}

ORDER = list(PROGRAMS)


def prog(name):
    """The program for one enumerated case, as a list of lines."""
    return [ln for ln in PROGRAMS[name].strip().splitlines() if ln.strip()]
