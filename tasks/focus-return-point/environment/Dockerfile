FROM python:3.12-slim
COPY app_src /app
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
RUN python run_ui.py cases/dialog.txt > /dev/null && python run_ui.py cases/stacked.txt > /dev/null
