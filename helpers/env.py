from pydantic import BaseSettings, root_validator
import secrets
from typing import Optional


class EnvVariabels(BaseSettings):
    """
    Rules:
    - All variables must be in uppercase
    - All variables must be in .env file
    - All variables must be in .env.example file

    - ALL properties must be in lowercase
    """

    ENVIRONMENT: str = "development"
    IS_LOCAL: bool = False
    LOGIN_TOKEN_SECRET: str = secrets.token_hex(64)
    WATCH_TOKEN_SECRET: str = secrets.token_hex(64)
    FIRST_LOGIN_SECRET: str = secrets.token_hex(64)
    RESET_PASSWORD_SECRET: str = secrets.token_hex(64)
    REGISTRATION_TOKEN_SECRET: str = secrets.token_hex(64)

    DB_CONNECTION_STRING: str = "mongodb://localhost:27017"
    DB_NAME: str

    PORT: int = 8000

    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = None

    SITE_URL: str = "http://localhost:3000"

    SEND_GRID_KEY: str
    SEND_GRID_SENDER: str
    THREE_WALL_EMAIL: str

    BUCKET_NAME: str
    BUCKET_ALLOWED_ORIGINS: str

    COOKIE_DOMAIN: Optional[str] = None

    @root_validator
    def validate(cls, values):
        for key, value in values.items():
            if "URL" in key:
                if not value.startswith("http"):
                    raise ValueError(f"{key} must start with http or https")

        return values

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development" or self.ENVIRONMENT == "dev"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production" or self.ENVIRONMENT == "prod"


EnvVars = EnvVariabels()
