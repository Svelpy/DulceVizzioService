"""
Schemas Pydantic para Usuario
Validación y serialización de datos de usuarios
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Literal
from datetime import datetime


class UserBase(BaseModel):
    """Schema base para Usuario"""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    username: Optional[str] = Field(None, min_length=3, max_length=50)


class UserCreate(UserBase):
    """Schema para crear usuario"""
    password: str = Field(..., min_length=8, max_length=100)
    role: Literal["ADMIN", "USER"] = "USER"
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        return v


class UserUpdate(BaseModel):
    """Schema para actualizar usuario"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Schema de respuesta de usuario (sin contraseña)"""
    id: str  # ObjectId como string
    email: EmailStr
    full_name: str
    username: Optional[str] = None
    role: str
    is_active: bool
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "email": "estudiante@example.com",
                "full_name": "María García",
                "username": "mariagarcia",
                "role": "USER",
                "is_active": True,
                "avatar_url": None,
                "created_at": "2025-12-19T14:00:00Z",
                "updated_at": "2025-12-19T14:00:00Z"
            }
        }


class UserLogin(BaseModel):
    """Schema para login"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema de respuesta de token JWT"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ChangePasswordSchema(BaseModel):
    """Schema para cambiar contraseña"""
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Las contraseñas no coinciden')
        return v


class UserListResponse(BaseModel):
    """Schema de respuesta paginada de usuarios"""
    users: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
