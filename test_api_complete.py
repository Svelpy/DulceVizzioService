#!/usr/bin/env python3
"""
Script de prueba E2E completo para DulceVizzio API
Prueba todos los endpoints de Course, Lesson y Material
"""

import requests
from urllib.parse import urlencode

BASE_URL = "http://127.0.0.1:8000"
USERNAME = "[EMAIL_ADDRESS]"
PASSWORD = "[PASSWORD]" 

# Colores para output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

def log_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")

def log_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")

def log_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")

def log_section(msg):
    print(f"\n{Colors.BOLD}{Colors.YELLOW}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.YELLOW}{msg}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.YELLOW}{'='*60}{Colors.RESET}\n")

def login():
    """Autenticación usando JSON (UserLogin schema)"""
    log_section("1. AUTENTICACIÓN")
    
    # El endpoint espera JSON con email/password
    login_data = {
        'email': USERNAME,
        'password': PASSWORD
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=login_data,
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            log_success(f"Login exitoso para: {USERNAME}")
            return data['access_token']
        else:
            log_error(f"Login falló: {response.status_code}")
            log_error(f"Detalles: {response.text}")
            return None
    except Exception as e:
        log_error(f"Error de conexión: {e}")
        return None

def test_courses(token):
    """Prueba todos los endpoints de Course"""
    log_section("2. PRUEBAS DE CURSOS (COURSE)")
    
    headers = {'Authorization': f'Bearer {token}'}
    course_id = None
    
    # 2.1 Crear curso
    log_info("2.1 POST /courses - Crear curso")
    course_data = {
        "title": "Curso de Prueba E2E",
        "description": "Descripción completa del curso de prueba",
        "price": 199.99,
        "difficulty": "INTERMEDIATE",
        "category": "Testing",
        "subcategory": "Automatización",
        "tags": ["test", "e2e", "automation"]
    }
    
    response = requests.post(f"{BASE_URL}/courses", json=course_data, headers=headers)
    if response.status_code == 201:
        course = response.json()
        course_id = course['id']
        log_success(f"Curso creado: {course['title']} (ID: {course_id}, Slug: {course.get('slug')})")
    else:
        log_error(f"Error creando curso: {response.status_code} - {response.text}")
        return None
    
    # 2.2 Listar cursos
    log_info("2.2 GET /courses - Listar cursos")
    response = requests.get(f"{BASE_URL}/courses?page=1&limit=10", headers=headers)
    if response.status_code == 200:
        data = response.json()
        log_success(f"Cursos listados: {data['total']} total, página {data['page']}/{data['pages']}")
    else:
        log_error(f"Error listando cursos: {response.status_code}")
    
    # 2.3 Obtener curso por slug
    log_info(f"2.3 GET /courses/{course.get('slug')} - Obtener curso por slug")
    response = requests.get(f"{BASE_URL}/courses/{course.get('slug')}", headers=headers)
    if response.status_code == 200:
        log_success(f"Curso obtenido: {response.json()['title']}")
    else:
        log_error(f"Error obteniendo curso: {response.status_code}")
    
    # 2.4 Actualizar curso
    log_info(f"2.4 PUT /courses/{course_id} - Actualizar curso")
    update_data = {
        "description": "Descripción actualizada del curso",
        "price": 249.99
    }
    response = requests.put(f"{BASE_URL}/courses/{course_id}", json=update_data, headers=headers)
    if response.status_code == 200:
        log_success(f"Curso actualizado: nuevo precio ${response.json()['price']}")
    else:
        log_error(f"Error actualizando curso: {response.status_code}")
    
    # 2.5 Cambiar estado del curso
    log_info(f"2.5 PATCH /courses/{course_id}/status - Cambiar estado")
    response = requests.patch(
        f"{BASE_URL}/courses/{course_id}/status",
        json={"status": "PUBLISHED"},
        headers=headers
    )
    if response.status_code == 200:
        log_success(f"Estado cambiado a: {response.json()['status']}")
    else:
        log_error(f"Error cambiando estado: {response.status_code}")
    
    return course_id

def test_lessons(token, course_id):
    """Prueba todos los endpoints de Lesson"""
    log_section("3. PRUEBAS DE LECCIONES (LESSON)")
    
    headers = {'Authorization': f'Bearer {token}'}
    lesson_ids = []
    
    # 3.1 Crear lecciones
    log_info(f"3.1 POST /courses/{course_id}/lessons - Crear lecciones")
    lessons_data = [
        {
            "title": "Lección 1: Introducción",
            "summary": "Resumen de la primera lección",
            "video_url": "https://video.bunnycdn.com/play/123/abc",
            "video_id": "abc-123",
            "duration_seconds": 180,
            "is_preview": True
        },
        {
            "title": "Lección 2: Contenido Principal",
            "summary": "Contenido avanzado",
            "video_url": "https://video.bunnycdn.com/play/456/def",
            "video_id": "def-456",
            "duration_seconds": 420,
            "is_preview": False
        }
    ]
    
    for lesson_data in lessons_data:
        response = requests.post(
            f"{BASE_URL}/courses/{course_id}/lessons",
            json=lesson_data,
            headers=headers
        )
        if response.status_code == 201:
            lesson = response.json()
            lesson_ids.append(lesson['id'])
            log_success(f"Lección creada: {lesson['title']} (Order: {lesson.get('order')})")
        else:
            log_error(f"Error creando lección: {response.status_code} - {response.text}")
    
    # 3.2 Listar lecciones del curso
    log_info(f"3.2 GET /courses/{course_id}/lessons - Listar lecciones")
    response = requests.get(f"{BASE_URL}/courses/{course_id}/lessons", headers=headers)
    if response.status_code == 200:
        lessons = response.json()
        log_success(f"Lecciones listadas: {len(lessons)} lecciones encontradas")
    else:
        log_error(f"Error listando lecciones: {response.status_code}")
    
    if lesson_ids:
        # 3.3 Obtener lección por ID
        log_info(f"3.3 GET /lessons/{lesson_ids[0]} - Obtener lección")
        response = requests.get(f"{BASE_URL}/lessons/{lesson_ids[0]}", headers=headers)
        if response.status_code == 200:
            log_success(f"Lección obtenida: {response.json()['title']}")
        else:
            log_error(f"Error obteniendo lección: {response.status_code}")
        
        # 3.4 Actualizar lección
        log_info(f"3.4 PUT /lessons/{lesson_ids[0]} - Actualizar lección")
        update_data = {
            "summary": "Resumen actualizado de la lección",
            "duration_seconds": 200
        }
        response = requests.put(
            f"{BASE_URL}/lessons/{lesson_ids[0]}",
            json=update_data,
            headers=headers
        )
        if response.status_code == 200:
            log_success(f"Lección actualizada: {response.json()['duration_seconds']}s")
        else:
            log_error(f"Error actualizando lección: {response.status_code}")
    
    return lesson_ids

def test_materials(token, lesson_id):
    """Prueba todos los endpoints de Material"""
    log_section("4. PRUEBAS DE MATERIALES (MATERIAL)")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # 4.1 Subir material
    log_info(f"4.1 POST /lessons/{lesson_id}/materials - Subir material")
    
    # Crear archivo dummy
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as tmp:
        tmp.write(b'%PDF-1.4\nDummy PDF content for testing')
        tmp_path = tmp.name
    
    try:
        with open(tmp_path, 'rb') as f:
            files = {'file': ('receta_prueba.pdf', f, 'application/pdf')}
            data = {
                'title': 'Receta de Prueba',
                'is_downloadable': 'true'
            }
            
            response = requests.post(
                f"{BASE_URL}/lessons/{lesson_id}/materials",
                files=files,
                data=data,
                headers=headers
            )
            
            if response.status_code == 201:
                material = response.json()
                log_success(f"Material subido: {material['title']}")
            else:
                log_error(f"Error subiendo material: {response.status_code} - {response.text}")
    finally:
        os.unlink(tmp_path)
    
    # 4.2 Eliminar todos los materiales
    log_info(f"4.2 DELETE /lessons/{lesson_id}/materials - Eliminar materiales")
    response = requests.delete(f"{BASE_URL}/lessons/{lesson_id}/materials", headers=headers)
    if response.status_code == 200:
        log_success(f"Materiales eliminados: {response.json()['message']}")
    else:
        log_error(f"Error eliminando materiales: {response.status_code}")

def test_statistics(token, course_id):
    """Verifica que las estadísticas se calculen correctamente"""
    log_section("5. VERIFICACIÓN DE ESTADÍSTICAS")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    log_info(f"5.1 Verificar estadísticas del curso")
    response = requests.get(f"{BASE_URL}/courses?page=1&limit=100", headers=headers)
    
    if response.status_code == 200:
        courses = response.json()['data']
        # Buscar curso usando get() para manejar ambos 'id' y '_id'
        target_course = next((c for c in courses if c.get('id') == course_id or c.get('_id') == course_id), None)
        
        if target_course:
            lessons_count = target_course.get('lessons_count', 0)
            duration = target_course.get('total_duration_hours', 0)
            
            log_success(f"Estadísticas verificadas:")
            log_success(f"  - Lecciones: {lessons_count} (esperado: 2)")
            log_success(f"  - Duración total: {duration} horas")
            
            if lessons_count == 2 and duration > 0:
                log_success("✓ Estadísticas correctas")
            else:
                log_error("✗ Estadísticas incorrectas")
        else:
            log_error("Curso no encontrado en el listado")
    else:
        log_error(f"Error verificando estadísticas: {response.status_code}")

def cleanup(token, course_id, lesson_ids):
    """Limpieza: eliminar datos de prueba"""
    log_section("6. LIMPIEZA (CLEANUP)")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Eliminar lecciones
    for lesson_id in lesson_ids:
        log_info(f"6.1 DELETE /lessons/{lesson_id} - Eliminar lección")
        response = requests.delete(f"{BASE_URL}/lessons/{lesson_id}", headers=headers)
        if response.status_code == 200:
            log_success("Lección eliminada")
        else:
            log_error(f"Error eliminando lección: {response.status_code}")
    
    # Eliminar curso
    log_info(f"6.2 DELETE /courses/{course_id} - Eliminar curso")
    response = requests.delete(f"{BASE_URL}/courses/{course_id}", headers=headers)
    if response.status_code == 200:
        log_success(f"Curso eliminado: {response.json()['message']}")
    else:
        log_error(f"Error eliminando curso: {response.status_code}")

def main():
    """Flujo principal de pruebas"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}🚀 SCRIPT DE PRUEBAS E2E - DulceVizzio API{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    # 1. Login
    token = login()
    if not token:
        log_error("No se pudo autenticar. Abortando pruebas.")
        return
    
    # 2. Pruebas de Course
    course_id = test_courses(token)
    if not course_id:
        log_error("No se pudo crear curso. Abortando pruebas.")
        return
    
    # 3. Pruebas de Lesson
    lesson_ids = test_lessons(token, course_id)
    
    # 4. Pruebas de Material
    if lesson_ids:
        test_materials(token, lesson_ids[0])
    
    # 5. Verificar estadísticas
    test_statistics(token, course_id)
    
    # 6. Limpieza
    cleanup(token, course_id, lesson_ids)
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}🏁 PRUEBAS FINALIZADAS{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}{'='*70}{Colors.RESET}\n")

if __name__ == "__main__":
    main()
