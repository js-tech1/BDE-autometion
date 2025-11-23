"""
Configuration settings for BDE Automation System
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # IBM Watson Configuration
    ibm_watson_api_key: str
    ibm_watson_url: str = "https://api.us-south.watsonx.ai/v1"
    ibm_watson_project_id: str
    
    # IBM WatsonX AI Configuration
    watsonx_api_key: str
    watsonx_project_id: str
    watsonx_url: str = "https://us-south.ml.cloud.ibm.com"
    
    # Database Configuration
    database_url: str = "sqlite:///./bde_automation.db"
    
    # Email Configuration
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str
    smtp_password: str
    sender_email: str
    sender_name: str = "BDE Automation Agent"
    
    # Application Configuration
    app_name: str = "BDE Automation System"
    app_version: str = "1.0.0"
    debug_mode: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Agent Configuration
    lead_scoring_threshold: float = 0.7
    max_email_retries: int = 3
    meeting_scheduling_window_days: int = 14
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
