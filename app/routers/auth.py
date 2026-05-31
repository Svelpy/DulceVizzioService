"""
Router de Autenticación
Endpoints para login, registro y gestión de cuenta
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Request
from typing import Optional

from app.schemas.user_schema import (
    UserLogin,
    TokenResponse,
    UserResponse,
    ChangePasswordSchema,
    UserSelfRegister
)
from app.services.auth_service import auth_service
from app.services.cloudinary_service import cloudinary_service
from app.utils.dependencies import get_current_user
from app.utils.limiter import limiter
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["Authentication"])





@router.post("/login", response_model=TokenResponse)
@limiter.limit("3/5minutes")
async def login(request: Request, credentials: UserLogin):
    """
    Iniciar sesión
    
    - **email**: Email del usuario
    - **password**: Contraseña
    
    Retorna un token JWT para autenticación en endpoints protegidos
    
    **Rate Limit:** 3 intentos por 5 minutos por IP
    """
    return await auth_service.login(credentials)


@router.get("/me", response_model=UserResponse)
@limiter.limit("30/minute")
async def get_current_user_info(request: Request, current_user: User = Depends(get_current_user)):
    """
    Obtener información del usuario autenticado

    Requiere token JWT en el header: Authorization: Bearer <token>

    **Rate Limit:** 30 peticiones por minuto por IP
    """
    return await auth_service.get_current_user_info(current_user)


@router.patch("/me/avatar", response_model=UserResponse)
@limiter.limit("5/minute")
async def update_my_avatar(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Actualizar mi foto de perfil

    Permite al usuario subir una nueva imagen de perfil.

    **Rate Limit:** 5 subidas por minuto por IP (protege costos de Cloudinary)
    """
    # Subir imagen usando el servicio
    avatar_url = await cloudinary_service.upload_image(file, folder="avatars")

    current_user.avatar_url = avatar_url
    current_user.updated_by = str(current_user.id)
    await current_user.save()

    return current_user





@router.patch("/me/change-password")
@limiter.limit("3/day")
async def change_password(
    request: Request,
    password_data: ChangePasswordSchema,
    current_user: User = Depends(get_current_user)
):
    """
    Cambiar contraseña del usuario autenticado
    
    - **current_password**: Contraseña actual
    - **new_password**: Nueva contraseña (mínimo 8 caracteres)
    - **confirm_password**: Confirmación de nueva contraseña
    
    **Rate Limit:** 3 intentos por día por IP
    """
    return await auth_service.change_password(
        user=current_user,
        current_password=password_data.current_password,
        new_password=password_data.new_password
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, user_data: UserSelfRegister):
    """
    Registrar un nuevo estudiante (público)
    
    - **email**: Email único para la cuenta (obligatorio)
    - **full_name**: Nombre completo (obligatorio)
    - **password**: Contraseña segura (obligatorio)
    - **username**: Nombre de usuario (obligatorio)
    - **phone_number**: Teléfono con formato (opcional)
    - **birth_date**: Fecha de nacimiento (opcional)
    
    **Rate Limit:** Máximo 5 registros por minuto por IP.
    """
    return await auth_service.register_self(user_data)