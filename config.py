```python
# config.py
"""
Autonomous Interview Scheduling System - Configuration Module

This module defines the configuration settings for the Autonomous Interview Scheduling System.
It handles environment variables, secrets management, and application constants.
"""
import os
import logging
from typing import Dict, List, Optional, Union, Any
from functools import lru_cache

from pydantic import AnyHttpUrl, BaseSettings, validator, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and secrets.
    
    Attributes are loaded with the following priority:
    1. Environment variables
    2. AWS Secrets Manager (in production)
    3. Default values
    """
    # API Configuration
    PROJECT_NAME: str = "Autonomous Interview Scheduling System"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    VERSION: str = "0.1.0"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parse CORS origins from string or list format."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Authentication and Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # OAuth2 Settings
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    
    # Okta/Azure SSO Settings
    SSO_ENABLED: bool = False
    SSO_PROVIDER: str = "okta"  # or "azure"
    SSO_CLIENT_ID: Optional[str] = None
    SSO_CLIENT_SECRET: Optional[str] = None
    SSO_DOMAIN: Optional[str] = None
    
    # Database Configuration
    DATABASE_TYPE: str = "postgresql"  # or "firestore"
    
    # PostgreSQL Settings
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    
    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        """Construct PostgreSQL connection string from individual components."""
        if isinstance(v, str):
            return v
        
        # Only assemble if database type is PostgreSQL
        if values.get("DATABASE_TYPE") != "postgresql":
            return None
            
        return PostgresDsn.build(
            scheme="postgresql",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER", ""),
            path=f"/{values.get('POSTGRES_DB', '')}"
        )
    
    # Firestore Settings (if used instead of PostgreSQL)
    FIRESTORE_PROJECT_ID: Optional[str] = None
    FIRESTORE_CREDENTIALS_PATH: Optional[str] = None
    
    # External API Integration
    SLACK_BOT_TOKEN: Optional[str] = None
    SLACK_SIGNING_SECRET: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    
    # Email Configuration
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # AWS Configuration
    AWS_REGION: str = "us-west-2"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    
    # AWS Services
    AWS_SECRETS_MANAGER_ENABLED: bool = False
    AWS_SECRETS_NAME: Optional[str] = None
    AWS_ECS_CLUSTER: Optional[str] = None
    AWS_ECS_TASK_DEFINITION: Optional[str] = None
    
    # Temporal Configuration
    TEMPORAL_HOST: str = "localhost:7233"
    TEMPORAL_NAMESPACE: str = "interview-scheduling"
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    CLOUDWATCH_LOG_GROUP: Optional[str] = None
    CLOUDWATCH_LOG_STREAM: Optional[str] = None
    
    # Application Constants
    DEFAULT_INTERVIEW_DURATION_MINUTES: int = 60
    DEFAULT_TIMEZONE: str = "UTC"
    MAX_SCHEDULING_ATTEMPTS: int = 3
    SCHEDULING_WINDOW_DAYS: int = 14
    
    # Model Config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    def get_aws_secrets(self) -> None:
        """
        Fetch secrets from AWS Secrets Manager when running in production.
        
        This method updates the current settings instance with values from AWS Secrets Manager.
        Only called in production environments when AWS_SECRETS_MANAGER_ENABLED is True.
        """
        if not self.AWS_SECRETS_MANAGER_ENABLED:
            return
            
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            client = boto3.client(
                'secretsmanager',
                region_name=self.AWS_REGION,
                aws_access_key_id=self.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY
            )
            
            response = client.get_secret_value(SecretId=self.AWS_SECRETS_NAME)
            if 'SecretString' in response:
                import json
                secrets_dict = json.loads(response['SecretString'])
                
                # Update settings with secrets
                for key, value in secrets_dict.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
                        
            logging.info("Successfully loaded secrets from AWS Secrets Manager")
            
        except ImportError:
            logging.error("boto3 is required for AWS Secrets Manager integration")
        except ClientError as e:
            logging.error(f"Failed to retrieve secrets from AWS Secrets Manager: {str(e)}")
        except Exception as e:
            logging.error(f"Unexpected error when retrieving AWS secrets: {str(e)}")


@lru_cache()
def get_settings() -> Settings:
    """
    Create and return a cached Settings instance.
    
    Returns:
        Settings: Application configuration settings
    """
    settings = Settings()
    
    # Load secrets from AWS in production environments
    if os.getenv("ENVIRONMENT", "").lower() == "production" and settings.AWS_SECRETS_MANAGER_ENABLED:
        settings.get_aws_secrets()
    
    # Configure logging based on settings
    logging_level = getattr(logging, settings.LOG_LEVEL)
    logging.basicConfig(
        level=logging_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    return settings


# Initialize settings instance for importing elsewhere
settings = get_settings()
```