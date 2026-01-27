from enum import Enum

class Role(str, Enum):
    SUPERADMIN = "SUPERADMIN"
    ADMIN = "ADMIN"
    MODERATOR = "MODERATOR"
    USER = "USER"


class CourseStatus(str, Enum):
    """Estado del curso en el ciclo de vida"""
    DRAFT = "DRAFT"  # En construcción
    REVIEW = "REVIEW"  # En revisión
    PUBLISHED = "PUBLISHED"  # Publicado y disponible
    ARCHIVED = "ARCHIVED"  # Archivado (no disponible para nuevas inscripciones)
    RETIRED = "RETIRED"  # Retirado (no visible en catálogo)


class CourseDifficulty(str, Enum):
    """Nivel de dificultad del curso"""
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"


class EnrollmentStatus(str, Enum):
    """Estados de inscripción a curso"""
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"

