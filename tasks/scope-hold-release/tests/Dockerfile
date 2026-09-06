FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2
COPY . /tests/
RUN mv /tests/pristine /pristine
RUN mkdir -p /app
RUN mkdir -p /app/wire
RUN mkdir -p /work
RUN chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py
RUN chmod 755 /tests/test.sh
