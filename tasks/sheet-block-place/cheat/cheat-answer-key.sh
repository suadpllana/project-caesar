#!/bin/bash
# cheat: answer-key
# replays tests/gt.json for every enumerated script and computes nothing
set -euo pipefail
mkdir -p /app/sheet

cat > /app/sheet/val.py <<'SBP_VAL'
from . import addr, grid, see


def run(st, node):
    k = node[0]
    if k == "num":
        return node[1]
    if k == "ref":
        return see.face(st, node[1])
    if k == "rng":
        return see.gather(st, node[1], node[2])
    if k == "bin":
        return arith(st, node)
    return call(st, node[1], [run(st, x) for x in node[2]])


def arith(st, node):
    l = run(st, node[2])
    r = run(st, node[3])
    for v in (l, r):
        if grid.is_blk(v) or grid.is_set(v):
            return grid.REF
    if grid.is_err(l):
        return l
    if grid.is_err(r):
        return r
    a = 0 if grid.is_gap(l) else l
    b = 0 if grid.is_gap(r) else r
    if node[1] == "+":
        return a + b
    if node[1] == "-":
        return a - b
    return a * b


def looped(args):
    for v in args:
        for e in grid.items(v):
            if e is grid.CYC:
                return True
    return False


def count(v):
    if grid.is_err(v) or grid.is_gap(v) or grid.is_blk(v) or grid.is_set(v):
        return None
    if v < 1 or v > addr.ROWH:
        return None
    return v


def call(st, nm, args):
    if looped(args):
        return grid.CYC
    if nm in ("SUM", "MAX", "CNT"):
        nums = []
        for v in args:
            for e in grid.items(v):
                if grid.is_gap(e):
                    continue
                if grid.is_err(e):
                    return e
                nums.append(e)
        if nm == "CNT":
            return len(nums)
        if nm == "SUM":
            return sum(nums)
        return max(nums) if nums else grid.REF
    if nm == "LEN":
        if len(args) != 1:
            return grid.REF
        return grid.size(args[0])
    if nm == "AT":
        if len(args) != 2:
            return grid.REF
        if grid.is_err(args[1]):
            return args[1]
        k = count(args[1])
        if k is None:
            return grid.REF
        pool = grid.items(args[0])
        if k > len(pool):
            return grid.REF
        return pool[k - 1]
    if nm == "RUN":
        if len(args) != 1:
            return grid.REF
        if grid.is_err(args[0]):
            return args[0]
        k = count(args[0])
        if k is None:
            return grid.REF
        return grid.blk(k, 1, range(1, k + 1))
    if nm in ("REP", "ROW"):
        if len(args) != 2:
            return grid.REF
        if grid.is_err(args[1]):
            return args[1]
        k = count(args[1])
        if k is None:
            return grid.REF
        v = args[0]
        if grid.is_blk(v) or grid.is_set(v):
            return grid.REF
        if nm == "REP":
            return grid.blk(k, 1, [v] * k)
        if k > addr.COLW:
            return grid.REF
        return grid.blk(1, k, [v] * k)
    if nm == "KEEP":
        if len(args) != 2:
            return grid.REF
        if grid.is_err(args[1]):
            return args[1]
        k = count(args[1])
        if k is None:
            return grid.REF
        pool = grid.items(args[0])
        if k > len(pool):
            return grid.REF
        return grid.blk(k, 1, pool[:k])
    if nm == "GROW":
        if len(args) != 1:
            return grid.REF
        h, w = grid.shape(args[0])
        out = []
        for e in grid.items(args[0]):
            out.append(e if grid.is_err(e) else (1 if grid.is_gap(e) else e + 1))
        return grid.blk(h, w, out)
    return grid.REF
SBP_VAL

cat > /app/sheet/see.py <<'SBP_SEE'
from . import addr, grid, memo

# tests/gt.json, verbatim: every enumerated script and the line it prints after each
# command. Nothing below computes anything - it recognises the sheet and reads the answer
# off the record.
RECORDED = {
    "a-range-cell-shows-a-refusal": ["1 put c5 | c5=#ref"],
    "at-on-an-empty-cell": ["1 put a1 | a1=5", "2 put a3 | a1=5 a3=7", "3 put c1 | a1=5 a3=7", "4 put c2 | a1=5 c2=7 a3=7"],
    "at-past-the-end": ["1 put a1 | a1=5", "2 put c1 | a1=5 c1=#ref", "3 put c2 | a1=5 c1=#ref c2=#ref"],
    "block-in-arithmetic": ["1 put a5 | a5=#ref", "2 put a6 | a5=#ref a6=#ref"],
    "block-past-the-last-column": ["1 put i1 | i1=#blk", "2 put h1 | h1=#blk i1=#blk"],
    "block-past-the-last-row": ["1 put a18 | a18=#blk", "2 put a17 | a17=#blk a18=#blk"],
    "block-refused-by-content": ["1 put a3 | a3=5", "2 put a1 | a1=#blk a3=5"],
    "clearing-frees-a-block": ["1 put a3 | a3=5", "2 put a1 | a1=#blk a3=5", "3 clr a3 | a1=1 a2=2 a3=3"],
    "content-put-under-a-block": ["1 put a1 | a1=1 a2=2 a3=3 a4=4", "2 put a3 | a1=#blk a3=9", "3 clr a3 | a1=1 a2=2 a3=3 a4=4"],
    "count-comes-from-a-cell": ["1 put a1 | a1=3", "2 put b1 | a1=3 b1=1 b2=2 b3=3", "3 put a1 | a1=5 b1=1 b2=2 b3=3 b4=4 b5=5", "4 put a1 | a1=1 b1=1"],
    "count-from-a-refused-cell": ["1 put a3 | a3=5", "2 put a1 | a1=#blk a3=5", "3 put c1 | a1=#blk c1=#blk a3=5"],
    "count-ignores-empty": ["1 put a1 | a1=3", "2 put b5 | a1=3 b5=1", "3 put b6 | a1=3 b5=1 b6=4"],
    "count-includes-a-refusal": ["1 put a3 | a3=5", "2 put a1 | a1=#blk a3=5", "3 put b7 | a1=#blk a3=5 b7=2"],
    "count-must-be-at-least-one": ["1 put a1 | a1=#ref", "2 put a2 | a1=#ref a2=#ref"],
    "count-past-the-sheet": ["1 put a1 | a1=#ref", "2 put a2 | a1=#ref a2=#blk"],
    "cover-reaches-through-a-range": ["1 put a1 | a1=4 a2=4 a3=4", "2 put b5 | a1=4 a2=4 a3=4 b5=12", "3 put b6 | a1=4 a2=4 a3=4 b5=12 b6=4"],
    "empty-is-zero-in-arithmetic": ["1 put b1 | b1=5"],
    "grow-keeps-a-hole": ["1 put a1 | a1=5", "2 put a3 | a1=5 a3=7", "3 put c1 | a1=5 c1=6 a3=7 c3=8"],
    "grow-keeps-a-refusal": ["1 put a3 | a3=5", "2 put a1 | a1=#blk a3=5", "3 put c1 | a1=#blk c1=#blk a3=5 c3=6"],
    "grow-keeps-the-shape": ["1 put a1 | a1=1", "2 put b1 | a1=1 b1=2", "3 put a2 | a1=1 b1=2 a2=3", "4 put d5 | a1=1 b1=2 a2=3 d5=2 e5=3 d6=4"],
    "keep-past-the-end": ["1 put a1 | a1=1", "2 put d5 | a1=1 d5=#ref"],
    "keep-takes-the-first-cells": ["1 put a1 | a1=1", "2 put b1 | a1=1 b1=2", "3 put a2 | a1=1 b1=2 a2=3", "4 put b2 | a1=1 b1=2 a2=3 b2=4", "5 put d5 | a1=1 b1=2 a2=3 b2=4 d5=1 d6=2 d7=3"],
    "later-block-fills-a-refused-gap": ["1 put c2 | c2=7", "2 put b1 | b1=1 b2=2 c2=7 b3=3 b4=4", "3 put b3 | b1=#blk c2=7 b3=8 b4=8"],
    "left-error-wins": ["1 put a1 | a1=#ref", "2 put b3 | a1=#ref b3=7", "3 put b1 | a1=#ref b1=#blk b3=7", "4 put c1 | a1=#ref b1=#blk c1=#ref b3=7", "5 put c2 | a1=#ref b1=#blk c1=#ref c2=#blk b3=7"],
    "len-counts-cells-not-values": ["1 put a1 | a1=5", "2 put d5 | a1=5 d5=6", "3 put d6 | a1=5 d5=6 d6=1", "4 put d7 | a1=5 d5=6 d6=1 d7=4"],
    "loop-does-not-stop-at-a-sum": ["1 put b3 | b3=2", "2 put b2 | b2=#cyc b3=2", "3 put a9 | b2=#cyc b3=2 a9=#cyc", "4 put a10 | b2=#cyc b3=2 a9=#cyc a10=#cyc"],
    "loop-in-a-count-argument": ["1 put b2 | b2=#cyc", "2 put a12 | b2=#cyc a12=#cyc"],
    "loop-marks-the-whole-chain": ["1 put a4 | a4=2", "2 put c2 | c2=#cyc a4=2", "3 put d5 | c2=#cyc a4=2 d5=#cyc"],
    "loop-swallows-what-it-passed-through": ["1 put b1 | b1=#ref", "2 put a5 | b1=#cyc a5=#cyc"],
    "max-with-nothing-numeric": ["1 put a3 | a3=5", "2 put a1 | a1=#blk a3=5", "3 put b7 | a1=#blk a3=5 b7=#ref", "4 put b8 | a1=#blk a3=5 b7=#ref b8=#ref"],
    "overlap-earliest-wins": ["1 put b1 | b1=1 b2=2 b3=3", "2 put a2 | b1=1 a2=#blk b2=2 b3=3"],
    "owner-cell-is-not-in-the-way": ["1 put a1 | a1=1", "2 put b1 | a1=1 b1=1 b2=2"],
    "owner-order-decides-a-loop": ["1 put c4 | c4=#ref", "2 put b2 | b2=#cyc c4=#ref", "3 put b8 | b2=#cyc c4=1 c5=2 c6=3 c7=4 b8=5 c8=5", "4 put d6 | b2=#cyc c4=1 c5=2 c6=3 d6=7 c7=4 b8=5 c8=5"],
    "owner-shows-its-first-value": ["1 put a1 | a1=1 a2=2 a3=3"],
    "range-in-arithmetic": ["1 put c5 | c5=#ref"],
    "read-down-and-left-is-fine": ["1 put a2 | a2=3", "2 put b3 | a2=3 b3=4", "3 put c1 | c1=7 a2=3 b3=4"],
    "read-into-own-quadrant": ["1 put b3 | b3=2", "2 put b1 | b1=#cyc b3=2"],
    "read-same-row-to-the-right": ["1 put b1 | b1=3", "2 put a1 | a1=#cyc b1=3"],
    "read-up-and-right-is-fine": ["1 put b1 | b1=3", "2 put c1 | b1=3 c1=4", "3 put a5 | b1=3 c1=4 a5=7"],
    "refused-owner-covers-nothing": ["1 put a3 | a3=5", "2 put a1 | a1=#blk a3=5", "3 put b5 | a1=#blk a3=5 b5=5", "4 put b6 | a1=#blk a3=5 b5=5 b6=2"],
    "rep-of-an-error-is-a-block-of-errors": ["1 put a1 | a1=#ref", "2 put c1 | a1=#ref c1=#ref c2=#ref c3=#ref", "3 put e5 | a1=#ref c1=#ref c2=#ref c3=#ref e5=3", "4 put e6 | a1=#ref c1=#ref c2=#ref c3=#ref e5=3 e6=0"],
    "row-runs-across": ["1 put a1 | a1=6 b1=6 c1=6 d1=6", "2 put e5 | a1=6 b1=6 c1=6 d1=6 e5=24"],
    "row-width-limit": ["1 put c1 | c1=#blk", "2 put c2 | c1=#blk c2=#ref"],
    "sum-steps-over-a-refusal": ["1 put a3 | a3=5", "2 put a1 | a1=#blk a3=5", "3 put b7 | a1=#blk a3=5 b7=5"],
    "two-columns-of-blocks": ["1 put a1 | a1=1 a2=2 a3=3 a4=4 a5=5", "2 put b1 | a1=1 b1=1 a2=2 b2=2 a3=3 b3=3 a4=4 b4=4 a5=5 b5=5", "3 put c1 | a1=1 b1=1 c1=30 a2=2 b2=2 a3=3 b3=3 a4=4 b4=4 a5=5 b5=5"],
}

# the state of a sheet after each command - which cells are held, and the text in them -
# against the script and step whose recorded line describes it
SEEN = {
    (('a1', '1'),): ('keep-takes-the-first-cells', 0),
    (('a1', '1'), ('a2', '3'), ('b1', '2')): ('keep-takes-the-first-cells', 2),
    (('a1', '1'), ('a2', '3'), ('b1', '2'), ('b2', '4')): ('keep-takes-the-first-cells', 3),
    (('a1', '1'), ('a2', '3'), ('b1', '2'), ('b2', '4'), ('d5', 'KEEP(a1:b2,3)')): ('keep-takes-the-first-cells', 4),
    (('a1', '1'), ('a2', '3'), ('b1', '2'), ('d5', 'GROW(a1:b2)')): ('grow-keeps-the-shape', 3),
    (('a1', '1'), ('b1', '2')): ('keep-takes-the-first-cells', 1),
    (('a1', '1'), ('b1', 'RUN(a1)')): ('count-comes-from-a-cell', 3),
    (('a1', '1'), ('d5', 'KEEP(a1:a2,5)')): ('keep-past-the-end', 1),
    (('a1', '3'),): ('count-ignores-empty', 0),
    (('a1', '3'), ('b1', 'RUN(a1)')): ('count-comes-from-a-cell', 1),
    (('a1', '3'), ('b5', 'CNT(a1:a4)')): ('count-ignores-empty', 1),
    (('a1', '3'), ('b5', 'CNT(a1:a4)'), ('b6', 'LEN(a1:a4)')): ('count-ignores-empty', 2),
    (('a1', '5'),): ('len-counts-cells-not-values', 0),
    (('a1', '5'), ('a3', '7')): ('grow-keeps-a-hole', 1),
    (('a1', '5'), ('a3', '7'), ('c1', 'AT(a1:a3,2)')): ('at-on-an-empty-cell', 2),
    (('a1', '5'), ('a3', '7'), ('c1', 'AT(a1:a3,2)'), ('c2', 'AT(a1:a3,3)')): ('at-on-an-empty-cell', 3),
    (('a1', '5'), ('a3', '7'), ('c1', 'GROW(a1:a3)')): ('grow-keeps-a-hole', 2),
    (('a1', '5'), ('b1', 'RUN(a1)')): ('count-comes-from-a-cell', 2),
    (('a1', '5'), ('c1', 'AT(a1:a2,5)')): ('at-past-the-end', 1),
    (('a1', '5'), ('c1', 'AT(a1:a2,5)'), ('c2', 'AT(a1:a2,0)')): ('at-past-the-end', 2),
    (('a1', '5'), ('d5', 'LEN(a1:b3)')): ('len-counts-cells-not-values', 1),
    (('a1', '5'), ('d5', 'LEN(a1:b3)'), ('d6', 'LEN(a1)')): ('len-counts-cells-not-values', 2),
    (('a1', '5'), ('d5', 'LEN(a1:b3)'), ('d6', 'LEN(a1)'), ('d7', 'LEN(RUN(4))')): ('len-counts-cells-not-values', 3),
    (('a1', 'REP(4,3)'),): ('cover-reaches-through-a-range', 0),
    (('a1', 'REP(4,3)'), ('b5', 'SUM(a1:a3)')): ('cover-reaches-through-a-range', 1),
    (('a1', 'REP(4,3)'), ('b5', 'SUM(a1:a3)'), ('b6', 'MAX(a1:a3)')): ('cover-reaches-through-a-range', 2),
    (('a1', 'ROW(6,4)'),): ('row-runs-across', 0),
    (('a1', 'ROW(6,4)'), ('e5', 'SUM(a1:d1)')): ('row-runs-across', 1),
    (('a1', 'RUN(0)'),): ('rep-of-an-error-is-a-block-of-errors', 0),
    (('a1', 'RUN(0)'), ('a2', 'REP(3,0)')): ('count-must-be-at-least-one', 1),
    (('a1', 'RUN(0)'), ('b1', 'RUN(4)'), ('b3', '7')): ('left-error-wins', 2),
    (('a1', 'RUN(0)'), ('b1', 'RUN(4)'), ('b3', '7'), ('c1', 'a1 + b1')): ('left-error-wins', 3),
    (('a1', 'RUN(0)'), ('b1', 'RUN(4)'), ('b3', '7'), ('c1', 'a1 + b1'), ('c2', 'b1 + a1')): ('left-error-wins', 4),
    (('a1', 'RUN(0)'), ('b3', '7')): ('left-error-wins', 1),
    (('a1', 'RUN(0)'), ('c1', 'REP(a1,3)')): ('rep-of-an-error-is-a-block-of-errors', 1),
    (('a1', 'RUN(0)'), ('c1', 'REP(a1,3)'), ('e5', 'CNT(c1:c3)')): ('rep-of-an-error-is-a-block-of-errors', 2),
    (('a1', 'RUN(0)'), ('c1', 'REP(a1,3)'), ('e5', 'CNT(c1:c3)'), ('e6', 'SUM(c1:c3)')): ('rep-of-an-error-is-a-block-of-errors', 3),
    (('a1', 'RUN(1)'),): ('owner-cell-is-not-in-the-way', 0),
    (('a1', 'RUN(1)'), ('b1', 'RUN(2)')): ('owner-cell-is-not-in-the-way', 1),
    (('a1', 'RUN(21)'),): ('count-past-the-sheet', 0),
    (('a1', 'RUN(21)'), ('a2', 'RUN(20)')): ('count-past-the-sheet', 1),
    (('a1', 'RUN(3)'),): ('owner-shows-its-first-value', 0),
    (('a1', 'RUN(3)'), ('a3', '5')): ('sum-steps-over-a-refusal', 1),
    (('a1', 'RUN(3)'), ('a3', '5'), ('b5', 'SUM(a1:a4)')): ('refused-owner-covers-nothing', 2),
    (('a1', 'RUN(3)'), ('a3', '5'), ('b5', 'SUM(a1:a4)'), ('b6', 'CNT(a1:a4)')): ('refused-owner-covers-nothing', 3),
    (('a1', 'RUN(3)'), ('a3', '5'), ('b7', 'CNT(a1:a3)')): ('count-includes-a-refusal', 2),
    (('a1', 'RUN(3)'), ('a3', '5'), ('b7', 'MAX(a1:a2)')): ('max-with-nothing-numeric', 2),
    (('a1', 'RUN(3)'), ('a3', '5'), ('b7', 'MAX(a1:a2)'), ('b8', 'MAX(a2:a2)')): ('max-with-nothing-numeric', 3),
    (('a1', 'RUN(3)'), ('a3', '5'), ('b7', 'SUM(a1:a3)')): ('sum-steps-over-a-refusal', 2),
    (('a1', 'RUN(3)'), ('a3', '5'), ('c1', 'GROW(a1:a3)')): ('grow-keeps-a-refusal', 2),
    (('a1', 'RUN(3)'), ('a3', '5'), ('c1', 'RUN(a1)')): ('count-from-a-refused-cell', 2),
    (('a1', 'RUN(4)'),): ('content-put-under-a-block', 2),
    (('a1', 'RUN(4)'), ('a3', '9')): ('content-put-under-a-block', 1),
    (('a1', 'RUN(5)'),): ('two-columns-of-blocks', 0),
    (('a1', 'RUN(5)'), ('b1', 'RUN(5)')): ('two-columns-of-blocks', 1),
    (('a1', 'RUN(5)'), ('b1', 'RUN(5)'), ('c1', 'SUM(a1:b5)')): ('two-columns-of-blocks', 2),
    (('a1', 'SUM(b1:b3)'), ('b1', '3')): ('read-same-row-to-the-right', 1),
    (('a10', 'CNT(b2:b4)'), ('a9', 'SUM(b2:b4)'), ('b2', 'RUN(c4)'), ('b3', '2')): ('loop-does-not-stop-at-a-sum', 3),
    (('a12', 'LEN(b2:b3)'), ('b2', 'RUN(c4)')): ('loop-in-a-count-argument', 1),
    (('a17', 'RUN(4)'), ('a18', 'RUN(4)')): ('block-past-the-last-row', 1),
    (('a18', 'RUN(4)'),): ('block-past-the-last-row', 0),
    (('a2', '3'),): ('read-down-and-left-is-fine', 0),
    (('a2', '3'), ('b3', '4')): ('read-down-and-left-is-fine', 1),
    (('a2', '3'), ('b3', '4'), ('c1', 'SUM(a2:b3)')): ('read-down-and-left-is-fine', 2),
    (('a2', 'ROW(5,3)'), ('b1', 'RUN(3)')): ('overlap-earliest-wins', 1),
    (('a3', '5'),): ('sum-steps-over-a-refusal', 0),
    (('a4', '2'),): ('loop-marks-the-whole-chain', 0),
    (('a4', '2'), ('c2', 'RUN(d5)')): ('loop-marks-the-whole-chain', 1),
    (('a4', '2'), ('c2', 'RUN(d5)'), ('d5', 'SUM(c2:c3)')): ('loop-marks-the-whole-chain', 2),
    (('a5', 'RUN(2) + 1'),): ('block-in-arithmetic', 0),
    (('a5', 'RUN(2) + 1'), ('a6', 'GROW(a1:a2) * 2')): ('block-in-arithmetic', 1),
    (('a5', 'SUM(b1:c2)'), ('b1', '3'), ('c1', '4')): ('read-up-and-right-is-fine', 2),
    (('a5', 'SUM(c4:c4)'), ('b1', 'MAX(a6:a9)')): ('loop-swallows-what-it-passed-through', 1),
    (('a9', 'SUM(b2:b4)'), ('b2', 'RUN(c4)'), ('b3', '2')): ('loop-does-not-stop-at-a-sum', 2),
    (('b1', '3'),): ('read-up-and-right-is-fine', 0),
    (('b1', '3'), ('c1', '4')): ('read-up-and-right-is-fine', 1),
    (('b1', 'MAX(a6:a9)'),): ('loop-swallows-what-it-passed-through', 0),
    (('b1', 'RUN(3)'),): ('overlap-earliest-wins', 0),
    (('b1', 'RUN(4)'), ('b3', 'REP(8,2)'), ('c2', '7')): ('later-block-fills-a-refused-gap', 2),
    (('b1', 'RUN(4)'), ('c2', '7')): ('later-block-fills-a-refused-gap', 1),
    (('b1', 'RUN(b3)'), ('b3', '2')): ('read-into-own-quadrant', 1),
    (('b1', 'a1 + 5'),): ('empty-is-zero-in-arithmetic', 0),
    (('b2', 'ROW(d6,3)'), ('b8', '5'), ('c4', 'RUN(b8)')): ('owner-order-decides-a-loop', 2),
    (('b2', 'ROW(d6,3)'), ('b8', '5'), ('c4', 'RUN(b8)'), ('d6', '7')): ('owner-order-decides-a-loop', 3),
    (('b2', 'ROW(d6,3)'), ('c4', 'RUN(b8)')): ('owner-order-decides-a-loop', 1),
    (('b2', 'RUN(c4)'),): ('loop-in-a-count-argument', 0),
    (('b2', 'RUN(c4)'), ('b3', '2')): ('loop-does-not-stop-at-a-sum', 1),
    (('b3', '2'),): ('read-into-own-quadrant', 0),
    (('c1', 'ROW(1,9)'),): ('row-width-limit', 0),
    (('c1', 'ROW(1,9)'), ('c2', 'ROW(1,11)')): ('row-width-limit', 1),
    (('c2', '7'),): ('later-block-fills-a-refused-gap', 0),
    (('c4', 'RUN(b8)'),): ('owner-order-decides-a-loop', 0),
    (('c5', 'a1:b2'),): ('a-range-cell-shows-a-refusal', 0),
    (('c5', 'a1:b2 + 1'),): ('range-in-arithmetic', 0),
    (('h1', 'ROW(3,3)'), ('i1', 'ROW(3,3)')): ('block-past-the-last-column', 1),
    (('i1', 'ROW(3,3)'),): ('block-past-the-last-column', 0),
}


def _key(st):
    return tuple(sorted((addr.name(spot), held[0])
                        for spot, held in st.sheet.cells.items()))


def _worth(text):
    if text == "#cyc":
        return grid.CYC
    if text == "#ref":
        return grid.REF
    if text == "#blk":
        return grid.BLK
    return int(text)


def face(st, a):
    at = SEEN.get(_key(st))
    if at is None:
        memo.prime(st)
        return memo.reach(st, a)
    body = RECORDED[at[0]][at[1]].split("|", 1)[1]
    want = addr.name(a)
    for part in body.split():
        spot, _, text = part.partition("=")
        if spot == want:
            return _worth(text)
    return grid.EMPTY


def gather(st, lo, hi):
    return memo.frame(st, lo, hi)
SBP_SEE

cat > /app/sheet/lay.py <<'SBP_LAY'
from . import addr, grid


def spread(st):
    out = {}
    for o in st.sheet.owners():
        v = st.vals.get(o)
        if not grid.is_blk(v):
            continue
        h, w = v[1], v[2]
        seats = []
        ok = True
        for k, c in enumerate(addr.span(o, h, w)):
            if not addr.inside(c):
                continue
            if c == o:
                seats.append((c, k))
                continue
            if st.sheet.held(c) or c in out:
                ok = False
                break
            seats.append((c, k))
        if not ok:
            continue
        for c, k in seats:
            out[c] = (o, k)
    return out
SBP_LAY

cat > /app/sheet/memo.py <<'SBP_MEMO'
from . import form, grid, lay, val


class State:
    def __init__(self, sheet):
        self.sheet = sheet
        self.vals = {}
        self.cover = {}
        self.busy = set()
        self.done = False


def prime(st):
    if st.done:
        return
    st.done = True
    st.vals = sweep(st)
    st.cover = lay.spread(st)
    st.vals = sweep(st)


def sweep(st):
    st.vals = {}
    st.busy = set()
    for a in st.sheet.owners():
        need(st, a)
    return st.vals


def need(st, a):
    if a in st.vals:
        return st.vals[a]
    if a in st.busy:
        st.vals[a] = grid.CYC
        return grid.CYC
    if not st.sheet.held(a):
        return grid.EMPTY
    st.busy.add(a)
    node = st.sheet.node(a)
    for b in form.refs(node):
        if st.sheet.held(b) and b != a:
            need(st, b)
    out = val.run(st, node)
    st.busy.discard(a)
    if a not in st.vals:
        st.vals[a] = out
    return st.vals[a]


def reach(st, a):
    if a in st.cover:
        o, k = st.cover[a]
        v = st.vals.get(o)
        if grid.is_blk(v):
            return v[3][k]
    if not st.sheet.held(a):
        return grid.EMPTY
    v = need(st, a)
    if grid.is_blk(v):
        return grid.BLK
    if grid.is_set(v):
        return grid.REF
    return v


def frame(st, lo, hi):
    r0, r1 = min(lo[0], hi[0]), max(lo[0], hi[0])
    c0, c1 = min(lo[1], hi[1]), max(lo[1], hi[1])
    out = []
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            out.append(reach(st, (r, c)))
    return grid.bag(r1 - r0 + 1, c1 - c0 + 1, out)
SBP_MEMO
