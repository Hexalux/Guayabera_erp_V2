from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from app.api.deps import get_db, get_current_admin
from app.services.contabilidad_service import ContabilidadService
from app.schemas.contabilidad import (
    CuentaContableCreate, CuentaContableUpdate, CuentaContableResponse,
    CentroCostoCreate, CentroCostoResponse,
    PeriodoContableCreate, PeriodoContableResponse,
    AsientoContableCreate, AsientoContableUpdate, AsientoContableResponse,
    FiltroCuentasContables, FiltroAsientosContables,
    ReporteBalanceComprobacion
)
from app.models.admin import Admin

router = APIRouter()


# ==================== CUENTAS CONTABLES ====================

@router.post("/cuentas", response_model=CuentaContableResponse, status_code=status.HTTP_201_CREATED)
async def crear_cuenta(
    cuenta_data: CuentaContableCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_admin),
    tenant_id: int = 1
):
    """Crear una nueva cuenta contable"""
    service = ContabilidadService(db)
    try:
        cuenta = await service.crear_cuenta(cuenta_data, tenant_id, current_user.id)
        return cuenta
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/cuentas", response_model=List[CuentaContableResponse])
async def listar_cuentas(
    tipo_cuenta: Optional[str] = None,
    es_activa: Optional[bool] = None,
    parent_id: Optional[str] = None,
    busca_codigo: Optional[str] = None,
    busca_nombre: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = 1
):
    """Listar cuentas contables con filtros opcionales"""
    service = ContabilidadService(db)
    
    filtro = FiltroCuentasContables(
        tipo_cuenta=tipo_cuenta,
        es_activa=es_activa,
        parent_id=parent_id,
        busca_codigo=busca_codigo,
        busca_nombre=busca_nombre
    ) if any([tipo_cuenta, es_activa is not None, parent_id, busca_codigo, busca_nombre]) else None
    
    cuentas = await service.obtener_cuentas(tenant_id, filtro)
    return cuentas


@router.get("/cuentas/{cuenta_id}", response_model=CuentaContableResponse)
async def obtener_cuenta(
    cuenta_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = 1
):
    """Obtener una cuenta contable por ID"""
    service = ContabilidadService(db)
    cuenta = await service.obtener_cuenta_por_id(cuenta_id, tenant_id)
    
    if not cuenta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")
    
    return cuenta


@router.put("/cuentas/{cuenta_id}", response_model=CuentaContableResponse)
async def actualizar_cuenta(
    cuenta_id: str,
    cuenta_data: CuentaContableUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = 1
):
    """Actualizar una cuenta contable"""
    service = ContabilidadService(db)
    cuenta = await service.actualizar_cuenta(cuenta_id, tenant_id, cuenta_data)
    
    if not cuenta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")
    
    return cuenta


@router.delete("/cuentas/{cuenta_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_cuenta(
    cuenta_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = 1
):
    """Eliminar una cuenta contable (solo si no tiene movimientos)"""
    service = ContabilidadService(db)
    
    try:
        eliminado = await service.eliminar_cuenta(cuenta_id, tenant_id)
        if not eliminado:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== CENTROS DE COSTO ====================

@router.post("/centros-costo", response_model=CentroCostoResponse, status_code=status.HTTP_201_CREATED)
async def crear_centro_costo(
    centro_data: CentroCostoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_admin),
    tenant_id: int = 1
):
    """Crear un nuevo centro de costo"""
    service = ContabilidadService(db)
    try:
        centro = await service.crear_centro_costo(centro_data, tenant_id)
        return centro
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/centros-costo", response_model=List[CentroCostoResponse])
async def listar_centros_costo(
    es_activo: bool = True,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = 1
):
    """Listar centros de costo"""
    service = ContabilidadService(db)
    centros = await service.obtener_centros_costo(tenant_id, es_activo)
    return centros


# ==================== PERÍODOS CONTABLES ====================

@router.post("/periodos", response_model=PeriodoContableResponse, status_code=status.HTTP_201_CREATED)
async def crear_periodo(
    periodo_data: PeriodoContableCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_admin),
    tenant_id: int = 1
):
    """Crear un nuevo período contable"""
    service = ContabilidadService(db)
    periodo = await service.crear_periodo(periodo_data, tenant_id)
    return periodo


@router.get("/periodos", response_model=List[PeriodoContableResponse])
async def listar_periodos(
    db: AsyncSession = Depends(get_db),
    tenant_id: int = 1
):
    """Listar períodos contables"""
    service = ContabilidadService(db)
    periodos = await service.obtener_periodos(tenant_id)
    return periodos


@router.post("/periodos/{periodo_id}/cerrar", response_model=PeriodoContableResponse)
async def cerrar_periodo(
    periodo_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_admin),
    tenant_id: int = 1
):
    """Cerrar un período contable"""
    service = ContabilidadService(db)
    exito = await service.cerrar_periodo(periodo_id, tenant_id, current_user.id)
    
    if not exito:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Período no encontrado")
    
    periodo = await service.db.get(service.db.model_class(PeriodoContable), periodo_id)
    return periodo


# ==================== ASIENTOS CONTABLES ====================

@router.post("/asientos", response_model=AsientoContableResponse, status_code=status.HTTP_201_CREATED)
async def crear_asiento(
    asiento_data: AsientoContableCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_admin),
    tenant_id: int = 1
):
    """Crear un nuevo asiento contable"""
    service = ContabilidadService(db)
    try:
        asiento = await service.crear_asiento(asiento_data, tenant_id, current_user.id)
        return asiento
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/asientos", response_model=List[AsientoContableResponse])
async def listar_asientos(
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    periodo_id: Optional[str] = None,
    estado: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = 1
):
    """Listar asientos contables con filtros"""
    service = ContabilidadService(db)
    
    filtro = FiltroAsientosContables(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        periodo_id=periodo_id,
        estado=estado
    ) if any([fecha_desde, fecha_hasta, periodo_id, estado]) else None
    
    asientos = await service.obtener_asientos(tenant_id, filtro)
    return asientos


@router.get("/asientos/{asiento_id}", response_model=AsientoContableResponse)
async def obtener_asiento(
    asiento_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = 1
):
    """Obtener un asiento contable por ID"""
    service = ContabilidadService(db)
    asiento = await service.obtener_asiento_por_id(asiento_id, tenant_id)
    
    if not asiento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asiento no encontrado")
    
    return asiento


@router.post("/asientos/{asiento_id}/registrar", response_model=AsientoContableResponse)
async def registrar_asiento(
    asiento_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_admin),
    tenant_id: int = 1
):
    """Registrar un asiento contable"""
    service = ContabilidadService(db)
    asiento = await service.registrar_asiento(asiento_id, tenant_id, current_user.id)
    
    if not asiento:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo registrar el asiento")
    
    return asiento


@router.post("/asientos/{asiento_id}/anular", response_model=AsientoContableResponse)
async def anular_asiento(
    asiento_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_admin),
    tenant_id: int = 1
):
    """Anular un asiento contable registrado"""
    service = ContabilidadService(db)
    asiento = await service.anular_asiento(asiento_id, tenant_id, current_user.id)
    
    if not asiento:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo anular el asiento")
    
    return asiento


# ==================== REPORTES ====================

@router.get("/reportes/balance-comprobacion", response_model=ReporteBalanceComprobacion)
async def obtener_balance_comprobacion(
    fecha_desde: datetime,
    fecha_hasta: datetime,
    periodo_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = 1
):
    """Generar reporte de balance de comprobación"""
    service = ContabilidadService(db)
    
    try:
        resultado = await service.obtener_balance_comprobacion(
            tenant_id, fecha_desde, fecha_hasta, periodo_id
        )
        return ReporteBalanceComprobacion(**resultado)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
