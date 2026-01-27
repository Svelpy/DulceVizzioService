"""
Modelos de Lección y componentes relacionados
"""

from beanie import PydanticObjectId
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime
from .base import BaseDocument


class LessonMaterial(BaseModel):
    """
    Material/Archivos específicos de una lección
    EMBEBIDO dentro de Lesson (no tiene colección propia)
    """
    title: str = Field(..., description="Título del archivo")
    resource_url: HttpUrl = Field(..., description="URL del recurso en Cloudinary")
    file_format: Optional[str] = Field(None, description="Formato del archivo (pdf, jpg, etc)")
    is_downloadable: bool = Field(default=True, description="Si es descargable")
    order: int = Field(default=1, description="Orden del archivo")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    
    # NO tiene Settings, NO tiene colección propia
    # Vive únicamente dentro de lesson.materials


class LessonComment(BaseDocument):
    """
    Comentario en una lección específica
    Sistema de comentarios por clase (reemplaza foro para etapa 1)
    """
    lesson_id: str = Field(..., description="ID de la lección")
    user_id: str = Field(..., description="ID del usuario que comentó")
    user_name: str = Field(..., description="Nombre del usuario (desnormalizado)")
    user_avatar_url: Optional[HttpUrl] = Field(None, description="Avatar del usuario")
    comment: str = Field(..., min_length=1, max_length=1000, description="Contenido del comentario")
    parent_comment_id: Optional[str] = Field(None, description="ID del comentario padre si es respuesta")
    is_approved: bool = Field(default=True, description="Si el comentario está aprobado")
    likes_count: int = Field(default=0, description="Número de likes")
    
    class Settings:
        name = "lesson_comments"
        indexes = [
            "lesson_id",
            "user_id",
            "parent_comment_id",
            "created_at",
            "is_approved"
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "lesson_id": "lesson_123",
                "user_id": "user_456",
                "user_name": "María García",
                "comment": "Excelente explicación, muy clara!",
                "is_approved": True
            }
        }


class Lesson(BaseDocument):
    """
    Modelo de Lección/Clase del curso
    Cada lección representa un video individual almacenado en Bunny.net
    Relacionado con Course por course_id
    """
    course_id: PydanticObjectId = Field(..., description="ID del curso al que pertenece")
    title: str = Field(..., description="Título de la lección")
    summary: Optional[str] = Field(None, description="Resumen de la lección")
    duration_seconds: Optional[int] = Field(None, description="Duración del video en segundos")    
    order: int = Field(default=1, description="Orden de la lección en el curso")
    is_preview: bool = Field(default=False, description="Si la lección es de vista previa gratuita")
    video_url: Optional[HttpUrl] = Field(None, description="URL del video en Bunny.net")
    video_id: Optional[str] = Field(None, description="ID del video en Bunny.net")
    materials: List[LessonMaterial] = Field(default_factory=list, description="Archivos de la clase")
   
    class Settings:
        name = "lessons"
        indexes = ["course_id", "order", "is_preview"]
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Introducción a la técnica de merengue",
                "summary": "Aprende los fundamentos del merengue francés paso a paso",
                "video_url": "https://video.bunnycdn.com/play/12345/abc",
                "video_id": "abc123",
                "duration_seconds": 1200,
                "order": 1,
                "is_preview": True,
                "materials": []
            }
        }
