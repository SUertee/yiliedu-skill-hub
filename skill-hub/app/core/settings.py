from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    PG_DSN: str
    PG_POOL_MIN: int = 1
    PG_POOL_MAX: int = 10

    # 可选鉴权：OpenWebUI 调用时带 header: x-api-key
    API_KEY: str | None = None

settings = Settings()
