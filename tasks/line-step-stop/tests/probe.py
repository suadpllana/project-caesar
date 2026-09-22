"""Worker for one graded session. Runs as the unprivileged debugger user.

It loads the pristine session driver with the three submitted files laid over it, attaches
to the target through the socket the judge handed it, plays the script, and writes the lines
the driver prints to the pipe the judge reads. It never sees the tape or the expected lines,
and nothing it writes can reach the verdict or the reward, which live in root-only places.

    probe.py APP SESSION_DIR SOCKET_FD LINES_FD
"""
import os
import sys

app, where, sock_fd, lines_fd = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
sys.path.insert(0, app)
lines = os.fdopen(lines_fd, "w", buffering=1)

from dbg.image import load  # noqa: E402
from dbg.sess import play  # noqa: E402
from tgt.link import attach  # noqa: E402

img = load(os.path.join(where, "p.img"))
with open(os.path.join(where, "p.cmd")) as f:
    cmds = f.read().splitlines()
play(img, attach(sock_fd), cmds, lambda line: lines.write(line + "\n"))
lines.flush()
