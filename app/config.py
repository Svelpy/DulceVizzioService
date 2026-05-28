"""
Configuración de la aplicación
Variables de entorno y configuraciones globales
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuración de la aplicación usando variables de entorno"""
    
    # App
    APP_NAME: str = "DulceVicio API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # MongoDB Atlas
    MONGODB_URL: str
    MONGODB_DB_NAME: str = "dulcevicio_db"
    
    # JWT Authentication
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES_DEBUG: int = 1440  # 1 día para desarrollo
    ACCESS_TOKEN_EXPIRE_MINUTES_PROD: int = 180    # 3 horas para producción
    
    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        """
        Retorna el tiempo de expiración del token según el modo DEBUG
        - DEBUG=True: 1 día (1440 minutos)
        - DEBUG=False: 3 horas (180 minutos)
        """
        if self.DEBUG:
            return self.ACCESS_TOKEN_EXPIRE_MINUTES_DEBUG
        return self.ACCESS_TOKEN_EXPIRE_MINUTES_PROD
    
    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    
    # CORS — Orígenes de desarrollo (DEBUG=True)
    DEV_ORIGINS: str = "http://localhost:3000,http://localhost:5175,http://localhost:5174"

    # CORS — Orígenes de producción (DEBUG=False)
    #ALLOWED_ORIGINS: str = "" Definido solo en el .env ;)

    @property
    def cors_origins_list(self) -> list:
        """
        Retorna la lista de orígenes CORS según el modo:
        - DEBUG=True  → DEV_ORIGINS   (orígenes de desarrollo local)
        - DEBUG=False → ALLOWED_ORIGINS (orígenes de producción del .env)
        """
        if self.DEBUG:
            #return ["*"]
            return [o.strip() for o in self.DEV_ORIGINS.split(",") if o.strip()]

        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instancia singleton de Settings
settings = Settings()
