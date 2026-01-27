"""
Servicio para lógica de negocio de Materiales de Lección
REFACTORIZADO: LessonMaterial es EMBEBIDO en Lesson (no tiene colección)
"""

from typing import List, Optional, Dict, Any
from fastapi import UploadFile, HTTPException, status
from app.models.lesson import Lesson, LessonMaterial
from app.models.user import User
from app.services.cloudinary_service import CloudinaryService
from datetime import datetime
import os

class MaterialService:
    """
    Servicio para materiales embebidos en Lesson.
    
    Nota: Para LEER materials, usa GET /lessons/{id} (materials incluidos).
    Este servicio solo maneja CREATE y DELETE.
    """
    
    @staticmethod
    async def upload_material(
        lesson_id: str, 
        file: UploadFile,
        title: str,
        is_downloadable: bool,
        user: User
    ) -> LessonMaterial:
        """
        Subir archivo y crear material embebido.
        Patrón CRUD para embebidos: Crear objeto → Agregarlo a lista → Guardar padre
        """
        lesson = await Lesson.get(lesson_id)
        if not lesson:
            raise HTTPException(status_code=404, detail="Lección no encontrada")
            
        # Validar archivo
        ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.docx', '.xlsx', '.zip'}
        filename = file.filename.lower()
        ext = os.path.splitext(filename)[1]
        
        if ext not in ALLOWED_EXTENSIONS:
             raise HTTPException(
                 status_code=400, 
                 detail=f"Tipo de archivo no permitido. Permitidos: {', '.join(ALLOWED_EXTENSIONS)}"
             )
             
        # Subir a Cloudinary
        resource_type = "image" if ext in {'.jpg', '.jpeg', '.png'} else "raw"
        folder = "courses/materials"
        
        try:
            if resource_type == "image":
                url = await CloudinaryService.upload_image(file, folder=folder)
            else:
                # Raw files (PDF, DOCX, etc)
                import cloudinary.uploader
                content = await file.read()
                
                if len(content) > 10 * 1024 * 1024:
                    raise HTTPException(status_code=400, detail="El archivo excede 10MB")
                
                response = cloudinary.uploader.upload(
                    content,
                    folder=f"dulcevicio/{folder}",
                    resource_type="raw",
                    public_id=f"{lesson_id}_{os.path.splitext(file.filename)[0]}"
                )
                url = response.get("secure_url")
                await file.seek(0)

        except Exception as e:
             if isinstance(e, HTTPException): 
                 raise e
             raise HTTPException(status_code=500, detail=f"Error al subir archivo: {str(e)}")

        # Calcular orden
        max_order = 0
        if lesson.materials:
            max_order = max(m.order for m in lesson.materials)
            
        # Crear Material embebido (BaseModel, no BaseDocument)
        material = LessonMaterial(
            title=title,
            resource_url=url,
            file_format=ext.replace('.', ''),
            is_downloadable=is_downloadable,
            order=max_order + 1,
            created_at=datetime.utcnow(),
            created_by=str(user.id)
        )
        
        # PATRÓN EMBEBIDO: Agregar a lista y guardar padre
        lesson.materials.append(material)
        lesson.updated_by = str(user.id)
        await lesson.save()
        
        return material

    @staticmethod
    async def delete_all_materials(lesson_id: str, user: User) -> Dict[str, str]:
        """
        Eliminar TODOS los materiales embebidos de una lección.
        Patrón CRUD para embebidos: Vaciar lista → Guardar padre
        """
        lesson = await Lesson.get(lesson_id)
        if not lesson:
            raise HTTPException(status_code=404, detail="Lección no encontrada")
            
        # PATRÓN EMBEBIDO: Vaciar la lista
        deleted_count = len(lesson.materials)
        lesson.materials = []
        lesson.updated_by = str(user.id)
        await lesson.save()
        
        return {"message": f"Se eliminaron {deleted_count} materiales correctamente"}
