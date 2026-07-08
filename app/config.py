from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve dotenv files from project root (independent of process cwd).
# Load order: `.env.example` first, then `.env` so local `.env` overrides the template.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _dotenv_files() -> tuple[str, ...] | None:
    paths: list[str] = []
    for name in (".env.example", ".env"):
        candidate = _PROJECT_ROOT / name
        if candidate.is_file():
            paths.append(str(candidate))
    return tuple(paths) if paths else None


class Settings(BaseSettings):
    app_name: str = "LangGraph Demo"
    log_level: str = "INFO"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str | None = Field(
        default=None,
        description="OpenAI-compatible API base URL (proxy, Azure, etc.); omit for api.openai.com",
    )
    mcp_timeout_seconds: float = Field(
        default=30.0,
        ge=1.0,
        description="Timeout for MCP discovery and tool invocation",
    )
    mcp_tool_name_prefix: bool = Field(
        default=True,
        description="Prefix MCP tool names with server name to avoid collisions",
    )

    @field_validator("openai_base_url", mode="before")
    @classmethod
    def normalize_openai_base_url(cls, value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return str(value)

    @field_validator("openai_api_key", mode="before")
    @classmethod
    def normalize_openai_api_key(cls, value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return str(value)

    model_config = SettingsConfigDict(
        env_file=_dotenv_files(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
