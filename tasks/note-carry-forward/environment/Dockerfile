FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

COPY app_src/scr ./scr
COPY app_src/rev ./rev
COPY app_src/note ./note
COPY app_src/streams ./streams
COPY app_src/run_review.py ./run_review.py

RUN set -eux; \
    python run_review.py streams/guard.txt; \
    python run_review.py streams/repeat.txt
