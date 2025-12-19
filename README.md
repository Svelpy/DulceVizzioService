# DulceVicio - Plataforma de Cursos de Repostería 🎂

Backend API para gestión de cursos virtuales de repostería con MongoDB Atlas.

## 🎯 Características Principales

- ✅ Gestión de usuarios (Admin y Estudiantes)
- ✅ Cursos con múltiples lecciones (videos)
- ✅ Recetas con imágenes individuales + PDF consolidado generado automáticamente
- ✅ Grupos privados de WhatsApp por curso
- ✅ Sistema de membresías temporales
- ✅ Foro de comentarios por curso
- ✅ Tracking de progreso por lección
- ✅ Almacenamiento en la nube (Cloudinary + MongoDB Atlas)

---

## 🏗️ Tecnologías

- **Backend**: FastAPI (Python 3.10+)
- **Base de Datos**: MongoDB Atlas (Cloud)
- **ODM**: Beanie (con Pydantic V2)
- **Autenticación**: JWT
- **Almacenamiento**: Cloudinary (videos, imágenes, PDFs)
- **Generación PDF**: ReportLab + Pillow

---

## 📦 Instalación

### 1. Clonar repositorio

```bash
git clone <repository-url>
cd DulceVicio
```

### 2. Crear entorno virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia `.env.example` a `.env` y completa:

```bash
cp .env.example .env
```

Edita `.env`:
```env
# MongoDB Atlas - Obtén tu connection string de https://cloud.mongodb.com
MONGODB_URL=mongodb+srv://username:password@cluster.xxxxx.mongodb.net/...
MONGODB_DB_NAME=dulcevicio_db

# JWT - Genera una clave secreta segura
SECRET_KEY=tu-clave-super-secreta-aqui

# Cloudinary - Obtén de https://cloudinary.com/console
CLOUDINARY_CLOUD_NAME=tu-cloud-name
CLOUDINARY_API_KEY=tu-api-key
CLOUDINARY_API_SECRET=tu-api-secret
```

### 5. Ejecutar servidor

```bash
uvicorn app.main:app --reload
```

Servidor corriendo en: http://localhost:8000

---

## 📚 Documentación

### API Docs (Swagger)
- **URL**: http://localhost:8000/docs
- Interfaz interactiva para probar endpoints

### Guías de Configuración

1. **MongoDB Atlas**: `.agent/workflows/configurar-mongodb-atlas.md`
2. **Modelos de Datos**: `.agent/workflows/modelos-mongodb.md`
3. **Modelo de Negocio**: `.agent/workflows/modelo-negocio.md`
4. **Planificación Completa**: `.agent/workflows/planificacion-backend.md`

---

## 🗂️ Estructura del Proyecto

```
DulceVicio/
├── app/
│   ├── models/           # Modelos MongoDB (Beanie)
│   ├── schemas/          # Schemas Pydantic
│   ├── routers/          # Endpoints API
│   ├── services/         # Lógica de negocio
│   ├── utils/            # Utilidades (JWT, security)
│   ├── database.py       # Conexión MongoDB Atlas
│   └── main.py           # App principal
├── tests/                # Tests
├── .agent/workflows/     # Documentación y guías
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔑 Endpoints Principales

### Autenticación
```
POST   /api/auth/login          # Login
POST   /api/auth/register       # Registro
GET    /api/auth/me             # Usuario actual
```

### Cursos
```
GET    /api/courses             # Listar cursos
POST   /api/courses             # Crear curso (Admin)
GET    /api/courses/{id}        # Obtener curso con lecciones y recetas
POST   /api/courses/{id}/lessons              # Agregar lección
POST   /api/courses/{id}/recipes/bulk-upload  # Subir múltiples recetas
POST   /api/courses/{id}/generate-recipe-pdf  # Generar PDF consolidado
```

### Inscripciones
```
POST   /api/enrollments         # Inscribir estudiante (Admin)
GET    /api/enrollments         # Listar inscripciones
DELETE /api/enrollments/{id}    # Revocar acceso
```

---

## 💾 Colecciones MongoDB

| Colección | Descripción |
|-----------|-------------|
| `users` | Usuarios (Admin y Estudiantes) |
| `courses` | Cursos con lessons[] y recipes[] embebidos |
| `enrollments` | Inscripciones a cursos |
| `memberships` | Membresías temporales |
| `comments` | Comentarios y respuestas |
| `lesson_progress` | Progreso de lecciones por usuario |

---

## 🎨 Modelo de Negocio

### Lo que recibe un estudiante al comprar un curso:

1. **Videos** (múltiples lecciones/partes)
2. **Recetas** (~10 imágenes individuales)
3. **PDF Consolidado** (1 archivo con todas las recetas)
4. **Grupo WhatsApp** (enlace privado)

### Flujo de Admin:

```
Admin crea curso
  ↓
Admin sube múltiples videos como lecciones
  ↓
Admin sube 10 imágenes de recetas (drag & drop)
  ↓
Sistema genera PDF consolidado automáticamente
  ↓
Admin configura grupo de WhatsApp
  ↓
Admin inscribe estudiantes
```

---

## 🔒 Roles y Permisos

### ADMIN
- ✅ CRUD completo de usuarios, cursos, lecciones, recetas
- ✅ Asignar/revocar accesos
- ✅ Crear membresías
- ✅ Moderar comentarios
- ✅ Subir contenido a Cloudinary

### USER (Estudiante)
- ✅ Ver cursos accesibles
- ✅ Ver lecciones y recetas
- ✅ Marcar lecciones como completadas
- ✅ Comentar en foros
- ✅ Descargar PDFs

---

## 🚀 Despliegue

### MongoDB Atlas
- Ya está en la nube (configurado en `.env`)
- Plan gratuito: 512 MB
- Upgrade cuando lo necesites

### Opciones de Hosting para FastAPI

1. **Railway** (Recomendado - Fácil)
   - Deploy automático desde GitHub
   - Free tier disponible

2. **Render**
   - Free tier con límites
   - Bueno para empezar

3. **DigitalOcean App Platform**
   - $5/mes básico
   - Más control

4. **AWS/GCP**
   - Más complejo pero poderoso

---

## 🧪 Testing

```bash
# Ejecutar tests
pytest

# Con coverage
pytest --cov=app tests/
```

---

## 📝 Variables de Entorno Requeridas

| Variable | Descripción |
|----------|-------------|
| `MONGODB_URL` | Connection string de MongoDB Atlas |
| `MONGODB_DB_NAME` | Nombre de la base de datos |
| `SECRET_KEY` | Clave secreta para JWT |
| `CLOUDINARY_CLOUD_NAME` | Cloud name de Cloudinary |
| `CLOUDINARY_API_KEY` | API Key de Cloudinary |
| `CLOUDINARY_API_SECRET` | API Secret de Cloudinary |

---

## 🐛 Troubleshooting

### Error: "pymongo.errors.ServerSelectionTimeoutError"
- ✅ Verifica que tu IP esté en whitelist (0.0.0.0/0 para desarrollo)
- ✅ Verifica connection string en `.env`
- ✅ Cluster debe estar activo en Atlas

### Error: "cloudinary.exceptions.Error: Must supply api_key"
- ✅ Verifica credenciales de Cloudinary en `.env`
- ✅ Crea cuenta gratuita en Cloudinary si no tienes

---

## 📈 Roadmap

### Fase 1 (Actual)
- ✅ Autenticación y usuarios
- ✅ CRUD de cursos
- ✅ Sistema de lecciones y recetas
- ✅ PDF consolidado automático

### Fase 2 (Próxima)
- ⏳ Chat IA con recetas (OpenAI/Gemini)
- ⏳ Notificaciones por email
- ⏳ Sistema de certificados

### Fase 3 (Futuro)
- 💡 Pagos integrados
- 💡 Live streaming
- 💡 Marketplace de recetas

---

## 👥 Contribuir

1. Fork el proyecto
2. Crea tu feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto es privado y propietario de DulceVicio.

---

## 📞 Soporte

Para dudas o problemas:
- 📧 Email: soporte@dulcevicio.com
- 📱 WhatsApp: +591 XXX XXXXX

---

## 🎉 Créditos

Desarrollado con ❤️ para DulceVicio - Cursos de Repostería

**Stack**: FastAPI + MongoDB Atlas + Cloudinary + Beanie
