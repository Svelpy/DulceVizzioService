"""
Schemas Pydantic para Enrollments (Inscripciones)
Validación y serialización de datos de inscripciones a cursos
"""

from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from typing import Optional, List, TypeVar, Generic
from datetime import datetime
from beanie import PydanticObjectId
from app.models.enums import EnrollmentStatus,Role
from .course_schema import CourseResponseSchema


class EnrollmentCreateSchema(BaseModel):
    """
    Schema para crear enrollment (solo admin).
    El admin inscribe manualmente al estudiante.
    """
    user_id: PydanticObjectId = Field(..., description="ID del estudiante a inscribir")
    course_id: PydanticObjectId = Field(..., description="ID del curso")
    notes: Optional[str] = Field(None, max_length=500, description="Notas administrativas")


class EnrollmentProgressUpdateSchema(BaseModel):
    """
    Schema para actualizar progreso de video.
    Enviado por frontend cada 10-30 segundos.
    """
    lesson_id: PydanticObjectId = Field(..., description="ID de la lección actual")
    video_position_seconds: int = Field(..., ge=0, description="Posición del video en segundos")


class EnrollmentExtendSchema(BaseModel):
    """Schema para extender expiración (admin)"""
    additional_days: int = Field(..., ge=1, le=3650, description="Días adicionales (máx 10 años)")


class UserEmbeddedSchema(BaseModel):
    id: PydanticObjectId
    username: str
    full_name: str
    role: Role
    is_active: bool
    avatar_url: Optional[HttpUrl] = None
    model_config = ConfigDict(from_attributes=True)
#------------------------------------------------------------------------
class EnrollmentResponseSchema(BaseModel):
    """
    Schema de respuesta de enrollment.
    Usado en GET /enrollments
    """
    id: PydanticObjectId
    user: UserEmbeddedSchema
    course: CourseResponseSchema
    # Estado
    status: EnrollmentStatus
    enrolled_at: datetime
    expires_at: datetime
    
    # Progreso
    last_accessed_lesson_id: Optional[PydanticObjectId] = None
    last_video_position_seconds: Optional[int] = None
    last_accessed_at: Optional[datetime] = None
    
    # Completado
    completed_at: Optional[datetime] = None
    certificate_url: Optional[HttpUrl] = None
    
    # Metadata
    notes: Optional[str] = None
    
    # Campos de auditoría
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "69b82442ec85b6165e252b63",
                "user": {
                    "id": "695cecf6d3c63cf174c7f068",
                    "username": "string1",
                    "full_name": "string 1",
                    "role": "USER",
                    "is_active": True,
                    "avatar_url": None
                },
                "course": {
                    "id": "698c92f85a7111c912ec9835",
                    "title": "Curso de Torta Comercial",
                    "slug": "curso-de-torta-comercial",
                    "description": "Un curso completo para aprender repostería comercial...",
                    "category": 1,
                    "subcategory": "Tortas",
                    "difficulty": "INTERMEDIATE",
                    "tags": ["tortas", "comercial"],
                    "price": 45,
                    "currency": "USD",
                    "whatsapp_group_url": "https://chat.whatsapp.com/abc123",
                    "cover_image_url": "https://res.cloudinary.com/dmxooones/image/upload/v1770821020/dulcevicio/courses/covers/xgw3ft4vikhyo3pfj65v.png",
                    "status": "PUBLISHED",
                    "rating_average": 4.5,
                    "enrollment_count": 10,
                    "is_enrolled": True,
                    "lessons_count": 5,
                    "total_duration_hours": 3.5,
                    "created_at": "2026-01-20T10:00:00Z",
                    "published_at": "2026-01-22T10:00:00Z",
                    "updated_at": "2026-01-22T10:00:00Z",
                    "created_by": "695cc40748b8077a89cb103e",
                    "updated_by": "695cc40748b8077a89cb103e"
                },
                "status": "ACTIVE",
                "enrolled_at": "2026-03-16T15:39:46.157000",
                "expires_at": "2028-03-15T15:39:46.157000",
                "last_accessed_lesson_id": None,
                "last_video_position_seconds": None,
                "last_accessed_at": None,
                "completed_at": None,
                "certificate_url": None,
                "notes": "string",
                "created_at": "2026-03-16T15:39:46.158000",
                "updated_at": "2026-03-16T15:42:36.046000",
                "created_by": "695cc40748b8077a89cb103e",
                "updated_by": "695cc40748b8077a89cb103e"
            }
        }
    )

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Schema genérico de respuesta paginada"""
    total: int          # Total de registros encontrados
    page: int           # Página actual
    per_page: int       # Registros por página
    total_pages: int    # Total de páginas
    data: List[T]       # Lista de objetos


class EnrollmentListResponse(PaginatedResponse[EnrollmentResponseSchema]):
    """Respuesta paginada de enrollments"""
    pass
