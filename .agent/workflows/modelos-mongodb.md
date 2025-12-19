# Modelos MongoDB - DulceVicio

## 📚 Estructura de Colecciones

MongoDB tendrá las siguientes colecciones:
- `users` - Usuarios del sistema
- `courses` - Cursos (con lessons y recipes embebidas)
- `enrollments` - Inscripciones
- `memberships` - Membresías
- `comments` - Comentarios del foro
- `lesson_progress` - Progreso por lección

---

## 1. User Collection

```python
from beanie import Document, Indexed
from pydantic import EmailStr
from datetime import datetime
from typing import Optional

class User(Document):
    email: Indexed(EmailStr, unique=True)
    username: Optional[Indexed(str, unique=True)] = None
    password_hash: str
    full_name: str
    role: str = "USER"  # 'ADMIN' | 'USER'
    is_active: bool = True
    avatar_url: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    
    class Settings:
        name = "users"
```

---

## 2. Course Collection (con subdocumentos embebidos)

```python
from beanie import Document
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

# Subdocumento: Lesson (embebido en Course)
class Lesson(BaseModel):
    id: str = str(ObjectId())  # ID único para cada lección
    title: str
    description: Optional[str] = None
    order: int = 1
    
    # Video en Cloudinary
    video_url: Optional[str] = None
    video_public_id: Optional[str] = None
    video_duration: Optional[int] = None  # segundos
    
    is_preview: bool = False
    is_active: bool = True
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

# Subdocumento: Recipe (embebido en Course)
class Recipe(BaseModel):
    id: str = str(ObjectId())  # ID único para cada receta
    title: str
    description: Optional[str] = None  # Ingredientes, pasos
    order: int = 1
    
    # Solo imagen individual (NO PDF individual)
    image_url: Optional[str] = None
    image_public_id: Optional[str] = None
    
    # Texto para futuro chatbot
    recipe_text: Optional[str] = None
    
    is_active: bool = True
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

# Documento principal: Course
class Course(Document):
    title: str
    description: str
    thumbnail_url: Optional[str] = None
    thumbnail_public_id: Optional[str] = None
    difficulty_level: str = "BEGINNER"  # 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED'
    estimated_duration_minutes: int = 0
    is_active: bool = True
    order: int = 0  # Para ordenar en catálogo
    
    # Grupo de WhatsApp
    whatsapp_group_url: Optional[str] = None
    
    # PDF CONSOLIDADO único (no hay PDFs individuales)
    consolidated_recipe_pdf_url: Optional[str] = None
    consolidated_recipe_pdf_public_id: Optional[str] = None
    
    # Subdocumentos embebidos
    lessons: List[Lesson] = []  # Array de lecciones
    recipes: List[Recipe] = []  # Array de recetas (solo imágenes)
    
    # Referencias
    created_by: ObjectId  # Referencia a User
    
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    
    class Settings:
        name = "courses"
        indexes = [
            "is_active",
            "order",
            "created_by",
        ]
```

**Flujo de Recetas:**
1. Admin sube 10 imágenes → Se crean 10 `Recipe` en array `recipes[]`
2. Sistema genera PDF consolidado → Se guarda en `consolidated_recipe_pdf_url`
3. Estudiante ve: 10 imágenes individuales + 1 PDF para descargar

---

## 3. Enrollment Collection

```python
from beanie import Document
from bson import ObjectId
from datetime import datetime
from typing import Optional

class Enrollment(Document):
    user_id: ObjectId  # Referencia a User
    course_id: ObjectId  # Referencia a Course
    enrolled_at: datetime = datetime.utcnow()
    expires_at: Optional[datetime] = None  # Para accesos temporales
    is_active: bool = True
    granted_by: ObjectId  # Admin que otorgó el acceso
    
    class Settings:
        name = "enrollments"
        indexes = [
            "user_id",
            "course_id",
            ("user_id", "course_id"),  # Compound index (unique)
        ]
```

---

## 4. Membership Collection

```python
from beanie import Document
from bson import ObjectId
from datetime import datetime
from typing import Optional

class Membership(Document):
    user_id: ObjectId  # Referencia a User
    membership_type: str = "FULL_ACCESS"
    start_date: datetime
    end_date: datetime
    is_active: bool = True
    granted_by: ObjectId  # Admin que otorgó
    notes: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    
    class Settings:
        name = "memberships"
        indexes = [
            "user_id",
            "end_date",
            "is_active",
        ]
```

---

## 5. Comment Collection

```python
from beanie import Document
from bson import ObjectId
from datetime import datetime
from typing import Optional

class Comment(Document):
    course_id: ObjectId  # Referencia a Course
    user_id: ObjectId  # Referencia a User
    parent_id: Optional[ObjectId] = None  # Para respuestas
    content: str
    is_admin_response: bool = False
    is_active: bool = True
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    
    class Settings:
        name = "comments"
        indexes = [
            "course_id",
            "parent_id",
            ("course_id", "created_at"),
        ]
```

---

## 6. LessonProgress Collection

```python
from beanie import Document
from bson import ObjectId
from datetime import datetime
from typing import Optional

class LessonProgress(Document):
    user_id: ObjectId  # Referencia a User
    course_id: ObjectId  # Referencia a Course
    lesson_id: str  # ID de la lección dentro del array de Course.lessons
    enrollment_id: Optional[ObjectId] = None
    
    completed: bool = False
    last_watched_position: Optional[int] = None  # segundos
    completed_at: Optional[datetime] = None
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    
    class Settings:
        name = "lesson_progress"
        indexes = [
            ("user_id", "lesson_id"),  # Compound unique
            "enrollment_id",
        ]
```

---

## 🔄 Ventajas de MongoDB para este Proyecto

### ✅ **Documentos Embebidos (Lessons y Recipes):**
```javascript
// 1 query trae todo
{
  "_id": ObjectId("..."),
  "title": "Torta de Chocolate",
  "lessons": [
    { "id": "...", "title": "Parte 1", "video_url": "..." },
    { "id": "...", "title": "Parte 2", "video_url": "..." }
  ],
  "recipes": [
    { "id": "...", "title": "Receta 1", "image_url": "..." },
    { "id": "...", "title": "Receta 2", "image_url": "..." }
  ],
  "consolidated_recipe_pdf_url": "https://cloudinary.com/..."
}
```

### ✅ **Flexibilidad:**
- Fácil agregar campos nuevos sin migraciones
- Documentos pueden tener estructuras diferentes
- Perfecto para schema evolutivo

### ✅ **Performance:**
- 1 query para obtener curso completo con lecciones y recetas
- No necesita JOINs
- Rápido para lectura

### ✅ **Escalabilidad:**
- Horizontal scaling automático
- Sharding si crece mucho

---

## 🎯 Comparación: SQL vs MongoDB

| Aspecto | PostgreSQL (antes) | MongoDB (ahora) |
|---------|-------------------|-----------------|
| Lessons | Tabla separada | Embebido en Course |
| Recipes | Tabla separada | Embebido en Course |
| PDF consolidado | ¿Receta especial? | Campo en Course |
| Queries | Múltiples JOINs | 1 query simple |
| Migr aciones | Alembic | No necesita |
| Validación | SQLAlchemy + Pydantic | Beanie (Pydantic) |

---

## 📝 Ejemplo de Documento Course Completo

```json
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "title": "Alfajores de Maicena Gourmet",
  "description": "Aprende a hacer alfajores profesionales...",
  "thumbnail_url": "https://res.cloudinary.com/...",
  "difficulty_level": "INTERMEDIATE",
  "estimated_duration_minutes": 45,
  "whatsapp_group_url": "https://chat.whatsapp.com/ABC123",
  "consolidated_recipe_pdf_url": "https://res.cloudinary.com/alfajores_recetas.pdf",
  
  "lessons": [
    {
      "id": "lesson_001",
      "title": "Preparación de la masa",
      "order": 1,
      "video_url": "https://res.cloudinary.com/video1.mp4",
      "video_duration": 600,
      "is_preview": false
    },
    {
      "id": "lesson_002",
      "title": "Cocción perfecta",
      "order": 2,
      "video_url": "https://res.cloudinary.com/video2.mp4",
      "video_duration": 480
    }
  ],
  
  "recipes": [
    {
      "id": "recipe_001",
      "title": "Masa de maicena",
      "order": 1,
      "image_url": "https://res.cloudinary.com/receta1.jpg"
    },
    {
      "id": "recipe_002",
      "title": "Dulce de leche casero",
      "order": 2,
      "image_url": "https://res.cloudinary.com/receta2.jpg"
    },
    // ... hasta recipe_010
  ],
  
  "created_by": ObjectId("507f1f77bcf86cd799439012"),
  "created_at": ISODate("2024-01-15T10:30:00Z"),
  "is_active": true,
  "order": 1
}
```

---

## 🚀 Inicialización de MongoDB

```python
# app/database.py
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.user import User
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.membership import Membership
from app.models.comment import Comment
from app.models.lesson_progress import LessonProgress

async def init_db():
    # Conectar a MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    database = client.dulcevicio
    
    # Inicializar Beanie con todos los modelos
    await init_beanie(
        database=database,
        document_models=[
            User,
            Course,
            Enrollment,
            Membership,
            Comment,
            LessonProgress,
        ]
    )
    
    print("✅ MongoDB conectado y Beanie inicializado")
```

---

## ✨ Beneficios del Diseño con 1 PDF Consolidado

### **Campo en Course:**
```python
consolidated_recipe_pdf_url: Optional[str] = None
consolidated_recipe_pdf_public_id: Optional[str] = None
```

### **Flujo simplificado:**
1. Admin sube 10 imágenes
2. Sistema crea 10 `Recipe` en `recipes[]` (solo con `image_url`)
3. Sistema ejecuta `generate_consolidated_pdf()`
4. PDF se guarda en `consolidated_recipe_pdf_url`
5. ✅ Listo - 1 curso, 10 imágenes, 1 PDF

### **Estudiante ve:**
- ✅ 10 recetas individuales (navegación fácil)
- ✅ 1 botón "Descargar PDF completo"
- ✅ No confusión con múltiples PDFs
