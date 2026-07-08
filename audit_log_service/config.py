from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    grpc_server_host: str = Field(default="localhost", env="GRPC_SERVER_HOST")
    grpc_server_port: int = Field(default=50051, env="GRPC_SERVER_PORT")
    poll_interval: int = Field(default=5, env="POLL_INTERVAL")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    platform: str = Field(default="auto", env="PLATFORM")

    # HTTP inject endpoint — lets the Agent login page push events in directly
    inject_host: str = Field(default="0.0.0.0", env="INJECT_HOST")
    inject_port: int = Field(default=8081, env="INJECT_PORT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
