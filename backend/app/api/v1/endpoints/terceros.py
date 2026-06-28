"""
API de Terceros Unificados
Gestión de Clientes, Proveedores, Empleados y Otros
Fusión de CONTPAQi (robustez), Odoo (flexibilidad), Management Pro (opciones)
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.services.terceros_service import TerceroService
from app.schemas.terceros import (
    TerceroCreate, TerceroUpdate, TerceroResponse, TerceroFiltro,
    ClienteCreate, ProveedorCreate, ResumenTerceroReporte
)
from app.models.usuario import Usuario
from app.core.security import get_current_active_user
from app.core.dependencies import get_tenant_id, get_current_user

router = APIRouter(prefix="/terceros", tags=["Terceros"])


@router.post("/", response_model=TerceroResponse, status_code=status.HTTP_201_CREATED)
async def crear_tercero(
    data: TerceroCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    usuario: Usuario = Depends(get_current_active_user)
):
    """
    Crear un nuevo tercero (Cliente, Proveedor, Empleado, etc.)
    
    - **tipo_tercero**: Tipo de tercero (cliente, proveedor, empleado, etc.)
    - **identificación**: Número de documento (RUC, cédula, pasaporte)
    - **razón_social**: Nombre completo o razón social
    - **límite_credito**: Límite de crédito opcional
    - **dias_plazo**: Días de plazo para pago
    """
    service = TerceroService(db)
    try:
        tercero = await service.crear_tercero(
            data=data,
            tenant_id=tenant_id,
            usuario_id=usuario.id
        )
        return tercero
    except Exception as e:
        if "Ya existe" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[TerceroResponse])
async def listar_terceros(
    tipo_tercero: Optional[str] = Query(None, description="Filtrar por tipo de tercero"),
    identificacion: Optional[str] = Query(None, description="Buscar por identificación"),
    razon_social: Optional[str] = Query(None, description="Buscar por razón social"),
    activo: Optional[bool] = Query(True, description="Solo activos"),
    limite: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Listar terceros con filtros opcionales
    
    - **tipo_tercero**: cliente, proveedor, empleado, accionista, otro
    - **identificacion**: Filtrar por número de documento
    - **razon_social**: Buscar por nombre o razón social
    - **activo**: Mostrar solo terceros activos (default: True)
    """
    filtro = TerceroFiltro(
        tipo_tercero=tipo_tercero,
        identificacion=identificacion,
        razon_social=razon_social,
        activo=activo
    )
    
    service = TerceroService(db)
    terceros = await service.listar_terceros(
        filtro=filtro,
        tenant_id=tenant_id,
        limite=limite,
        offset=offset
    )
    return terceros


@router.get("/{tercero_id}", response_model=TerceroResponse)
async def obtener_tercero(
    tercero_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Obtener detalles de un tercero específico"""
    service = TerceroService(db)
    try:
        tercero = await service.obtener_tercero(tercero_id, tenant_id)
        return tercero
    except Exception as e:
        if "no encontrado" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{tercero_id}", response_model=TerceroResponse)
async def actualizar_tercero(
    tercero_id: UUID,
    data: TerceroUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    usuario: Usuario = Depends(get_current_active_user)
):
    """
    Actualizar información de un tercero
    
    Solo se actualizan los campos proporcionados
    """
    service = TerceroService(db)
    try:
        tercero = await service.actualizar_tercero(
            tercero_id=tercero_id,
            data=data,
            tenant_id=tenant_id,
            usuario_id=usuario.id
        )
        return tercero
    except Exception as e:
        if "no encontrado" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{tercero_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_tercero(
    tercero_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    usuario: Usuario = Depends(get_current_active_user)
):
    """
    Eliminar lógico de un tercero (soft delete)
    
    No se puede eliminar si tiene saldo pendiente
    """
    service = TerceroService(db)
    try:
        await service.eliminar_tercero(
            tercero_id=tercero_id,
            tenant_id=tenant_id,
            usuario_id=usuario.id
        )
    except Exception as e:
        if "no encontrado" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        if "saldo" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{tercero_id}/resumen-cartera", response_model=ResumenTerceroReporte)
async def obtener_resumen_cartera(
    tercero_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Obtener resumen de cartera del tercero
    
    Incluye saldos pendientes, vencidos y disponible de crédito
    """
    service = TerceroService(db)
    try:
        resumen = await service.obtener_resumen_cartera(tercero_id, tenant_id)
        return resumen
    except Exception as e:
        if "no encontrado" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/buscar/{identificacion}", response_model=TerceroResponse)
async def buscar_por_identificacion(
    identificacion: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Buscar tercero por número de identificación
    
    Útil para validación rápida en facturación
    """
    service = TerceroService(db)
    tercero = await service.buscar_por_identificacion(identificacion, tenant_id)
    
    if not tercero:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró tercero con identificación {identificacion}"
        )
    
    return tercero


# ==================== ENDPOINTS ESPECÍFICOS ====================

@router.post("/clientes", response_model=TerceroResponse, status_code=status.HTTP_201_CREATED)
async def crear_cliente(
    data: ClienteCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    usuario: Usuario = Depends(get_current_active_user)
):
    """Crear cliente directamente (tipo_tercero ya es 'cliente')"""
    service = TerceroService(db)
    tercero = await service.crear_tercero(
        data=data,
        tenant_id=tenant_id,
        usuario_id=usuario.id
    )
    return tercero


@router.post("/proveedores", response_model=TerceroResponse, status_code=status.HTTP_201_CREATED)
async def crear_proveedor(
    data: ProveedorCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    usuario: Usuario = Depends(get_current_active_user)
):
    """Crear proveedor directamente (tipo_tercero ya es 'proveedor')"""
    service = TerceroService(db)
    tercero = await service.crear_tercero(
        data=data,
        tenant_id=tenant_id,
        usuario_id=usuario.id
    )
    return tercero
