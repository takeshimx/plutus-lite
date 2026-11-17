import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    project_id: str
    dataset: str
    allowed_emails: frozenset[str]
    cors_origins: tuple[str, ...]
    bigquery_emulator_host: str | None
    rate_limit_per_minute: int = 60


def _split(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings(
        project_id=os.environ["GCP_PROJECT_ID"],
        dataset=os.environ.get("BQ_DATASET", "plutus_lite"),
        # メールアドレスはリポジトリに書かず、環境変数で渡す(ADR-002)
        allowed_emails=frozenset(e.lower() for e in _split(os.environ.get("ALLOWED_EMAILS", ""))),
        cors_origins=tuple(_split(os.environ.get("CORS_ORIGINS", ""))),
        bigquery_emulator_host=os.environ.get("BIGQUERY_EMULATOR_HOST") or None,
        rate_limit_per_minute=int(os.environ.get("RATE_LIMIT_PER_MINUTE", "60")),
    )
