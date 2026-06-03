import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Añadir el directorio actual al path para importar correctamente el config e inicializar .env
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# Cargar variables de entorno del archivo .env antes de cualquier import de la app
dotenv_path = os.path.join(script_dir, '.env')
load_dotenv(dotenv_path=dotenv_path)

try:
    from app.config import settings
except ImportError as e:
    print(f"Error al importar la configuración de la app: {e}")
    print("Asegúrate de ejecutar este script desde la raíz de DulceVizzioService.")
    sys.exit(1)


async def analyze_users():
    # Validar que tengamos las variables de entorno necesarias
    mongodb_url = os.getenv("MONGODB_URL") or getattr(settings, "MONGODB_URL", None)
    db_name = os.getenv("MONGODB_DB_NAME") or getattr(settings, "MONGODB_DB_NAME", "dulcevicio_db")
    
    if not mongodb_url:
        print("[ERR] Error: MONGODB_URL no está definido en el archivo .env o en settings.")
        return

    print("[...] Conectando a MongoDB...")
    client = AsyncIOMotorClient(mongodb_url)
    db = client[db_name]
    collection = db['users']

    # Obtener todos los documentos de la colección de usuarios
    try:
        cursor = collection.find({})
        users = await cursor.to_list(length=None)
    except Exception as e:
        print(f"[ERR] Error al consultar la colección de usuarios: {e}")
        client.close()
        return

    total_users = len(users)
    print(f"[OK] Conexion exitosa. Base de datos: '{db_name}' | Coleccion: 'users'")
    print(f"[INFO] Total de documentos de usuario en la base de datos: {total_users}\n")

    if total_users == 0:
        print("[WARN] No hay usuarios registrados en la base de datos.")
        client.close()
        return

    # Campos opcionales declarados en el modelo User
    optional_fields = {
        "username": "Indexado, unico. Por defecto es None",
        "avatar_url": "URL de avatar. Por defecto es None",
        "phone_number": "Numero de telefono. Por defecto es None",
        "birth_date": "Fecha de nacimiento. Por defecto es None"
    }

    # Campos opcionales declarados en BaseDocument (Auditoria)
    base_optional_fields = {
        "created_by": "Creado por. Por defecto es None",
        "updated_by": "Actualizado por. Por defecto es None",
        "deleted_at": "Fecha de eliminacion (soft-delete). Por defecto es None",
        "deleted_by": "Eliminado por. Por defecto es None"
    }

    def inspect_fields(fields_dict, category_name):
        print("=" * 80)
        print(f"ANALYZE: {category_name}")
        print("=" * 80)
        
        for field, desc in fields_dict.items():
            missing_count = 0
            null_count = 0
            empty_str_count = 0
            affected_emails = []

            for user in users:
                email = user.get("email") or f"Sin Email (ID: {user.get('_id')})"
                
                if field not in user:
                    missing_count += 1
                    affected_emails.append(email)
                else:
                    val = user[field]
                    if val is None:
                        null_count += 1
                        affected_emails.append(email)
                    elif isinstance(val, str) and val.strip() == "":
                        empty_str_count += 1
                        affected_emails.append(email)

            total_empty = missing_count + null_count + empty_str_count
            pct = (total_empty / total_users) * 100

            print(f"\n* Campo: '{field}' ({desc})")
            print(f"   Estado general: {total_empty}/{total_users} vacios ({pct:.2f}%)")
            print(f"   -> Faltantes en el documento (no existe la clave): {missing_count}")
            print(f"   -> Nulos (clave existe pero es null/None): {null_count}")
            print(f"   -> Cadenas vacias (''): {empty_str_count}")
            
            if total_empty > 0:
                print("   [!] Usuarios afectados (primeros 15):")
                for u_email in affected_emails[:15]:
                    print(f"     - {u_email}")
                if len(affected_emails) > 15:
                    print(f"     - ... y {len(affected_emails) - 15} mas.")
            else:
                print("   [OK] Ningun usuario tiene este campo vacio.")

    # Ejecutar inspeccion para ambos conjuntos de campos
    inspect_fields(optional_fields, "Campos de User (user.py)")
    inspect_fields(base_optional_fields, "Campos heredados de BaseDocument (base.py)")

    client.close()

if __name__ == "__main__":
    if sys.platform == 'win32':
        # Evitar usar set_event_loop_policy si tira warning en python moderno, 
        # pero motor suele requerir SelectorEventLoop en Windows en ciertas versiones
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except AttributeError:
            pass
    asyncio.run(analyze_users())

