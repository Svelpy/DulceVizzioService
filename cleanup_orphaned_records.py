import asyncio
from bson import ObjectId
from app.database import connect_to_mongo
from app.models.course import Course, CourseReview
from app.models.lesson import Lesson
from app.models.enrollment import Enrollment

async def clear_orphaned_records():
    print("🔄 Iniciando limpieza de registros huérfanos...")
    
    # 1. Conectar a la base de datos a través de Beanie
    await connect_to_mongo()
    
    # 2. Capturar todos los IDs de los Cursos (Course) que existen en la BD
    courses = await Course.find().to_list()
    
    # Extraemos tanto los ObjectIds para Lesson/Enrollment como los Strings para Reviews
    valid_course_ids = [c.id for c in courses]
    valid_course_ids_str = [str(c.id) for c in courses]
    
    print(f"✅ Se encontraron {len(valid_course_ids)} cursos válidos.")
    
    if not valid_course_ids:
        print("⚠️ No hay ningún curso en la base de datos. Si se limpian huérfanos, se borrarán todos los enrollments y lecciones.")
        confirm = input("¿Deseas continuar y borrar TODO? (y/n): ")
        if confirm.lower() != 'y':
            print("Abortando...")
            return

    # --- 3. Limpieza de Lecciones (Lessons) ---
    print("\n🔍 Buscando lecciones huérfanas...")
    orphaned_lessons = await Lesson.find({"course_id": {"$nin": valid_course_ids}}).to_list()
    if orphaned_lessons:
        for ol in orphaned_lessons:
            print(f"  🗑️ Borrando Lección {ol.id} (Pertenecía al curso fantasma {ol.course_id})")
            await ol.delete()
        print(f"✅ Se borraron físicamente {len(orphaned_lessons)} lecciones huérfanas.")
    else:
        print("✅ No hay lecciones huérfanas.")

    # --- 4. Limpieza de Inscripciones (Enrollments) ---
    print("\n🔍 Buscando inscripciones (enrollments) huérfanas...")
    orphaned_enrollments = await Enrollment.find({"course_id": {"$nin": valid_course_ids}}).to_list()
    if orphaned_enrollments:
        for oe in orphaned_enrollments:
            print(f"  🗑️ Borrando Inscripción {oe.id} (Estudiante {oe.user_id} - Curso fantasma {oe.course_id})")
            await oe.delete()
        print(f"✅ Se borraron físicamente {len(orphaned_enrollments)} inscripciones huérfanas.")
    else:
        print("✅ No hay inscripciones huérfanas.")
        
    # --- 5. Limpieza de Reseñas (CourseReviews) ---
    print("\n🔍 Buscando reseñas huérfanas...")
    # NOTA: En CourseReview, course_id está tipado como 'str' en tu modelo
    orphaned_reviews = await CourseReview.find({"course_id": {"$nin": valid_course_ids_str}}).to_list()
    if orphaned_reviews:
        for r in orphaned_reviews:
            print(f"  🗑️ Borrando Reseña {r.id} (Curso fantasma {r.course_id})")
            await r.delete()
        print(f"✅ Se borraron físicamente {len(orphaned_reviews)} reseñas huérfanas.")
    else:
        print("✅ No hay reseñas huérfanas.")
        
    print("\n🎉 Limpieza completada con éxito.")

if __name__ == "__main__":
    try:
        # Ejecutar el loop en un entorno que soporta async
        asyncio.run(clear_orphaned_records())
    except KeyboardInterrupt:
        print("\nCancelado por el usuario.")
    except Exception as e:
        print(f"\n❌ Ocurrió un error: {e}")
