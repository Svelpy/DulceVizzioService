"""
Router de Gestión de Usuarios
Thin router — delega toda la lógica de negocio a UserService
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body, File, UploadFile, Query
from typing import Optional

from app.schemas.user_schema import UserResponse, UserUpdate, UserCreate, PasswordValidationMixin, PaginatedResponse
from app.models.user import User
from app.models.enums import Role
from app.utils.dependencies import get_current_admin, get_current_superadmin
from app.services.auth_service import auth_service
from app.services.user_service import user_service

router = APIRouter(prefix="/api/users", tags=["User Management"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, current_user: User = Depends(get_current_admin)):
    """
    Crear usuario (ADMIN o SUPERADMIN)

    **Permisos:**
    - ✅ **SUPERADMIN**: Puede crear ADMIN, MODERATOR, USER
    - ✅ **ADMIN**: Puede crear MODERATOR, USER
    - ❌ **MODERATOR/USER**: Sin acceso

    **Roles disponibles:**
    - `ADMIN` - Solo SUPERADMIN puede crear
    - `MODERATOR` - ADMIN o SUPERADMIN pueden crear
    - `USER` - ADMIN o SUPERADMIN pueden crear
    """
    if user_data.role == Role.ADMIN and current_user.role != Role.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo SUPERADMIN puede crear administradores"
        )

    if user_data.role == Role.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pueden crear nuevos SUPERADMIN"
        )

    return await auth_service.register_user(user_data, created_by=str(current_user.id))



@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    q: Optional[str] = None,
    role: Optional[Role] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_admin)
):
    """
    Listar usuarios con paginación y filtros (ADMIN o SUPERADMIN)

    **Paginación:**
    - **page**: Número de página (mínimo 1)
    - **per_page**: Registros por página (entre 1 y 100, por defecto 10)

    **Filtros opcionales:**
    - **q**: Búsqueda general en email, username, full_name, phone_number
    - **role**: Filtrar por rol (ADMIN, MODERATOR, USER)
    - **is_active**: Filtrar por estado activo/inactivo
    """
    return await user_service.list_users(page=page, per_page=per_page, q=q, role=role, is_active=is_active)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, current_user: User = Depends(get_current_admin)):
    """
    Obtener información de un usuario específico (ADMIN o SUPERADMIN)
    """
    return await user_service.get_user(user_id)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    update_data: UserUpdate,
    current_user: User = Depends(get_current_admin)
):
    """
    Actualizar datos del usuario (Datos textuales)

    Permite actualizar: username, full_name, phone_number, birth_date.

    **Permisos:**
    - SUPERADMIN puede editar a cualquiera.
    - ADMIN puede editar a MODERATOR y USER.
    """
    return await user_service.update_user(user_id, update_data, actor=current_user)


@router.patch("/{user_id}/avatar", response_model=UserResponse)
async def update_user_avatar(
    user_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin)
):
    """
    Actualizar avatar de usuario (ADMIN o SUPERADMIN)

    Sube una nueva imagen de perfil para el usuario especificado.
    La imagen se sube a Cloudinary y se guarda la URL.
    """
    return await user_service.update_avatar(user_id, file, actor=current_user)


@router.patch("/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
async def admin_reset_password(
    user_id: str,
    password_data: PasswordValidationMixin = Body(...),
    current_user: User = Depends(get_current_admin)
):
    """
    Restablecer contraseña de usuario (ADMIN o SUPERADMIN)

    Permite a un administrador forzar el cambio de contraseña de un usuario.
    Útil si el usuario perdió su acceso.
    """
    await user_service.reset_password(user_id, password_data.password, actor=current_user)
    return None


@router.patch("/{user_id}/toggle-active", response_model=UserResponse)
async def toggle_user_active(user_id: str, current_user: User = Depends(get_current_admin)):
    """
    Activar/Desactivar usuario (ADMIN o SUPERADMIN)

    Alterna el estado is_active del usuario.
    """
    return await user_service.toggle_active(user_id, actor=current_user)


@router.patch("/{user_id}/role", response_model=UserResponse)
async def change_user_role(
    user_id: str,
    new_role: Role = Body(..., embed=True),
    current_user: User = Depends(get_current_superadmin)
):
    """
    Cambiar rol de usuario (SOLO SUPERADMIN)

    **Solo SUPERADMIN puede cambiar roles.**
    No se puede cambiar a SUPERADMIN.
    """
    return await user_service.change_role(user_id, new_role, actor=current_user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, current_user: User = Depends(get_current_admin)):
    """
    Eliminar usuario (Híbrido)

    - **SUPERADMIN**: Borrado Físico (Elimina de la BD).
    - **ADMIN**: Borrado Lógico (Marca is_deleted=True).
    """
    await user_service.delete_user(user_id, actor=current_user)
    return None
