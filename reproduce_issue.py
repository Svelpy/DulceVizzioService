import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

# 1. Login para obtener token (Asumimos que existe admin@dulcevizzio.com)
def login():
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", data={
            "username": "admin@dulcevizzio.com",
            "password": "securepassword" # Ajustar si es diferente
        })
        if resp.status_code == 200:
            return resp.json()["access_token"]
        print(f"Login failed: {resp.text}")
        return None
    except Exception as e:
        print(f"Error conectando (Login): {e}")
        return None

# 2. Crear Lección
def create_lesson(token, course_id):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "title": "Lección de Prueba Automática",
        "description": "Creada por Antigravity para validar",
        "video_url": "https://video.bunnycdn.com/play/123/abc",
        "video_id": "abc-123",
        "duration_seconds": 60,
        "is_preview": False
    }
    
    print(f"Creando lección en curso {course_id}...")
    resp = requests.post(f"{BASE_URL}/courses/{course_id}/lessons", json=payload, headers=headers)
    
    if resp.status_code == 201:
        print("✅ Lección creada EXITOSAMENTE.")
        return resp.json()
    else:
        print(f"❌ Falló creación de lección: {resp.status_code} - {resp.text}")
        return None

# 3. Verificar Cursos Fantasma
def check_ghost_courses(token):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/courses?limit=100", headers=headers)
    if resp.status_code == 200:
        courses = resp.json()["data"]
        ghosts = [c for c in courses if c["title"] == "Lección de Prueba Automática"]
        if ghosts:
            print(f"👻 ¡ALERTA! Se encontraron {len(ghosts)} cursos fantasma con el nombre de la lección.")
            print("El bug de duplicación persiste.")
        else:
            print("🛡️ No se encontraron cursos fantasma. La creación fue limpia.")
    else:
        print(f"Error listando cursos: {resp.status_code}")

if __name__ == "__main__":
    token = login()
    if token:
        # Usamos el ID del curso "Prueba1" que vimos en el log anterior
        # Reemplazar por uno válido si ese ya no existe
        COURSE_ID = "6977ede06545205144bce0f8" 
        
        create_lesson(token, COURSE_ID)
        check_ghost_courses(token)
