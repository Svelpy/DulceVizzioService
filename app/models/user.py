"""
Modelo de Usuario - MongoDB con Beanie
"""

from beanie import Document, Indexed
from pydantic import EmailStr, Field
from datetime import datetime
from typing import Optional


class User(Document):
    """
    Modelo de Usuario
    
    Roles:
    - ADMIN: Acceso completo a la plataforma
    - USER: Estudiante con acceso limitado a cursos asignados
    """
    
    email: Indexed(EmailStr, unique=True)  # Email único e indexado
    username: Optional[Indexed(str, unique=True)] = None  # Username opcional pero único
    password_hash: str  # Contraseña hasheada con bcrypt
    full_name: str
    role: str = "USER"  # "ADMIN" | "USER"
    is_active: bool = True
    avatar_url: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "users"  # Nombre de la colección en MongoDB
        indexes = [
            "email",
            "username",
            "role",
            "is_active",
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "admin@dulcevicio.com",
                "username": "admin",
                "full_name": "Admin DulceVicio",
                "role": "ADMIN",
                "is_active": True
            }
        }
    
    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
    
    def __str__(self):
        return self.email
