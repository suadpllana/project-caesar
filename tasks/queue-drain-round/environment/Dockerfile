FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY app_src /app
WORKDIR /app
RUN python -c "import house.bk, house.ev, house.rnd; print(house.bk.OPEN, house.bk.PAID, house.bk.GONE)"
