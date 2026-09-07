FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY app_src /app
RUN for script in cases/*.txt; do python run_sheet.py "$script" >/dev/null; done
