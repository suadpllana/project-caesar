import sys


class Sink:
    def skip(self, rid):
        sys.stdout.write("skip %s\n" % rid)

    def void(self, rid):
        sys.stdout.write("void %s\n" % rid)

    def lay(self, rid, first, pieces, scored, num, den):
        sys.stdout.write("lay %s %d %d %d %d/%d\n" % (rid, first, pieces, scored, num, den))

    def drop(self, idx, wins, pos):
        sys.stdout.write("drop %d %d %d\n" % (idx, wins, pos))

    def step(self, idx, wins, pos, num, den):
        sys.stdout.write("step %d %d %d %d/%d\n" % (idx, wins, pos, num, den))
