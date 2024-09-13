# app/config.py

import os

class Settings:
    """Configuration settings for the application."""
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/uim_db')

settings = Settings()