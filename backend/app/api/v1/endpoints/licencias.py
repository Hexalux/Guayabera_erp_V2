from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime, timedelta
import uuid
import secrets
import string

from app.core.database import get_db
from app.models.licencia import Licencia, TipoLicencia
from app.models.admin import Admin
from app.models.tenant import Tenant
from app.api.deps import get_current_admin_user
from app.schemas.licencia import (
    TipoLicenciaCreate,
    TipoLicenciaUpdate,
    TipoLicenciaOut,
    LicenciaCreate,
    LicenciaUpdate,
    LicenciaOut,
    CompraLicenciaRequest
)

router = APIRouter()


def generar_codigo_licencia(longitud: int = 16) -> str:
    """Genera un código único para la licencia"""
    caracteres = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(caracteres) for _ in range(longitud))


@router.get("/tipos-licencia", response_model=List[TipoLicenciaOut])
async def get_tipos_licencia(
    skip: int = 0,
    limit: int = 100,
    current_admin = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener lista de tipos de licencia (solo para admins)
    """
    from sqlalchemy import select
    result = await db.execute(
        select(TipoLicencia).offset(skip).limit(limit)
    )
    tipos_licencia = result.scalars().all()
    
    return [
        TipoLicenciaOut(
            id=t.id,
            nombre=t.nombre,
            descripcion=t.descripcion,
            duracion_dias=t.duracion_dias,
            precio=t.precio,
            es_prueba=t.es_prueba
        ) for t in tipos_licencia
    ]


@router.post("/tipos-licencia", response_model=TipoLicenciaOut)
async def create_tipo_licencia(
    tipo_licencia_in: TipoLicenciaCreate,
    current_admin = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Crear un nuevo tipo de licencia
    """
    # Verificar que no exista un tipo de licencia con el mismo nombre
    from sqlalchemy import select
    result = await db.execute(
        select(TipoLicencia).where(TipoLicencia.nombre == tipo_licencia_in.nombre)
    )
    existing_tipo = result.scalar_one_or_none()
    
    if existing_tipo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un tipo de licencia con ese nombre"
        )
    
    # Crear el nuevo tipo de licencia
    tipo_licencia = TipoLicencia(
        nombre=tipo_licencia_in.nombre,
        descripcion=tipo_licencia_in.descripcion,
        duracion_dias=tipo_licencia_in.duracion_dias,
        precio=tipo_licencia_in.precio,
        es_prueba=tipo_licencia_in.es_prueba
    )
    
    db.add(tipo_licencia)
    await db.commit()
    await db.refresh(tipo_licencia)
    
    return TipoLicenciaOut(
        id=tipo_licencia.id,
        nombre=tipo_licencia.nombre,
        descripcion=tipo_licencia.descripcion,
        duracion_dias=tipo_licencia.duracion_dias,
        precio=tipo_licencia.precio,
        es_prueba=tipo_licencia.es_prueba
    )


@router.put("/tipos-licencia/{tipo_licencia_id}", response_model=TipoLicenciaOut)
async def update_tipo_licencia(
    tipo_licencia_id: str,
    tipo_licencia_in: TipoLicenciaUpdate,
    current_admin = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Actualizar un tipo de licencia existente
    """
    from sqlalchemy import select
    result = await db.execute(
        select(TipoLicencia).where(TipoLicencia.id == tipo_licencia_id)
    )
    tipo_licencia = result.scalar_one_or_none()
    
    if not tipo_licencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de licencia no encontrado"
        )
    
    # Actualizar campos
    update_data = tipo_licencia_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tipo_licencia, field, value)
    
    await db.commit()
    await db.refresh(tipo_licencia)
    
    return TipoLicenciaOut(
        id=tipo_licencia.id,
        nombre=tipo_licencia.nombre,
        descripcion=tipo_licencia.descripcion,
        duracion_dias=tipo_licencia.duracion_dias,
        precio=tipo_licencia.precio,
        es_prueba=tipo_licencia.es_prueba
    )


@router.get("/licencias", response_model=List[LicenciaOut])
async def get_licencias(
    skip: int = 0,
    limit: int = 100,
    current_admin = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener lista de licencias (solo para admins)
    """
    from sqlalchemy import select
    result = await db.execute(
        select(Licencia).offset(skip).limit(limit)
    )
    licencias = result.scalars().all()
    
    return [
        LicenciaOut(
            id=l.id,
            tenant_id=l.tenant_id,
            tipo_licencia_id=l.tipo_licencia_id,
            codigo=l.codigo,
            fecha_inicio=l.fecha_inicio,
            fecha_fin=l.fecha_fin,
            activa=l.activa,
            usada=l.usada,
            notas=l.notas
        ) for l in licencias
    ]


@router.post("/licencias", response_model=LicenciaOut)
async def create_licencia(
    licencia_in: LicenciaCreate,
    current_admin = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Crear una nueva licencia
    """
    from sqlalchemy import select
    
    # Verificar que el tenant exista
    tenant_result = await db.execute(
        select(Tenant).where(Tenant.id == licencia_in.tenant_id)
    )
    tenant = tenant_result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )
    
    # Verificar que el tipo de licencia exista
    tipo_result = await db.execute(
        select(TipoLicencia).where(TipoLicencia.id == licencia_in.tipo_licencia_id)
    )
    tipo_licencia = tipo_result.scalar_one_or_none()
    
    if not tipo_licencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de licencia no encontrado"
        )
    
    # Generar código único para la licencia
    codigo = generar_codigo_licencia()
    
    # Calcular fecha de finalización basada en la duración del tipo de licencia
    fecha_inicio = datetime.utcnow()
    fecha_fin = fecha_inicio + timedelta(days=tipo_licencia.duracion_dias)
    
    # Crear la nueva licencia
    licencia = Licencia(
        tenant_id=licencia_in.tenant_id,
        tipo_licencia_id=licencia_in.tipo_licencia_id,
        codigo=codigo,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        activa=True,
        usada=False,
        notas=licencia_in.notas
    )
    
    db.add(licencia)
    await db.commit()
    await db.refresh(licencia)
    
    return LicenciaOut(
        id=licencia.id,
        tenant_id=licencia.tenant_id,
        tipo_licencia_id=licencia.tipo_licencia_id,
        codigo=licencia.codigo,
        fecha_inicio=licencia.fecha_inicio,
        fecha_fin=licencia.fecha_fin,
        activa=licencia.activa,
        usada=licencia.usada,
        notas=licencia.notas
    )


@router.put("/licencias/{licencia_id}", response_model=LicenciaOut)
async def update_licencia(
    licencia_id: str,
    licencia_in: LicenciaUpdate,
    current_admin = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Actualizar una licencia existente
    """
    from sqlalchemy import select
    result = await db.execute(
        select(Licencia).where(Licencia.id == licencia_id)
    )
    licencia = result.scalar_one_or_none()
    
    if not licencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Licencia no encontrada"
        )
    
    # Actualizar campos
    update_data = licencia_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(licencia, field, value)
    
    await db.commit()
    await db.refresh(licencia)
    
    return LicenciaOut(
        id=licencia.id,
        tenant_id=licencia.tenant_id,
        tipo_licencia_id=licencia.tipo_licencia_id,
        codigo=licencia.codigo,
        fecha_inicio=licencia.fecha_inicio,
        fecha_fin=licencia.fecha_fin,
        activa=licencia.activa,
        usada=licencia.usada,
        notas=licencia.notas
    )


@router.post("/comprar-licencia")
async def comprar_licencia(
    compra_request: CompraLicenciaRequest,
    current_admin = Depends(get_current_admin_user),  # Temporalmente solo admin puede comprar licencias
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para comprar licencias
    En una implementación completa, este endpoint estaría protegido por diferentes permisos
    y tendría integración con un sistema de pagos
    """
    from sqlalchemy import select
    
    # Verificar que el tenant exista
    tenant_result = await db.execute(
        select(Tenant).where(Tenant.id == compra_request.tenant_id)
    )
    tenant = tenant_result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )
    
    # Verificar que el tipo de licencia exista
    tipo_result = await db.execute(
        select(TipoLicencia).where(TipoLicencia.id == compra_request.tipo_licencia_id)
    )
    tipo_licencia = tipo_result.scalar_one_or_none()
    
    if not tipo_licencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de licencia no encontrado"
        )
    
    # En una implementación completa, aquí iría la lógica de procesamiento de pago
    # Por ahora, simplemente creamos las licencias solicitadas
    
    licencias_creadas = []
    for i in range(compra_request.cantidad):
        # Generar código único para la licencia
        codigo = generar_codigo_licencia()
        
        # Calcular fecha de finalización basada en la duración del tipo de licencia
        fecha_inicio = datetime.utcnow()
        fecha_fin = fecha_inicio + timedelta(days=tipo_licencia.duracion_dias)
        
        # Crear la nueva licencia
        licencia = Licencia(
            tenant_id=compra_request.tenant_id,
            tipo_licencia_id=compra_request.tipo_licencia_id,
            codigo=codigo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            activa=True,  # Activar inmediatamente después del pago
            usada=False,
            notas=f"Licencia adquirida el {fecha_inicio.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        db.add(licencia)
        licencias_creadas.append(licencia)
    
    await db.commit()
    
    # Refrescar las licencias creadas para obtener sus IDs
    for licencia in licencias_creadas:
        await db.refresh(licencia)
    
    codigos = [licencia.codigo for licencia in licencias_creadas]
    
    return {
        "mensaje": f"{compra_request.cantidad} licencia(s) adquirida(s) exitosamente",
        "codigos_licencia": codigos,
        "detalle": [
            LicenciaOut(
                id=l.id,
                tenant_id=l.tenant_id,
                tipo_licencia_id=l.tipo_licencia_id,
                codigo=l.codigo,
                fecha_inicio=l.fecha_inicio,
                fecha_fin=l.fecha_fin,
                activa=l.activa,
                usada=l.usada,
                notas=l.notas
            ) for l in licencias_creadas
        ]
    }


@router.get("/licencias-tenant/{tenant_id}", response_model=List[LicenciaOut])
async def get_licencias_tenant(
    tenant_id: str,
    current_admin = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener licencias de un tenant específico
    """
    from sqlalchemy import select
    result = await db.execute(
        select(Licencia).where(Licencia.tenant_id == tenant_id)
    )
    licencias = result.scalars().all()
    
    return [
        LicenciaOut(
            id=l.id,
            tenant_id=l.tenant_id,
            tipo_licencia_id=l.tipo_licencia_id,
            codigo=l.codigo,
            fecha_inicio=l.fecha_inicio,
            fecha_fin=l.fecha_fin,
            activa=l.activa,
            usada=l.usada,
            notas=l.notas
        ) for l in licencias
    ]