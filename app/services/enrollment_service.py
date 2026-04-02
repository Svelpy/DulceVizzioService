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
    async def _build_enrollment_response(enrollment: Enrollment,user: Optional[User] = None,course: Optional[Course] = None) -> Dict[str, Any]:
        """Helper para construir el diccionario de respuesta anidado."""
        from app.models.lesson import Lesson
        
        # Si no nos pasan el usuario/curso, lo buscamos en la BD
        if not user:
            user = await User.get(enrollment.user_id)
        if not course:
            course = await Course.get(enrollment.course_id)
            
        # Tolerancia a fallos: Si la última lección vista la borró el admin, la recolocamos a la primera activa
        if enrollment.last_accessed_lesson_id:
            lesson = await Lesson.get(enrollment.last_accessed_lesson_id)
            if not lesson or lesson.is_deleted:
                # Buscar la primera válida
                first_lesson = await Lesson.find(
                    {"course_id": enrollment.course_id, "is_deleted": False}
                ).sort("+order").first_or_none()
                
                enrollment.last_accessed_lesson_id = first_lesson.id if first_lesson else None
                await enrollment.save()
                
        enrollment_dict = enrollment.model_dump(mode='json')
        
        enrollment_dict["user"] = {
            "id": str(user.id),
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "avatar_url": str(user.avatar_url) if user.avatar_url else None
        } if user else None
        
        if course:
            course_dict = course.model_dump(mode='json')
            course_dict["is_enrolled"] = True
            enrollment_dict["course"] = course_dict
        else:
            enrollment_dict["course"] = None
        
        return enrollment_dict

    @staticmethod
    async def create_enrollment(data: EnrollmentCreateSchema, admin: User) -> Dict[str, Any]:
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
            Enrollment.is_deleted == False
        )
        
        if existing:
            raise HTTPException(status_code=400,detail="El usuario ya tiene una inscripción en este curso")
        
        # Crear enrollment con expiración de 1 año
        enrollment = Enrollment.create_with_expiration(
            user_id=data.user_id,
            course_id=data.course_id,
            notes=data.notes,
            created_by=str(admin.id)
        )
        
        await enrollment.save()
        
        return await EnrollmentService._build_enrollment_response(enrollment=enrollment, user=user, course=course)
    
    @staticmethod
    async def get_user_enrollments(
        user_id: str,
        search: Optional[str] = None,
        status: Optional[EnrollmentStatus] = None,
        page: int = 1,
        size: int = 10
    ) -> Dict[str, Any]:
        """Obtener enrollments de un usuario con paginación y búsqueda"""
        from bson import ObjectId
        
        # Convertir user_id string a ObjectId
        try:
            user_oid = ObjectId(user_id)
        except Exception:
            # Si el ID es inválido, retornar vacío
            return {
                "total": 0,
                "page": page,
                "per_page": size,
                "total_pages": 0,
                "data": []
            }
        
        # Usar filtros de diccionario para mayor compatibilidad
        query_filters = [{"user_id": user_oid}, {"is_deleted": False}]
        
        if status:
            query_filters.append({"status": status})
        
        # Si hay búsqueda, necesitamos filtrar por título de curso
        if search:
            # Buscar cursos que coincidan
            matching_courses = await Course.find(
                {"title": {"$regex": search, "$options": "i"}, "is_deleted": False}
            ).to_list()
            
            if matching_courses:
                course_ids = [c.id for c in matching_courses]
                query_filters.append({"course_id": {"$in": course_ids}})
            else:
                # Si no hay cursos que coincidan, retornar vacío
                return {
                    "total": 0,
                    "page": page,
                    "per_page": size,
                    "total_pages": 0,
                    "data": []
                }
        
        total = await Enrollment.find(*query_filters).count()
        
        # Calcular paginación
        total_pages = (total + size - 1) // size
        
        # Obtener items
        items = await Enrollment.find(*query_filters)\
            .sort("-enrolled_at")\
            .skip((page - 1) * size)\
            .limit(size)\
            .to_list()
        
        # Armamos un diccionario con todos los cursos de un solo usuario
        course_ids = list(set([e.course_id for e in items]))
        courses = await Course.find({"_id": {"$in": course_ids}, "is_deleted": False}).to_list()
        courses_dict = {c.id: c for c in courses}  #diccionario {course_id:course object}
        #un unico user_doc para todas las vueltas
        user_doc = await User.get(user_id)      
        enrollments_data = []

        for enrollment in items:
            #un course_doc distinto para cada vuelta
            course_doc = courses_dict.get(enrollment.course_id)
            #mandamos a la funcion helpper el usuario que no cambia y el curso que cambia en cada vuelta
            enrollment_dict = await EnrollmentService._build_enrollment_response(enrollment=enrollment,user=user_doc,course=course_doc)
            enrollments_data.append(enrollment_dict)
        
        return {
            "total": total,
            "page": page,
            "per_page": size,
            "total_pages": total_pages,
            "data": enrollments_data
        }

    @staticmethod
    async def get_all_enrollments(
        search: Optional[str] = None,
        page: int = 1,
        size: int = 10,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Obtener todos los enrollments (Admin) con filtros, búsqueda y paginación"""
        query_filters = [Enrollment.is_deleted == False]
        
        if filters:
            if filters.get("user_id"):
                query_filters.append(Enrollment.user_id == filters["user_id"])
            if filters.get("course_id"):
                query_filters.append(Enrollment.course_id == filters["course_id"])
            if filters.get("status"):
                query_filters.append(Enrollment.status == filters["status"])
        
        # Si hay búsqueda, buscar en usuarios Y cursos
        if search:
            matching_user_ids = []
            matching_course_ids = []
            
            # Buscar usuarios por username o full_name
            matching_users = await User.find(
                {"$or": [
                    {"username": {"$regex": search, "$options": "i"}},
                    {"full_name": {"$regex": search, "$options": "i"}}
                ], "is_deleted": False}
            ).to_list()
            matching_user_ids = [u.id for u in matching_users]
            
            # Buscar cursos por título
            matching_courses = await Course.find(
                {"title": {"$regex": search, "$options": "i"}, "is_deleted": False}
            ).to_list()
            matching_course_ids = [c.id for c in matching_courses]
            
            # Filtrar enrollments que coincidan con usuarios O cursos
            if matching_user_ids or matching_course_ids:
                or_conditions = []
                if matching_user_ids:
                    or_conditions.append({"user_id": {"$in": matching_user_ids}})
                if matching_course_ids:
                    or_conditions.append({"course_id": {"$in": matching_course_ids}})
                
                query_filters.append({"$or": or_conditions})
            else:
                # Si no hay coincidencias, retornar vacío
                return {
                    "total": 0,
                    "page": page,
                    "per_page": size,
                    "total_pages": 0,
                    "data": []
                }
            
        # Ejecutar query
        query = Enrollment.find(*query_filters)
        total = await query.count()
        
        total_pages = (total + size - 1) // size
        
        items = await query.sort("-enrolled_at")\
            .skip((page - 1) * size)\
            .limit(size)\
            .to_list()
        
        # Armamos dos diccionarios, uno con todos los cursos y otro con todos los usuarios
        course_ids = list(set([e.course_id for e in items]))
        user_ids = list(set([e.user_id for e in items]))
        
        courses = await Course.find({"_id": {"$in": course_ids}}).to_list()
        users = await User.find({"_id": {"$in": user_ids}}).to_list()
        
        courses_dict = {c.id: c for c in courses}#diccionario {course_id:course_object}
        users_dict = {u.id: u for u in users}#diccionario {user_id:user_object}
        
   
        enrollments_data = []
        for enrollment in items:
            
            #un course_doc distinto para cada vuelta
            course_doc = courses_dict.get(enrollment.course_id)
            #un user_doc distinto para cada vuelta
            user_doc = users_dict.get(enrollment.user_id)
           
            enrollment_dict = await EnrollmentService._build_enrollment_response(enrollment=enrollment,user=user_doc,course=course_doc)
            enrollments_data.append(enrollment_dict)
            
        return {
            "total": total,
            "page": page,
            "per_page": size,
            "total_pages": total_pages,
            "data": enrollments_data
        }
    
    @staticmethod
    async def get_enrollment_by_id(enrollment_id: str, user: User) -> Dict[str, Any]:
        """Obtener enrollment por ID"""
        enrollment = await Enrollment.get(enrollment_id)
        
        if not enrollment or enrollment.is_deleted:
            raise HTTPException(status_code=404, detail="Inscripción no encontrada")
        
        # Verificar permisos
        is_admin = user.role in [Role.ADMIN, Role.SUPERADMIN]
        is_owner = str(enrollment.user_id) == str(user.id)
        
        if not is_admin and not is_owner:
            raise HTTPException(status_code=403, detail="No tienes permiso para ver esta inscripción")    
        
        return await EnrollmentService._build_enrollment_response(enrollment)
    
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
        
        if not enrollment or enrollment.is_deleted:
            raise HTTPException(status_code=404, detail="Inscripción no encontrada")
        
        # Solo el dueño puede actualizar su progreso
        if str(enrollment.user_id) != str(user.id):
            raise HTTPException(status_code=403, detail="No puedes actualizar esta inscripción")
        
        # Verificar que no haya expirado
        if not await enrollment.is_active_now():
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
    ) -> Dict[str, Any]:
        """Extender expiración de enrollment (admin)"""
        enrollment = await Enrollment.get(enrollment_id)
        
        if not enrollment or enrollment.is_deleted:
            raise HTTPException(status_code=404, detail="Inscripción no encontrada")
        
        # Extender fecha
        from datetime import timedelta
        enrollment.expires_at = enrollment.expires_at + timedelta(days=data.additional_days)
        enrollment.updated_by = str(admin.id)
        
        # Si estaba expirado y se extiende, reactivar
        if enrollment.status == EnrollmentStatus.EXPIRED:
            enrollment.status = EnrollmentStatus.ACTIVE
        
        await enrollment.save()
        
        return await EnrollmentService._build_enrollment_response(enrollment)
    
    @staticmethod
    async def delete_enrollment(enrollment_id: str, admin: User) -> Dict[str, str]:
        """Eliminar enrollment (Admin) - Físico o Lógico según rol"""
        enrollment = await Enrollment.get(enrollment_id)
        
        if not enrollment or enrollment.is_deleted:
            raise HTTPException(status_code=404, detail="Inscripción no encontrada")
        
        if admin.role == Role.SUPERADMIN:
            # Borrado FÍSICO
            await enrollment.delete()
            return {"message": "Inscripción eliminada permanentemente"}
        else:
            # Borrado LÓGICO
            enrollment.is_deleted = True
            enrollment.deleted_at = datetime.utcnow()
            enrollment.updated_by = str(admin.id)
            await enrollment.save()
            return {"message": "Inscripción enviada a papelera"}
