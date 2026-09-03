FROM python:3.12-slim

WORKDIR /app
COPY app_src .

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

RUN python -c "import pnl.loop, pnl.net, pnl.lex, pnl.ev" \
 && python run_panel.py panels/plain.txt > /dev/null
