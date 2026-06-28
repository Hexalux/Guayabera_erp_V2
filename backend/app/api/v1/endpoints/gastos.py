from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date

from app.core.database import get_db
from app.services.gastos_service import GastosService
from app.schemas.gastos import (
    CategoriaGastoCreate, CategoriaGastoResponse,
    GastoCreate, GastoResponse, GastoUpdate,
    GastoViajeCreate, GastoViajeResponse,
    GastoViajeDetalleCreate, GastoViajeDetalleResponse,
    NominaGastoCreate, NominaGastoResponse,
    DepreciacionActivoCreate, DepreciacionActivoResponse,
    PresupuestoGastoCreate, PresupuestoGastoResponse
)

router = APIRouter(prefix="/gastos", tags=["Control de Gastos"])

# --- Categorías ---
@router.post("/categorias", response_model=CategoriaGastoResponse)
async def crear_categoria(
    data: CategoriaGastoCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Query(..., description="ID del Tenant")
):
    service = GastosService(db)
    return await service.crear_categoria(data, tenant_id)

@router.get("/categorias", response_model=List[CategoriaGastoResponse])
async def listar_categorias(
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Query(..., description="ID del Tenant"),
    activo: bool = True
):
    service = GastosService(db)
    return await service.obtener_categorias(tenant_id, activo)

# --- Gastos ---
@router.post("/", response_model=GastoResponse)
async def registrar_gasto(
    data: GastoCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Query(..., description="ID del Tenant"),
    usuario_id: int = Query(1, description="ID del Usuario")  # Temporal
):
    service = GastosService(db)
    return await service.registrar_gasto(data, tenant_id, usuario_id)

@router.put("/{gasto_id}/aprobar", response_model=GastoResponse)
async def aprobar_gasto(
    gasto_id: int,
    db: AsyncSession = Depends(get_db),
    usuario_id: int = Query(1, description="ID del Usuario")
):
    service = GastosService(db)
    try:
        return await service.aprobar_gasto(gasto_id, usuario_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# --- Gastos de Viaje ---
@router.post("/viajes", response_model=GastoViajeResponse)
async def crear_gasto_viaje(
    data: GastoViajeCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Query(..., description="ID del Tenant")
):
    service = GastosService(db)
    return await service.crear_gasto_viaje(data, tenant_id)

@router.post("/viajes/detalles", response_model=GastoViajeDetalleResponse)
async def agregar_detalle_viaje(
    data: GastoViajeDetalleCreate,
    db: AsyncSession = Depends(get_db)
):
    service = GastosService(db)
    return await service.agregar_detalle_viaje(data)

# --- Nómina ---
@router.post("/nomina", response_model=NominaGastoResponse)
async def registrar_nomina(
    data: NominaGastoCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Query(..., description="ID del Tenant")
):
    service = GastosService(db)
    return await service.registrar_nomina(data, tenant_id)

# --- Depreciación ---
@router.post("/depreciacion", response_model=DepreciacionActivoResponse)
async def registrar_depreciacion(
    data: DepreciacionActivoCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Query(..., description="ID del Tenant")
):
    service = GastosService(db)
    return await service.registrar_depreciacion(data, tenant_id)

@router.get("/depreciacion/{activo_id}/calcular")
async def calcular_depreciacion(
    activo_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = GastosService(db)
    try:
        monto = await service.calcular_depreciacion_mensual(activo_id)
        return {"activo_id": activo_id, "depreciacion_mensual": monto}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# --- Presupuesto ---
@router.post("/presupuesto", response_model=PresupuestoGastoResponse)
async def crear_presupuesto(
    data: PresupuestoGastoCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Query(..., description="ID del Tenant")
):
    service = GastosService(db)
    return await service.crear_presupuesto(data, tenant_id)

# --- Reportes ---
@router.get("/reportes/analitico")
async def reporte_analitico_gastos(
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Query(..., description="ID del Tenant"),
    fecha_inicio: date = Query(...),
    fecha_fin: date = Query(...),
    categoria_id: Optional[int] = None
):
    service = GastosService(db)
    return await service.obtener_reporte_gastos(tenant_id, fecha_inicio, fecha_fin, categoria_id)
