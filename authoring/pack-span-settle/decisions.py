"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
raw ones the shipped tree exposes at that moment - the room left in the window, the tokens a
record still has to place, the width the window was opened at, the scored positions a step has
taken and the floor it was opened with, and for a record its length, its piece count and how
many of the steps it touched were kept. Nothing derived is offered, because the derivation is
the task: neither a record's scored count nor its divisor is a feature of any row.

The verdict to want is that at least one graded quantity has no short rule. Two should not:
the piece a record puts in a window, because it is the largest of a bounded set under a
condition on what would be left over rather than a comparison between two visible numbers, and
a record's divisor, because it is a sum over the steps that were kept rather than a property of
the record at all. Two honestly do: a step is kept when its positions reach its floor, and a
window closes when it is full or the record continues, and both of those are stated in the
brief in as many words.

    python3 authoring/pack-span-settle/decisions.py
"""
import collections
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "pack-span-settle"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import gen  # noqa: E402
import cases  # noqa: E402
import model  # noqa: E402

ROWS = collections.defaultdict(list)


def _instrument():
    real_piece = model.piece_len
    real_open = model.Engine.open_window
    real_close_step = model.Engine.close_step
    real_settle = model.Engine.settle_record
    live = {}

    def open_window(self):
        real_open(self)
        live["ww"] = self.width
        live["eng"] = self

    def piece_len(room, rem):
        out = real_piece(room, rem)
        ww = live.get("ww", room)
        ROWS["piece-length"].append(
            ({"room": room, "rem": rem, "width": ww, "fill": ww - room},
             out if out is not None else 0))
        if out is not None:
            ROWS["window-closed"].append(
                ({"room_after": room - out, "rem_after": rem - out, "took": out, "width": ww},
                 room - out == 0 or rem - out > 0))
        return out

    def close_step(self):
        step = self.cur
        ROWS["step-kept"].append(
            ({"pos": step.positions, "flr": step.floor, "wins": step.windows,
              "cap": step.cap, "recs": len(step.share)},
             step.positions >= step.floor))
        real_close_step(self)

    def settle_record(self, rec):
        kept = sum(1 for i in rec.steps if self.steps[i].kept)
        divisor = sum(self.steps[i].share[rec.rid] for i in rec.steps if self.steps[i].kept)
        feats = {"n": rec.length, "parts": rec.pieces, "first": rec.first,
                 "steps": len(rec.steps), "kept": kept, "weight": rec.weight}
        ROWS["record-divisor"].append((dict(feats), divisor))
        ROWS["record-scored"].append((dict(feats), rec.length - rec.pieces))
        real_settle(self, rec)

    model.piece_len = piece_len
    model.Engine.open_window = open_window
    model.Engine.close_step = close_step
    model.Engine.settle_record = settle_record


def samples():
    _instrument()
    work = [cases.ops(name) for name in cases.ORDER]
    work += [lines for fam, _n, lines in gen.programs("decisions", 6) if fam not in ("wide", "deep")]
    for lines in work:
        model.Engine().run(lines)
    return dict(ROWS)


if __name__ == "__main__":
    for name, rows in sorted(samples().items()):
        print("%-18s %5d rows, %d distinct outcomes"
              % (name, len(rows), len({str(y) for _f, y in rows})))
