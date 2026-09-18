FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

COPY app_src/ /app/

# A COPY that misses part of the tree builds fine and dies at trial time with a compose
# error that looks like a broken task. Import every module and drive a session here, so a
# tree that cannot run fails the build instead.
RUN python -c "import mkt.rd, mkt.bk, mkt.ev, mkt.drv, eng.take, eng.shown, eng.hand, eng.hold, eng.trip" \
    && python run_book.py sess/s1.txt > /dev/null \
    && python run_book.py sess/s2.txt > /dev/null
