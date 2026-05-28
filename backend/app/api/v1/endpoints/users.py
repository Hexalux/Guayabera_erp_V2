from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.usuario import Usuario
from app.models.admin import Admin
from app.api.deps import get_current_admin_user
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioOut

router = APIRouter()


@router.get("/", response_model=List[UsuarioOut])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_admin = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener lista de usuarios (solo para admins)
    """
    result = await db.execute(Usuario.__table__.select().offset(skip).limit(limit))
    usuarios = [Usuario(**row._mapping) for row in result.fetchall()]
    
    return [
        UsuarioOut(
            id=u.id,
            email=u.email,
            nombre_completo=u.nombre_completo,
            tipo_usuario=u.tipo_usuario,
            tenant_id=u.tenant_id,
            is_active=u.is_active
        ) for u in usuarios
    ]


@router.post("/", response_model=UsuarioOut)
async def create_user(
    user_in: UsuarioCreate,
    current_admin = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Crear un nuevo usuario
    """
    # Verificar que el email no exista
    result = await db.execute(
        Usuario.__table__.select().where(Usuario.email == user_in.email)
    )
    existing_user = result.fetchone()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email ya está en uso"
        )
    
    # Crear el nuevo usuario
    hashed_password = get_password_hash(user_in.password)
    
    user = Usuario(
        id=str(uuid.uuid4()),
        email=user_in.email,
        hashed_password=hashed_password,
        nombre_completo=user_in.nombre_completo,
        tipo_usuario=user_in.tipo_usuario,
        tenant_id=user_in.tenant_id
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return UsuarioOut(
        id=user.id,
        email=user.email,
        nombre_completo=user.nombre_completo,
        tipo_usuario=user.tipo_usuario,
        tenant_id=user.tenant_id,
        is_active=user.is_active
    )


@router.put("/{user_id}", response_model=UsuarioOut)
async def update_user(
    user_id: str,
    user_in: UsuarioUpdate,
    current_admin = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Actualizar un usuario existente
    """
    result = await db.execute(
        Usuario.__table__.select().where(Usuario.id == user_id)
    )
    user = result.fetchone()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    user_obj = Usuario(**user._mapping)
    
    # Actualizar campos
    update_data = user_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field != "password":  # No actualizar contraseña aquí directamente
            setattr(user_obj, field, value)
    
    if user_in.password:
        user_obj.hashed_password = get_password_hash(user_in.password)
    
    await db.commit()
    await db.refresh(user_obj)
    
    return UsuarioOut(
        id=user_obj.id,
        email=user_obj.email,
        nombre_completo=user_obj.nombre_completo,
        tipo_usuario=user_obj.tipo_usuario,
        tenant_id=user_obj.tenant_id,
        is_active=user_obj.is_active
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_admin = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Eliminar (desactivar) un usuario
    """
    result = await db.execute(
        Usuario.__table__.select().where(Usuario.id == user_id)
    )
    user = result.fetchone()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    user_obj = Usuario(**user._mapping)
    user_obj.is_active = False  # Desactivar en lugar de eliminar
    
    await db.commit()
    
    return {"message": "Usuario desactivado exitosamente"}