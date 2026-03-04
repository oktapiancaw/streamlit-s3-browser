# ===
# 🐍 Python base image
# ===
FROM python:3.10.12-slim-bookworm AS base

# Set common environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    VENV_PATH="/app/.venv"

# Create working directory
WORKDIR /app


# ===
# 🔧 Builder stage
# ===
FROM base AS builder

# Install `uv` (copy statically linked binary)
COPY --from=ghcr.io/astral-sh/uv:0.7.4 /uv /bin/uv

# Copy only lock + manifest first (for layer caching)
COPY uv.lock pyproject.toml ./

# Install dependencies without project code
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy full source
COPY . .

# Install again with project (excluding dev deps)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


# ===
# 🚀 Runtime / Development stage
# ===
FROM base AS development

COPY --from=ghcr.io/astral-sh/uv:0.7.4 /uv /bin/uv
# Copy pre-built app with dependencies and virtualenv
COPY --from=builder /app /app

# Activate virtual environment
ENV PATH="${VENV_PATH}/bin:$PATH"

# Optionally set working directory to /app
WORKDIR /app


ENTRYPOINT [ "streamlit", "run", "/app/src/main.py" , "--browser.gatherUsageStats", "false"]