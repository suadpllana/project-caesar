FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# The client, its four example programs and nothing else. There is no ground truth here and no
# expected output beside the programs.
COPY app_src/ /app/

WORKDIR /app
