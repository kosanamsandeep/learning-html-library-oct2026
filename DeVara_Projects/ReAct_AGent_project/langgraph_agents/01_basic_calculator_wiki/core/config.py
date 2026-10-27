from __future__ import annotations
from pathlib import Path
from functools import lru_cache
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()
ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    temperature: float = 0.0
    verbose: bool = True

    @property
    def prompts_dir(self) -> Path: return ROOT / "data" / "prompts"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache
def _g() -> Settings: return Settings()
settings = _g()
