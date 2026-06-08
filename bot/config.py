import os
from typing import Optional
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from bot.exceptions import ConfigError


class TradingBotConfig(BaseSettings):
    """Configuration class that loads settings from environment variables and validates them."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    binance_api_key: SecretStr = Field(..., alias="BINANCE_API_KEY")
    binance_secret_key: SecretStr = Field(..., alias="BINANCE_SECRET_KEY")
    binance_base_url: str = Field("https://testnet.binancefuture.com", alias="BINANCE_BASE_URL")
    binance_use_testnet: bool = Field(True, alias="BINANCE_USE_TESTNET")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    @field_validator("binance_api_key", "binance_secret_key")
    @classmethod
    def check_non_empty(cls, v: SecretStr) -> SecretStr:
        if not v.get_secret_value() or v.get_secret_value().strip() == "" or "your_testnet" in v.get_secret_value():
            raise ValueError("API credentials cannot be empty or default placeholder values.")
        return v

    def get_masked_api_key(self) -> str:
        key = self.binance_api_key.get_secret_value()
        if len(key) <= 8:
            return "********"
        return f"{key[:4]}...{key[-4:]}"

    def get_masked_secret_key(self) -> str:
        secret = self.binance_secret_key.get_secret_value()
        if len(secret) <= 8:
            return "********"
        return f"{secret[:4]}...{secret[-4:]}"


def load_config() -> TradingBotConfig:
    """Helper function to load and validate configuration, raising a ConfigError on failure."""
    try:
        return TradingBotConfig()
    except Exception as e:
        raise ConfigError(
            f"Failed to load environment configuration. Please ensure your .env file is set up correctly. Details: {e}"
        )
