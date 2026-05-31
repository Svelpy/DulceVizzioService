"""
Servicio para lógica de negocio de Usuarios
Extraído de routers/users.py — sigue el patrón arquitectónico del proyecto
"""

from typing import Optional, Dict, Any, List
from fastapi import HTTPException, UploadFile, status
from datetime import datetime
import re
import math

from app.utils.user_utils import generate_user_password, generate_chef_username

from app.models.user import User
from app.models.enums import Role
from app.schemas.user_schema import UserUpdate, UserCreate
from app.services.cloudinary_service import cloudinary_service
from app.utils.security import hash_password


class UserService:

    # ─────────────────────────────────────────────
    # HELPERS INTERNOS
    # ─────────────────────────────────────────────

    @staticmethod
    def _check_hierarchy(actor: User, target: User):
        """
        Valida que el actor tenga jerarquía suficiente sobre el target.
        Lanza HTTP 403 si la jerarquía del actor es menor o igual a la del target.
        """
        levels={Role.SUPERADMIN:0, Role.ADMIN:1, Role.MODERATOR:2, Role.USER:3}
        actor_level=levels[actor.role]
        target_level=levels[target.role]
        if actor_level >= target_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para gestionar a este usuario"
            )

    @staticmethod
    async def _get_active_user(user_id: str) -> User:
        """
        Obtiene un usuario por ID y lanza 404 si no existe o fue eliminado lógicamente.
        """
        from bson import ObjectId
        try:
            user = await User.get(ObjectId(user_id))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no existente"
            )

        if not user or user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario eliminado logicamente."
            )

        return user

    # ─────────────────────────────────────────────
    # CRUD
    # ─────────────────────────────────────────────

    @staticmethod
    async def list_users(
        page: int = 1,
        per_page: int = 10,
        q: Optional[str] = None,
        role: Optional[Role] = None,
        is_active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Lista usuarios con paginación y filtros opcionales."""
        from beanie.operators import Or

        query = User.find(User.is_deleted == False)

        if q:
            safe_q = re.escape(q)
            regex = {"$regex": safe_q, "$options": "i"}
            query = query.find(Or(
                User.email == regex,
                User.username == regex,
                User.full_name == regex,
                User.phone_number == regex
            ))

        if role:
            query = query.find(User.role == role)

        if is_active is not None:
            query = query.find(User.is_active == is_active)

        total_count = await query.count()
        skip = (page - 1) * per_page
        users = await query.skip(skip).limit(per_page).to_list()
        total_pages = math.ceil(total_count / per_page) if per_page > 0 else 0

        return {
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "data": users,
        }

    @staticmethod
    async def get_user(user_id: str) -> User:
        """Obtiene un usuario activo por ID."""
        return await UserService._get_active_user(user_id)

    @staticmethod
    async def update_user(user_id: str, update_data: UserUpdate, actor: User) -> User:
        """Actualiza datos textuales del usuario con validación de jerarquía y unicidad."""
        user = await UserService._get_active_user(user_id)
        UserService._check_hierarchy(actor, user)

        if update_data.username is not None and update_data.username != user.username:
            existing = await User.find_one(User.username == update_data.username)
            if existing:
                raise HTTPException(status_code=400, detail="El username ya está en uso")

        if update_data.email is not None and update_data.email != user.email:
            existing_email = await User.find_one(User.email == update_data.email)
            if existing_email:
                raise HTTPException(status_code=400, detail="El email ya está en uso")

        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(user, key, value)

        user.updated_by = str(actor.id)
        await user.save()
        return user

    @staticmethod
    async def update_avatar(user_id: str, file: UploadFile, actor: User) -> User:
        """Actualiza el avatar del usuario subiendo la imagen a Cloudinary."""
        user = await UserService._get_active_user(user_id)
        UserService._check_hierarchy(actor, user)

        avatar_url = await cloudinary_service.upload_image(file, folder="avatars")
        user.avatar_url = avatar_url
        user.updated_by = str(actor.id)
        await user.save()
        return user

    @staticmethod
    async def reset_password(user_id: str, new_password: str, actor: User) -> None:
        """
        Restablece la contraseña de un usuario (acción administrativa).
        FIX: Ahora registra updated_by correctamente.
        """
        user = await UserService._get_active_user(user_id)

        if actor.role == Role.ADMIN and user.role in [Role.SUPERADMIN, Role.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para cambiar la contraseña de este usuario"
            )

        user.password_hash = hash_password(new_password)
        user.updated_by = str(actor.id)  # FIX: antes no se registraba
        await user.save()

    @staticmethod
    async def toggle_active(user_id: str, actor: User) -> User:
        """
        Activa o desactiva un usuario.
        FIX: Ahora registra updated_by correctamente.
        """
        user = await UserService._get_active_user(user_id)

        if str(user.id) == str(actor.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes desactivar tu propia cuenta"
            )

        UserService._check_hierarchy(actor, user)

        user.is_active = not user.is_active
        user.updated_by = str(actor.id)  # FIX: antes no se registraba
        await user.save()
        return user

    @staticmethod
    async def change_role(user_id: str, new_role: Role, actor: User) -> User:
        """
        Cambia el rol de un usuario (solo SUPERADMIN puede invocar este método).
        FIX: Ahora registra updated_by correctamente.
        """
        if new_role == Role.SUPERADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede asignar el rol SUPERADMIN"
            )

        user = await UserService._get_active_user(user_id)

        if user.role == Role.SUPERADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede cambiar el rol del SUPERADMIN"
            )

        user.role = new_role
        user.updated_by = str(actor.id)  # FIX: antes no se registraba
        await user.save()
        return user

    @staticmethod
    async def delete_user(user_id: str, actor: User) -> None:
        """
        Elimina un usuario:
        - ADMIN: Soft delete + cancela enrollments activos.
        - SUPERADMIN: Hard delete físico + elimina enrollments.
        """
        from app.models.enrollment import Enrollment
        from app.models.enums import EnrollmentStatus

        user = await UserService._get_active_user(user_id)

        if str(user.id) == str(actor.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes eliminar tu propia cuenta"
            )

        if actor.role == Role.ADMIN:
            if user.role in [Role.SUPERADMIN, Role.ADMIN]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos para eliminar a este usuario"
                )
            # Soft delete del usuario
            user.is_deleted = True
            user.deleted_at = datetime.utcnow()
            user.deleted_by = str(actor.id)
            user.updated_by = str(actor.id)
            await user.save()

            # Cascada: cancelar enrollments activos
            enrollments = await Enrollment.find({"user_id": user.id, "is_deleted": False}).to_list()
            for e in enrollments:
                e.is_deleted = True
                e.deleted_at = datetime.utcnow()
                e.deleted_by = str(actor.id)
                e.updated_by = str(actor.id)
                e.status = EnrollmentStatus.CANCELLED
                await e.save()

        elif actor.role == Role.SUPERADMIN:
            if user.role == Role.SUPERADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos para eliminar a este usuario"
                )
            # Hard delete físico con cascada
            await Enrollment.find({"user_id": user.id}).delete()
            await user.delete()


user_service = UserService()
