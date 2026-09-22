OPS = {"nop": 0, "set": 1, "in": 2, "dec": 3, "jnz": 4, "jmp": 5, "call": 6, "ret": 7}
REGS = "abcd"


def load_code(text):
    code = []
    entry = None
    for raw in text.splitlines():
        w = raw.split()
        if not w:
            continue
        if w[0] == "fn" and entry is None:
            entry = int(w[2])
        if not w[0].isdigit():
            continue
        if int(w[0]) != len(code):
            raise ValueError("code out of order at %s" % w[0])
        op = OPS[w[1]]
        x = y = 0
        if op in (1, 2, 3, 4):
            x = REGS.index(w[2])
        if op == 1:
            y = int(w[3])
        elif op == 4:
            y = int(w[3])
        elif op in (5, 6):
            x = int(w[2])
        code.append((op, x, y))
    return code, entry


class Mach:
    def __init__(self, code, entry, tape):
        self.code = code
        self.pc = entry
        self.regs = [0, 0, 0, 0]
        self.calls = []
        self.tape = tape
        self.at = 0
        self.done = False

    def rets(self):
        return [r for r, _ in self.calls]

    def one(self):
        if self.done:
            return None
        op, x, y = self.code[self.pc]
        pc = self.pc
        if op == 0:
            pc += 1
        elif op == 1:
            self.regs[x] = y
            pc += 1
        elif op == 2:
            self.regs[x] = self.tape[self.at] if self.at < len(self.tape) else 0
            self.at += 1
            pc += 1
        elif op == 3:
            self.regs[x] -= 1
            pc += 1
        elif op == 4:
            pc = y if self.regs[x] else pc + 1
        elif op == 5:
            pc = x
        elif op == 6:
            self.calls.append((pc + 1, self.regs))
            self.regs = [0, 0, 0, 0]
            pc = x
        else:
            if not self.calls:
                self.done = True
                return None
            pc, self.regs = self.calls.pop()
        self.pc = pc
        return pc

    def go(self, stops):
        if self.done:
            return None
        code = self.code
        calls = self.calls
        tape = self.tape
        n = len(tape)
        pc = self.pc
        regs = self.regs
        at = self.at
        while True:
            op, x, y = code[pc]
            if op == 3:
                regs[x] -= 1
                pc += 1
            elif op == 4:
                pc = y if regs[x] else pc + 1
            elif op == 0:
                pc += 1
            elif op == 1:
                regs[x] = y
                pc += 1
            elif op == 2:
                regs[x] = tape[at] if at < n else 0
                at += 1
                pc += 1
            elif op == 5:
                pc = x
            elif op == 6:
                calls.append((pc + 1, regs))
                regs = [0, 0, 0, 0]
                pc = x
            else:
                if not calls:
                    self.done = True
                    break
                pc, regs = calls.pop()
            if pc in stops:
                break
        self.pc = pc
        self.regs = regs
        self.at = at
        return None if self.done else pc
