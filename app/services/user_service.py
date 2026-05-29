"""
Servicio para lógica de negocio de Usuarios
Extraído de routers/users.py — sigue el patrón arquitectónico del proyecto
"""

from typing import Optional, Dict, Any, List
from fastapi import HTTPException, UploadFile, status
from datetime import datetime
import re
import math
import io

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

    # ─────────────────────────────────────────────
    # CARGA MASIVA POR LOTE (EXCEL)
    # ─────────────────────────────────────────────

    @staticmethod
    async def batch_create_users(
        file: UploadFile,
        actor: User
    ) -> Dict[str, Any]:
        """
        Crea usuarios por lote desde un archivo Excel (.xlsx).
        - Soporta Archivos con o sin encabezados.
        - Orden sugerido: Nombre, Telefono, Cumpleaños, Email.
        """
        import openpyxl

        # Validar tipo de archivo
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(400, detail="El archivo debe ser un Excel (.xlsx)")

        try:
            contents = await file.read()
            wb = openpyxl.load_workbook(io.BytesIO(contents), read_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
        except Exception as e:
            raise HTTPException(400, detail=f"Error al leer Excel: {str(e)}")

        if not rows:
            raise HTTPException(400, detail="Archivo vacío")

        # 1. Identificar columnas (Headers vs Data)
        headers = [str(c).lower().strip() if c else "" for c in rows[0]]
        
        # Mapeo inicial (por posición segun tu ejemplo)
        idx_fullname, idx_phone, idx_birth, idx_email = 0, 1, 2, 3
        start_row = 1 # Por defecto saltamos la primera si detectamos que es header

        # Buscar si hay nombres de columnas reales
        found_header = False
        for i, h in enumerate(headers):
            if any(key in h for key in ["email", "correo", "mail"]): 
                idx_email = i
                found_header = True
            if any(key in h for key in ["nombre", "fullname", "completo"]): 
                idx_fullname = i
                found_header = True
            if any(key in h for key in ["telefono", "phone", "tel"]): 
                idx_phone = i
                found_header = True
            if any(key in h for key in ["cumple", "birth", "nacimiento"]): 
                idx_birth = i
                found_header = True

        # Si el primer registro parece ser DATA (contiene un @), empezamos desde la fila 0
        if not found_header or "@" in str(rows[0][idx_email]):
            start_row = 0

        # 2. Procesar
        created_users, errors = [], []
        used_emails = set()
        actor_id = str(actor.id)
        from app.services.auth_service import auth_service

        for i in range(start_row, len(rows)):
            row = rows[i]
            if not any(row): continue # Saltar vacías

            try:
                # Extraer con seguridad de índices
                def get_val(idx): return row[idx] if idx < len(row) else None

                fullname_val = str(get_val(idx_fullname) or "").strip()
                phone_val = str(get_val(idx_phone) or "").strip()
                birth_val = get_val(idx_birth)
                email_val = str(get_val(idx_email) or "").strip().lower()

                if not email_val or not fullname_val:
                    errors.append({"row": i+1, "error": "Email y Nombre son obligatorios"})
                    continue

                if email_val in used_emails:
                    errors.append({"row": i+1, "error": f"Email duplicado: {email_val}"})
                    continue

                # Normalizar Fecha
                birth_date = None
                if birth_val:
                    if isinstance(birth_val, datetime):
                        birth_date = birth_val
                    else:
                        try:
                            from dateutil import parser as date_parser
                            birth_date = date_parser.parse(str(birth_val))
                        except: pass

                # Normalizar Telefono
                phone = phone_val
                if phone and not phone.startswith('+'):
                    phone = f"+{phone.replace(' ', '')}"

                # Username y Password (DvDDMMAAAA)
                username = await generate_chef_username(fullname_val)
                raw_password = generate_user_password(birth_date)

                # Registrar!
                user_data = UserCreate(
                    email=email_val, 
                    username=username, 
                    full_name=fullname_val,
                    password=raw_password, 
                    role=Role.USER,
                    phone_number=phone, 
                    birth_date=birth_date
                )
                
                new_user = await auth_service.register_user(user_data, created_by=actor_id)
                used_emails.add(email_val)

                created_users.append({
                    "row": i+1, "id": str(new_user.id), "email": email_val,
                    "username": username, "full_name": fullname_val,
                    "temporary_password": raw_password
                })

            except HTTPException as he:
                errors.append({"row": i+1, "error": he.detail})
            except Exception as e:
                errors.append({"row": i+1, "error": str(e)})

        wb.close()

        return {
            "total_processed": len(rows) - start_row,
            "created_count": len(created_users),
            "error_count": len(errors),
            "created_users": created_users,
            "errors": errors,
        }


# Instancia global (mismo patrón que auth_service)
user_service = UserService()
