from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # OpenAI
    OPENAI_API_KEY: str
    
    # Database
    DATABASE_URL: str
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    
    # MCP
    MCP_SERVER_URL: str = "http://mcp-postgres:3000"
    
    # App
    APP_NAME: str = "RoomFlow AI Agent"
    DEBUG: bool = False
    
    class Config:
        case_sensitive = True

settings = Settings()