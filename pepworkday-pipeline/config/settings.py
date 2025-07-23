"""
Configuration settings for the PepWorkday pipeline.

This module uses Pydantic Settings to manage configuration from environment variables
and .env files with proper type validation and default values.
"""

from typing import Optional, List
from pathlib import Path
from pydantic import BaseSettings, Field, validator
import os


class GoogleSheetsSettings(BaseSettings):
    """Google Sheets integration settings."""
    
    credentials_path: str = Field(..., env="GOOGLE_SHEETS_CREDENTIALS_PATH")
    spreadsheet_id: str = Field(..., env="GOOGLE_SHEETS_SPREADSHEET_ID")
    worksheet_name: str = Field(default="RawData", env="GOOGLE_SHEETS_WORKSHEET_NAME")
    
    @validator("credentials_path")
    def validate_credentials_path(cls, v):
        if not Path(v).exists():
            raise ValueError(f"Google Sheets credentials file not found: {v}")
        return v


class SlackSettings(BaseSettings):
    """Slack notification settings."""
    
    bot_token: Optional[str] = Field(None, env="SLACK_BOT_TOKEN")
    channel: str = Field(default="#automation-alerts", env="SLACK_CHANNEL")
    webhook_url: Optional[str] = Field(None, env="SLACK_WEBHOOK_URL")
    
    @validator("bot_token", "webhook_url")
    def validate_slack_config(cls, v, values):
        # At least one of bot_token or webhook_url must be provided
        if not v and not values.get("webhook_url") and not values.get("bot_token"):
            raise ValueError("Either SLACK_BOT_TOKEN or SLACK_WEBHOOK_URL must be provided")
        return v


class SamsaraSettings(BaseSettings):
    """Samsara integration settings for PEPMove."""

    # PEPMove-specific Samsara configuration
    api_token: str = Field(default="samsara_api_7qCpNNFjxM5S4jojGWzO9vxciB8o8I", env="SAMSARA_API_TOKEN")
    base_url: str = Field(default="https://api.samsara.com", env="SAMSARA_BASE_URL")
    organization_id: str = Field(default="5005620", env="SAMSARA_ORGANIZATION_ID")
    group_id: str = Field(default="129031", env="SAMSARA_GROUP_ID")

    # API behavior settings
    use_api: bool = Field(default=True, env="SAMSARA_USE_API")
    api_timeout: int = Field(default=30, env="SAMSARA_API_TIMEOUT")
    max_retries: int = Field(default=3, env="SAMSARA_MAX_RETRIES")

    # PEPMove operational settings
    default_vehicle_group: str = Field(default="129031", env="SAMSARA_DEFAULT_VEHICLE_GROUP")
    enable_real_time_tracking: bool = Field(default=True, env="SAMSARA_ENABLE_REAL_TIME_TRACKING")
    location_update_interval: int = Field(default=300, env="SAMSARA_LOCATION_UPDATE_INTERVAL")  # seconds

    @validator("organization_id", "group_id")
    def validate_ids(cls, v):
        if not v or not v.isdigit():
            raise ValueError("Organization ID and Group ID must be numeric strings")
        return v


class PipelineSettings(BaseSettings):
    """Main pipeline configuration settings."""
    
    log_level: str = Field(default="INFO", env="PIPELINE_LOG_LEVEL")
    dry_run: bool = Field(default=False, env="PIPELINE_DRY_RUN")
    batch_size: int = Field(default=1000, env="PIPELINE_BATCH_SIZE")
    max_workers: int = Field(default=4, env="MAX_WORKERS")
    chunk_size: int = Field(default=500, env="CHUNK_SIZE")
    timeout_seconds: int = Field(default=300, env="TIMEOUT_SECONDS")
    
    # File paths
    excel_input_path: str = Field(default="data/input/", env="EXCEL_INPUT_PATH")
    samsara_data_path: str = Field(default="data/samsara/", env="SAMSARA_DATA_PATH")
    output_path: str = Field(default="data/output/", env="OUTPUT_PATH")
    log_path: str = Field(default="logs/", env="LOG_PATH")
    
    # Notification settings
    enable_slack_notifications: bool = Field(default=True, env="ENABLE_SLACK_NOTIFICATIONS")
    notification_on_success: bool = Field(default=True, env="NOTIFICATION_ON_SUCCESS")
    notification_on_error: bool = Field(default=True, env="NOTIFICATION_ON_ERROR")
    
    # Data validation
    strict_schema_validation: bool = Field(default=True, env="STRICT_SCHEMA_VALIDATION")
    allow_missing_columns: bool = Field(default=False, env="ALLOW_MISSING_COLUMNS")
    
    @validator("log_level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()


class Settings(BaseSettings):
    """Main settings class combining all configuration sections."""
    
    google_sheets: GoogleSheetsSettings = GoogleSheetsSettings()
    slack: SlackSettings = SlackSettings()
    samsara: SamsaraSettings = SamsaraSettings()
    pipeline: PipelineSettings = PipelineSettings()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
