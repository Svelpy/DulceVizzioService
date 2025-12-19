"""
Router de Autenticación
Endpoints para login, registro y gestión de cuenta
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.user_schema import (
    UserCreate,
    UserLogin,
    TokenResponse,
    UserResponse,
    ChangePasswordSchema
)
from app.services.auth_service import auth_service
from app.utils.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Registrar un nuevo usuario
    
    - **email**: Email único del usuario
    - **password**: Contraseña (mínimo 8 caracteres)
    - **full_name**: Nombre completo
    - **username**: Username opcional (único)
    - **role**: "ADMIN" o "USER" (por defecto "USER")
    
    Retorna los datos del usuario creado (sin la contraseña)
    """
    user = await auth_service.register_user(user_data)
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        username=user.username,
        role=user.role,
        is_active=user.is_active,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """
    Iniciar sesión
    
    - **email**: Email del usuario
    - **password**: Contraseña
    
    Retorna un token JWT para autenticación en endpoints protegidos
    """
    return await auth_service.login(credentials)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Obtener información del usuario autenticado
    
    Requiere token JWT en el header: Authorization: Bearer <token>
    """
    return await auth_service.get_current_user_info(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    full_name: str = None,
    username: str = None,
    avatar_url: str = None,
    current_user: User = Depends(get_current_user)
):
    """
    Actualizar perfil del usuario autenticado
    
    Permite actualizar:
    - **full_name**: Nombre completo
    - **username**: Username (debe ser único)
    - **avatar_url**: URL de avatar
    """
    # Verificar si el username está disponible (si se proporcionó)
    if username and username != current_user.username:
        existing = await User.find_one(User.username == username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El username ya está en uso"
            )
        current_user.username = username
    
    # Actualizar campos
    if full_name:
        current_user.full_name = full_name
    if avatar_url is not None:  # Permitir cadena vacía para borrar avatar
        current_user.avatar_url = avatar_url
    
    await current_user.save()
    
    return await auth_service.get_current_user_info(current_user)


@router.put("/change-password")
async def change_password(
    password_data: ChangePasswordSchema,
    current_user: User = Depends(get_current_user)
):
    """
    Cambiar contraseña del usuario autenticado
    
    - **current_password**: Contraseña actual
    - **new_password**: Nueva contraseña (mínimo 8 caracteres)
    - **confirm_password**: Confirmación de nueva contraseña
    """
    return await auth_service.change_password(
        user=current_user,
        current_password=password_data.current_password,
        new_password=password_data.new_password
    )
