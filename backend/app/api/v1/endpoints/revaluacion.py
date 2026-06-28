from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date

from app.core.database import get_db
from app.services.revaluacion_service import RevaluacionService
from app.schemas.revaluacion import (
    TipoCambioCreate, TipoCambioResponse,
    RevaluacionAutomaticaCreate, RevaluacionAutomaticaResponse,
    EjecucionRevaluacionResponse,
    ValuacionTipoCambioCreate, ValuacionTipoCambioResponse,
    ParametrosRevaluacionCreate, ParametrosRevaluacionResponse
)

router = APIRouter(prefix="/revaluacion", tags=["Revaluación Cambiaria"])

# --- Tipos de Cambio ---
@router.post("/tipos-cambio", response_model=TipoCambioResponse)
async def registrar_tipo_cambio(
    data: TipoCambioCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Query(..., description="ID del Tenant")
):
    service = RevaluacionService(db)
    return await service.registrar_tipo_cambio(data, tenant_id)

@router.get("/tipos-cambio/vigente")
async def obtener_tipo_cambio_vigente(
    moneda_origen: str = Query(...),
    moneda_destino: str = Query(...),
    fecha: date = Query(...),
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Query(..., description="ID del Tenant")
):
    service = RevaluacionService(db)
    tipo_cambio = await service.obtener_tipo_cambio_vigente(
        moneda_origen, moneda_destino, fecha, tenant_id
    )
    if not tipo_cambio:
        raise HTTPException(status_code=404, detail="Tipo de cambio no encontrado")
    return tipo_cambio

# --- Revaluación Automática ---
@router.post("/configuracion", response_model=RevaluacionAutomaticaResponse)
async def configurar_revaluacion(
    data: RevaluacionAutomaticaCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Query(..., description="ID del Tenant")
):
    service = RevaluacionService(db)
    return await service.configurar_revaluacion(data, tenant_id)

@router.post("/ejecutar/{revaluacion_id}", response_model=EjecucionRevaluacionResponse)
async def ejecutar_revaluacion(
    revaluacion_id: int,
    fecha: date = Query(...),
    db: AsyncSession = Depends(get_db)
):
    service = RevaluacionService(db)
    try:
        return await service.ejecutar_revaluacion(revaluacion_id, fecha)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# --- Valuación de Tipos de Cambio ---
@router.post("/valuaciones", response_model=ValuacionTipoCambioResponse)
async def registrar_valuacion(
    data: ValuacionTipoCambioCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Query(..., description="ID del Tenant")
):
    service = RevaluacionService(db)
    return await service.registrar_valuacion(data, tenant_id)

@router.get("/valuaciones/historial")
async def obtener_historial_valuaciones(
    moneda: str = Query(...),
    fecha_inicio: date = Query(...),
    fecha_fin: date = Query(...),
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Query(..., description="ID del Tenant")
):
    service = RevaluacionService(db)
    return await service.obtener_historial_valuaciones(
        moneda, fecha_inicio, fecha_fin, tenant_id
    )

# --- Parámetros ---
@router.get("/parametros", response_model=Optional[ParametrosRevaluacionResponse])
async def obtener_parametros(
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Query(..., description="ID del Tenant")
):
    service = RevaluacionService(db)
    return await service.obtener_parametros(tenant_id)

@router.put("/parametros", response_model=ParametrosRevaluacionResponse)
async def actualizar_parametros(
    data: ParametrosRevaluacionCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Query(..., description="ID del Tenant")
):
    service = RevaluacionService(db)
    return await service.actualizar_parametros(tenant_id, data)

# --- Reportes ---
@router.get("/reporte/{ejecucion_id}")
async def reporte_revaluacion(
    ejecucion_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = RevaluacionService(db)
    try:
        return await service.reporte_revaluacion(ejecucion_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
