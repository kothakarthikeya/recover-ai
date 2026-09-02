import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "RecoverAI"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database Settings
    DATABASE_URL: str = "sqlite:///./recover_ai.db"

    # Razorpay Test Mode Credentials
    RAZORPAY_KEY_ID: str = "rzp_test_placeholder"
    RAZORPAY_KEY_SECRET: str = "placeholder_secret"
    RAZORPAY_WEBHOOK_SECRET: str = "placeholder_webhook_secret"

    # AI Configuration
    OPENAI_API_KEY: str = "placeholder_key"
    AI_MODEL_NAME: str = "gpt-4o-mini"

    # Policy Defaults
    MIN_RECOVERY_PROBABILITY_THRESHOLD: float = 0.25
    MAX_AUTOMATIC_RETRY_ATTEMPTS: int = 2
    HIGH_VALUE_ESCALATION_THRESHOLD_PAISE: int = 10000000  # ₹1,00,000 in paise
    RECOVERY_WINDOW_HOURS: int = 72

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
