# Nothing is shipped into this image. The single file the task is about,
# /app/change_script.py, gets written from scratch against the specification in
# instruction.md, and it is the only path the verifier reads back out.
#
# Only the Python standard library is importable when it is graded, so anything
# installed in here while working on it will not be present later on.
FROM python:3.13-slim-bookworm

WORKDIR /app

RUN mkdir -p /app
