FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.8 /uv /bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
# 手元のビルドで社内プロキシやウイルス対策ソフトの証明書が必要な場合だけ、--secret id=extra_ca で渡す。
# イメージには残らない。CI では渡さない
RUN --mount=type=secret,id=extra_ca,required=false \
    if [ -f /run/secrets/extra_ca ]; then export SSL_CERT_FILE=/run/secrets/extra_ca; fi; \
    uv sync --locked --no-dev --no-install-project

COPY app ./app

RUN useradd --system --uid 10001 app
USER app

ENV PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "exec /app/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
