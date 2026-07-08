from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    agent_port: int = Field(default=50052, env="AGENT_PORT")
    hmac_secret: str = Field(default="dev-secret-change-in-prod", env="HMAC_SECRET")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Login API — small HTTP server that sits beside the gRPC agent
    login_api_port: int = Field(default=8080, env="LOGIN_API_PORT")
    login_api_host: str = Field(default="0.0.0.0", env="LOGIN_API_HOST")

    # Where to forward login events (the Audit Log Service HTTP inject endpoint)
    audit_host: str = Field(default="localhost", env="AUDIT_HOST")
    audit_inject_port: int = Field(default=8081, env="AUDIT_INJECT_PORT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
