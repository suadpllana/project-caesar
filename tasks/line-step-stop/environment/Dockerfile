FROM python:3.12-slim

# The target is a second Python process; keep both from leaving bytecode in /app.
ENV PYTHONDONTWRITEBYTECODE=1

COPY app_src /app
WORKDIR /app

# Play the short sample once so a broken link or target fails the build, not the session.
RUN python3 run_dbg.py samples/rows.img samples/rows.cmd samples/rows.tape > /dev/null \
    && chmod -R a+rX /app
