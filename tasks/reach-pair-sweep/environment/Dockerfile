FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1

COPY app_src/ /app/

WORKDIR /app

RUN python run_prog.py progs/tiny.txt > /dev/null
