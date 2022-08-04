import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseSettings, validator, constr


class FileError(Exception):
    pass


class Settings(BaseSettings):
    ppa_service_create: Path
    ppa_service_modify: Path
    ppa_service_remove: Path
    ppa_service_timeout: int = 180
    # HTTP signatures not implemented in Sonar yet
    # ppa_key_id: str
    # ppa_key_secret: str
    ppa_port: int = 8888
    ppa_log_level: constr(to_lower=True, regex='^(debug|info|warning|error)$')
    ppa_log_dir: str

    @validator("ppa_service_create", "ppa_service_modify", "ppa_service_remove")
    def file_exists(cls, file: Path):
        if not os.access(file, os.X_OK):
            raise FileError(f"{file.name} doesn't exist at given path, or isn't executable.")
        return file

    def __getitem__(self, item):
        return self.__dict__[item]


@lru_cache
def get_settings():
    return Settings()
