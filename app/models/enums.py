from enum import Enum

class Role(str, Enum):
    SUPERADMIN = "SUPERADMIN"
    ADMIN = "ADMIN"
    MODERATOR = "MODERATOR"
    USER = "USER"


class CourseStatus(str, Enum):
    """Estado del curso en el ciclo de vida"""
    DRAFT = "DRAFT"  # En construcción
    REVIEW = "REVIEW"  # Para futuras etapas
    PUBLISHED = "PUBLISHED"  # DIsponible en explorar y mis cursos
    ARCHIVED = "ARCHIVED"  # No disponible en explorar pero si en mis cursos
    RETIRED = "RETIRED"  # No disponible en explorar ni en mis cursos


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

