"""
Router para endpoints de Enrollments (Inscripciones)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.models.user import User
from app.models.enums import EnrollmentStatus
from app.schemas.enrollment_schema import (
    EnrollmentCreateSchema,
    EnrollmentResponseSchema,
    EnrollmentProgressUpdateSchema,
    EnrollmentExtendSchema
)
from app.services.enrollment_service import EnrollmentService
from app.utils.dependencies import get_current_user, get_current_admin

router = APIRouter(
    tags=["Enrollments"]
)

# --- Endpoints de Usuario ---

@router.get("/enrollments/me", response_model=List[EnrollmentResponseSchema])
async def get_my_enrollments(
    status: Optional[EnrollmentStatus] = Query(None, description="Filtrar por estado"),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener mis enrollments (cursos a los que estoy inscrito).
    
    Query params:
    - status: ACTIVE | EXPIRED | CANCELLED (opcional)
    """
    return await EnrollmentService.get_user_enrollments(
        str(current_user.id),
        status
    )

@router.get("/enrollments/{enrollment_id}", response_model=EnrollmentResponseSchema)
async def get_enrollment(
    enrollment_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Obtener detalle de un enrollment.
    Solo el dueño o admin puede verlo.
    """
    return await EnrollmentService.get_enrollment_by_id(enrollment_id, current_user)

@router.patch("/enrollments/{enrollment_id}/progress")
async def update_progress(
    enrollment_id: str,
    data: EnrollmentProgressUpdateSchema,
    current_user: User = Depends(get_current_user)
):
    """
    Guardar progreso de video.
    
    Frontend debe llamar esto cada 10-30 segundos mientras ve el video.
    Guarda la posición actual para "continuar viendo".
    """
    return await EnrollmentService.update_progress(enrollment_id, data, current_user)

# --- Endpoints Admin ---

@router.post("/enrollments", response_model=EnrollmentResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_enrollment(
    data: EnrollmentCreateSchema,
    current_user: User = Depends(get_current_admin)
):
    """
    Inscribir estudiante a un curso (Admin).
    
    Crea un enrollment con:
    - expires_at = enrolled_at + 1 año
    - status = ACTIVE
    """
    return await EnrollmentService.create_enrollment(data, current_user)

@router.patch("/enrollments/{enrollment_id}/extend", response_model=EnrollmentResponseSchema)
async def extend_enrollment(
    enrollment_id: str,
    data: EnrollmentExtendSchema,
    current_user: User = Depends(get_current_admin)
):
    """
    Extender expiración de un enrollment (Admin).
    
    Agrega días adicionales a expires_at.
    """
    return await EnrollmentService.extend_enrollment(enrollment_id, data, current_user)

@router.delete("/enrollments/{enrollment_id}")
async def cancel_enrollment(
    enrollment_id: str,
    current_user: User = Depends(get_current_admin)
):
    """
    Cancelar enrollment (Admin).
    
    Cambia status a CANCELLED.
    """
    return await EnrollmentService.cancel_enrollment(enrollment_id, current_user)
