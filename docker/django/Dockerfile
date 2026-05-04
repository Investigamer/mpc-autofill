# UV Docker / Multi-Stage
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0

# Install project dependencies
WORKDIR /app/MPCAutofill
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=MPCAutofill/uv.lock,target=uv.lock \
    --mount=type=bind,source=MPCAutofill/pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Copy project files
COPY MPCAutofill/. /app/MPCAutofill/.
COPY docker/django/scripts/. /app/MPCAutofill/scripts/.

# Install the project
RUN --mount=type=cache,target=/root/.cache/uv \
    set -eux; \
    uv sync --locked --no-dev; \
    uv add gunicorn; \
    mv config config-staging

# Switch to final image without uv
FROM python:3.12-slim-bookworm

# Copy application from the builder, add project to path
COPY --from=builder --chown=urza:urza /app /app
ENV PATH="/app/MPCAutofill/.venv/bin:$PATH"
WORKDIR /app/MPCAutofill

# Install gosu, make scripts executable, cleanup caches
RUN set -eux; \
	apt-get update && apt-get install -y --no-install-recommends gosu dos2unix; \
    chmod -R +x ./scripts && dos2unix ./scripts/*.sh; \
    apt-get purge -y dos2unix; \
	rm -rf /var/lib/apt/lists/*

###
# * Initialization Logic
#   * pre-run.sh: Setup non-root user, run basic pre-flight checks, run one of the following as non-root user:
#       - entrypoint.sh: (APP_RUN_MODE="server") Update data, run CMD below or as defined in docker-compose.
#       - worker.entrypoint.sh: (APP_RUN_MODE="worker") Run Django Q2 cluster.
###
ENTRYPOINT ["./scripts/pre-run.sh"]
CMD ["gunicorn", "MPCAutofill.wsgi:application", "--bind=0.0.0.0:8000", "--workers=8", "--timeout=60", "--access-logfile=-", "--error-logfile=-", "--log-level=info", "2>&1"]
