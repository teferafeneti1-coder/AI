from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    agent_port: int = Field(default=50052, env="AGENT_PORT")
    hmac_secret: str = Field(default="dev-secret-change-in-prod", env="HMAC_SECRET")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
