"""
Schemas Pydantic para Materiales de Lección
Validación y serialización de datos de archivos adjuntos
"""

from pydantic import BaseModel, HttpUrl, ConfigDict, Field
from datetime import datetime

# NO se usa CreateSchema porque la creación es por FormData
# (UploadFile + Form fields en el endpoint)

class MaterialResponseSchema(BaseModel):
    """
    Schema de respuesta para Material de Lección.
    Devuelto al crear/obtener materiales embebidos.
    """
    title: str = Field(..., description="Título descriptivo del archivo")
    resource_url: HttpUrl = Field(..., description="URL del recurso en Cloudinary")
    file_format: str = Field(..., description="Formato del archivo (pdf, jpg, etc)")
    is_downloadable: bool = Field(default=True, description="Si se permite descargar")
    order: int = Field(..., description="Orden del material en la lista")
    created_at: datetime = Field(..., description="Fecha de creación")
    created_by: str = Field(..., description="ID del usuario que lo subió")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "title": "Receta de Macarons en PDF",
                "resource_url": "https://res.cloudinary.com/demo/raw/upload/receta.pdf",
                "file_format": "pdf",
                "is_downloadable": True,
                "order": 1,
                "created_at": "2026-01-20T10:00:00Z",
                "created_by": "507f1f77bcf86cd799439011"
            }
        }
    )
