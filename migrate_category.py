"""
Script de migración: convierte category de str a int (valor 1) en todos los cursos
Ejecutar UNA sola vez: python migrate_category.py
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings


async def migrate():
    print("🔌 Conectando a MongoDB Atlas...")
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    collection = db["courses"]

    # Actualiza TODOS los documentos → category = 1
    result = await collection.update_many(
        {},                          # filtro vacío = todos los documentos
        {"$set": {"category": 1}}   # set category a 1
    )

    print(f"✅ Migración completa.")
    print(f"   Documentos encontrados : {result.matched_count}")
    print(f"   Documentos modificados : {result.modified_count}")

    client.close()


if __name__ == "__main__":
    asyncio.run(migrate())
