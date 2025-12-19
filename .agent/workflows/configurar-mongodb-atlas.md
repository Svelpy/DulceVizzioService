# Guía de Configuración: MongoDB Atlas (Cloud)

## 🌐 Configuración de MongoDB Atlas para DulceVicio

MongoDB Atlas es el servicio de base de datos en la nube de MongoDB, **gratuito para comenzar** y muy fácil de usar.

---

## 1. Crear Cuenta en MongoDB Atlas

### Paso 1: Ir a MongoDB Atlas
1. Visita: https://www.mongodb.com/cloud/atlas/register
2. Crear cuenta con email o Google/GitHub
3. Elegir el **plan gratuito (M0)** - Suficiente para empezar

### Paso 2: Crear un Cluster (Base de Datos)
1. Después de iniciar sesión, click en **"Build a Database"**
2. Seleccionar **FREE** (M0 Sandbox)
3. Configuración recomendada:
   - **Cloud Provider**: AWS (o el que prefieras)
   - **Region**: Elegir la más cercana a tu ubicación
     - Para Bolivia: `us-east-1 (Virginia)` o `sa-east-1 (São Paulo)`
   - **Cluster Name**: `DulceVicio` (o el que prefieras)
4. Click en **"Create"**

**⏱️ Espera 1-3 minutos mientras se crea el cluster**

---

## 2. Configurar Seguridad

### Paso 1: Crear Usuario de Base de Datos
1. Se abrirá automáticamente la pantalla de **Security Quickstart**
2. **Username**: `dulcevicio_admin` (o el que prefieras)
3. **Password**: Generar una contraseña segura (guárdala)
   - Ejemplo: `SecurePass123!`
   - ⚠️ **Importante**: Guarda esta contraseña en un lugar seguro
4. Click en **"Create User"**

### Paso 2: Configurar IP Whitelist
1. Abajo verás **"Where would you like to connect from?"**
2. Para desarrollo, puedes seleccionar:
   - **"My Local Environment"** → "Add My Current IP Address"
   - O mejor: **"Cloud Environment"** → **"0.0.0.0/0"** (permite cualquier IP)
     - ⚠️ **Nota**: En producción, deberías restringir a IPs específicas
3. Click en **"Add Entry"**
4. Click en **"Finish and Close"**

---

## 3. Obtener String de Conexión

### Paso 1: Connect to Cluster
1. En el Dashboard, click en **"Connect"** en tu cluster
2. Seleccionar **"Connect your application"**
3. Configuración:
   - **Driver**: Python
   - **Version**: 3.12 or later
4. Copiar el **Connection String** que se muestra:

```
mongodb+srv://dulcevicio_admin:<password>@dulcevicio.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

5. **Reemplazar** `<password>` con tu contraseña real
6. **Reemplazar** `xxxxx` con tu cluster específico (ya viene correcto)

---

## 4. Configurar en tu Proyecto

### Actualizar `.env`

Crea un archivo `.env` en la raíz del proyecto:

```bash
# MongoDB Atlas (Cloud)
MONGODB_URL=mongodb+srv://dulcevicio_admin:SecurePass123!@dulcevicio.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=dulcevicio_db

# JWT
SECRET_KEY=tu-clave-secreta-super-segura-cambiar-en-produccion
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Cloudinary
CLOUDINARY_CLOUD_NAME=tu-cloud-name
CLOUDINARY_API_KEY=tu-api-key
CLOUDINARY_API_SECRET=tu-api-secret

# App
DEBUG=True
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

**⚠️ Important**: Reemplaza:
- `SecurePass123!` con tu contraseña real
- `xxxxx` con tu cluster ID
- Los valores de Cloudinary cuando los tengas

---

## 5. Código de Conexión (FastAPI)

### `app/database.py`

```python
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import os
from dotenv import load_dotenv

# Importar todos los modelos
from app.models.user import User
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.membership import Membership
from app.models.comment import Comment
from app.models.lesson_progress import LessonProgress

# Cargar variables de entorno
load_dotenv()

# Variables de configuración
MONGODB_URL = os.getenv("MONGODB_URL")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "dulcevicio_db")

# Cliente de MongoDB
mongodb_client: AsyncIOMotorClient = None

async def connect_to_mongo():
    """
    Conectar a MongoDB Atlas
    """
    global mongodb_client
    
    try:
        # Crear cliente
        mongodb_client = AsyncIOMotorClient(MONGODB_URL)
        
        # Obtener base de datos
        database = mongodb_client[MONGODB_DB_NAME]
        
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
        
        print("✅ Conectado exitosamente a MongoDB Atlas")
        print(f"📊 Base de datos: {MONGODB_DB_NAME}")
        
    except Exception as e:
        print(f"❌ Error conectando a MongoDB Atlas: {e}")
        raise

async def close_mongo_connection():
    """
    Cerrar conexión a MongoDB
    """
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()
        print("🔌 Conexión a MongoDB Atlas cerrada")

# Para obtener la base de datos actual
def get_database():
    return mongodb_client[MONGODB_DB_NAME]
```

### `app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from app.database import connect_to_mongo, close_mongo_connection
from app.routers import auth, users, courses, enrollments, memberships, comments

# Cargar variables de entorno
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Conectar a MongoDB
    await connect_to_mongo()
    yield
    # Shutdown: Cerrar conexión
    await close_mongo_connection()

# Crear app FastAPI
app = FastAPI(
    title="DulceVicio API",
    description="API para gestión de cursos de repostería",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(users.router, prefix="/api", tags=["Users"])
app.include_router(courses.router, prefix="/api", tags=["Courses"])
app.include_router(enrollments.router, prefix="/api", tags=["Enrollments"])
app.include_router(memberships.router, prefix="/api", tags=["Memberships"])
app.include_router(comments.router, prefix="/api", tags=["Comments"])

@app.get("/")
async def root():
    return {
        "message": "Bienvenido a DulceVicio API 🎂",
        "docs": "/docs",
        "database": "MongoDB Atlas (Cloud)"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "MongoDB Atlas",
        "service": "DulceVicio API"
    }
```

---

## 6. Verificar Conexión

### Ejecutar el servidor:

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
uvicorn app.main:app --reload
```

### Deberías ver en consola:

```
✅ Conectado exitosamente a MongoDB Atlas
📊 Base de datos: dulcevicio_db
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Probar salud del API:

Visita: http://localhost:8000/health

Deberías ver:
```json
{
  "status": "healthy",
  "database": "MongoDB Atlas",
  "service": "DulceVicio API"
}
```

---

## 7. Explorar la Base de Datos en Atlas

MongoDB Atlas tiene una interfaz web excelente:

1. En el Dashboard de Atlas, click en **"Browse Collections"**
2. Verás tu base de datos `dulcevicio_db`
3. Puedes:
   - Ver documentos
   - Agregar/editar/eliminar manualmente
   - Ejecutar queries
   - Ver índices
   - Monitorear performance

---

## 8. Ventajas de MongoDB Atlas

### ✅ **Gratuito para Comenzar**
- 512 MB de almacenamiento
- Shared CPU
- Perfecto para desarrollo y MVP

### ✅ **Backups Automáticos**
- Snapshots diarios (en planes pagos)
- Point-in-time recovery

### ✅ **Escalabilidad Fácil**
- Upgrade a cluster más grande con 1 click
- No downtime

### ✅ **Seguridad**
- Encriptación en tránsito y reposo
- IP Whitelisting
- Autenticación robusta

### ✅ **Monitoreo**
- Dashboard de performance
- Alertas automáticas
- Query profiling

### ✅ **API Nativa**
- Compatible con todos los drivers oficiales
- Mismo código que MongoDB local

---

## 9. Límites del Plan Gratuito (M0)

| Recurso | Límite |
|---------|--------|
| Almacenamiento | 512 MB |
| RAM | Shared |
| Conexiones simultáneas | 500 |
| Clusters | 1 por proyecto |

**💡 Para DulceVicio:**
- 512 MB = ~50,000 documentos pequeños
- Más que suficiente para comenzar
- Cuando necesites más, upgrade a M10 (~$57/mes)

---

## 10. Solución de Problemas

### Problema: No se puede conectar

**Verificar:**
1. ✅ IP está en whitelist (0.0.0.0/0 permite todas)
2. ✅ Usuario y contraseña correctos
3. ✅ String de conexión correcto (sin espacios)
4. ✅ Cluster está activo (puede estar pausado)

### Problema: "Authentication failed"

**Solución:**
1. Verifica la contraseña en `.env`
2. Si tiene caracteres especiales (@, #, etc.), encodea la URL:
   ```python
   from urllib.parse import quote_plus
   password = quote_plus("Pass@123!")
   ```

### Problema: Cluster pausado

**Solución:**
- Los clusters M0 se pausan después de 60 días de inactividad
- Click en "Resume" en el Dashboard

---

## 11. Próximos Pasos

Una vez conectado:

1. ✅ Crear primer usuario admin (vía endpoint POST /api/users)
2. ✅ Login y obtener JWT
3. ✅ Crear primer curso
4. ✅ Probar subida de videos/recetas
5. ✅ Verificar en Atlas que se están creando los documentos

---

## 12. Recursos Útiles

- **MongoDB Atlas Docs**: https://docs.atlas.mongodb.com/
- **Motor (Async Driver)**: https://motor.readthedocs.io/
- **Beanie ODM**: https://beanie-odm.dev/
- **MongoDB Universidad (gratis)**: https://university.mongodb.com/

---

## ✨ Resumen

```bash
# 1. Crear cuenta en MongoDB Atlas (gratis)
# 2. Crear cluster M0
# 3. Crear usuario de BD
# 4. Whitelist IP (0.0.0.0/0 para desarrollo)
# 5. Copiar connection string
# 6. Pegar en .env como MONGODB_URL
# 7. pip install -r requirements.txt
# 8. uvicorn app.main:app --reload
# 9. ✅ ¡Listo!
```

**¿Necesitas ayuda con algún paso específico?** 🚀
