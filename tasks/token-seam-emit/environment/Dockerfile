FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

WORKDIR /app

COPY app_src/tok ./tok
COPY app_src/strm ./strm
COPY app_src/reqs ./reqs
COPY app_src/run_stream.py ./run_stream.py

RUN python run_stream.py reqs/r1.txt reqs/r3.txt > /dev/null
