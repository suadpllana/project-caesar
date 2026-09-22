import sys

from reb.mark import Marks
from reb.place import Place
from reb.prog import read
from reb.say import Say
from reb.sift import Sift
from reb.store import Store
from reb.tally import Tally
from reb.wait import Wait
from reb.walk import Walk


def run(text):
    say = Say()
    store = Store()
    marks = Marks()
    wait = Wait()
    place = Place(wait, say)
    walk = None
    sift = None
    for ins in read(text):
        head = ins[0]
        if head == "cfg":
            walk = Walk(store, marks, ins[1])
            sift = Sift(store, walk, marks)
        elif head == "set":
            store.put(ins[1], ins[2], ins[3], ins[4])
        elif head == "del":
            store.kill(ins[1])
        elif head == "copy":
            step(store, walk, place, say)
        elif head == "play":
            deal(sift, place, say, ins[1])
        elif head == "cut":
            close(store, walk, sift, place, say)
    return say.lines


def step(store, walk, place, say):
    keys, mark = walk.take()
    say.chunk(len(keys), walk.cur, mark)
    for k in keys:
        a, b, c = store.at(k)
        place.offer(k, a, b, c)


def deal(sift, place, say, n):
    for pos, kind, k, a, b, c, verdict in sift.take(n):
        say.entry(pos, k, verdict)
        if verdict != "done":
            continue
        if kind == "set":
            place.offer(k, a, b, c)
        else:
            place.remove(k)


def close(store, walk, sift, place, say):
    while True:
        before = walk.cur
        step(store, walk, place, say)
        deal(sift, place, say, store.depth())
        if walk.cur == before:
            break
    say.end(*Tally(place).close())


def main():
    with open(sys.argv[1], encoding="utf-8") as fh:
        text = fh.read()
    for line in run(text):
        print(line)


if __name__ == "__main__":
    main()
