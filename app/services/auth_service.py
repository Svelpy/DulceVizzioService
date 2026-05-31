"""
Servicio de Autenticación
Lógica de negocio para login, registro y gestión de tokens
"""

from typing import Optional
from datetime import timedelta
from fastapi import HTTPException, status

from app.models.user import User
from app.models.enums import Role
from app.schemas.user_schema import UserCreate, UserSelfRegister, UserLogin, TokenResponse, UserResponse, UserSelfUpdate
from app.utils.security import hash_password, verify_password, create_access_token
from bson import ObjectId


class AuthService:
    """Servicio de autenticación"""
    

    
    @staticmethod
    async def register_user(user_data: UserCreate, created_by: Optional[str] = None) -> User:
        """
        Registrar un nuevo usuario (USO ADMINISTRATIVO)
        
        Args:
            user_data: Datos del usuario a crear
            
        Returns:
            Usuario creado
            
        Raises:
            HTTPException 400: Si el email o username ya existe
        """
        # Verificar si el email ya existe
        existing_user = await User.find_one(User.email == user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
        
        # Verificar si el username ya existe
        existing_username = await User.find_one(User.username == user_data.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El username ya está en uso"
            )
        
        # Crear nuevo usuario
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            password_hash=hash_password(user_data.password),
            role=user_data.role,
            is_active=True,
            created_by=created_by,
            updated_by=created_by,
            phone_number=user_data.phone_number,
            birth_date=user_data.birth_date
        )
        
        await new_user.insert()
        
        return new_user
    
    @staticmethod
    async def login(credentials: UserLogin) -> TokenResponse:
        """
        Autenticar usuario y generar token JWT
        
        Args:
            credentials: Email y contraseña
            
        Returns:
            Token de acceso y datos del usuario
            
        Raises:
            HTTPException 401: Si las credenciales son inválidas
        """
        # Buscar usuario por email
        user = await User.find_one(User.email == credentials.email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verificar si el usuario fue eliminado
        if user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Esta cuenta ha sido eliminada. Contacta al administrador.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verificar contraseña
        if not verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verificar que el usuario esté activo
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo. Contacta al administrador."
            )
        
        # Crear token JWT
        access_token = create_access_token(
            data={
                "user_id": str(user.id),
                "email": user.email,
                "role": user.role
            }
        )
        
        # Preparar respuesta de usuario
        # Preparar respuesta de token (Pydantic serializará 'user' usando UserResponse)
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user  # Pasamos el modelo completo Beanie
        )
    
    @staticmethod
    async def get_current_user_info(user: User) -> User:
        """
        Obtener información del usuario actual
        
        Args:
            user: Usuario autenticado (Modelo completo)
            
        Returns:
            Modelo User (el Router se encarga de convertirlo a UserResponse)
        """
        return user
    
    @staticmethod
    async def change_password(
        user: User,
        current_password: str,
        new_password: str
    ) -> dict:
        """
        Cambiar contraseña del usuario
        
        Args:
            user: Usuario autenticado
            current_password: Contraseña actual
            new_password: Nueva contraseña
            
        Returns:
            Mensaje de confirmación
            
        Raises:
            HTTPException 400: Si la contraseña actual es incorrecta
        """
        # Verificar contraseña actual
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contraseña actual incorrecta"
            )
        
        # Actualizar contraseña
        user.password_hash = hash_password(new_password)
        await user.save()
        
        return {"message": "Contraseña actualizada exitosamente"}

    @staticmethod
    async def register_self(user_data: UserSelfRegister) -> User:
        """
        Registrar un nuevo usuario de forma pública (auto-registro)
        El rol siempre será Role.USER (Estudiante)
        
        Args:
            user_data: Datos de auto-registro del usuario
            
        Returns:
            Usuario creado
            
        Raises:
            HTTPException 400: Si el email o el username ya están en uso
        """
        # 1. Verificar si el email ya existe
        existing_user = await User.find_one(User.email == user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
        
        # 2. Gestionar y verificar el username
        username = user_data.username
        if username:
            existing_username = await User.find_one(User.username == username)
            if existing_username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El username ya está en uso"
                )
        else:
            # Si no se ingresó username, lo autogeneramos a partir del nombre completo de forma única
            from app.utils.user_utils import generate_chef_username
            username = await generate_chef_username(user_data.full_name)

        # 3. Crear e insertar el nuevo usuario en MongoDB
        new_user = User(
            email=user_data.email,
            username=username,
            full_name=user_data.full_name,
            password_hash=hash_password(user_data.password),
            role=Role.USER,
            is_active=True,
            created_by="self_register",
            updated_by="self_register",
            phone_number=user_data.phone_number,
            birth_date=user_data.birth_date
        )
        
        await new_user.insert()
        return new_user
    
    @staticmethod
    async def update_profile(user: User, update_data: UserSelfUpdate) -> User:
        """
        Actualiza los datos del perfil del propio usuario autenticado.
        Valida que el nuevo username (si cambia) sea único en la base de datos.
        """
        # 1. Si cambia el username, validar que no esté en uso por otra persona
        username = update_data.username
        if username and username != user.username:
            existing_username = await User.find_one(User.username == username)
            if existing_username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El username ya está en uso"
                )
        # 2. Actualizar dinámicamente los campos enviados
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(user, key, value)

        # 3. Registrar auditoría básica y guardar
        user.updated_by = str(user.id)
        await user.save()

        return user

# Instancia global del servicio
auth_service = AuthService()
