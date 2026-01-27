"""
Servicio para lógica de negocio de Enrollments
Gestión de inscripciones a cursos individuales
"""

from typing import List, Optional, Dict, Any
from fastapi import HTTPException
from datetime import datetime
from app.models.enrollment import Enrollment
from app.models.course import Course
from app.models.user import User
from app.models.enums import EnrollmentStatus, Role
from app.schemas.enrollment_schema import (
    EnrollmentCreateSchema,
    EnrollmentProgressUpdateSchema,
    EnrollmentExtendSchema
)


class EnrollmentService:
    
    @staticmethod
    async def create_enrollment(data: EnrollmentCreateSchema, admin: User) -> Enrollment:
        """
        Crear enrollment (solo admin).
        El admin inscribe manualmente al estudiante.
        """
        # Verificar que el curso existe
        course = await Course.get(data.course_id)
        if not course or course.is_deleted:
            raise HTTPException(status_code=404, detail="Curso no encontrado")
        
        # Verificar que el usuario existe
        user = await User.get(data.user_id)
        if not user or user.is_deleted:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Verificar si ya está inscrito
        existing = await Enrollment.find_one(
            Enrollment.user_id == data.user_id,
            Enrollment.course_id == data.course_id,
            Enrollment.status == EnrollmentStatus.ACTIVE
        )
        
        if existing and existing.is_active_now():
            raise HTTPException(
                status_code=400,
                detail="El usuario ya tiene una inscripción activa en este curso"
            )
        
        # Crear enrollment con expiración de 1 año
        enrollment = Enrollment.create_with_expiration(
            user_id=data.user_id,
            course_id=data.course_id,
            notes=data.notes,
            created_by=str(admin.id)
        )
        
        await enrollment.save()
        
        return enrollment
    
    @staticmethod
    async def get_user_enrollments(
        user_id: str,
        status: Optional[EnrollmentStatus] = None
    ) -> List[Enrollment]:
        """Obtener enrollments de un usuario"""
        filters = [Enrollment.user_id == user_id]
        
        if status:
            filters.append(Enrollment.status == status)
        
        enrollments = await Enrollment.find(*filters).sort("-enrolled_at").to_list()
        
        return enrollments
    
    @staticmethod
    async def get_enrollment_by_id(enrollment_id: str, user: User) -> Enrollment:
        """Obtener enrollment por ID"""
        enrollment = await Enrollment.get(enrollment_id)
        
        if not enrollment:
            raise HTTPException(status_code=404, detail="Inscripción no encontrada")
        
        # Verificar permisos
        is_admin = user.role in [Role.ADMIN, Role.SUPERADMIN]
        is_owner = str(enrollment.user_id) == str(user.id)
        
        if not is_admin and not is_owner:
            raise HTTPException(status_code=403, detail="No tienes permiso para ver esta inscripción")
        
        return enrollment
    
    @staticmethod
    async def update_progress(
        enrollment_id: str,
        data: EnrollmentProgressUpdateSchema,
        user: User
    ) -> Dict[str, str]:
        """
        Actualizar progreso de video.
        Llamado por frontend cada 10-30 segundos.
        """
        enrollment = await Enrollment.get(enrollment_id)
        
        if not enrollment:
            raise HTTPException(status_code=404, detail="Inscripción no encontrada")
        
        # Solo el dueño puede actualizar su progreso
        if str(enrollment.user_id) != str(user.id):
            raise HTTPException(status_code=403, detail="No puedes actualizar esta inscripción")
        
        # Verificar que no haya expirado
        if not enrollment.is_active_now():
            raise HTTPException(status_code=403, detail="Tu inscripción ha expirado")
        
        # Actualizar progreso
        enrollment.last_accessed_lesson_id = data.lesson_id
        enrollment.last_video_position_seconds = data.video_position_seconds
        enrollment.last_accessed_at = datetime.utcnow()
        enrollment.updated_by = str(user.id)
        
        await enrollment.save()
        
        return {"message": "Progreso guardado correctamente"}
    
    @staticmethod
    async def extend_enrollment(
        enrollment_id: str,
        data: EnrollmentExtendSchema,
        admin: User
    ) -> Enrollment:
        """Extender expiración de enrollment (admin)"""
        enrollment = await Enrollment.get(enrollment_id)
        
        if not enrollment:
            raise HTTPException(status_code=404, detail="Inscripción no encontrada")
        
        # Extender fecha
        from datetime import timedelta
        enrollment.expires_at = enrollment.expires_at + timedelta(days=data.additional_days)
        enrollment.updated_by = str(admin.id)
        
        # Si estaba expirado y se extiende, reactivar
        if enrollment.status == EnrollmentStatus.EXPIRED:
            enrollment.status = EnrollmentStatus.ACTIVE
        
        await enrollment.save()
        
        return enrollment
    
    @staticmethod
    async def cancel_enrollment(enrollment_id: str, admin: User) -> Dict[str, str]:
        """Cancelar enrollment (admin)"""
        enrollment = await Enrollment.get(enrollment_id)
        
        if not enrollment:
            raise HTTPException(status_code=404, detail="Inscripción no encontrada")
        
        enrollment.status = EnrollmentStatus.CANCELLED
        enrollment.updated_by = str(admin.id)
        
        await enrollment.save()
        
        return {"message": "Inscripción cancelada correctamente"}
