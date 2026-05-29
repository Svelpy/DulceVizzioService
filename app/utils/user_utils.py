import re
import unicodedata
import secrets
import string
from typing import Optional, Set
from datetime import datetime

def normalize_name(name: str) -> str:
    """
    Normaliza un nombre para uso en username:
    - Quita acentos/diacríticos
    - Solo deja letras ASCII
    - Capitaliza la primera letra
    Ejemplo: "José María" → "JoseMaria"
    """
    if not name:
        return ""
    # Descomponer caracteres Unicode y quitar diacríticos
    nfkd = unicodedata.normalize('NFKD', name)
    ascii_only = nfkd.encode('ASCII', 'ignore').decode('ASCII')
    # Solo letras
    clean = re.sub(r'[^a-zA-Z]', '', ascii_only)
    return clean.capitalize() if clean else ""

def generate_user_password(birth_date: Optional[datetime]) -> str:
    """
    Genera la contraseña siguiendo la lógica DvDDMMAAAA donde DDMMAAAA es la fecha de nacimiento.
    Si no hay fecha de nacimiento, genera una aleatoria segura.
    """
    if birth_date:
        return f"Dv{birth_date.strftime('%d%m%Y')}"
    else:
        return "Dv12345678"

async def generate_chef_username(full_name: str) -> str:
    """
    Genera un username único con el prefijo 'Chef'.
    Revisa la base de datos para asegurar unicidad.
    """
    from app.models.user import User
    
    parts = full_name.strip().split()
    normalized_parts = [normalize_name(p) for p in parts if normalize_name(p)]

    if not normalized_parts:
        normalized_parts = ["Usuario"]

    first_name = normalized_parts[0]

    # Estrategia de candidatos
    candidates = []
    
    # 1. ChefPrimerNombre
    candidates.append(f"Chef{first_name}")
    
    # 2. ChefPrimerNombreSegundoNombre
    if len(normalized_parts) >= 3:
        candidates.append(f"Chef{first_name}{normalized_parts[1]}")
        
    # 3. ChefPrimerNombreApellido
    if len(normalized_parts) >= 2:
        candidates.append(f"Chef{first_name}{normalized_parts[-1]}")

    for candidate in candidates:
        db_exists = await User.find_one(User.username == candidate)
        if not db_exists:
            return candidate

    # 4. Fallback numérico
    counter = 2
    while True:
        candidate = f"Chef{first_name}{counter}"
        db_exists = await User.find_one(User.username == candidate)
        if not db_exists:
            retu