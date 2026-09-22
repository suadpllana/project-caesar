FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

# Stage one runs as this user. Nothing else in the image does, which is what makes ownership
# a complete test for "came from the submission" when the survivors are cleared.
RUN useradd --create-home --uid 1002 sandbox

# The collected files come back at the paths they had, so their parent has to exist first.
RUN mkdir -p /app/eng
RUN mkdir -p /work
RUN mkdir -p /logs/verifier

COPY . /tests/

RUN chmod 700 /tests/seal
RUN chmod +x /tests/test.sh
