FROM docker.io/astral/uv:0.12.13-python3.14-trixie-slim@sha256:d2525beeae88affd18389bf69292abf9b5cbbb3f5c5242b6da3d20e304959b37 AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app
COPY pyproject.toml uv.lock README.md LICENSE.md ./
RUN uv sync --locked --no-dev --no-install-project
COPY scim2_cli ./scim2_cli
RUN uv sync --locked --no-dev --no-editable

FROM python:3.14-slim-trixie@sha256:9aaa474097d094040649f2162a627c0049b408f52138d980916788d80f04802f

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /work
USER nobody
ENTRYPOINT ["scim2"]
