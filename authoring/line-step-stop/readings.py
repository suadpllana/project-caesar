"""Write every wrong reading as a patched copy of the reference, under readings/<name>/.

Each reading is a list of (file, old, new) replacements applied to the reference files.
Every replacement must fire at least once (count recorded), or the script fails: a patch that
silently changes nothing produces a "reading" that is the reference, scores 1 for the wrong
reason, and hides the gap it was written to find.
"""
import os
import re
import shutil
import sys

from lab import SOL, HERE

OUT = os.path.join(HERE, "readings")

# name -> (what the reading believes, [(file, old, new, regex?)])
READINGS = {
    "ret-address": (
        "caller frames are shown at the return address instead of the call instruction",
        [("frames.py", "[(r - 1, 0) for r in reversed(stack)]", "[(r, 0) for r in reversed(stack)]", False)]),
    "no-adopt": (
        "a part-way landing keeps the line being stepped",
        [("steps.py", "            if r.line:\n                self.line = r.line\n            return q",
          "            return q", False)]),
    "ns-stops": (
        "a non-statement row start of another line stops the step",
        [("steps.py", "if r.stmt and r.line and r.line != self.line:", "if r.line and r.line != self.line:", False)]),
    "ns-adopts": (
        "a non-statement row start makes its line the line being stepped",
        [("steps.py", "                    self.hid = 0\n                    return \"step\"\n                return q",
          "                    self.hid = 0\n                    return \"step\"\n                if not r.stmt and r.line:\n                    self.line = r.line\n                return q", False)]),
    "zero-stops": (
        "a line-0 statement row start stops the step",
        [("steps.py", "if r.stmt and r.line and r.line != self.line:", "if r.stmt and r.line != self.line:", False)]),
    "same-line-stops": (
        "any statement row start stops, even of the line being stepped",
        [("steps.py", "if r.stmt and r.line and r.line != self.line:", "if r.stmt and r.line:", False)]),
    "entry-always-in": (
        "an instance entry is always stepped into (step) or over (next), whatever its call line",
        [("steps.py", "if below[0].call == self.line:", "if True:", False)]),
    "entry-never-in": (
        "an instance entry always stops at the call site with everything hidden",
        [("steps.py", "if below[0].call == self.line:", "if False:", False)]),
    "reveal-all": (
        "step at a call site reveals every hidden instance at once",
        [("steps.py", "                self.hid -= 1\n", "                self.hid = 0\n", False)]),
    "never-hide": (
        "inline frames are read off the program counter and never hidden",
        [("steps.py", "self.hid = len(below) - 1", "self.hid = 0", False),
         ("steps.py", "self.hid = len(below)\n", "self.hid = 0\n", False),
         ("steps.py", "self.hid = len(m.starting(q))", "self.hid = 0", False)]),
    "finish-real": (
        "finish from an inlined frame runs until the real frame returns",
        [("steps.py", "        if isinstance(scope, Inl):\n            out = self._leave(scope, depth)",
          "        if False:\n            out = self._leave(scope, depth)", False),
         ("steps.py", "        else:\n            ret = stack[-1]\n", "        else:\n            ret = stack[-1] if stack else -1\n", False)]),
    "trust-first-hit": (
        "a planted return address or instance exit is trusted on its first hit, at any depth",
        [("steps.py", "if q == ret and self._depth() == self.depth:", "if q == ret:", False),
         ("steps.py", "if q == ret and self._depth() == depth - 1:", "if q == ret:", False),
         ("steps.py", "if q == inst.hi + 1 and self._depth() == depth:", "if q == inst.hi + 1:", False)]),
    "rowless-stops": (
        "step stops at the entry of a function that has no lines",
        [("steps.py", "if self.into and m.fn[q].lines:", "if self.into:", False)]),
    "break-per-function": (
        "a breakpoint gets one location per function, ignoring inline instances",
        [("marks.py", "scope = m.chain(r.at)[-1]", "scope = m.chain(r.at)[0]", False)]),
    "break-every-row": (
        "a breakpoint gets every statement row of its line",
        [("marks.py", "        if id(scope) not in lowest or r.at < lowest[id(scope)]:\n            lowest[id(scope)] = r.at",
          "        lowest[r.at] = r.at", False)]),
    "break-ns-rows": (
        "non-statement rows are breakpoint locations too",
        [("marks.py", "if not r.stmt or r.line != line:", "if r.line != line:", False)]),
    "cont-rechecks": (
        "cont stops again at once when it starts on a location",
        [("steps.py", "    def cont(self):\n        if self._go(set()) is None:",
          "    def cont(self):\n        if self.link.pc() in self.locs:\n            self.hid = 0\n            return \"hit\"\n        if self._go(set()) is None:", False)]),
    "return-keeps-line": (
        "after the stepping frame returns, a part-way landing keeps the callee's line",
        [("steps.py", "                self.scope = ch[len(ch) - 1 - len(m.starting(q))]\n",
          "                self.scope = ch[len(ch) - 1 - len(m.starting(q))]\n                self._keep = True\n", False),
         ("steps.py", "            if r.line:\n                self.line = r.line\n            return q",
          "            if r.line and not getattr(self, \"_keep\", False):\n                self.line = r.line\n            self._keep = False\n            return q", False)]),
    "finish-shows-all": (
        "finish leaves the instances starting where it lands visible",
        [("steps.py", "        self.hid = len(m.starting(q))\n        return \"done\"",
          "        self.hid = 0\n        return \"done\"", False)]),
    "hit-hides": (
        "a hit hides the instances starting at its address, like a step stop",
        [("steps.py", r'self\.hid = 0\n(\s+)return "hit"',
          r'self.hid = len(self.m.starting(self.link.pc()))\n\1return "hit"', True)]),
    "call-return-unjudged": (
        "a call stepped over never counts as passing into another row",
        [("steps.py", "                if lo <= q <= hi:\n                    pc = q\n                    continue\n            elif d < self.depth:",
          "                pc = q\n                continue\n            elif d < self.depth:", False)]),
    "call-return-always-judged": (
        "a call stepped over always counts as arriving part-way into its row",
        [("steps.py", "                if lo <= q <= hi:\n                    pc = q\n                    continue\n            elif d < self.depth:",
          "            elif d < self.depth:", False)]),
    "leave-takes-call-line": (
        "leaving an inlined instance makes its call line the line being stepped",
        [("steps.py", "            while isinstance(scope, Inl) and not scope.lo <= q <= scope.hi:\n                scope = scope.up",
          "            while isinstance(scope, Inl) and not scope.lo <= q <= scope.hi:\n                self.line = scope.call\n                scope = scope.up", False)]),
    "next-reveals": (
        "next at a call site reveals the hidden instance like step",
        [("steps.py", "        if self.hid:\n            if into:", "        if self.hid:\n            if True:", False)]),
    "hidden-shows-pc-line": (
        "a visible scope above a hidden instance shows the line at the pc, not the call line",
        [("frames.py", "line = ch[k + 1].call if k + 1 < len(ch) else m.line(addr)",
          "line = ch[k + 1].call if k + 1 < len(ch) - hidden else m.line(addr)", False)]),
    "run-skips-entry": (
        "run does not stop on a location at the first address",
        [("steps.py", "    def run(self):\n        if self.link.pc() in self.locs:",
          "    def run(self):\n        if False:", False)]),
    "inrow-call-unplanted": (
        "a call whose target lies inside the current row needs no planted address",
        [("steps.py", "                elif op == \"call\":\n                    exits.add(ins[1])",
          "                elif op == \"call\":\n                    if not lo <= ins[1] <= hi:\n                        exits.add(ins[1])", False)]),
    "ret-unplanted": (
        "a row that returns needs no planted return address",
        [("steps.py", "            if has_ret:\n                stack = self.link.stack()", "            if False:\n                stack = self.link.stack()", False)]),
    "step-callee-shows-all": (
        "stepping into a function leaves the instances starting at its entry visible",
        [("steps.py", "                if self.into and m.fn[q].lines:\n                    self.hid = len(m.starting(q))",
          "                if self.into and m.fn[q].lines:\n                    self.hid = 0", False)]),
}


def build(name):
    what, patches = READINGS[name]
    d = os.path.join(OUT, name)
    if os.path.exists(d):
        shutil.rmtree(d)
    os.makedirs(d)
    texts = {}
    for f in ("frames.py", "marks.py", "steps.py"):
        texts[f] = open(os.path.join(SOL, f)).read()
    touched = set()
    for f, old, new, is_re in patches:
        if is_re:
            texts[f], n = re.subn(old, new, texts[f])
        else:
            n = texts[f].count(old)
            texts[f] = texts[f].replace(old, new)
        if n == 0:
            raise SystemExit("reading %s: patch did not fire in %s: %r" % (name, f, old[:60]))
        touched.add(f)
    for f in touched:
        assert "\r" not in texts[f]
        with open(os.path.join(d, f), "w", newline="\n") as fh:
            fh.write("# wrong reading: %s\n" % what + texts[f])
    return d


if __name__ == "__main__":
    names = sys.argv[1:] or list(READINGS)
    for n in names:
        build(n)
    print("wrote %d readings to %s" % (len(names), OUT))


# The instruction sentence that rules each reading out, verbatim (write_trace.py checks it).
RULE = {
    "ret-address": "The innermost frame is read at the program counter and each caller at its return address minus one, its `call`",
    "no-adopt": "Part-way into a row, a line that is not 0 becomes the stepping line",
    "ns-stops": "a statement row whose line is not 0 and differs from the stepping line stops the command",
    "ns-adopts": "No other arrival stops them or changes the stepping line",
    "zero-stops": "a statement row whose line is not 0 and differs from the stepping line stops the command",
    "same-line-stops": "a statement row whose line is not 0 and differs from the stepping line stops the command",
    "entry-always-in": "when its call line equals the stepping line, `step` stops with it visible and the deeper ones hidden",
    "entry-never-in": "when its call line equals the stepping line, `step` stops with it visible and the deeper ones hidden",
    "reveal-all": "`step` makes the outermost hidden one visible and stops without running anything",
    "never-hide": "The innermost frame may have its deepest scopes hidden",
    "finish-real": "When the deepest visible scope of the innermost frame is an instance, `finish` runs until the frame leaves that instance",
    "trust-first-hit": "`next` runs it until it returns",
    "rowless-stops": "`step` stops at the first address of the called function if that function has lines, hiding the instances that start there, and otherwise runs it until it returns",
    "break-per-function": "each body or instance with statement rows of line L gives the breakpoint one address, the lowest of them",
    "break-every-row": "each body or instance with statement rows of line L gives the breakpoint one address, the lowest of them",
    "break-ns-rows": "each body or instance with statement rows of line L gives the breakpoint one address",
    "cont-rechecks": "The instruction a command starts at runs without that check",
    "return-keeps-line": "The stepping line is kept and the arrival is judged",
    "finish-shows-all": "It stops where it lands, hiding the instances that start there",
    "hit-hides": "A stop hides nothing unless a rule below says so",
    "call-return-unjudged": "A call that returns counts as a move from the `call` to its return address",
    "call-return-always-judged": "A call that returns counts as a move from the `call` to its return address",
    "leave-takes-call-line": "the enclosing scope that holds the new address becomes the stepping scope first",
    "next-reveals": "`next` runs until the frame leaves that instance and then judges where it lands",
    "hidden-shows-pc-line": "The scope above them still shows the call line of the first hidden one",
    "run-skips-entry": "except that `run` stops at once when address 0 is a breakpoint",
    "inrow-call-unplanted": "`step` stops at the first address of the called function if that function has lines",
    "ret-unplanted": "When the stepping frame returns, its caller becomes the stepping frame",
    "step-callee-shows-all": "`step` stops at the first address of the called function if that function has lines, hiding the instances that start there",
}
assert set(RULE) == set(READINGS), set(RULE) ^ set(READINGS)
