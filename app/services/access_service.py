"""
Servicio para verificación de acceso a cursos
Preparado para convivir con Membership futuro
"""

from app.models.enrollment import Enrollment
from app.models.enums import EnrollmentStatus


class AccessService:
    """
    Servicio de verificación de acceso.
    
    IMPORTANTE: Preparado para convivir con Membership.
    Cuando se implemente Membership, solo descomentar las líneas marcadas.
    """
    
    @staticmethod
    async def user_can_access_course(user_id: str, course_id: str) -> bool:
        """
        Verifica si un usuario tiene acceso a un curso.
        
        FUTURO: Cuando se implemente Membership, agregar check aquí:
        # user = await User.get(user_id)
        # if user.has_active_membership:
        #     return True
        
        Args:
            user_id: ID del usuario
            course_id: ID del curso
            
        Returns:
            bool: True si tiene acceso, False si no
        """
        
        # Por ahora: Solo verificar Enrollment
        enrollment = await Enrollment.find_one(
            Enrollment.user_id == user_id,
            Enrollment.course_id == course_id,
            Enrollment.status == EnrollmentStatus.ACTIVE
        )
        
        if not enrollment:
            return False
        
        # Verificar que no haya expirado
        return enrollment.is_active_now()
    
    @staticmethod
    async def get_user_enrollment_for_course(user_id: str, course_id: str):
        """
        Obtiene el enrollment activo de un usuario para un curso.
        
        Returns:
            Enrollment | None: El enrollment si existe y está activo
        """
        enrollment = await Enrollment.find_one(
            Enrollment.user_id == user_id,
            Enrollment.course_id == course_id,
            Enrollment.status == EnrollmentStatus.ACTIVE
        )
        
        if enrollment and enrollment.is_active_now():
            return enrollment
        
        return None
