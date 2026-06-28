from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date

from app.core.database import get_db
from app.services.cxp_service import CXPService
from app.schemas.cxp import (
    ProveedorCreate, ProveedorResponse, ProveedorUpdate,
    FacturaProveedorCreate, FacturaProveedorResponse,
    PagoProveedorCreate, PagoProveedorResponse,
    NotaCreditoProveedorCreate, NotaCreditoProveedorResponse,
    RetencionProveedorCreate, RetencionProveedorResponse
)

router = APIRouter(prefix="/cxp", tags=["Cuentas por Pagar"])

@router.post("/proveedores", response_model=ProveedorResponse)
async def crear_proveedor(
    data: ProveedorCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Query(..., description="ID del Tenant")
):
    service = CXPService(db)
    return await service.crear_proveedor(data, tenant_id)

@router.get("/proveedores", response_model=List[ProveedorResponse])
async def listar_proveedores(
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Query(..., description="ID del Tenant"),
    activo: bool = True
):
    service = CXPService(db)
    return await service.obtener_proveedores(tenant_id, activo)

@router.post("/facturas", response_model=FacturaProveedorResponse)
async def registrar_factura(
    data: FacturaProveedorCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Query(..., description="ID del Tenant")
):
    service = CXPService(db)
    try:
        return await service.registrar_factura(data, tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/pagos", response_model=PagoProveedorResponse)
async def registrar_pago(
    data: PagoProveedorCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Query(..., description="ID del Tenant")
):
    service = CXPService(db)
    return await service.registrar_pago(data, tenant_id)

@router.post("/notas-credito", response_model=NotaCreditoProveedorResponse)
async def registrar_nota_credito(
    data: NotaCreditoProveedorCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Query(..., description="ID del Tenant")
):
    service = CXPService(db)
    return await service.registrar_nota_credito(data, tenant_id)

@router.post("/retenciones", response_model=RetencionProveedorResponse)
async def registrar_retencion(
    data: RetencionProveedorCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Query(..., description="ID del Tenant")
):
    service = CXPService(db)
    return await service.registrar_retencion(data, tenant_id)

@router.get("/reportes/cuentas-por-pagar")
async def reporte_cuentas_por_pagar(
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Query(..., description="ID del Tenant"),
    fecha_corte: Optional[date] = None
):
    service = CXPService(db)
    return await service.obtener_cuentas_por_pagar(tenant_id, fecha_corte)
