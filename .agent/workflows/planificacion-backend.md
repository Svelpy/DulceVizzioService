---
description: Planificación del Backend - DulceVicio
---

# Planificación del Backend - Plataforma de Cursos de Repostería "DulceVicio"

## 1. Visión General

Sistema de gestión de cursos virtuales de repostería sin procesamiento de pagos. Los administradores gestionan usuarios, cursos y accesos. Se implementarán membresías temporales para acceso completo al catálogo.

**Modelo de Negocio:**
- Admin sube múltiples imágenes de recetas por curso
- Sistema genera automáticamente 1 PDF consolidado con todas las recetas
- Estudiantes reciben: videos, imágenes individuales, PDF consolidado y acceso a grupo WhatsApp

---

## 2. Stack Tecnológico

- **Framework**: FastAPI (Python 3.10+)
- **Base de Datos**: MongoDB (NoSQL)
- **ODM**: Motor (async) + Beanie (ODM para FastAPI)
- **Autenticación**: JWT (JSON Web Tokens)
- **Almacenamiento de Videos**: Cloudinary
- **Validación**: Pydantic V2

---

## 3. Arquitectura del Proyecto

```
dulcevicio/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Punto de entrada de FastAPI
│   ├── config.py               # Configuración (env vars, Cloudinary, DB)
│   ├── database.py             # Conexión a la base de datos
│   │
│   ├── models/                 # Modelos SQLAlchemy
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── course.py
│   │   ├── lesson.py           # Videos/lecciones del curso
│   │   ├── recipe.py           # Recetas asociadas al curso
│   │   ├── enrollment.py
│   │   ├── membership.py
│   │   ├── comment.py          # Sistema de foro/comentarios
│   │   └── lesson_progress.py  # Progreso por lección
│   │
│   ├── schemas/                # Schemas Pydantic
│   │   ├── __init__.py
│   │   ├── user_schema.py
│   │   ├── course_schema.py
│   │   ├── lesson_schema.py
│   │   ├── recipe_schema.py
│   │   ├── enrollment_schema.py
│   │   ├── membership_schema.py
│   │   └── comment_schema.py
│   │
│   ├── routers/                # Endpoints API
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── courses.py
│   │   ├── lessons.py
│   │   ├── recipes.py
│   │   ├── enrollments.py
│   │   ├── memberships.py
│   │   └── comments.py         # Foro/comentarios
│   │
│   ├── services/               # Lógica de negocio
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── course_service.py
│   │   ├── lesson_service.py
│   │   ├── recipe_service.py
│   │   ├── enrollment_service.py
│   │   ├── membership_service.py
│   │   ├── comment_service.py
│   │   └── cloudinary_service.py
│   │
│   ├── middleware/             # Middleware personalizado
│   │   ├── __init__.py
│   │   └── auth_middleware.py
│   │
│   └── utils/                  # Utilidades
│       ├── __init__.py
│       ├── security.py         # Hash de contraseñas, JWT
│       └── dependencies.py     # Dependencias reutilizables
│
├── tests/                      # Tests unitarios e integración
├── requirements.txt
├── .env.example
└── README.md

# Nota: MongoDB no requiere migraciones (schema-less)
```

---

## 4. Modelos de Base de Datos (MongoDB)

**Nota importante sobre MongoDB:**
- No hay relaciones FK tradicionales (se usan referencias por ObjectId)
- Documentos anidados cuando tiene sentido (ej: recipes dentro de course)
- Beanie maneja validación con Pydantic
- Sin migraciones (schema-less, pero con validación)

### 4.1 User (Usuario)

```python
from beanie import Document
from pydantic import EmailStr
from datetime import datetime
from typing import Optional

class User(Document):
    email: EmailStr  # Unique index
    username: Optional[str] = None  # Unique index if provided
    password_hash: str
    full_name: str
    role: str = "USER"  # 'ADMIN' | 'USER'
    is_active: bool = True
    avatar_url: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    
    class Settings:
        name = "users"
        indexes = [
            "email",
            "username",
        ]
```

### 4.2 Course (Curso) - Documento Principal con Subdocumentos Embebidos

```python
from beanie import Document
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

# Subdocumento: Lesson
class Lesson(BaseModel):
    id: str = str(ObjectId())
    title: str
    description: Optional[str] = None
    order: int  # 1, 2, 3...
    video_url: Optional[str] = None
    video_public_id: Optional[str] = None
    video_duration: Optional[int] = None  # segundos
    is_preview: bool = False
    is_active: bool = True
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

# Subdocumento: Recipe (solo imagen, NO PDF individual)
class Recipe(BaseModel):
    id: str = str(ObjectId())
    title: str
    description: Optional[str] = None
    order: int  # 1, 2, 3... hasta 10+
    image_url: Optional[str] = None  # Imagen individual en Cloudinary
    image_public_id: Optional[str] = None
    recipe_text: Optional[str] = None  # Para futuro chatbot
    is_active: bool = True
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

# Documento Course
class Course(Document):
    title: str
    description: str
    thumbnail_url: Optional[str] = None
    thumbnail_public_id: Optional[str] = None
    difficulty_level: str = "BEGINNER"
    estimated_duration_minutes: int = 0
    is_active: bool = True
    order: int = 0
    
    # Grupo WhatsApp
    whatsapp_group_url: Optional[str] = None
    
    # PDF CONSOLIDADO ÚNICO (generado automáticamente)
    consolidated_recipe_pdf_url: Optional[str] = None
    consolidated_recipe_pdf_public_id: Optional[str] = None
    
    # Subdocumentos embebidos
    lessons: List[Lesson] = []  # Array de lecciones
    recipes: List[Recipe] = []  # Array de recetas (solo imágenes)
    
    # Referencia al creador
    created_by: ObjectId  # User ID
    
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    
    class Settings:
        name = "courses"
        indexes = ["is_active", "order", "created_by"]
```

**Nota sobre el PDF Consolidado:**
- NO hay PDFs individuales por receta
- Admin sube N imágenes → Se crean N `Recipe` en array
- Sistema genera automáticamente 1 PDF con todas las imágenes
- Se guarda en `consolidated_recipe_pdf_url`

---

### 4.3 Enrollment (Inscripción)

```python
from beanie import Document
from bson import ObjectId
from datetime import datetime
from typing import Optional

class Enrollment(Document):
    user_id: ObjectId  # Referencia a User
    course_id: ObjectId  # Referencia a Course
    enrolled_at: datetime = datetime.utcnow()
    expires_at: Optional[datetime] = None
    is_active: bool = True
    granted_by: ObjectId  # Admin que otorgó acceso
    
    class Settings:
        name = "enrollments"
        indexes = [
            "user_id",
            "course_id",
            ("user_id", "course_id"),  # Compound unique index
        ]
```

---

### 4.4 Membership (Membresía)

```python
from beanie import Document
from bson import ObjectId
from datetime import datetime
from typing import Optional

class Membership(Document):
    user_id: ObjectId
    membership_type: str = "FULL_ACCESS"
    start_date: datetime
    end_date: datetime
    is_active: bool = True
    granted_by: ObjectId
    notes: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    
    class Settings:
        name = "memberships"
        indexes = ["user_id", "end_date", "is_active"]
```

---

### 4.5 Comment (Comentario/Foro)

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

### 4.6 LessonProgress (Progreso por Lección)

```python
from beanie import Document
from bson import ObjectId
from datetime import datetime
from typing import Optional

class LessonProgress(Document):
    user_id: ObjectId  # Referencia a User
    course_id: ObjectId  # Referencia a Course
    lesson_id: str  # ID de lección dentro de Course.lessons[]
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

**Lógica de Completado del Curso:**
- Un curso está completado cuando todas sus lecciones tienen `LessonProgress.completed = True`
- Query: `count(completed) == len(course.lessons)`

**Nota para el futuro (Chat IA):**
- Campo `Recipe.recipe_text` alimentará el chatbot
- Endpoint `/api/courses/{id}/chat` usará todas las recetas como contexto
- Integración con OpenAI/Anthropic/Gemini

---

## 5. Ventajas de MongoDB para DulceVicio

### ✅ **1 Query para Curso Completo:**
```python
# Con MongoDB (1 query)
course = await Course.get(course_id)
# Ya incluye: lessons[], recipes[], consolidated_pdf_url

# Vs PostgreSQL (múltiples queries o JOINs)
# course = get_course()
# lessons = get_lessons(course_id)
# recipes = get_recipes(course_id)
```

### ✅ **Flexibilidad sin Migraciones:**
```python
# Agregar campo nuevo es trivial
class Course(Document):
    # ... campos existentes ...
    tags: List[str] = []  # ← Nuevo campo, no requiere migración
```

### ✅ **Documentos Embebidos (Performance):**
- `lessons[]` y `recipes[]` vienen incluidos
- No hay N+1 queries
- Perfecto para este caso de uso

### ✅ **Escalabilidad:**
- Sharding automático si crece
- Réplicas para alta disponibilidad
- Atlas MongoDB (cloud) muy fácil

---

---

## 5. Roles y Permisos

### 5.1 ADMIN
**Puede:**
- ✅ Crear, editar, eliminar usuarios
- ✅ Crear, editar, eliminar cursos
- ✅ Crear, editar, eliminar lecciones
- ✅ Crear, editar, eliminar recetas
- ✅ Subir videos, PDFs e imágenes a Cloudinary
- ✅ Asignar/revocar acceso a cursos específicos (Enrollments)
- ✅ Crear/gestionar membresías temporales
- ✅ Ver todos los usuarios y su progreso
- ✅ Moderar comentarios en el foro
- ✅ Acceso completo a todos los cursos

### 5.2 USER
**Puede:**
- ✅ Ver su perfil y editarlo (nombre, avatar)
- ✅ Cambiar su contraseña
- ✅ Ver cursos a los que tiene acceso (por enrollment o membership)
- ✅ Ver lecciones y recetas de cursos accesibles
- ✅ Marcar lecciones como completadas
- ✅ Guardar posición de reproducción de cada lección
- ✅ Participar en el foro (crear y responder comentarios)
- ✅ Ver lecciones marcadas como "preview" sin necesidad de acceso
- ❌ No puede crear usuarios ni cursos
- ❌ No puede acceder a cursos sin permiso

---

## 6. Endpoints de la API

### 6.1 Autenticación (`/api/auth`)

```
POST   /api/auth/login          # Login (retorna JWT)
POST   /api/auth/refresh        # Refrescar token
POST   /api/auth/logout         # Logout (opcional, blacklist token)
GET    /api/auth/me             # Obtener datos del usuario actual
PUT    /api/auth/me             # Actualizar perfil
PUT    /api/auth/change-password # Cambiar contraseña
```

### 6.2 Usuarios (`/api/users`) - ADMIN only

```
GET    /api/users               # Listar todos los usuarios (paginado)
POST   /api/users               # Crear nuevo usuario
GET    /api/users/{id}          # Obtener usuario por ID
PUT    /api/users/{id}          # Actualizar usuario
DELETE /api/users/{id}          # Eliminar/desactivar usuario
GET    /api/users/{id}/progress # Ver progreso del usuario en todos los cursos
```

### 6.3 Cursos (`/api/courses`)

```
GET    /api/courses                    # Listar cursos (ADMIN: todos, USER: accesibles)
POST   /api/courses                    # Crear curso (ADMIN only)
GET    /api/courses/{id}               # Obtener curso completo con lecciones y recetas
PUT    /api/courses/{id}               # Actualizar curso (ADMIN only)
DELETE /api/courses/{id}               # Eliminar curso (ADMIN only)
POST   /api/courses/{id}/upload-thumbnail  # Subir thumbnail (ADMIN only)
PUT    /api/courses/{id}/whatsapp-group    # Actualizar enlace de grupo WhatsApp (ADMIN)
GET    /api/courses/{id}/students      # Ver estudiantes inscritos (ADMIN only)
GET    /api/courses/{id}/progress      # Ver progreso de un curso (todas las lecciones)
POST   /api/courses/{id}/generate-recipe-pdf  # Generar PDF consolidado de recetas (ADMIN)
```

### 6.4 Lecciones (`/api/lessons`)

```
GET    /api/courses/{course_id}/lessons    # Listar lecciones de un curso
POST   /api/courses/{course_id}/lessons    # Crear lección en curso (ADMIN only)
GET    /api/lessons/{id}                   # Obtener lección (verifica acceso)
PUT    /api/lessons/{id}                   # Actualizar lección (ADMIN only)
DELETE /api/lessons/{id}                   # Eliminar lección (ADMIN only)
POST   /api/lessons/{id}/upload-video      # Subir video a Cloudinary (ADMIN)
POST   /api/lessons/{id}/progress          # Actualizar progreso de lección (USER)
PUT    /api/lessons/{id}/complete          # Marcar lección como completada (USER)
```

### 6.5 Recetas (`/api/recipes`)

```
GET    /api/courses/{course_id}/recipes    # Listar recetas de un curso
POST   /api/courses/{course_id}/recipes    # Crear receta en curso (ADMIN only)
GET    /api/recipes/{id}                   # Obtener receta (verifica acceso)
PUT    /api/recipes/{id}                   # Actualizar receta (ADMIN only)
DELETE /api/recipes/{id}                   # Eliminar receta (ADMIN only)
POST   /api/recipes/{id}/upload-pdf        # Subir PDF (ADMIN only)
POST   /api/recipes/{id}/upload-image      # Subir imagen (ADMIN only)
```

### 6.6 Comentarios/Foro (`/api/comments`)

```
GET    /api/courses/{course_id}/comments        # Listar comentarios de un curso
POST   /api/courses/{course_id}/comments        # Crear comentario en curso
GET    /api/comments/{id}                       # Obtener comentario específico
PUT    /api/comments/{id}                       # Editar propio comentario
DELETE /api/comments/{id}                       # Eliminar propio comentario (o ADMIN)
POST   /api/comments/{id}/reply                 # Responder a un comentario
PUT    /api/comments/{id}/moderate              # Ocultar/mostrar comentario (ADMIN)
```

### 6.7 Inscripciones (`/api/enrollments`) - ADMIN only

```
GET    /api/enrollments         # Listar todas las inscripciones (filtros)
POST   /api/enrollments         # Crear inscripción (asignar curso a usuario)
GET    /api/enrollments/{id}    # Obtener inscripción
PUT    /api/enrollments/{id}    # Actualizar inscripción (ej: extender fecha)
DELETE /api/enrollments/{id}    # Revocar acceso a curso
```

### 6.8 Membresías (`/api/memberships`) - ADMIN only

```
GET    /api/memberships         # Listar todas las membresías
POST   /api/memberships         # Crear membresía temporal
GET    /api/memberships/{id}    # Obtener membresía
PUT    /api/memberships/{id}    # Actualizar membresía (extender, desactivar)
DELETE /api/memberships/{id}    # Eliminar membresía
```

### 6.9 Dashboard (`/api/dashboard`) - Opcional

```
GET    /api/dashboard/stats     # Estadísticas generales (ADMIN)
GET    /api/dashboard/my-courses # Mis cursos con progreso por lección (USER)
GET    /api/dashboard/my-progress # Resumen de progreso general (USER)
```

---

## 7. Lógica de Acceso a Cursos

```python
# Pseudo-código para verificar acceso a un curso

def user_has_access_to_course(user_id, course_id):
    # 1. Si es ADMIN, siempre tiene acceso
    if user.role == 'ADMIN':
        return True
    
    # 2. Verificar si tiene membresía activa
    active_membership = get_active_membership(user_id)
    if active_membership and active_membership.end_date > now():
        return True
    
    # 3. Verificar si tiene enrollment específico al curso
    enrollment = get_enrollment(user_id, course_id)
    if enrollment and enrollment.is_active:
        # Si tiene expires_at, verificar que no haya expirado
        if enrollment.expires_at is None or enrollment.expires_at > now():
            return True
    
    return False
```

---

## 8. Integración con Cloudinary

### 8.1 Configuración

```python
# config.py
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key = os.getenv("CLOUDINARY_API_KEY"),
    api_secret = os.getenv("CLOUDINARY_API_SECRET")
)
```

### 8.2 Service para Videos y Recetas

```python
# services/cloudinary_service.py

async def upload_video(file: UploadFile, folder: str = "dulcevicio/courses/videos"):
    """
    Sube un video a Cloudinary
    Returns: {url, public_id, duration, format}
    """
    result = cloudinary.uploader.upload(
        file.file,
        resource_type="video",
        folder=folder,
        quality="auto",
        fetch_format="auto"
    )
    return {
        "url": result["secure_url"],
        "public_id": result["public_id"],
        "duration": result.get("duration"),
        "format": result.get("format")
    }

async def upload_recipe_pdf(file: UploadFile, folder: str = "dulcevicio/courses/recipes/pdf"):
    """
    Sube un PDF de receta a Cloudinary
    Returns: {url, public_id}
    """
    result = cloudinary.uploader.upload(
        file.file,
        resource_type="raw",  # Para PDFs
        folder=folder,
        format="pdf"
    )
    return {
        "url": result["secure_url"],
        "public_id": result["public_id"]
    }

async def upload_recipe_image(file: UploadFile, folder: str = "dulcevicio/courses/recipes/images"):
    """
    Sube una imagen de receta a Cloudinary
    Returns: {url, public_id, width, height}
    """
    result = cloudinary.uploader.upload(
        file.file,
        resource_type="image",
        folder=folder,
        quality="auto",
        fetch_format="auto"
    )
    return {
        "url": result["secure_url"],
        "public_id": result["public_id"],
        "width": result.get("width"),
        "height": result.get("height")
    }

async def upload_thumbnail(file: UploadFile, folder: str = "dulcevicio/courses/thumbnails"):
    """
    Sube una miniatura/portada de curso a Cloudinary
    Returns: {url, public_id}
    """
    result = cloudinary.uploader.upload(
        file.file,
        resource_type="image",
        folder=folder,
        transformation=[
            {"width": 1280, "height": 720, "crop": "fill"},
            {"quality": "auto"},
            {"fetch_format": "auto"}
        ]
    )
    return {
        "url": result["secure_url"],
        "public_id": result["public_id"]
    }

async def delete_resource(public_id: str, resource_type: str = "video"):
    """
    Elimina un recurso de Cloudinary
    resource_type: 'video' | 'image' | 'raw' (para PDFs)
    """
    result = cloudinary.uploader.destroy(
        public_id,
        resource_type=resource_type
    )
    return result

async def generate_consolidated_recipe_pdf(course_id: int, recipes: List[Recipe]):
    """
    Genera un PDF consolidado con todas las recetas de un curso
    Opción 1: Usar library como ReportLab o WeasyPrint
    Opción 2: Crear HTML y convertirlo a PDF
    Opción 3: Usar servicio externo como PDFShift
    
    Returns: {url, public_id} del PDF consolidado subido a Cloudinary
    """
    # TODO: Implementar generación de PDF en Fase posterior
    pass
```

**Nota sobre Recetas:**
El sistema soporta dos flujos:
1. **Imágenes individuales**: Cada receta es una imagen separada (~10 recetas)
2. **PDF consolidado**: Se genera automáticamente un PDF con todas las recetas del curso

Ambos archivos se almacenan en Cloudinary y se entregan al estudiante al inscribirse.

---

## 9. Seguridad y Validaciones

### 9.1 Autenticación JWT

```python
# utils/security.py

- Generar JWT con payload: {user_id, email, role, exp}
- Expiración: 24 horas (configurable)
- Refresh token: 7 días
- Algoritmo: HS256
- Almacenar SECRET_KEY en variables de entorno
```

### 9.2 Hashing de Contraseñas

```python
- Usar bcrypt o passlib con bcrypt
- Nunca almacenar contraseñas en texto plano
```

### 9.3 Validaciones

```python
- Email: formato válido, único
- Username: opcional, único si se proporciona
- Contraseñas: mínimo 8 caracteres
- Roles: solo ADMIN puede crear otros ADMIN
- Fechas de membresía: end_date > start_date
```

---

## 10. Variables de Entorno (.env)

```env
# Database
DATABASE_URL=postgresql://user:password@localhost/dulcevicio

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# App
DEBUG=True
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## 11. Orden de Implementación Sugerido

### Fase 1: Fundación (Semana 1)
1. ✅ Configurar proyecto FastAPI
2. ✅ Configurar base de datos y Alembic
3. ✅ Crear modelos User, Course, Lesson, Recipe, Enrollment, Membership, Comment, LessonProgress
4. ✅ Implementar sistema de autenticación JWT
5. ✅ Crear endpoints de autenticación (/login, /me)

### Fase 2: Gestión de Usuarios (Semana 2)
6. ✅ Implementar CRUD de usuarios (ADMIN)
7. ✅ Implementar roles y middleware de autorización
8. ✅ Crear endpoints de perfil de usuario

### Fase 3: Gestión de Cursos, Lecciones y Recetas (Semana 3)
9. ✅ Implementar CRUD de cursos
10. ✅ Implementar CRUD de lecciones (MVP: 1 por curso)
11. ✅ Implementar CRUD de recetas (MVP: 1 por curso)
12. ✅ Integrar Cloudinary para subida de videos, PDFs, imágenes y thumbnails
13. ✅ Implementar endpoints de visualización de cursos para usuarios
14. ✅ Implementar modelo LessonProgress para tracking

### Fase 4: Sistema de Accesos (Semana 4)
13. ✅ Crear modelo y endpoints de Enrollment
14. ✅ Crear modelo y endpoints de Membership
15. ✅ Implementar lógica de verificación de acceso
16. ✅ Implementar expiración de accesos

### Fase 5: Sistema de Foro/Comentarios (Semana 5)
19. ✅ Implementar modelo Comment
20. ✅ Crear endpoints de comentarios y respuestas
21. ✅ Implementar moderación de comentarios (ADMIN)
22. ✅ Sistema de threading (respuestas anidadas)

### Fase 6: Dashboard, Testing y Documentación (Semana 6)
23. ✅ Implementar dashboard para usuarios y admin
24. ✅ Implementar estadísticas y analytics
25. ✅ Pruebas unitarias de servicios críticos
26. ✅ Pruebas de integración de endpoints
27. ✅ Documentación de API (Swagger automático)
28. ✅ Manual de despliegue

---

## 12. Consideraciones Adicionales

### 12.1 Escalabilidad Futura
- **Múltiples lecciones por curso**: El modelo ya soporta esto, solo agregar más lecciones con `order > 1`
- **Múltiples recetas por curso**: El modelo ya soporta esto, solo agregar más recetas con `order > 1`
- **Pagos**: Dejar preparado el modelo Enrollment para agregar campos de pago (monto, método, fecha)
- **Certificados**: Agregar modelo Certificate cuando un usuario complete todas las lecciones
- **Chat IA**: Implementar chatbot retroalimentado con `Recipe.recipe_text`
  - Endpoint `/api/recipes/{id}/chat` con contexto de la receta
  - Integrar con OpenAI/Anthropic/Gemini
  - Responder dudas sobre ingredientes, pasos, técnicas
- **Notificaciones**: Sistema de notificaciones
  - Email cuando se asigna un curso
  - Email cuando expira membresía
  - Notificaciones de nuevas respuestas en el foro
  - Notificaciones de nuevas lecciones en cursos inscritos
- **Reacciones en comentarios**: Sistema de likes/reactions en comentarios
- **Valoraciones**: Sistema de ratings y reseñas de cursos
- **Playlists/Rutas de aprendizaje**: Agrupar cursos relacionados
- **Lecciones de tipo "texto"**: Además de videos, soportar lecciones de solo lectura

### 12.2 Performance
- **Caché**: Implementar Redis para cachear cursos, lecciones y recetas frecuentes
- **Paginación**: Todos los listados deben estar paginados (especialmente comentarios y lecciones)
- **Índices**: Crear índices en campos frecuentemente consultados:
  - `User.email`
  - `Course.is_active`, `Course.order`
  - `Lesson.course_id`, `Lesson.order`
  - `Recipe.course_id`, `Recipe.order`
  - `Enrollment.user_id`, `Enrollment.course_id`
  - `Membership.user_id`, `Membership.end_date`
  - `Comment.course_id`, `Comment.created_at`
  - `Comment.parent_id`
  - `LessonProgress.user_id`, `LessonProgress.lesson_id`

### 12.3 Monitoreo
- Logs estructurados con `loguru` o `structlog`
- Tracking de errores con Sentry (opcional)
- Métricas de uso de endpoints

---

## 13. Schemas Pydantic Ejemplo

### User Schema
```python
# schemas/user_schema.py

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    username: Optional[str] = None

class UserCreate(UserBase):
    password: str
    role: Literal['ADMIN', 'USER'] = 'USER'

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    avatar_url: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChangePasswordSchema(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str
```

### Course Schema
```python
# schemas/course_schema.py

class CourseBase(BaseModel):
    title: str
    description: str
    difficulty_level: Literal['BEGINNER', 'INTERMEDIATE', 'ADVANCED']
    estimated_duration_minutes: int
    order: int = 0

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    difficulty_level: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None

class CourseResponse(CourseBase):
    id: int
    is_active: bool
    created_by: int
    created_at: datetime
    
    # URLs de Cloudinary
    thumbnail_url: Optional[str] = None
    thumbnail_public_id: Optional[str] = None
    
    # Grupo de WhatsApp
    whatsapp_group_url: Optional[str] = None
    
    # Contadores
    lessons_count: int = 0
    recipes_count: int = 0
    enrolled_count: int = 0
    comments_count: int = 0
    
    class Config:
        from_attributes = True

class CourseWithProgress(CourseResponse):
    """Course con progreso del usuario actual"""
    total_lessons: int = 0
    completed_lessons: int = 0
    progress_percentage: float = 0.0
    user_enrolled_at: Optional[datetime] = None
```

### Lesson Schema
```python
# schemas/lesson_schema.py

class LessonBase(BaseModel):
    title: str
    description: Optional[str] = None
    order: int = 1
    is_preview: bool = False

class LessonCreate(LessonBase):
    course_id: int

class LessonUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None
    is_preview: Optional[bool] = None
    is_active: Optional[bool] = None

class LessonResponse(LessonBase):
    id: int
    course_id: int
    video_url: Optional[str] = None
    video_public_id: Optional[str] = None
    video_duration: Optional[int] = None  # en segundos
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class LessonWithProgress(LessonResponse):
    """Lección con progreso del usuario"""
    user_completed: bool = False
    user_last_position: Optional[int] = None  # segundos
    user_completed_at: Optional[datetime] = None

class UpdateLessonProgressSchema(BaseModel):
    last_watched_position: int  # Posición en segundos

class CompleteLessonSchema(BaseModel):
    completed: bool = True
```

### Recipe Schema
```python
# schemas/recipe_schema.py

class RecipeBase(BaseModel):
    title: str
    description: Optional[str] = None  # Ingredientes, pasos, etc.
    recipe_text: Optional[str] = None  # Para futuro chatbot
    order: int = 1

class RecipeCreate(RecipeBase):
    course_id: int

class RecipeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    recipe_text: Optional[str] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None

class RecipeResponse(RecipeBase):
    id: int
    course_id: int
    pdf_url: Optional[str] = None
    pdf_public_id: Optional[str] = None
    image_url: Optional[str] = None
    image_public_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

### Enrollment Schema
```python
# schemas/enrollment_schema.py

class EnrollmentCreate(BaseModel):
    user_id: int
    course_id: int
    expires_at: Optional[datetime] = None

class EnrollmentUpdate(BaseModel):
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None

class EnrollmentResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    enrolled_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    granted_by: int
    
    # Nested relationships
    user: UserResponse
    course: CourseResponse
    
    class Config:
        from_attributes = True

class EnrollmentWithProgress(EnrollmentResponse):
    """Enrollment con progreso calculado del curso"""
    total_lessons: int = 0
    completed_lessons: int = 0
    progress_percentage: float = 0.0
    last_activity: Optional[datetime] = None
```

### Comment Schema
```python
# schemas/comment_schema.py

class CommentCreate(BaseModel):
    content: str
    parent_id: Optional[int] = None  # Para respuestas

class CommentUpdate(BaseModel):
    content: str

class CommentResponse(BaseModel):
    id: int
    course_id: int
    user_id: int
    parent_id: Optional[int]
    content: str
    is_admin_response: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Usuario que comentó
    user: UserResponse
    
    # Respuestas (opcional, solo para comentarios padre)
    replies: List['CommentResponse'] = []
    replies_count: int = 0
    
    class Config:
        from_attributes = True

# Para paginación
class CommentListResponse(BaseModel):
    items: List[CommentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
```

### Membership Schema
```python
# schemas/membership_schema.py

class MembershipCreate(BaseModel):
    user_id: int
    start_date: datetime
    end_date: datetime
    notes: Optional[str] = None

class MembershipResponse(BaseModel):
    id: int
    user_id: int
    membership_type: str
    start_date: datetime
    end_date: datetime
    is_active: bool
    granted_by: int
    notes: Optional[str]
    created_at: datetime
    
    user: UserResponse
    
    class Config:
        from_attributes = True
```

---

## 14. Ejemplo de Endpoint con Autorización

```python
# routers/courses.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.utils.dependencies import get_db, get_current_user, require_admin
from app.models.user import User
from app.schemas.course_schema import CourseCreate, CourseResponse

router = APIRouter(prefix="/api/courses", tags=["Courses"])

@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(require_admin),  # Solo ADMIN
    db: Session = Depends(get_db)
):
    """
    Crear un nuevo curso (Solo ADMIN)
    """
    new_course = course_service.create_course(
        db=db,
        course_data=course_data,
        created_by=current_user.id
    )
    return new_course

@router.get("/", response_model=List[CourseResponse])
async def list_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Listar cursos:
    - ADMIN: ve todos los cursos
    - USER: ve solo cursos a los que tiene acceso
    """
    if current_user.role == "ADMIN":
        courses = course_service.get_all_courses(db)
    else:
        courses = course_service.get_accessible_courses(db, current_user.id)
    
    return courses
```

---

## 15. Testing

### Estructura de Tests
```
tests/
├── __init__.py
├── conftest.py              # Fixtures compartidos
├── test_auth.py
├── test_users.py
├── test_courses.py
├── test_lessons.py
├── test_recipes.py
├── test_comments.py
├── test_enrollments.py
└── test_memberships.py
```

### Ejemplo de Test
```python
# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient

def test_login_success(client: TestClient, test_user):
    response = client.post("/api/auth/login", json={
        "email": test_user.email,
        "password": "testpassword123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_invalid_credentials(client: TestClient):
    response = client.post("/api/auth/login", json={
        "email": "wrong@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
```

---

## 16. Documentación Automática

FastAPI genera automáticamente documentación interactiva:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

Asegúrate de documentar cada endpoint con:
```python
@router.post("/courses/", response_model=CourseResponse)
async def create_course(
    course: CourseCreate,
    current_user: User = Depends(require_admin)
):
    """
    Crear un nuevo curso de repostería
    
    Parámetros:
    - **title**: Nombre del curso
    - **description**: Descripción detallada
    - **difficulty_level**: BEGINNER | INTERMEDIATE | ADVANCED
    
    Permisos: Solo ADMIN
    """
    pass
```

---

## 17. Próximos Pasos

1. **Revisar este documento** y confirmar que cumple con tus expectativas
2. **Definir prioridades**: ¿Quieres que inicie con la implementación completa?
3. **Ajustes**: ¿Necesitas modificar algún modelo o agregar funcionalidades?
4. **Base de datos**: ¿Ya tienes preferencia entre PostgreSQL o MySQL?

---

**¿Quieres que proceda con la implementación de la Fase 1, o prefieres ajustar algo en esta planificación primero?**
