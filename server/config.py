from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Keys
    coingecko_api_key: str = ""
    news_api_key: str = ""
    anthropic_api_key: str = ""

    # CoinGecko
    coingecko_base_url: str = "https://api.coingecko.com/api/v3"

    # NewsAPI
    news_api_base_url: str = "https://newsapi.org/v2"

    # Timeouts
    http_timeout_seconds: int = 30


settings = Settings()