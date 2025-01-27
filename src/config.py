from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    PROJECT_ID: str = "yellduck"
    LOG_TOPIC: str = "error_logs"
    SERVICE_NAME: str = "price-comparison"

    API_KEYS: dict = {}

    model_config = SettingsConfigDict(env_file=".env")

config = Config()