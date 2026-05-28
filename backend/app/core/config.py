from pydantic_settings import BaseSettings
from typing import List, Union
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "Guayabera ERP Suite v2.0"
    API_V1_STR: str = "/api/v1"
    
    # Database settings
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = os.getenv("POSTGRES_PORT", 5435)  # Puerto diferente al de la versión 1
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "guayabera_erp_v2")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "guayabera_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "guayabera_pass_2025")
    
    # Construcción de la URL de la base de datos
    DATABASE_URL: str = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    
    # Configuración de seguridad
    SECRET_KEY: str = os.getenv("SECRET_KEY", "tu_clave_secreta_aqui")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 * 24 * 60  # 30 días
    
    # Configuración de backend CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # Frontend
        "http://localhost:8001",  # Backend
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8001"
    ]
    
    # Configuración de frontend URL
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Activar logs de la base de datos
    DB_ECHO: bool = os.getenv("DB_ECHO", "False").lower() == "true"
    
    # Header para identificación de tenant
    TENANT_IDENTIFICATION_HEADER: str = "X-Tenant-ID"


settings = Settings()