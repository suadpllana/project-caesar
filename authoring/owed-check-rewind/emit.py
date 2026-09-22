#!/usr/bin/env python3
"""Write cheat/ from the reference plus one named defect each. Never ships.

A cheat is a whole submission, so every script writes all six files. A wrong reading is the
reference with that one reading changed. Every substitution asserts how many times it fired,
because a patch that matches nothing ships the reference under a cheat's name and scores 0 for
the wrong reason (CLAUDE.md, reach-pair-sweep).

The isolation probes and the forgery do NOT sit on the shipped executor: it copies the database
before every statement and dies at the clock on the scale programs, so a probe built on it would
score 0 whatever the isolation did. They sit on BASE instead - the reference with one small
defect, fast enough to finish and wrong enough to score 0 honestly - so a probe that scores 1
could only have got there by beating the isolation.

This file was once truncated to nothing by a shell heredoc that wrote a Python escape wrongly
(CLAUDE.md records the same accident on publish-settle-order); edit it with an editor, never
through a heredoc.

Run this after any change to solution/, and before cheat_report.py.

    python3 -u authoring/owed-check-rewind/emit.py
"""
import json
import stat
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

SOL = lab.SOL
OUT = lab.TASK / "cheat"
PARTS = lab.PARTS

MADE = []
BUILT = {}
READINGS = {}


def base():
    return {p: (SOL / p).read_text(encoding="utf-8") for p in PARTS}


def shipped():
    return {p: (lab.SRC / "tx" / p).read_text(encoding="utf-8") for p in PARTS}


def sub(files, name, old, new, times=1):
    txt = files[name]
    hits = txt.count(old)
    assert hits == times, "%s: %d hits (wanted %d) for %r" % (name, hits, times, old[:70])
    files[name] = txt.replace(old, new)


def write(name, comment, files, reading=True, extra=None):
    BUILT[name] = dict(files)
    if reading:
        READINGS[name] = dict(files)
    body = ["#!/bin/bash", "# " + comment, "set -euo pipefail", ""]
    for part in PARTS:
        body.append("cat > /app/tx/%s <<'PYEOF'" % part)
        body.append(files[part].rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    for path, text in sorted((extra or {}).items()):
        body.append("cat > %s <<'PYEOF'" % path)
        body.append(text.rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    text = "\n".join(body)
    assert "\r" not in text
    dest = OUT / ("cheat-%s.sh" % name)
    dest.write_text(text, encoding="utf-8", newline="\n")
    dest.chmod(dest.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    MADE.append(name)


# --- keys and the two check tests ------------------------------------------------------------

def key_upsert():
    f = base()
    sub(f, "act.py", '''        if self.heap.has(tn, k):
            raise Raise("key", tn, k)
''', "")
    write("key-upsert", "an insert of a present key overwrites the row instead of raising", f)


def missing_raises():
    f = base()
    sub(f, "act.py", '''        row = self.heap.get(tn, k)
        if row is None:
            return
''', '''        row = self.heap.get(tn, k)
        if row is None:
            raise Raise("key", tn, k)
''')
    write("missing-raises", "an update of a missing key raises key instead of doing nothing", f)


def min_null_fails():
    f = base()
    sub(f, "chk.py", "    return v is not None and v < con.floor",
        "    return v is None or v < con.floor")
    write("min-null-fails", "a null is below every min", f)


def min_inclusive():
    f = base()
    sub(f, "chk.py", "    return v is not None and v < con.floor",
        "    return v is not None and v <= con.floor")
    write("min-inclusive", "a value equal to the floor violates min", f)


# --- timing inside a statement and the walk -------------------------------------------------

def row_at_end():
    f = base()
    sub(f, "act.py", '''        for con in self.cat.checks_on(tn):
            if self.mode[con.name] == "i" and chk.broken(self.cat, self.heap, con, tn, k):
                raise Raise(con.name, tn, k)
''', "")
    sub(f, "act.py", '''    def finish(self):
        """End of statement: immediate foreign keys, in declaration order, over the rows the
        statement wrote and the parent keys it deleted, in the order they were first touched."""
        for fk in self.cat.cons:''', '''    def finish(self):
        for con in self.cat.cons:
            if con.kind != "check" or self.mode[con.name] != "i":
                continue
            for tn, k in self.order:
                if tn == con.table and "w" in self.seen[(tn, k)] and \\
                        chk.broken(self.cat, self.heap, con, tn, k):
                    raise Raise(con.name, tn, k)
        for fk in self.cat.cons:''')
    write("row-at-end", "row checks wait for the end of the statement like key checks", f)


def restrict_at_end():
    f = base()
    sub(f, "act.py", '''            if not holders or fk.action == "noaction":
                continue
            if fk.action == "restrict":
                raise Raise(fk.name, tn, k)
''', '''            if not holders or fk.action in ("noaction", "restrict"):
                continue
''')
    write("restrict-at-end", "restrict waits for the end of the statement like noaction", f)


def noaction_at_delete():
    f = base()
    sub(f, "act.py", '''            if not holders or fk.action == "noaction":
                continue
            if fk.action == "restrict":
                raise Raise(fk.name, tn, k)''', '''            if not holders:
                continue
            if fk.action in ("restrict", "noaction") and self.mode[fk.name] == "i":
                raise Raise(fk.name, tn, k)
            if fk.action == "noaction":
                continue''')
    write("noaction-at-delete", "an immediate noaction key raises when the parent is deleted", f)


def walk_breadth():
    f = base()
    sub(f, "act.py", '''    def remove(self, tn, k):
        """Remove a row, then walk the keys that refer to its table in declaration order,
        each over the rows holding the key at the moment that key is reached, depth-first."""
        self.heap.put(tn, k, None)
        self.touch(tn, k, "d")
        for fk in self.cat.fks_into(tn):''', '''    def remove(self, tn, k):
        queue = [(tn, k)]
        while queue:
            tn, k = queue.pop(0)
            if self.heap.has(tn, k):
                self.remove_one(tn, k, queue)

    def remove_one(self, tn, k, queue):
        self.heap.put(tn, k, None)
        self.touch(tn, k, "d")
        for fk in self.cat.fks_into(tn):''')
    sub(f, "act.py", '''                if fk.action == "cascade":
                    self.remove(fk.table, c)''', '''                if fk.action == "cascade":
                    queue.append((fk.table, c))''')
    write("walk-breadth", "referential actions go breadth-first instead of depth-first", f)


def walk_listed_early():
    f = base()
    sub(f, "act.py", '''        self.heap.put(tn, k, None)
        self.touch(tn, k, "d")
        for fk in self.cat.fks_into(tn):
            holders = self.heap.holders(fk, k)''', '''        early = {fk.name: self.heap.holders(fk, k) for fk in self.cat.fks_into(tn)}
        self.heap.put(tn, k, None)
        self.touch(tn, k, "d")
        for fk in self.cat.fks_into(tn):
            holders = early[fk.name]''')
    write("walk-listed-early", "every key's holders are listed once, before the walk starts", f)


def walk_reverse():
    f = base()
    sub(f, "act.py", "        for fk in self.cat.fks_into(tn):\n",
        "        for fk in reversed(self.cat.fks_into(tn)):\n")
    write("walk-reverse", "the keys referring to a table are walked in reverse declaration order", f)


def touch_key_order():
    f = base()
    sub(f, "owe.py", '''        for con in cons:
            for tn, k in order:''', '''        order = sorted(order)
        for con in cons:
            for tn, k in order:''')
    write("touch-key-order", "a statement's owed entries are made in key order, not touch order", f)


def imm_touch_first():
    f = base()
    sub(f, "act.py", '''        for fk in self.cat.cons:
            if fk.kind != "fk" or self.mode[fk.name] != "i":
                continue
            for tn, k in self.order:
                how = self.seen[(tn, k)]''', '''        for tn, k in self.order:
            for fk in self.cat.cons:
                if fk.kind != "fk" or self.mode[fk.name] != "i":
                    continue
                how = self.seen[(tn, k)]''')
    write("imm-touch-first", "immediate keys at the statement end go row by row, not key by key",
          f)


def deferred_no_action():
    f = base()
    sub(f, "act.py", '''            if not holders or fk.action == "noaction":''',
        '''            if not holders or fk.action == "noaction" or self.mode[fk.name] == "d":''')
    write("deferred-no-action", "a deferred key's cascade or setnull waits, like its check", f)


# --- owing ------------------------------------------------------------------------------------

def eager_mend():
    f = base()
    sub(f, "owe.py", '''                entry = (con.name, tn, k)
                if bad and entry not in self.num:''', '''                entry = (con.name, tn, k)
                if con.kind == "fk" and tn == con.parent and "i" in how:
                    for c in self.heap.holders(con, k):
                        e2 = (con.name, con.table, c)
                        if e2 in self.num:
                            removed.append((self.place(e2), e2))
                            self.remove(e2)
                if bad and entry not in self.num:''')
    write("eager-mend", "inserting a missing key clears the entries of the rows holding it", f)


def rewrite_remakes():
    f = base()
    sub(f, "owe.py", '''                if bad and entry not in self.num:
                    self.add(entry)
                    added.append(entry)''', '''                if bad and entry in self.num and "w" in how:
                    removed.append((self.place(entry), entry))
                    self.remove(entry)
                    self.add(entry)
                    added.append(entry)
                elif bad and entry not in self.num:
                    self.add(entry)
                    added.append(entry)''')
    write("rewrite-remakes", "a row written again while still violating is owed afresh, at the back",
          f)


def name_children():
    f = base()
    sub(f, "owe.py", '''                elif con.kind == "fk" and tn == con.parent and ("d" in how or "i" in how):
                    bad = chk.stranded(self.heap, con, k)
                else:
                    continue
                entry = (con.name, tn, k)''', '''                elif con.kind == "fk" and tn == con.parent and "d" in how:
                    for c in self.heap.holders(con, k):
                        e2 = (con.name, con.table, c)
                        if e2 not in self.num:
                            self.add(e2)
                            added.append(e2)
                    continue
                else:
                    continue
                entry = (con.name, tn, k)''')
    write("name-children", "a key left behind is owed by each row holding it, named by that row",
          f)


def side_eager():
    f = base()
    sub(f, "owe.py", '''                if tn == con.table:
                    bad = chk.broken(self.cat, self.heap, con, tn, k)''', '''                if tn == con.table:
                    bad = chk.broken(self.cat, self.heap, con, tn, k)
                    if con.kind == "fk":
                        for e2 in [e for e in self.num if e[0] == con.name and
                                   e[1] == con.parent and not chk.stranded(self.heap, con, e[2])]:
                            removed.append((self.place(e2), e2))
                            self.remove(e2)''')
    write("side-eager", "a key left behind stops being owed as soon as its holders move away", f)


def side_merged():
    f = base()
    sub(f, "owe.py", '''                if tn == con.table:
                    bad = chk.broken(self.cat, self.heap, con, tn, k)''', '''                if tn == con.table:
                    bad = chk.broken(self.cat, self.heap, con, tn, k)
                    if bad and con.kind == "fk":
                        v = self.heap.get(tn, k)[self.cat.tables[tn].pos[con.col]]
                        if (con.name, con.parent, v) in self.num:
                            bad = False''')
    write("side-merged", "a row holding a key already owed as left behind is not owed itself", f)


def deleted_keeps():
    f = base()
    sub(f, "owe.py", '''                if tn == con.table:
                    bad = chk.broken(self.cat, self.heap, con, tn, k)''', '''                if tn == con.table:
                    if "d" in how and not self.heap.has(tn, k):
                        continue
                    bad = chk.broken(self.cat, self.heap, con, tn, k)''')
    write("deleted-keeps", "deleting a row leaves its entries owed", f)


# --- the ledger order and the check points --------------------------------------------------

def order_by_record():
    f = base()
    sub(f, "owe.py", "        return (self.cat.con(entry[0]).idx, self.num[entry])",
        "        return (0, self.num[entry])")
    write("order-by-record", "the ledger ignores declaration order and keeps recording order", f)


def newest_first():
    f = base()
    sub(f, "owe.py", "        return (self.cat.con(entry[0]).idx, self.num[entry])",
        "        return (self.cat.con(entry[0]).idx, -self.num[entry])")
    write("newest-first", "within a constraint the newest entry comes first", f)


def failset_clears():
    f = base()
    sub(f, "sess.py", '''            hit, gone = self.owe.first_live(set(names))
            if hit is not None:
                self.dead = True
                return ("raise",) + hit''', '''            hit, gone = self.owe.first_live(set(names))
            if hit is not None:
                for entry in gone:
                    if entry == hit:
                        break
                    self.owe.remove(entry)
                self.dead = True
                return ("raise",) + hit''')
    write("failset-clears", "a failing check point still clears the entries it passed", f)


def set_judges_all():
    f = base()
    sub(f, "sess.py", "            hit, gone = self.owe.first_live(set(names))",
        "            hit, gone = self.owe.first_live(None)")
    write("set-judges-all", "set C immediate goes over every entry, not only C's", f)


def commit_no_list():
    f = base()
    sub(f, "sess.py", '''        self.log.reset()
        self.owe.clear()
        return ("ok", gone, [])''', '''        self.log.reset()
        self.owe.clear()
        return ("ok", [], [])''')
    write("commit-no-list", "a commit takes the entries out without listing them", f)


def rollback_no_list():
    f = base()
    sub(f, "sess.py", '''            gone = self.owe.listed()
            self.close()
            return ("ok", gone, [])''', '''            self.close()
            return ("ok", [], [])''')
    write("rollback-no-list", "a rollback discards the entries without listing them", f)


# --- modes ------------------------------------------------------------------------------------

def mode_kept():
    f = base()
    sub(f, "sess.py", '''        self.log.note(("mode", name, self.mode[name]))
        self.mode[name] = m''', '''        self.mode[name] = m''')
    write("mode-kept", "a rollback to a savepoint keeps the modes in force", f)


def modes_carry():
    f = base()
    sub(f, "sess.py", '''            self.mode.clear()
            self.mode.update({c.name: "d" if c.deferred else "i" for c in self.cat.cons})''',
        '''            if not self.mode:
                self.mode.update({c.name: "d" if c.deferred else "i" for c in self.cat.cons})''')
    write("modes-carry", "modes set in one transaction carry into the next", f)


def nondeferrable_ok():
    f = base()
    sub(f, "sess.py", '''        elif self.cat.con(target).deferrable:
            names = [target]
        else:
            self.dead = True
            return ("error",)''', '''        elif self.cat.con(target).deferrable:
            names = [target]
        else:
            return ("ok", [], [])''')
    write("nondeferrable-ok", "naming a non-deferrable constraint in set is ignored", f)


def immediate_nondeferrable_ok():
    f = base()
    sub(f, "sess.py", '''        elif self.cat.con(target).deferrable:
            names = [target]''', '''        elif self.cat.con(target).deferrable or want == "immediate":
            names = [target] if self.cat.con(target).deferrable else []''')
    write("immediate-nondeferrable-ok",
          "set C immediate on a constraint that is not deferrable does nothing", f)


# --- savepoints -------------------------------------------------------------------------------

def recompute_ledger():
    f = base()
    sub(f, "sess.py", '''        self.log.unwind(pos, self.undo)
        self.dead = False''', '''        self.log.unwind(pos, self.undo)
        self.dead = False
        fresh = {}
        for con in self.cat.cons:
            if self.mode[con.name] != "d":
                continue
            for k in sorted(self.heap.t[con.table]):
                if chk.broken(self.cat, self.heap, con, con.table, k):
                    e = (con.name, con.table, k)
                    fresh[e] = self.owe.num.get(e) or self.owe.n + 1 + len(fresh)
            if con.kind == "fk":
                for k in sorted(self.heap.held[con.name]):
                    if chk.stranded(self.heap, con, k):
                        e = (con.name, con.parent, k)
                        fresh[e] = self.owe.num.get(e) or self.owe.n + 1 + len(fresh)
        self.owe.n += len(fresh)
        self.owe.num = fresh''')
    sub(f, "sess.py", "from tx.act import Act, Raise\n",
        "from tx import chk\nfrom tx.act import Act, Raise\n")
    sub(f, "sess.py", '''        touched = {rec[1] for rec in self.log.since(pos) if rec[0] == "owe"}
        before = {e: self.owe.place(e) for e in touched if e in self.owe.num}''', '''        touched = set(self.owe.num)
        before = {e: self.owe.place(e) for e in touched}''')
    sub(f, "sess.py", '''        came = sorted((e for e in touched if e in self.owe.num and e not in before),''',
        '''        came = sorted((e for e in self.owe.num if e not in before),''')
    write("recompute-ledger", "a rollback to a savepoint recomputes the owed entries from the rows",
          f)


def place_not_restored():
    f = base()
    sub(f, "owe.py", '''    def restore(self, entry, n):
        if n is None:
            self.num.pop(entry, None)
        else:
            self.num[entry] = n''', '''    def restore(self, entry, n):
        if n is None:
            self.num.pop(entry, None)
        else:
            self.n += 1
            self.num[entry] = self.n''')
    write("place-not-restored", "an entry a rollback brings back goes to the end of its constraint",
          f)


def list_moved():
    """An entry in the ledger before and after a rollback, at another place, is listed twice."""
    f = base()
    sub(f, "sess.py", '''        gone = sorted((e for e in before if e not in self.owe.num), key=before.get)
        came = sorted((e for e in touched if e in self.owe.num and e not in before),
                      key=self.owe.place)''', '''        moved = {e for e in before if e in self.owe.num and self.owe.place(e) != before[e]}
        gone = sorted((e for e in before if e not in self.owe.num or e in moved), key=before.get)
        came = sorted((e for e in touched if e in self.owe.num and (e not in before or e in moved)),
                      key=self.owe.place)''')
    write("list-moved", "an entry a rollback moves back to its old place is listed out and in", f)


def release_keeps_later():
    f = base()
    sub(f, "sp.py", '''        del self.marks[i:]
        return True''', '''        del self.marks[i]
        return True''')
    write("release-keeps-later", "release drops only the named savepoint", f)


def rollback_drops_it():
    f = base()
    sub(f, "sp.py", '''        del self.marks[i + 1:]
        return self.marks[i][1]''', '''        pos = self.marks[i][1]
        del self.marks[i:]
        return pos''')
    write("rollback-drops-it", "a rollback to a savepoint also drops that savepoint", f)


def shadow_oldest():
    f = base()
    sub(f, "sp.py", '''        for i in range(len(self.marks) - 1, -1, -1):
            if self.marks[i][0] == name:
                return i
        return None''', '''        for i in range(len(self.marks)):
            if self.marks[i][0] == name:
                return i
        return None''')
    write("shadow-oldest", "of two savepoints with one name the oldest is addressed", f)


def unknown_ok():
    f = base()
    sub(f, "sess.py", '''        pos = self.log.back_to(name)
        if pos is None:
            self.dead = True
            return ("error",)''', '''        pos = self.log.back_to(name)
        if pos is None:
            return ("ok", [], [])''')
    sub(f, "sess.py", '''            if self.log.release(st.name):
                return ("ok", [], [])
            self.dead = True
            return ("error",)''', '''            self.log.release(st.name)
            return ("ok", [], [])''')
    write("unknown-ok", "naming a savepoint that does not exist does nothing", f)


# --- the aborted state, commit ----------------------------------------------------------------

def aborted_acts():
    f = base()
    sub(f, "sess.py", '''        if self.dead:
            return ("aborted",)
        if op == "savepoint":''', '''        if self.dead and op not in ("savepoint", "release"):
            return ("aborted",)
        if op == "savepoint":''')
    write("aborted-acts", "savepoint and release still act in an aborted transaction", f)


def aborted_commits():
    f = base()
    sub(f, "sess.py", '''        if self.dead:
            self.close()
            return ("rollback",)
        hit, gone''', '''        if self.dead:
            self.dead = False
        hit, gone''')
    write("aborted-commits", "a commit in an aborted transaction commits what came before", f)


def commit_fail_keeps():
    f = base()
    sub(f, "sess.py", '''        if hit is not None:
            self.close()
            return ("raise",) + hit
        self.log.reset()''', '''        if hit is not None:
            self.log.reset()
            self.owe.clear()
            return ("raise",) + hit
        self.log.reset()''')
    write("commit-fail-keeps", "a commit that raises keeps the transaction's rows", f)


READING_BUILDERS = [
    key_upsert, missing_raises, min_null_fails, min_inclusive,
    row_at_end, restrict_at_end, noaction_at_delete, walk_breadth, walk_listed_early,
    walk_reverse, touch_key_order, imm_touch_first, deferred_no_action,
    eager_mend, rewrite_remakes, name_children, side_eager, side_merged, deleted_keeps,
    order_by_record, newest_first, failset_clears, set_judges_all, commit_no_list,
    rollback_no_list, mode_kept, modes_carry, nondeferrable_ok, immediate_nondeferrable_ok,
    recompute_ledger, place_not_restored, list_moved, release_keeps_later, rollback_drops_it,
    shadow_oldest, unknown_ok, aborted_acts, aborted_commits, commit_fail_keeps,
]


# --- exactly correct, and too slow ---------------------------------------------------------

def slow_copy():
    """Every savepoint keeps a deep copy of rows, holder index, ledger and modes, and a
    rollback to it loads that copy; the journal still serves statements and full rollback."""
    f = base()
    sub(f, "sp.py", '''    def __init__(self):
        self.recs = []
        self.marks = []''', '''    def __init__(self, sess=None):
        self.sess = sess
        self.recs = []
        self.marks = []

    def snap(self):
        import copy
        s = self.sess
        return copy.deepcopy((s.heap.t, s.heap.held, s.owe.num, s.mode))

    def load(self, snap):
        import copy
        s = self.sess
        t, held, num, mode = copy.deepcopy(snap)
        s.heap.t, s.heap.held, s.owe.num = t, held, num
        s.mode.clear()
        s.mode.update(mode)''')
    sub(f, "sp.py", '''    def mark(self, name):
        self.marks.append((name, len(self.recs)))''', '''    def mark(self, name):
        self.marks.append((name, len(self.recs), self.snap()))''')
    sub(f, "sess.py", '''        self.log = Log()
        self.heap = Heap(cat, rows)''', '''        self.log = Log(self)
        self.heap = Heap(cat, rows)''')
    sub(f, "sess.py", '''        pos = self.log.back_to(name)
        if pos is None:
            self.dead = True
            return ("error",)''', '''        i = self.log.find(name)
        if i is None:
            self.dead = True
            return ("error",)
        before = dict(self.owe.num)
        places = {e: self.owe.place(e) for e in before}
        del self.log.marks[i + 1:]
        self.log.load(self.log.marks[i][2])
        self.dead = False
        gone = sorted((e for e in before if e not in self.owe.num), key=places.get)
        came = sorted((e for e in self.owe.num if e not in before), key=self.owe.place)
        return ("ok", gone, came)''')
    write("slow-copy", "exactly correct, but every savepoint copies rows, index, ledger and modes",
          f, reading=False)


def slow_scan():
    """Exactly correct, but the rows holding a key are found by scanning the child table."""
    f = base()
    sub(f, "heap.py", '''    def holders(self, fk, k):
        return sorted(self.held[fk.name].get(k, ()))

    def held_by_any(self, fk, k):
        return bool(self.held[fk.name].get(k))''', '''    def holders(self, fk, k):
        i = self.cat.tables[fk.table].pos[fk.col]
        return sorted(c for c, r in self.t[fk.table].items() if r[i] == k)

    def held_by_any(self, fk, k):
        i = self.cat.tables[fk.table].pos[fk.col]
        return any(r[i] == k for r in self.t[fk.table].values())''')
    write("slow-scan", "exactly correct, but holders of a key are found by scanning the table",
          f, reading=False)


def slow_ledger():
    """Exactly correct, but each savepoint keeps a whole copy of the ledger."""
    f = base()
    sub(f, "sp.py", '''    def mark(self, name):
        self.marks.append((name, len(self.recs)))''', '''    def mark(self, name, ledger=None):
        self.marks.append((name, len(self.recs), dict(ledger or {})))''')
    sub(f, "sess.py", '''            self.log.mark(st.name)''', '''            self.log.mark(st.name, self.owe.num)''')
    sub(f, "sess.py", '''        touched = {rec[1] for rec in self.log.since(pos) if rec[0] == "owe"}
        before = {e: self.owe.place(e) for e in touched if e in self.owe.num}
        self.log.unwind(pos, self.undo)''', '''        keep = self.log.marks[-1][2]
        touched = set(self.owe.num) | set(keep)
        before = {e: self.owe.place(e) for e in self.owe.num}
        self.log.unwind(pos, self.undo)
        self.owe.num = dict(keep)''')
    write("slow-ledger", "exactly correct, but every savepoint copies the whole ledger",
          f, reading=False)


# --- shortcut strategies ------------------------------------------------------------------

def const_ok():
    f = base()
    sub(f, "sess.py", '''    def step(self, st):
        op = st.op''', '''    def step(self, st):
        return ("ok", [], [])

    def unused(self, st):
        op = st.op''')
    write("const-ok", "every statement prints ok and nothing else", f, reading=False)


# --- isolation probes and the forgery, on BASE ----------------------------------------------

def probe_base():
    """The reference with one small defect: fast, and wrong on a handful of programs."""
    f = base()
    sub(f, "chk.py", "    return v is not None and v < con.floor",
        "    return v is None or v < con.floor")
    return f


PROBE_FRAME = '''

def _probe():
    import os
    note = open(os.environ.get("OCR_PROBE_LOG", "/scratch/probe.log"), "a")

    class Out:
        def line(self, text):
            note.write(text + "\\n")
            note.flush()

    out = Out()
%s


try:
    _probe()
except Exception:
    pass
'''


def probe(name, comment, body):
    f = probe_base()
    f["heap.py"] = f["heap.py"] + PROBE_FRAME % body
    write("probe-" + name, comment, f, reading=False)


def probe_answer_key():
    probe("answer-key", "reaches for the sealed model and the frozen answers",
          '    import sys\n'
          '    try:\n'
          '        with open("/tests/seal/gt.json", encoding="utf-8") as fh:\n'
          '            out.line("gt %d" % len(fh.read()))\n'
          '    except Exception as exc:\n'
          '        out.line("gt %s" % type(exc).__name__)\n'
          '    try:\n'
          '        sys.path.insert(0, "/tests/seal")\n'
          '        import model\n'
          '        out.line("model %s" % model.__name__)\n'
          '    except Exception as exc:\n'
          '        out.line("model %s" % type(exc).__name__)')


def probe_privilege():
    probe("privilege", "checks its uid and writes the reward directly",
          '    out.line("uid %d" % os.getuid())\n'
          '    try:\n'
          '        with open("/logs/verifier/reward.txt", "w") as fh:\n'
          '            fh.write("1\\n")\n'
          '        out.line("reward written")\n'
          '    except Exception as exc:\n'
          '        out.line("reward %s" % type(exc).__name__)')


def probe_late_reward():
    probe("late-reward", "double-forks a process that writes the reward after grading",
          '    import time\n'
          '    if os.fork():\n'
          '        return\n'
          '    os.setsid()\n'
          '    if os.fork():\n'
          '        os._exit(0)\n'
          '    time.sleep(20)\n'
          '    for _ in range(40):\n'
          '        try:\n'
          '            with open("/logs/verifier/reward.txt", "w") as fh:\n'
          '                fh.write("1\\n")\n'
          '            out.line("late reward written")\n'
          '        except Exception as exc:\n'
          '            out.line("late reward %s" % type(exc).__name__)\n'
          '        time.sleep(1)\n'
          '    os._exit(0)')


def probe_plant_record():
    probe("plant-record", "writes a record claiming every program and lets the worker go on",
          '    import json\n'
          '    try:\n'
          '        with open("/scratch/record.json", "w") as fh:\n'
          '            json.dump([], fh)\n'
          '        out.line("planted")\n'
          '    except Exception as exc:\n'
          '        out.line("plant %s" % type(exc).__name__)')


def probe_crash_worker():
    probe("crash-worker", "plants a record and exits the worker clean before it is overwritten",
          '    import json\n'
          '    try:\n'
          '        with open("/scratch/record.json", "w") as fh:\n'
          '            json.dump([{"name": "key-dup", "n": 0, "digest": "", "prog": ""}], fh)\n'
          '        out.line("planted, exiting")\n'
          '    except Exception as exc:\n'
          '        out.line("plant %s" % type(exc).__name__)\n'
          '    os._exit(0)')


def probe_malformed():
    probe("malformed", "spoils the record as the worker leaves",
          '    import atexit\n'
          '\n'
          '    def spoil():\n'
          '        for path in ("/scratch/record.json", "/scratch/record.part"):\n'
          '            try:\n'
          '                with open(path, "w") as fh:\n'
          '                    fh.write("{not json")\n'
          '            except Exception:\n'
          '                pass\n'
          '\n'
          '    atexit.register(spoil)\n'
          '    out.line("spoiler armed")')


def probe_shrink_set():
    probe("shrink-set", "shrinks the population it is run on and tries to rewrite the generator",
          '    for path, text in (("/scratch/each", "1\\n"), ("/tests/gen.py", "FAMILIES = ()\\n"),\n'
          '                       ("/tests/cases.py", "ORDER = []\\n")):\n'
          '        try:\n'
          '            with open(path, "w") as fh:\n'
          '                fh.write(text)\n'
          '            out.line("rewrote %s" % path)\n'
          '        except Exception as exc:\n'
          '            out.line("%s %s" % (path, type(exc).__name__))')


def probe_disarm_grader():
    probe("disarm-grader", "rewrites the grading file so nothing is asserted",
          '    try:\n'
          '        with open("/tests/test_outputs.py", "w") as fh:\n'
          '            fh.write("def test_ok():\\n    assert True\\n")\n'
          '        out.line("grader rewritten")\n'
          '    except Exception as exc:\n'
          '        out.line("grader %s" % type(exc).__name__)')


def probe_uncollected_file():
    """The correct flow in a file beside the six, which is never collected."""
    f = {part: (SOL / part).read_text(encoding="utf-8") for part in PARTS}
    own = f["sess.py"]
    f["sess.py"] = "from tx.own import Session  # noqa: F401\n"
    write("probe-uncollected-file", "puts the flow in a file beside the six and imports it",
          f, reading=False, extra={"/app/tx/own.py": own})


FORGE = '''

GT = %s

PROGS = %s

KNOWN = {}
for _name, _lines in PROGS.items():
    _h = "\\n".join(ln for ln in _lines if ln.split()[0] in ("table", "check", "fk", "row"))
    _s = [ln for ln in _lines if ln.split()[0] not in ("table", "check", "fk", "row")]
    KNOWN.setdefault(_h, []).append([_s, GT[_name]])


def _v(v):
    return "-" if v is None else str(v)


def _head(cat, rows):
    out = []
    for t in cat.tables.values():
        out.append("table %%s %%s %%s" %% (t.name, t.key, " ".join(t.cols)))
    for c in cat.cons:
        tail = " deferrable deferred" if c.deferred else (" deferrable" if c.deferrable else "")
        if c.kind == "check":
            test = "notnull" if c.test == "notnull" else "min %%d" %% c.floor
            out.append("check %%s %%s %%s %%s%%s" %% (c.name, c.table, c.col, test, tail))
        else:
            out.append("fk %%s %%s %%s %%s %%s%%s" %% (c.name, c.table, c.col, c.parent,
                                                 c.action, tail))
    for t, k, vals in rows:
        out.append("row %%s %%d %%s" %% (t, k, " ".join(_v(v) for v in vals)))
    return "\\n".join(out)


def _text(st):
    if st.op in ("begin", "commit", "rollback"):
        return st.op
    if st.op == "back":
        return "rollback to " + st.name
    if st.op in ("savepoint", "release"):
        return "%%s %%s" %% (st.op, st.name)
    if st.op == "set":
        return "set %%s %%s" %% (st.name, st.want)
    if st.op == "insert":
        return "insert %%s %%d %%s" %% (st.table, st.key, " ".join(_v(v) for v in st.vals))
    if st.op == "update":
        return "update %%s %%d %%s" %% (st.table, st.key,
                                     " ".join("%%s %%s" %% (c, _v(v)) for c, v in st.sets))
    return "delete %%s %%d" %% (st.table, st.key)


def _outcome(line):
    w = line.split()
    if w[0] == "raise":
        return ("raise", w[1], w[2], int(w[3]))
    if w[0] != "ok":
        return (w[0],)
    gone, came = [], []
    for i in range(1, len(w), 3):
        e = (w[i][1:], w[i + 1], int(w[i + 2]))
        (gone if w[i][0] == "-" else came).append(e)
    return ("ok", gone, came)


class Session:
    def __init__(self, cat, rows):
        self.real = Real(cat, rows)
        self.pool = KNOWN.get(_head(cat, rows), [])
        self.seen = []

    def step(self, st):
        got = self.real.step(st)
        self.seen.append(_text(st))
        n = len(self.seen)
        for stmts, out in self.pool:
            if stmts[:n] == self.seen:
                return _outcome(out[n - 1])
        return got
'''


def forge_hand():
    """The frozen answer for every hand program, recognised by its declarations, rows and the
    statements seen so far, over BASE for anything else. Passes every enumerated program by
    construction and nothing it has not seen.

    It carries tests/seal/gt.json verbatim, as the adversary the anti-cheat gate models would:
    one that has already read the answer key. tools/forgecheck.py looks for exactly that."""
    gt = json.loads((lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    cases, _gen, _model = lab.sealed()
    progs = {name: cases.prog(name) for name in cases.ORDER}
    f = probe_base()
    f["sess.py"] = f["sess.py"].replace("class Session:", "class Real:", 1) + \
        FORGE % (json.dumps(gt, sort_keys=True), json.dumps(progs))
    write("forge-hand", "carries the frozen answer for every hand program, over BASE otherwise",
          f, reading=False)


def main():
    OUT.mkdir(exist_ok=True)
    for p in OUT.glob("cheat-*.sh"):
        p.unlink()
    for build in READING_BUILDERS:
        build()
    for build in (slow_copy, slow_scan, slow_ledger, const_ok,
                  probe_answer_key, probe_privilege, probe_late_reward, probe_plant_record,
                  probe_crash_worker, probe_malformed, probe_shrink_set, probe_disarm_grader,
                  probe_uncollected_file, forge_hand):
        build()
    print("wrote %d cheats: %d readings" % (len(MADE), len(READINGS)))


if __name__ == "__main__":
    main()
