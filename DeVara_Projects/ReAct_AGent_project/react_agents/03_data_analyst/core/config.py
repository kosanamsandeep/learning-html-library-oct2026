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
    max_iterations: int = 15
    verbose: bool = True
    csv_path: str = str(ROOT / "data" / "sales.csv")
    db_path: str = str(ROOT / "data" / "_db" / "analyst.db")

    @property
    def prompts_dir(self) -> Path: return ROOT / "data" / "prompts"
    @property
    def charts_dir(self) -> Path: return ROOT / "data" / "charts"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache
def _g() -> Settings: return Settings()
settings = _g()
