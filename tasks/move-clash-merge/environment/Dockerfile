FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY app_src /app
RUN python /app/run_sync.py /app/rounds/plain.txt > /dev/null \
    && python /app/run_sync.py /app/rounds/tidy.txt > /dev/null \
    && python /app/run_sync.py /app/rounds/away.txt > /dev/null
