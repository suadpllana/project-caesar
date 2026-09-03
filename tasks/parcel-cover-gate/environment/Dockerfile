FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY app_src/base ./base
COPY app_src/bay ./bay
COPY app_src/feeds ./feeds
COPY app_src/run_feed.py ./run_feed.py
RUN python run_feed.py feeds/handover.txt > /dev/null \
 && python run_feed.py feeds/settle.txt > /dev/null
