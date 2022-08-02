from functools import lru_cache
from pathlib import Path

from pydantic import BaseSettings, SecretStr, validator


APP_ROOT = Path(__file__).parent


class Settings(BaseSettings):
    app_root: Path = APP_ROOT

    ppa_service_create: str
    ppa_service_modify: str
    ppa_service_remove: str
    ppa_service_timeout: int
    ppa_key_id: str
    ppa_key_secret: str
    ppa_domain: str
    ppa_port: int

    @validator("ppa_service_create", "ppa_service_modify", "ppa_service_remove")
    def file_exists(cls, file: str):
        user_script = (APP_ROOT.parent / 'scripts' / file).resolve()
        if not user_script.exists():
            raise FileNotFoundError
        return user_script.as_posix()

    def __getitem__(self, item):
        return self.__dict__[item]

    class Config:
        env_file = APP_ROOT.parent / ".env"


@lru_cache
def get_settings():
    return Settings()
