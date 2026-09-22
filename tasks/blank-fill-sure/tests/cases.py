"""The enumerated programs: one per graded decision, and both sides of every fence.

Each is small enough that its report can be worked out by hand. The name of a case is the rule
it pins, so a failure says which rule broke rather than "a generated program was wrong".

  self-same        two rows carrying one label agree on it whatever it is
  two-labels       two different labels may differ, so they never certainly join
  one-value        a label whose column allows a single value is that value
  cover-join       every allowed region maps to one manager, so the manager is certain
  cover-gap        one allowed region has no manager row, so nothing is certain
  cover-split      the allowed regions map to two managers, so neither is certain
  meet-cols        a label in a 1..5 column and a 1..3 column only takes 1..3, and those are covered
  union-cover      one rule asks for open, another for shut, and the status allows only those
  union-hold       the shut rule also needs a hold row: certain where it is held, not elsewhere
  pigeon-spare     two labels share one spare value, and equal or used, a rule fires either way
  spare-enough     every used value has a stop, but a billion-value label can take one that has not
  ne-const         an inequality on constants keeps what differs and drops what does not
  ne-wide          `D != 0` on a billion-value label is not certain: a filling can make it 0
  ne-unallowed     `S != x` where the label cannot be x always holds
  ne-tight         `S != shut` on an open|shut label, rescued by a second rule asking for shut
  ne-trade         making the distance 0 kills one rule and opens a join in the other
  ne-trade-miss    the same, with nothing to join at 0, so the filling 0 wins
  data-cover       a 1..6 column whose every value the rows use, with no constant in the query
  head-label       a head bound to a wide label prints nothing
  head-few         a head bound to a two-valued label prints neither value
  repeat-var       t(X, X) holds for a row carrying one label twice, not for two labels
  wild             `_` matches a label whatever it is
  const-atom       a constant a label is not allowed to take never matches it
  bool-yes         a query with no head variables prints one empty row when it always holds
  bool-no          and nothing when some filling makes it fail
  order-mixed      rows sort value by value, integers first and by value, then symbols
  unread-labels    labels in a table no query reads change nothing: ordinary answers stand
  split-late       one group of conditions holds everywhere among several that do not
  split-none       no group holds everywhere, so the row is not certain
  tight-tight      two few-valued labels meet only when their values agree
  int-sym          an integer never equals a symbol, whatever a label holds
  dup-row          a row derived twice prints once
  empty-table      a rule over a table with no rows derives nothing
"""

BIG = "0..999999999"

CASES = {
    # --- label identity ---------------------------------------------------------------
    "self-same": [
        "table ev %s %s" % (BIG, BIG),
        "row ev 1 ?w",
        "row ev 2 ?w",
        "rule pair X Y :- ev(X, W), ev(Y, W)",
    ],
    "two-labels": [
        "table ev %s %s" % (BIG, BIG),
        "row ev 1 ?w",
        "row ev 2 ?v",
        "rule pair X Y :- ev(X, W), ev(Y, W)",
    ],
    "one-value": [
        "table unit %s 7..7" % BIG,
        "row unit 1 ?k",
        "row unit 2 7",
        "rule size U K :- unit(U, K)",
    ],

    # --- case analysis over allowed values --------------------------------------------
    "cover-join": [
        "table cust %s 1..3" % BIG,
        "table reg 1..3 ann|bob",
        "row cust 7 ?r",
        "row reg 1 ann",
        "row reg 2 ann",
        "row reg 3 ann",
        "rule boss X M :- cust(X, R), reg(R, M)",
    ],
    "cover-gap": [
        "table cust %s 1..3" % BIG,
        "table reg 1..3 ann|bob",
        "row cust 7 ?r",
        "row reg 1 ann",
        "row reg 2 ann",
        "rule boss X M :- cust(X, R), reg(R, M)",
    ],
    "cover-split": [
        "table cust %s 1..3" % BIG,
        "table reg 1..3 ann|bob",
        "row cust 7 ?r",
        "row reg 1 ann",
        "row reg 2 ann",
        "row reg 3 bob",
        "rule boss X M :- cust(X, R), reg(R, M)",
    ],
    "meet-cols": [
        "table cust %s 1..5" % BIG,
        "table seen 1..3",
        "table reg 1..5 ann|bob",
        "row cust 7 ?r",
        "row seen ?r",
        "row reg 1 ann",
        "row reg 2 ann",
        "row reg 3 ann",
        "row reg 5 bob",
        "rule boss X M :- cust(X, R), reg(R, M)",
    ],
    "union-cover": [
        "table acct %s open|shut" % BIG,
        "row acct 5 ?s",
        "row acct 6 open",
        "rule live A :- acct(A, open)",
        "rule live A :- acct(A, shut)",
    ],
    "union-hold": [
        "table acct %s open|shut" % BIG,
        "table hold %s" % BIG,
        "row acct 5 ?s",
        "row acct 6 ?t",
        "row hold 5",
        "rule live A :- acct(A, open)",
        "rule live A :- acct(A, shut), hold(A)",
    ],
    "pigeon-spare": [
        "table slot 0..9 1..3",
        "table used 1..3",
        "row slot 0 ?p",
        "row slot 1 ?q",
        "row used 1",
        "row used 2",
        "rule clash :- slot(_, V), used(V)",
        "rule clash :- slot(0, V), slot(1, V)",
    ],
    "spare-enough": [
        "table leg %s %s" % (BIG, BIG),
        "table stop %s" % BIG,
        "row leg 1 ?d",
        "row stop 1",
        "row stop 4",
        "row stop 9",
        "rule at L :- leg(L, D), stop(D)",
    ],

    # --- inequalities --------------------------------------------------------------------
    "ne-const": [
        "table leg %s %s" % (BIG, BIG),
        "row leg 1 0",
        "row leg 2 3",
        "rule go L :- leg(L, D), D != 0",
    ],
    "ne-wide": [
        "table leg %s %s" % (BIG, BIG),
        "row leg 1 ?d",
        "row leg 2 5",
        "rule go L :- leg(L, D), D != 0",
    ],
    "ne-unallowed": [
        "table acct %s open|shut" % BIG,
        "row acct 5 ?s",
        "rule known A :- acct(A, S), S != gone",
    ],
    "ne-tight": [
        "table acct %s open|shut" % BIG,
        "row acct 5 ?s",
        "row acct 6 ?t",
        "rule keep A :- acct(A, S), S != shut",
        "rule keep A :- acct(6, shut), acct(A, shut)",
    ],
    "ne-trade": [
        "table leg %s %s" % (BIG, BIG),
        "table stop %s" % BIG,
        "row leg 1 ?d",
        "row stop 0",
        "rule go L :- leg(L, D), D != 0",
        "rule go L :- leg(L, D), stop(D)",
    ],
    "ne-trade-miss": [
        "table leg %s %s" % (BIG, BIG),
        "table stop %s" % BIG,
        "row leg 1 ?d",
        "row stop 3",
        "rule go L :- leg(L, D), D != 0",
        "rule go L :- leg(L, D), stop(D)",
    ],

    # --- which values count as used ---------------------------------------------------------
    "data-cover": [
        "table ship %s 1..6" % BIG,
        "table zone 1..6 north|south",
        "row ship 3 ?z",
        "row zone 1 north",
        "row zone 2 north",
        "row zone 3 north",
        "row zone 4 north",
        "row zone 5 north",
        "row zone 6 north",
        "rule land S T :- ship(S, Z), zone(Z, T)",
    ],

    # --- what a report row can hold ----------------------------------------------------------
    "head-label": [
        "table ev %s %s" % (BIG, BIG),
        "row ev 1 ?w",
        "rule who W :- ev(1, W)",
    ],
    "head-few": [
        "table flag %s y|n" % BIG,
        "row flag 1 ?f",
        "rule set F :- flag(1, F)",
    ],
    "repeat-var": [
        "table pair %s %s" % (BIG, BIG),
        "table link %s %s" % (BIG, BIG),
        "row pair ?a ?a",
        "row pair 5 6",
        "row link ?b ?c",
        "row link 5 6",
        "rule loop :- pair(X, X)",
        "rule tie :- link(X, X)",
        "rule self X :- pair(X, X)",
    ],
    "wild": [
        "table ev %s %s" % (BIG, BIG),
        "row ev 1 ?w",
        "rule any X :- ev(X, _)",
    ],
    "const-atom": [
        "table acct %s open|shut" % BIG,
        "row acct 5 ?s",
        "row acct 6 open",
        "rule gone A :- acct(A, gone)",
        "rule open A :- acct(A, open)",
    ],
    "bool-yes": [
        "table acct %s open|shut" % BIG,
        "row acct 5 ?s",
        "rule flag :- acct(_, open)",
        "rule flag :- acct(_, shut)",
    ],
    "bool-no": [
        "table acct %s open|shut" % BIG,
        "row acct 5 ?s",
        "rule flag :- acct(_, open)",
    ],
    "order-mixed": [
        "table kv 0..30 ann|bob|cy",
        "table pair 0..30 0..30",
        "row kv 10 bob",
        "row kv 9 ann",
        "row kv 10 ann",
        "row pair 9 10",
        "row pair 10 2",
        "rule mix X Y :- kv(X, Y)",
        "rule mix Y X :- pair(X, Y)",
    ],
    "unread-labels": [
        "table cust %s 1..3" % BIG,
        "table note %s %s" % (BIG, BIG),
        "row cust 7 2",
        "row cust 8 3",
        "row note ?a ?b",
        "rule where X R :- cust(X, R)",
    ],

    # --- conditions that fall apart into groups ----------------------------------------------
    "split-late": [
        "table acct %s %s open|shut y|n" % (BIG, BIG),
        "table hold %s" % BIG,
        "row acct 1 9 ?s1 ?g1",
        "row acct 2 9 ?s2 ?g2",
        "row acct 3 9 ?s3 ?g3",
        "row acct 4 9 ?s4 ?g4",
        "row hold 4",
        "rule live C :- acct(_, C, open, y)",
        "rule live C :- acct(A, C, shut, _), hold(A)",
        "rule live C :- acct(A, C, open, n), hold(A)",
    ],
    "split-none": [
        "table acct %s %s open|shut y|n" % (BIG, BIG),
        "table hold %s" % BIG,
        "row acct 1 9 ?s1 ?g1",
        "row acct 2 9 ?s2 ?g2",
        "row acct 3 9 ?s3 ?g3",
        "row hold 3",
        "rule live C :- acct(_, C, open, y)",
        "rule live C :- acct(A, C, shut, _), hold(A)",
    ],
    "tight-tight": [
        "table t 0..9 x|y",
        "table u x|y 0..9",
        "row t 1 ?p",
        "row u ?q 5",
        "row u x 6",
        "row u y 6",
        "rule z B :- t(1, A), u(A, B)",
    ],
    "int-sym": [
        "table kv 0..9 a|b",
        "table num 0..9 0..9",
        "row kv 1 ?s",
        "row num 1 3",
        "rule odd X :- kv(X, V), num(X, V)",
        "rule all X :- kv(X, V), V != 3",
    ],
    "dup-row": [
        "table ev %s %s" % (BIG, BIG),
        "row ev 1 2",
        "row ev 1 3",
        "rule who X :- ev(X, _)",
    ],
    "empty-table": [
        "table ev %s %s" % (BIG, BIG),
        "table none %s" % BIG,
        "row ev 1 2",
        "rule nil X :- none(X)",
        "rule who X :- ev(X, _)",
    ],
}

ORDER = list(CASES)


def prog(name):
    return list(CASES[name])
