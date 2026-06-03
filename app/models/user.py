from beanie import Indexed
from pymongo import IndexModel, ASCENDING
from pydantic import EmailStr
from typing import Optional
from datetime import datetime
from .base import BaseDocument
from .enums import Role

class User(BaseDocument):
    """
    Modelo de Usuario
    
    Roles:
    - SUPERADMIN: Propietario, acceso total.
    - ADMIN: Administrador del sistema.
    - MODERATOR: Moderadora de comunidad (VIP).
    - USER: Estudiante.
    """
    
    email: Indexed(EmailStr, unique=True)
    username: Indexed(str, unique=True)
    full_name: str
    password_hash: str 
   
    role: Role = Role.USER
    is_active: bool = True

    avatar_url: Optional[str] = None
    phone_number: str
    birth_date: datetime
    
    class Settings:
        name = "users"  # Nombre de la colección en MongoDB
        indexes = [
            IndexModel([("is_deleted", ASCENDING), ("role", ASCENDING)]),
            IndexModel([("is_deleted", ASCENDING), ("is_active", ASCENDING)]),
        ]
    
    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
    
    def __str__(self):
        return self.email
  