"""
Servicio para lógica de negocio de Cursos
REFACTORIZADO: Trabaja con relaciones Course-Lesson
"""

from typing import List, Optional, Dict, Any
from fastapi import UploadFile, HTTPException
from beanie.operators import In
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.user import User
from app.models.enums import CourseStatus, Role
from app.schemas.course_schema import CourseCreateSchema, CourseUpdateSchema
from app.utils.slug import generate_slug, ensure_unique_slug_course
from app.services.cloudinary_service import CloudinaryService
from datetime import datetime

class CourseService:
    
    @staticmethod
    async def update_course_stats(course_id: str):
        """
        Recalcula y guarda estadísticas del curso en DB.
        Debe llamarse cuando se agregan/eliminan/editan lecciones.
        """
        from bson import ObjectId
        # Asegurar que sea ObjectId si viene como str
        if isinstance(course_id, str):
            try:
                course_id = ObjectId(course_id)
            except:
                return

        course = await Course.get(course_id)
        if not course:
            return
        
        # Calcular estadísticas reales
        lessons = await Lesson.find({"course_id": course.id}).to_list()
        
        course.lessons_count = len(lessons)
        total_seconds = sum(l.duration_seconds or 0 for l in lessons)
        course.total_duration_hours = round(total_seconds / 3600, 2)
        
        # Guardar cambios
        await course.save()

    @staticmethod
    async def get_courses(
        page: int = 1, 
        limit: int = 10,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        public_view: bool = False
    ) -> Dict[str, Any]:
        """
        Obtener lista paginada de cursos con filtros
        """
        query_filters = [Course.is_deleted == False]

        if public_view:
            query_filters.append(Course.status == CourseStatus.PUBLISHED)
        elif status:
            try:
                query_filters.append(Course.status == CourseStatus(status))
            except ValueError:
                pass
            
        if category:
            query_filters.append(Course.category == category)
            
        if difficulty:
            query_filters.append(Course.difficulty == difficulty)
            
        if search:
            query_filters.append({"title": {"$regex": search, "$options": "i"}})

        query = Course.find(*query_filters)
        total = await query.count()
        
        skip = (page - 1) * limit
        courses = await query.sort("-created_at").skip(skip).limit(limit).to_list()
        
        # Ya no necesitamos enriquecer, los datos están en la DB
        
        return {
            "data": courses,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }

    @staticmethod
    async def get_course_by_slug(slug: str, public_view: bool = False) -> Course:
        """Obtener curso por slug"""
        # Usar filtros por diccionario para evitar problemas con Beanie Indexed fields
        query_filters = [{"slug": slug}, {"is_deleted": False}]
        
        if public_view:
            query_filters.append({"status": CourseStatus.PUBLISHED})
            
        course = await Course.find_one(*query_filters)
        
        if not course and not public_view:
            try:
                from bson import ObjectId
                if ObjectId.is_valid(slug):
                    course = await Course.find_one({"_id": ObjectId(slug)}, {"is_deleted": False})
            except:
                pass

        if not course:
            raise HTTPException(status_code=404, detail="Curso no encontrado")
        
        return course

    @staticmethod
    async def create_course(data: CourseCreateSchema, user: User) -> Course:
        """Crear nuevo curso"""
        slug_base = generate_slug(data.title)
        slug = await ensure_unique_slug_course(slug_base)
        
        course_data = data.model_dump()
        course = Course(
            **course_data,
            slug=slug,
            status=CourseStatus.DRAFT,
            created_by=str(user.id)
        )
        
        await course.save()
        return course

    @staticmethod
    async def update_course(course_id: str, data: CourseUpdateSchema, user: User) -> Course:
        """Actualizar curso"""
        course = await Course.get(course_id)
        if not course or course.is_deleted:
            raise HTTPException(status_code=404, detail="Curso no encontrado")
            
        update_data = data.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(course, key, value)
            
        course.updated_by = str(user.id)
        await course.save()
        return course

    @staticmethod
    async def update_status(course_id: str, status: CourseStatus, user: User) -> Course:
        """Cambiar estado del curso"""
        course = await Course.get(course_id)
        if not course or course.is_deleted:
            raise HTTPException(status_code=404, detail="Curso no encontrado")
            
        if course.status != status:
            course.status = status
            
            if status == CourseStatus.PUBLISHED and not course.published_at:
                course.published_at = datetime.utcnow()
                
            course.updated_by = str(user.id)
            await course.save()
        
        return course

    @staticmethod
    async def upload_cover_image(course_id: str, file: UploadFile, user: User) -> Course:
        """Subir imagen de portada"""
        course = await Course.get(course_id)
        if not course or course.is_deleted:
            raise HTTPException(status_code=404, detail="Curso no encontrado")
            
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")
            
        try:
            url = await CloudinaryService.upload_image(file, folder="courses/covers")
            
            course.cover_image_url = url
            course.updated_by = str(user.id)
            await course.save()
            
            return course
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al subir imagen: {str(e)}")

    @staticmethod
    async def delete_course(course_id: str, user: User) -> Dict[str, str]:
        """
        Eliminar curso
        - ADMIN: Soft delete
        - SUPERADMIN: Hard delete (físico) + eliminar lessons relacionadas
        """
        course = await Course.get(course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Curso no encontrado")
            
        if user.role == Role.SUPERADMIN:
            # Borrado FÍSICO: eliminar lessons asociadas también
            await Lesson.find({"course_id": course.id}).delete()
            await course.delete()
            return {"message": "Curso eliminado permanentemente"}
        elif user.role == Role.ADMIN:
            # Borrado LÓGICO
            course.is_deleted = True
            course.deleted_at = datetime.utcnow()
            course.updated_by = str(user.id)
            await course.save()
            return {"message": "Curso enviado a papelera"}
        else:
             raise HTTPException(status_code=403, detail="No tienes permisos para eliminar cursos")
