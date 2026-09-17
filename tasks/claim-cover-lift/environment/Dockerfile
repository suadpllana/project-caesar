FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app
COPY app_src/ ./

# A syntax error in the shipped tree should fail the build, not the first program someone runs.
RUN python -c "import compileall, sys; sys.exit(0 if compileall.compile_dir('/app', quiet=2) else 1)" \
 && find /app -name __pycache__ -type d -prune -exec rm -rf {} +
