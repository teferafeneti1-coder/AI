from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    grpc_server_host: str = Field(default="localhost", env="GRPC_SERVER_HOST")
    grpc_server_port: int = Field(default=50051, env="GRPC_SERVER_PORT")
    agent_host: str = Field(default="localhost", env="AGENT_HOST")
    agent_port: int = Field(default=50052, env="AGENT_PORT")
    web_host: str = Field(default="0.0.0.0", env="WEB_HOST")
    web_port: int = Field(default=5000, env="WEB_PORT")
    hmac_secret: str = Field(default="dev-secret-change-in-prod", env="HMAC_SECRET")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
