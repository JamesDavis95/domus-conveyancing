"""
Production Configuration for Render Deployment
Sets up database connections and environment variables
"""

import os
from typing import Optional

class Settings:
    """Production settings for Render deployment"""
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-here")
    ALLOWED_HOSTS: list = os.getenv("ALLOWED_HOSTS", "*").split(",")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./domus_production.db")
    
    # If PostgreSQL URL, convert to SQLAlchemy format
    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        if self.DATABASE_URL.startswith("postgres://"):
            return self.DATABASE_URL.replace("postgres://", "postgresql://", 1)
        return self.DATABASE_URL
    
    # Stripe Configuration
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    
    # Server Configuration
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = "0.0.0.0"
    
    # Admin Configuration
    ADMIN_EMAIL: str = "admin@domusplanning.co.uk"
    ADMIN_PASSWORD: str = "admin123!"
    
    # Production Features
    ENABLE_DOCS: bool = True  # Keep API docs available in production
    ENABLE_CORS: bool = True
    CORS_ORIGINS: list = ["*"]  # Configure this properly for security
    
    # File Upload
    UPLOAD_DIR: str = "/tmp/uploads"  # Render uses ephemeral storage
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    
    # Email Configuration (for notifications)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    
    # Monitoring
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    
    class Config:
        env_file = ".env"

# Global settings instance
settings = Settings()