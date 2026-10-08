FROM docker.io/astral/uv:0.12.13-python3.14-trixie-slim@sha256:d2525beeae88affd18389bf69292abf9b5cbbb3f5c5242b6da3d20e304959b37 AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app
COPY pyproject.toml uv.lock README.md LICENSE.md ./
RUN uv sync --locked --no-dev --no-install-project
COPY scim2_cli ./scim2_cli
RUN uv sync --locked --no-dev --no-editable

FROM python:3.14-slim-trixie@sha256:51dafde81dbdb6ebde285137a295cf18a47ca95234fe388a343719cb97305b3d

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /work
USER nobody
ENTRYPOINT ["scim2"]
