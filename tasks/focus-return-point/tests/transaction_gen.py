"""Seeded legal render-frame histories; this module never computes focus."""

import copy
import hashlib
import random


class InputState:
    """Track only the input grammar and tree invariants, including rollback."""

    def __init__(self):
        self.nodes = {}
        self.screens = set()
        self.stack = []
        self.pushed = set()
        self.frames = []
        self.names = set()
        self.allocations = 0
        self.events = 0
        self.max_depth = 0
        self.reuses = 0

    def subtree(self, name):
        result = [name]
        for child in self.nodes[name]["kids"]:
            result.extend(self.subtree(child))
        return result

    def widgets(self):
        return sorted(set(self.nodes) - self.screens)

    def check(self):
        assert self.allocations <= 40
        assert len(self.screens) <= 5
        assert len(self.frames) <= 4
        selected = set()
        for name, node in self.nodes.items():
            if name in self.screens:
                assert node["par"] is None
                continue
            assert node["par"] in self.nodes
            assert name in self.nodes[node["par"]]["kids"]
            assert node["screen"] == self.nodes[node["par"]]["screen"]
            assert not ("comp" in node["flags"] and
                        ("foc" in node["flags"] or node["group"] is not None))
            if node["group"] is not None and "sel" in node["flags"]:
                key = node["screen"], node["group"]
                assert key not in selected
                selected.add(key)

    def apply(self, line):
        args = line.split()
        op = args[0]
        if op == "screen":
            name = args[1]
            assert name not in self.nodes and not self.events
            self.screens.add(name)
            self.nodes[name] = dict(par=None, kids=[], flags=set(), group=None,
                                    screen=name)
        elif op in ("w", "add"):
            name, parent = args[1:3]
            assert name not in self.nodes and name not in self.screens
            assert parent in self.nodes
            if op == "w":
                assert not self.events
                at, flags = len(self.nodes[parent]["kids"]), args[3:]
            else:
                at, flags = int(args[3]), args[4:]
            assert 0 <= at <= len(self.nodes[parent]["kids"])
            groups = [flag[4:] for flag in flags if flag.startswith("grp=")]
            assert len(groups) <= 1
            self.nodes[name] = dict(par=parent, kids=[],
                                    flags={flag for flag in flags if not flag.startswith("grp=")},
                                    group=groups[0] if groups else None,
                                    screen=self.nodes[parent]["screen"])
            self.nodes[parent]["kids"].insert(at, name)
            self.allocations += 1
            self.reuses += int(name in self.names)
            self.names.add(name)
        elif op == "begin":
            assert len(self.frames) < 4
            self.frames.append(copy.deepcopy(self.nodes))
            self.max_depth = max(self.max_depth, len(self.frames))
        elif op in ("commit", "abort"):
            assert self.frames
            snapshot = self.frames.pop()
            if op == "abort":
                self.nodes = snapshot
        elif op == "push":
            name = args[1]
            assert not self.frames and name in self.screens and name not in self.pushed
            self.stack.append(name)
            self.pushed.add(name)
        elif op == "pop":
            name = args[1]
            assert not self.frames and name in self.stack
            self.stack.remove(name)
            for child in self.subtree(name):
                del self.nodes[child]
            self.screens.remove(name)
        elif op in ("tab", "back", "next", "prev"):
            assert len(args) == 1
        elif op == "want":
            assert len(args) == 2 and args[1] not in self.screens
        elif op == "drop":
            name = args[1]
            assert name in self.nodes and name not in self.screens
            self.nodes[self.nodes[name]["par"]]["kids"].remove(name)
            for child in self.subtree(name):
                del self.nodes[child]
        elif op == "move":
            name, parent, at = args[1], args[2], int(args[3])
            assert name in self.nodes and name not in self.screens
            assert parent in self.nodes and parent not in self.subtree(name)
            assert self.nodes[name]["screen"] == self.nodes[parent]["screen"]
            self.nodes[self.nodes[name]["par"]]["kids"].remove(name)
            assert 0 <= at <= len(self.nodes[parent]["kids"])
            self.nodes[parent]["kids"].insert(at, name)
            self.nodes[name]["par"] = parent
        elif op == "pick":
            node = self.nodes[args[1]]
            if node["group"] is not None:
                for other in self.nodes.values():
                    if (other["screen"], other["group"]) == (node["screen"], node["group"]):
                        other["flags"].discard("sel")
                node["flags"].add("sel")
        elif op in ("hide", "show", "off", "on", "shut", "open"):
            flag = {"hide": "hid", "show": "hid", "off": "off", "on": "off",
                    "shut": "shut", "open": "shut"}[op]
            flags = self.nodes[args[1]]["flags"]
            if op in ("hide", "off", "shut"):
                flags.add(flag)
            else:
                flags.discard(flag)
        else:
            raise AssertionError("unknown event: " + line)
        self.events += int(op not in ("screen", "w"))
        self.check()


def text(seed, index):
    rng = random.Random(int(hashlib.sha256(f"{seed}/transaction/{index}".encode()).hexdigest(), 16))
    state = InputState()
    lines = []

    def emit(line):
        state.apply(line)
        lines.append(line)

    declarations = [
        "screen s", "w a s foc", "w c s comp", "w x c foc",
        "w d c comp", "w i d foc", "w j d foc grp=g", "w k d foc grp=g sel",
        "w e d comp", "w u e foc", "w v e foc", "w y c foc", "w z s foc",
        "w h s", "w h1 h foc", "screen m", "w m1 m foc",
        "screen n", "w n1 n foc",
    ]
    for line in declarations:
        emit(line)

    # The first frame discards nested requests and mutations but commits a
    # replacement of a queued target. The next frame discards an inner commit.
    prefix = [
        "push s", "want v", "begin", "want v", "drop v", "add v e 1 foc",
        "begin", "hide d", "begin", "want i", "begin", "tab", "abort",
        "commit", "abort", "next", "commit", "back", "tab",
        "begin", "want u", "drop e", "add e d 2 comp", "add u e 0 foc",
        "begin", "add draft e 1 foc", "want draft", "next", "commit", "abort",
        "add draft c 3 foc", "next", "push m", "begin", "want v", "begin",
        "drop v", "add v e 1 foc", "pick j", "commit", "want m1", "tab",
        "commit", "pop m", "back", "tab",
    ]
    for line in prefix:
        emit(line)

    serial = 0
    while state.events < 108:
        op = rng.randrange(16)
        pool = state.widgets()
        if op <= 3:
            emit(rng.choice(["tab", "back", "next", "prev"]))
        elif op == 4 and pool:
            emit("want " + rng.choice(pool))
        elif op == 5 and pool:
            emit(rng.choice(["hide", "show", "off", "on", "shut", "open"]) +
                 " " + rng.choice(pool))
        elif op == 6 and pool:
            name = rng.choice(pool)
            forbidden = set(state.subtree(name))
            hosts = sorted(parent for parent, node in state.nodes.items()
                           if parent not in forbidden and
                           node["screen"] == state.nodes[name]["screen"])
            if hosts:
                parent = rng.choice(hosts)
                count = len(state.nodes[parent]["kids"]) - int(state.nodes[name]["par"] == parent)
                emit(f"move {name} {parent} {rng.randrange(count + 1)}")
        elif op == 7 and len(pool) > 5:
            emit("drop " + rng.choice(pool))
        elif op == 8 and state.allocations < 40 and len(pool) < 28:
            serial += 1
            name = f"new{serial}"
            retired = sorted(state.names - set(state.nodes) - state.screens)
            if retired and rng.random() < 0.8:
                name = rng.choice(retired)
            parent = rng.choice(sorted(state.nodes))
            at = rng.randrange(len(state.nodes[parent]["kids"]) + 1)
            # New members start unselected. Only pick changes an existing
            # group's selection, including across nested composite scopes.
            flags = rng.choice(["foc", "foc grp=g", "comp", "", "foc hid"])
            emit(f"add {name} {parent} {at} {flags}".rstrip())
        elif op == 9 and pool:
            emit("pick " + rng.choice(pool))
        elif op in (10, 11) and len(state.frames) < 4:
            emit("begin")
        elif op in (12, 13) and state.frames:
            emit("commit" if op == 12 else "abort")
        elif op == 14 and not state.frames:
            available = sorted(state.screens - state.pushed)
            if available:
                emit("push " + rng.choice(available))
            elif len(state.stack) > 1:
                emit("pop " + rng.choice(state.stack))
            else:
                emit("begin")
        elif op == 15 and not state.frames and len(state.stack) > 1:
            emit("pop " + rng.choice(state.stack))
        else:
            emit(rng.choice(["tab", "back", "next", "prev"]))

    while state.frames:
        emit(rng.choice(["commit", "commit", "abort"]))
    while len(state.stack) > 1:
        emit("pop " + state.stack[-1])
    for key in ["tab", "next", "prev", "back"]:
        emit(key)
    if state.stack:
        emit("pop " + state.stack[-1])
    emit("tab")
    assert state.events <= 120
    assert not state.frames
    return "\n".join(lines) + "\n"


def batch(seed, count):
    return [(f"transaction-{i:04d}", text(seed, i)) for i in range(count)]


def audit(seed="frame-mixed-v1", count=600):
    summary = dict(scripts=0, events=0, maximum_events=0, maximum_allocations=0,
                   maximum_depth=0, reused_ids=0, begins=0, commits=0, aborts=0)
    for _, script in batch(seed, count):
        state = InputState()
        for line in script.splitlines():
            state.apply(line)
            op = line.split()[0]
            if op in ("begin", "commit", "abort"):
                summary[{"begin": "begins", "commit": "commits", "abort": "aborts"}[op]] += 1
        assert not state.frames and not state.stack
        summary["scripts"] += 1
        summary["events"] += state.events
        summary["maximum_events"] = max(summary["maximum_events"], state.events)
        summary["maximum_allocations"] = max(summary["maximum_allocations"], state.allocations)
        summary["maximum_depth"] = max(summary["maximum_depth"], state.max_depth)
        summary["reused_ids"] += state.reuses
    return summary


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", default="frame-mixed-v1")
    parser.add_argument("--count", type=int, default=600)
    args = parser.parse_args()
    print(json.dumps(audit(args.seed, args.count), sort_keys=True))
