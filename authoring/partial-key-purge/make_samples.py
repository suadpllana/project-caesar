"""Write the sample scripts shipped in /app/scripts. Authoring only.

tiny.txt is written by hand and is the worked example the brief quotes. The other three come
from the verifier's own generator with fixed seeds that the nonce population never uses, so
they show the graded shapes and sizes without being graded: a medium chain store, a store of
merge revisions and revisions based on one another, and one store of the deep family.
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.join(HERE, "..", "..", "tasks", "partial-key-purge")
sys.path.insert(0, os.path.join(TASK, "tests", "seal"))
import gen  # noqa: E402

OUT = os.path.join(TASK, "environment", "app_src", "scripts")

TINY = """table doc d
table rev d n bd bn
table note k d n
key doc_k doc d
key rev_k rev d n
key note_k note k
ref rev_doc rev d -> doc_k simple noaction
ref rev_base rev bd bn -> rev_k partial cascade
ref note_on note d n -> rev_k partial cascade
row doc 1 a
row rev 1 a 1 - -
row rev 2 a 2 a 1
row rev 3 a 3 a 1
row note 1 1 a 2
row note 2 2 a -
delete rev 2
dump note
delete rev 1
audit
"""


def write(name, text):
    assert "\r" not in text
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main():
    os.makedirs(OUT, exist_ok=True)
    write("tiny.txt", TINY)
    write("docs.txt", gen.story(random.Random("sample:docs"), "chain"))
    write("loops.txt", gen.story(random.Random("sample:loops:160"), "merge") + "audit\n")
    write("deep.txt", gen.deep(random.Random("sample:deep")))
    for name in sorted(os.listdir(OUT)):
        path = os.path.join(OUT, name)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        print(name, os.path.getsize(path), "bytes", text.count("\nrow ") + text.startswith("row "), "rows")


if __name__ == "__main__":
    main()
