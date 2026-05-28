from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid
from datetime import datetime

from app.core.database import get_db
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.api.deps import get_current_user
from app.schemas.operaciones_filiales import (
    OperacionFilialCreate,
    OperacionFilialUpdate,
    OperacionFilialOut,
    TipoOperacion
)

router = APIRouter()


class OperacionFilial:
    """
    Modelo para representar operaciones entre empresas filiales
    """
    def __init__(self, id=None, tipo_operacion=None, tenant_origen_id=None, 
                 tenant_destino_id=None, descripcion=None, monto=None, 
                 fecha_operacion=None, estado=None, created_at=None):
        self.id = id or str(uuid.uuid4())
        self.tipo_operacion = tipo_operacion
        self.tenant_origen_id = tenant_origen_id
        self.tenant_destino_id = tenant_destino_id
        self.descripcion = descripcion
        self.monto = monto
        self.fecha_operacion = fecha_operacion or datetime.utcnow()
        self.estado = estado or 'pendiente'
        self.created_at = created_at or datetime.utcnow()


@router.post("/", response_model=OperacionFilialOut)
async def crear_operacion_filial(
    operacion: OperacionFilialCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Crear una nueva operación entre empresas filiales del mismo grupo
    """
    # Verificar que los tenants existan
    origen_result = await db.execute(
        Tenant.__table__.select().where(Tenant.id == operacion.tenant_origen_id)
    )
    origen_tenant = origen_result.fetchone()
    
    destino_result = await db.execute(
        Tenant.__table__.select().where(Tenant.id == operacion.tenant_destino_id)
    )
    destino_tenant = destino_result.fetchone()
    
    if not origen_tenant or not destino_tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uno o ambos tenants no existen"
        )
    
    origen = Tenant(**origen_tenant._mapping)
    destino = Tenant(**destino_tenant._mapping)
    
    # Verificar que ambos pertenezcan al mismo grupo corporativo
    if not origen.grupo_corporativo_id or not destino.grupo_corporativo_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ambas empresas deben pertenecer a un grupo corporativo para realizar operaciones entre sí"
        )
    
    if origen.grupo_corporativo_id != destino.grupo_corporativo_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Las empresas deben pertenecer al mismo grupo corporativo para realizar operaciones entre sí"
        )
    
    # Crear la operación
    operacion_obj = OperacionFilial(
        tipo_operacion=operacion.tipo_operacion,
        tenant_origen_id=operacion.tenant_origen_id,
        tenant_destino_id=operacion.tenant_destino_id,
        descripcion=operacion.descripcion,
        monto=operacion.monto,
        fecha_operacion=operacion.fecha_operacion
    )
    
    # Aquí iría la lógica para registrar la operación en la base de datos
    # Por ahora simulamos guardando en memoria (esto debería cambiarse a una tabla real)
    
    return OperacionFilialOut(
        id=operacion_obj.id,
        tipo_operacion=operacion_obj.tipo_operacion,
        tenant_origen_id=operacion_obj.tenant_origen_id,
        tenant_destino_id=operacion_obj.tenant_destino_id,
        descripcion=operacion_obj.descripcion,
        monto=operacion_obj.monto,
        fecha_operacion=operacion_obj.fecha_operacion,
        estado=operacion_obj.estado
    )


@router.get("/", response_model=List[OperacionFilialOut])
async def obtener_operaciones_filiales(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener lista de operaciones entre empresas filiales
    """
    # Esta implementación es solo un placeholder
    # En una implementación real, esto consultaría una tabla de operaciones
    return []


@router.get("/{operacion_id}", response_model=OperacionFilialOut)
async def obtener_operacion_filial(
    operacion_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener una operación específica entre empresas filiales
    """
    # Esta implementación es solo un placeholder
    # En una implementación real, esto consultaría una tabla de operaciones
    return OperacionFilialOut(
        id=operacion_id,
        tipo_operacion=TipoOperacion.CONSIGNA,
        tenant_origen_id="",
        tenant_destino_id="",
        descripcion="",
        monto=0.0,
        fecha_operacion=datetime.utcnow(),
        estado="completada"
    )


@router.put("/{operacion_id}", response_model=OperacionFilialOut)
async def actualizar_operacion_filial(
    operacion_id: str,
    operacion_update: OperacionFilialUpdate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Actualizar una operación entre empresas filiales
    """
    # Esta implementación es solo un placeholder
    # En una implementación real, esto actualizaría un registro en una tabla de operaciones
    return OperacionFilialOut(
        id=operacion_id,
        tipo_operacion=TipoOperacion.CONSIGNA,
        tenant_origen_id="",
        tenant_destino_id="",
        descripcion=operacion_update.descripcion or "",
        monto=operacion_update.monto or 0.0,
        fecha_operacion=datetime.utcnow(),
        estado=operacion_update.estado or "completada"
    )