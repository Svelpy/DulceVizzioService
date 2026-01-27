"""
Servicio para lógica de negocio de Lecciones
REFACTORIZADO: Usa relaciones por course_id en lugar de embebido
"""

from typing import List, Optional, Dict, Any
from fastapi import HTTPException
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.user import User
from app.models.enums import Role, CourseStatus
from app.schemas.lesson_schema import LessonCreateSchema, LessonUpdateSchema
from datetime import datetime

class LessonService:
    
    @staticmethod
    async def get_lessons_by_course(course_id: str, user: Optional[User] = None) -> List[Lesson]:
        """
        Obtener lecciones de un curso.
        Ahora consulta directamente la colección lessons por course_id
        """
        course = await Course.get(course_id)
        if not course or course.is_deleted:
            raise HTTPException(status_code=404, detail="Curso no encontrado")
            
        # Si el curso no está publicado y no es admin, 404
        is_admin = user and user.role in [Role.ADMIN, Role.SUPERADMIN]
        if course.status != CourseStatus.PUBLISHED and not is_admin:
             raise HTTPException(status_code=404, detail="Curso no encontrado")
             
        # Consultar lessons por course_id
        lessons = await Lesson.find({"course_id": course.id}).sort("+order").to_list()
        return lessons

    @staticmethod
    async def get_lesson_by_id(lesson_id: str, user: Optional[User] = None) -> Lesson:
        """Obtener lección por ID"""
        lesson = await Lesson.get(lesson_id)
        if not lesson:
            raise HTTPException(status_code=404, detail="Lección no encontrada")
            
        return lesson

    @staticmethod
    async def create_lesson(course_id: str, data: LessonCreateSchema, user: User) -> Lesson:
        """
        Crear lección y asociarla al curso.
        REFACTORIZADO: Ya no se agrega a lista embebida del curso
        """
        # Import local para evitar circular si hubiera
        from app.services.course_service import CourseService
        
        course = await Course.get(course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Curso no encontrado")
            
        # Calcular orden: siempre al final
        max_order_lesson = await Lesson.find(
            {"course_id": course.id}
        ).sort("-order").first_or_none()
        
        next_order = (max_order_lesson.order + 1) if max_order_lesson else 1
            
        # Crear documento Lesson con course_id
        lesson_data = data.model_dump()
        lesson = Lesson(
            **lesson_data,
            order=next_order,     # Asignar orden calculado
            course_id=course.id,  # Asociar al curso
            created_by=str(user.id)
        )
        await lesson.save()
        
        # Actualizar estadísticas del curso
        await CourseService.update_course_stats(str(course.id))
        
        return lesson

    @staticmethod
    async def update_lesson(lesson_id: str, data: LessonUpdateSchema, user: User) -> Lesson:
        """
        Actualizar lección
        REFACTORIZADO: Ya no necesita sincronizar con Course
        """
        # Import local
        from app.services.course_service import CourseService
        
        lesson = await Lesson.get(lesson_id)
        if not lesson:
            raise HTTPException(status_code=404, detail="Lección no encontrada")
            
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(lesson, key, value)
            
        lesson.updated_by = str(user.id)
        await lesson.save()
        
        # Si cambia la duración, recalcular stats
        if "duration_seconds" in update_data:
            await CourseService.update_course_stats(str(lesson.course_id))
            
        return lesson

    @staticmethod
    async def reorder_lesson(lesson_id: str, new_order: int, user: User) -> List[Lesson]:
        """
        Cambiar orden de una lección
        REFACTORIZADO: Opera sobre la colección lessons directamente
        """
        lesson = await Lesson.get(lesson_id)
        if not lesson:
             raise HTTPException(status_code=404, detail="Lección no encontrada")
             
        # Obtener todas las lessons del mismo curso
        all_lessons = await Lesson.find(
            {"course_id": lesson.course_id}
        ).sort("+order").to_list()
        
        # Reordenar lógica
        current_index = next((i for i, l in enumerate(all_lessons) if l.id == lesson.id), None)
        
        if current_index is not None:
            # Remover de posición actual
            all_lessons.pop(current_index)
            
            # Insertar en nueva posición
            insert_index = max(0, min(new_order - 1, len(all_lessons)))
            all_lessons.insert(insert_index, lesson)
            
            # Recalcular order para todas
            for i, l in enumerate(all_lessons):
                l.order = i + 1
                l.updated_by = str(user.id)
                await l.save()
            
        return all_lessons

    @staticmethod
    async def delete_lesson(lesson_id: str, user: User) -> Dict[str, str]:
        """
        Eliminar lección
        REFACTORIZADO: Solo elimina de la colección lessons
        """
        # Import local
        from app.services.course_service import CourseService
        
        lesson = await Lesson.get(lesson_id)
        if not lesson:
            raise HTTPException(status_code=404, detail="Lección no encontrada")
            
        course_id = lesson.course_id
        
        # Eliminar documento
        await lesson.delete()
        
        # Opcional: Reordenar lecciones restantes
        remaining_lessons = await Lesson.find(
            {"course_id": course_id}
        ).sort("+order").to_list()
        
        for i, l in enumerate(remaining_lessons):
            if l.order != i + 1:
                l.order = i + 1
                await l.save()
                
        # Actualizar estadísticas del curso
        await CourseService.update_course_stats(str(course_id))
        
        return {"message": "Lección eliminada correctamente"}
