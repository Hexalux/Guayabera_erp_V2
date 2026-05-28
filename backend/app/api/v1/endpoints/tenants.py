from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from app.core.database import get_db
from app.models.tenant import Tenant, GrupoCorporativo
from app.models.admin import Admin
from app.api.deps import get_current_admin_user
from app.schemas.tenant import (
    TenantCreate, 
    TenantUpdate, 
    TenantOut,
    GrupoCorporativoCreate,
    GrupoCorporativoUpdate,
    GrupoCorporativoOut
)

router = APIRouter()


@router.get("/grupos-corporativos", response_model=List[GrupoCorporativoOut])
async def get_grupos_corporativos(
    skip: int = 0,
    limit: int = 100,
    current_admin = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener lista de grupos corporativos (solo para admins)
    """
    result = await db.execute(
        GrupoCorporativo.__table__.select().offset(skip).limit(limit)
    )
    grupos = [GrupoCorporativo(**row._mapping) for row in result.fetchall()]
    
    return [
        GrupoCorporativoOut(
            id=g.id,
            nombre=g.nombre,
            descripcion=g.descripcion
        ) for g in grupos
    ]


@router.post("/grupos-corporativos", response_model=GrupoCorporativoOut)
async def create_grupo_corporativo(
    grupo_in: GrupoCorporativoCreate,
    current_admin = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Crear un nuevo grupo corporativo
    """
    # Verificar que el nombre no exista
    result = await db.execute(
        GrupoCorporativo.__table__.select().where(GrupoCorporativo.nombre == grupo_in.nombre)
    )
    existing_grupo = result.fetchone()
    
    if existing_grupo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nombre de grupo corporativo ya está en uso"
        )
    
    # Crear el nuevo grupo corporativo
    grupo = GrupoCorporativo(
        id=str(uuid.uuid4()),
        nombre=grupo_in.nombre,
        descripcion=grupo_in.descripcion
    )
    
    db.add(grupo)
    await db.commit()
    await db.refresh(grupo)
    
    return GrupoCorporativoOut(
        id=grupo.id,
        nombre=grupo.nombre,
        descripcion=grupo.descripcion
    )


@router.put("/grupos-corporativos/{grupo_id}", response_model=GrupoCorporativoOut)
async def update_grupo_corporativo(
    grupo_id: str,
    grupo_in: GrupoCorporativoUpdate,
    current_admin = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Actualizar un grupo corporativo existente
    """
    result = await db.execute(
        GrupoCorporativo.__table__.select().where(GrupoCorporativo.id == grupo_id)
    )
    grupo = result.fetchone()
    
    if not grupo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo corporativo no encontrado"
        )
    
    grupo_obj = GrupoCorporativo(**grupo._mapping)
    
    # Actualizar campos
    update_data = grupo_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(grupo_obj, field, value)
    
    await db.commit()
    await db.refresh(grupo_obj)
    
    return GrupoCorporativoOut(
        id=grupo_obj.id,
        nombre=grupo_obj.nombre,
        descripcion=grupo_obj.descripcion
    )


@router.get("/", response_model=List[TenantOut])
async def get_tenants(
    skip: int = 0,
    limit: int = 100,
    current_admin = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener lista de tenants (solo para admins)
    """
    result = await db.execute(Tenant.__table__.select().offset(skip).limit(limit))
    tenants = [Tenant(**row._mapping) for row in result.fetchall()]
    
    return [
        TenantOut(
            id=t.id,
            name=t.name,
            subdomain=t.subdomain,
            schema_name=t.schema_name,
            es_grupo_corporativo=t.es_grupo_corporativo,
            grupo_corporativo_id=t.grupo_corporativo_id,
            is_active=t.is_active,
            contact_email=t.contact_email,
            contact_phone=t.contact_phone,
            descripcion=t.descripcion
        ) for t in tenants
    ]


@router.post("/", response_model=TenantOut)
async def create_tenant(
    tenant_in: TenantCreate,
    current_admin = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Crear un nuevo tenant (empresa/cliente)
    Si se especifica grupo_corporativo_id, la empresa será filial de ese grupo
    """
    # Verificar que el subdomain no exista
    result = await db.execute(
        Tenant.__table__.select().where(Tenant.subdomain == tenant_in.subdomain)
    )
    existing_tenant = result.fetchone()
    
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subdomain ya está en uso"
        )
    
    # Verificar que el schema_name no exista
    result = await db.execute(
        Tenant.__table__.select().where(Tenant.schema_name == tenant_in.schema_name)
    )
    existing_tenant = result.fetchone()
    
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nombre de esquema ya está en uso"
        )
    
    # Si se especifica grupo_corporativo_id, verificar que exista
    if tenant_in.grupo_corporativo_id:
        result = await db.execute(
            GrupoCorporativo.__table__.select().where(
                GrupoCorporativo.id == tenant_in.grupo_corporativo_id
            )
        )
        grupo = result.fetchone()
        
        if not grupo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Grupo corporativo especificado no existe"
            )
    
    # Crear el nuevo tenant
    tenant = Tenant(
        id=str(uuid.uuid4()),
        name=tenant_in.name,
        subdomain=tenant_in.subdomain,
        schema_name=tenant_in.schema_name,
        es_grupo_corporativo=tenant_in.es_grupo_corporativo,
        grupo_corporativo_id=tenant_in.grupo_corporativo_id,
        contact_email=tenant_in.contact_email,
        contact_phone=tenant_in.contact_phone,
        descripcion=tenant_in.descripcion
    )
    
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    
    return TenantOut(
        id=tenant.id,
        name=tenant.name,
        subdomain=tenant.subdomain,
        schema_name=tenant.schema_name,
        es_grupo_corporativo=tenant.es_grupo_corporativo,
        grupo_corporativo_id=tenant.grupo_corporativo_id,
        is_active=tenant.is_active,
        contact_email=tenant.contact_email,
        contact_phone=tenant.contact_phone,
        descripcion=tenant.descripcion
    )


@router.put("/{tenant_id}", response_model=TenantOut)
async def update_tenant(
    tenant_id: str,
    tenant_in: TenantUpdate,
    current_admin = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Actualizar un tenant existente
    """
    result = await db.execute(
        Tenant.__table__.select().where(Tenant.id == tenant_id)
    )
    tenant = result.fetchone()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )
    
    tenant_obj = Tenant(**tenant._mapping)
    
    # Si se cambia el grupo corporativo, verificar que exista
    if tenant_in.grupo_corporativo_id is not None:
        result = await db.execute(
            GrupoCorporativo.__table__.select().where(
                GrupoCorporativo.id == tenant_in.grupo_corporativo_id
            )
        )
        grupo = result.fetchone()
        
        if not grupo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Grupo corporativo especificado no existe"
            )
    
    # Actualizar campos
    update_data = tenant_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant_obj, field, value)
    
    await db.commit()
    await db.refresh(tenant_obj)
    
    return TenantOut(
        id=tenant_obj.id,
        name=tenant_obj.name,
        subdomain=tenant_obj.subdomain,
        schema_name=tenant_obj.schema_name,
        es_grupo_corporativo=tenant_obj.es_grupo_corporativo,
        grupo_corporativo_id=tenant_obj.grupo_corporativo_id,
        is_active=tenant_obj.is_active,
        contact_email=tenant_obj.contact_email,
        contact_phone=tenant_obj.contact_phone,
        descripcion=tenant_obj.descripcion
    )


@router.delete("/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    current_admin = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Eliminar (desactivar) un tenant
    """
    result = await db.execute(
        Tenant.__table__.select().where(Tenant.id == tenant_id)
    )
    tenant = result.fetchone()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )
    
    tenant_obj = Tenant(**tenant._mapping)
    tenant_obj.is_active = False  # Desactivar en lugar de eliminar
    
    await db.commit()
    
    return {"message": "Tenant desactivado exitosamente"}


@router.get("/{tenant_id}/empresas-filiales", response_model=List[TenantOut])
async def get_empresas_filiales(
    tenant_id: str,
    current_admin = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener las empresas filiales de un grupo corporativo
    """
    # Primero verificar que el tenant exista y sea un grupo corporativo
    result = await db.execute(
        Tenant.__table__.select().where(Tenant.id == tenant_id)
    )
    tenant = result.fetchone()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )
    
    tenant_obj = Tenant(**tenant._mapping)
    if not tenant_obj.es_grupo_corporativo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El tenant no es un grupo corporativo"
        )
    
    # Buscar empresas filiales de este grupo
    result = await db.execute(
        Tenant.__table__.select().where(Tenant.grupo_corporativo_id == tenant_id)
    )
    filiales = [Tenant(**row._mapping) for row in result.fetchall()]
    
    return [
        TenantOut(
            id=t.id,
            name=t.name,
            subdomain=t.subdomain,
            schema_name=t.schema_name,
            es_grupo_corporativo=t.es_grupo_corporativo,
            grupo_corporativo_id=t.grupo_corporativo_id,
            is_active=t.is_active,
            contact_email=t.contact_email,
            contact_phone=t.contact_phone,
            descripcion=t.descripcion
        ) for t in filiales
    ]