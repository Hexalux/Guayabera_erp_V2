"""
Endpoints API para el módulo de Tesorería - Caja
Inspirado en CONTPAQi (robustez), Odoo (flexibilidad) y Management Pro (opciones)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime

from app.core.database import get_db
from app.services.tesoreria.caja_service import (
    CajaService, ReciboCajaService, LiquidacionSucursalService,
    LiquidacionVendedorService, RecepcionValoresService,
    ArqueoCajaService, CorteCajaService
)
from app.schemas.tesoreria.caja import (
    CajaCreate, CajaResponse, CajaUpdate,
    ReciboCajaCreate, ReciboCajaResponse, ReciboCajaAnular,
    LiquidacionSucursalCreate, LiquidacionSucursalResponse,
    LiquidacionVendedorCreate, LiquidacionVendedorResponse,
    RecepcionValoresCreate, RecepcionValoresResponse,
    ArqueoCajaCreate, ArqueoCajaResponse, ArqueoCajaCerrar,
    CorteCajaCreate, CorteCajaFinalizar, CorteCajaResponse
)

router = APIRouter(prefix="/caja", tags=["Tesorería - Caja"])


# ==================== CAJAS ====================

@router.post("/cajas", response_model=CajaResponse, status_code=status.HTTP_201_CREATED)
async def crear_caja(
    caja_data: CajaCreate,
    db: AsyncSession = Depends(get_db)
):
    """Crear una nueva caja/punto de venta"""
    return await CajaService.crear_caja(
        db=db,
        tenant_id=caja_data.tenant_id,
        nombre=caja_data.nombre,
        codigo=caja_data.codigo,
        sucursal_id=caja_data.sucursal_id,
        responsable_id=caja_data.responsable_id,
        moneda=caja_data.moneda,
        activo=caja_data.activo
    )


@router.get("/cajas", response_model=List[CajaResponse])
async def listar_cajas(
    tenant_id: UUID = Query(...),
    sucursal_id: Optional[UUID] = None,
    activo: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """Listar todas las cajas filtradas"""
    return await CajaService.obtener_cajas(
        db=db,
        tenant_id=tenant_id,
        sucursal_id=sucursal_id,
        activo=activo
    )


@router.get("/cajas/{caja_id}", response_model=CajaResponse)
async def obtener_caja(caja_id: UUID, db: AsyncSession = Depends(get_db)):
    """Obtener detalles de una caja"""
    from sqlalchemy.future import select
    from app.models.tesoreria.caja import Caja
    
    result = await db.execute(select(Caja).where(Caja.id == caja_id))
    caja = result.scalar_one_or_none()
    if not caja:
        raise HTTPException(status_code=404, detail="Caja no encontrada")
    return caja


# ==================== RECIBOS DE CAJA ====================

@router.post("/recibos", response_model=ReciboCajaResponse, status_code=status.HTTP_201_CREATED)
async def crear_recibo_caja(
    recibo_data: ReciboCajaCreate,
    db: AsyncSession = Depends(get_db)
):
    """Crear recibo de caja con numeración automática"""
    return await ReciboCajaService.crear_recibo(
        db=db,
        tenant_id=recibo_data.tenant_id,
        caja_id=recibo_data.caja_id,
        serie=recibo_data.serie,
        cliente_id=recibo_data.cliente_id,
        concepto=recibo_data.concepto,
        monto=recibo_data.monto,
        forma_pago=recibo_data.forma_pago,
        referencia=recibo_data.referencia,
        aplicar_a_cxc=recibo_data.aplicar_a_cxc,
        factura_id=recibo_data.factura_id
    )


@router.post("/recibos/{recibo_id}/anular", response_model=ReciboCajaResponse)
async def anular_recibo_caja(
    recibo_id: UUID,
    anulacion_data: ReciboCajaAnular,
    db: AsyncSession = Depends(get_db)
):
    """Anular recibo de caja"""
    return await ReciboCajaService.anular_recibo(
        db=db,
        recibo_id=recibo_id,
        motivo=anulacion_data.motivo,
        usuario_id=anulacion_data.usuario_id
    )


@router.post("/recibos/depositar")
async def depositar_recibos(
    caja_id: UUID,
    banco_id: UUID,
    recibos_ids: List[UUID],
    numero_deposito: str,
    fecha_deposito: date,
    tenant_id: UUID,
    usuario_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Depositar múltiples recibos de caja al banco"""
    return await ReciboCajaService.depositar_recibos(
        db=db,
        tenant_id=tenant_id,
        caja_id=caja_id,
        banco_id=banco_id,
        recibos_ids=recibos_ids,
        numero_deposito=numero_deposito,
        fecha_deposito=fecha_deposito,
        usuario_id=usuario_id
    )


@router.get("/recibos", response_model=List[ReciboCajaResponse])
async def listar_recibos(
    tenant_id: UUID = Query(...),
    caja_id: Optional[UUID] = None,
    serie: Optional[str] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    db: AsyncSession = Depends(get_db)
):
    """Listar recibos de caja con filtros"""
    from sqlalchemy.future import select
    from app.models.tesoreria.caja import ReciboCaja
    
    query = select(ReciboCaja).where(ReciboCaja.tenant_id == tenant_id)
    
    if caja_id:
        query = query.where(ReciboCaja.caja_id == caja_id)
    if serie:
        query = query.where(ReciboCaja.serie == serie)
    if estado:
        query = query.where(ReciboCaja.estado == estado)
    if fecha_desde:
        query = query.where(ReciboCaja.fecha_emision >= fecha_desde)
    if fecha_hasta:
        query = query.where(ReciboCaja.fecha_emision <= fecha_hasta)
    
    query = query.order_by(ReciboCaja.fecha_emision.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


# ==================== LIQUIDACIÓN SUCURSAL ====================

@router.post("/liquidaciones/sucursal", response_model=LiquidacionSucursalResponse, status_code=status.HTTP_201_CREATED)
async def crear_liquidacion_sucursal(
    liquidacion_data: LiquidacionSucursalCreate,
    db: AsyncSession = Depends(get_db)
):
    """Crear liquidación diaria de sucursal"""
    return await LiquidacionSucursalService.crear_liquidacion(
        db=db,
        tenant_id=liquidacion_data.tenant_id,
        sucursal_id=liquidacion_data.sucursal_id,
        fecha=liquidacion_data.fecha,
        usuario_id=liquidacion_data.usuario_id
    )


@router.post("/liquidaciones/sucursal/{liquidacion_id}/calcular", response_model=LiquidacionSucursalResponse)
async def calcular_liquidacion_sucursal(
    liquidacion_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Calcular totales de liquidación de sucursal"""
    return await LiquidacionSucursalService.calcular_totales(
        db=db,
        liquidacion_id=liquidacion_id
    )


# ==================== LIQUIDACIÓN VENDEDOR ====================

@router.post("/liquidaciones/vendedor", response_model=LiquidacionVendedorResponse, status_code=status.HTTP_201_CREATED)
async def crear_liquidacion_vendedor(
    liquidacion_data: LiquidacionVendedorCreate,
    db: AsyncSession = Depends(get_db)
):
    """Crear liquidación de vendedor con comisiones"""
    return await LiquidacionVendedorService.crear_liquidacion(
        db=db,
        tenant_id=liquidacion_data.tenant_id,
        vendedor_id=liquidacion_data.vendedor_id,
        fecha_inicio=liquidacion_data.fecha_inicio,
        fecha_fin=liquidacion_data.fecha_fin,
        usuario_id=liquidacion_data.usuario_id
    )


@router.post("/liquidaciones/vendedor/{liquidacion_id}/calcular", response_model=LiquidacionVendedorResponse)
async def calcular_liquidacion_vendedor(
    liquidacion_id: UUID,
    porcentaje_comision: float = 0.0,
    db: AsyncSession = Depends(get_db)
):
    """Calcular comisiones de vendedor"""
    return await LiquidacionVendedorService.calcular_comisiones(
        db=db,
        liquidacion_id=liquidacion_id,
        porcentaje_comision=porcentaje_comision
    )


# ==================== RECEPCIÓN DE VALORES ====================

@router.post("/valores", response_model=RecepcionValoresResponse, status_code=status.HTTP_201_CREATED)
async def registrar_valor(
    valor_data: RecepcionValoresCreate,
    db: AsyncSession = Depends(get_db)
):
    """Registrar recepción de valores (cheques, pagarés)"""
    return await RecepcionValoresService.registrar_valor(
        db=db,
        tenant_id=valor_data.tenant_id,
        caja_id=valor_data.caja_id,
        tipo_valor=valor_data.tipo_valor,
        numero=valor_data.numero,
        banco_librador=valor_data.banco_librador,
        monto=valor_data.monto,
        fecha_emision=valor_data.fecha_emision,
        fecha_vencimiento=valor_data.fecha_vencimiento,
        cliente_id=valor_data.cliente_id,
        observations=valor_data.observations
    )


@router.post("/valores/{valor_id}/rebotar", response_model=RecepcionValoresResponse)
async def rebotar_valor(
    valor_id: UUID,
    motivo: str,
    usuario_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Marcar valor como rebotado"""
    return await RecepcionValoresService.rebotar_valor(
        db=db,
        valor_id=valor_id,
        motivo=motivo,
        usuario_id=usuario_id
    )


@router.get("/valores", response_model=List[RecepcionValoresResponse])
async def listar_valores(
    tenant_id: UUID = Query(...),
    caja_id: Optional[UUID] = None,
    tipo_valor: Optional[str] = None,
    estado: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Listar valores recibidos"""
    from sqlalchemy.future import select
    from app.models.tesoreria.caja import RecepcionValores
    
    query = select(RecepcionValores).where(RecepcionValores.tenant_id == tenant_id)
    
    if caja_id:
        query = query.where(RecepcionValores.caja_id == caja_id)
    if tipo_valor:
        query = query.where(RecepcionValores.tipo_valor == tipo_valor)
    if estado:
        query = query.where(RecepcionValores.estado == estado)
    
    result = await db.execute(query.order_by(RecepcionValores.fecha_emision.desc()))
    return list(result.scalars().all())


# ==================== ARQUEO DE CAJA ====================

@router.post("/arqueos", response_model=ArqueoCajaResponse, status_code=status.HTTP_201_CREATED)
async def crear_arqueo_caja(
    arqueo_data: ArqueoCajaCreate,
    db: AsyncSession = Depends(get_db)
):
    """Crear arqueo de caja (corte ciego)"""
    return await ArqueoCajaService.crear_arqueo(
        db=db,
        caja_id=arqueo_data.caja_id,
        usuario_id=arqueo_data.usuario_id,
        fecha_corte=arqueo_data.fecha_corte,
        turno=arqueo_data.turno
    )


@router.post("/arqueos/{arqueo_id}/cerrar", response_model=ArqueoCajaResponse)
async def cerrar_arqueo_caja(
    arqueo_id: UUID,
    cierre_data: ArqueoCajaCerrar,
    db: AsyncSession = Depends(get_db)
):
    """Cerrar arqueo calculando diferencias"""
    return await ArqueoCajaService.cerrar_arqueo(
        db=db,
        arqueo_id=arqueo_id,
        usuario_id=cierre_data.usuario_id
    )


@router.get("/arqueos", response_model=List[ArqueoCajaResponse])
async def listar_arqueos(
    tenant_id: UUID = Query(...),
    caja_id: Optional[UUID] = None,
    fecha: Optional[date] = None,
    turno: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Listar arqueos de caja"""
    from sqlalchemy.future import select
    from app.models.tesoreria.caja import ArqueoCaja
    from app.models.tesoreria.caja import Caja
    
    query = select(ArqueoCaja).join(Caja).where(Caja.tenant_id == tenant_id)
    
    if caja_id:
        query = query.where(ArqueoCaja.caja_id == caja_id)
    if fecha:
        query = query.where(ArqueoCaja.fecha_corte >= fecha)
    if turno:
        query = query.where(ArqueoCaja.turno == turno)
    
    result = await db.execute(query.order_by(ArqueoCaja.fecha_corte.desc()))
    return list(result.scalars().all())


# ==================== CORTES DE CAJA ====================

@router.post("/cortes", response_model=CorteCajaResponse, status_code=status.HTTP_201_CREATED)
async def crear_corte_caja(
    corte_data: CorteCajaCreate,
    db: AsyncSession = Depends(get_db)
):
    """Crear corte de caja (parcial, turno, diario, general)"""
    return await CorteCajaService.crear_corte(
        db=db,
        caja_id=corte_data.caja_id,
        usuario_id=corte_data.usuario_id,
        tipo_corte=corte_data.tipo_corte,
        turno=corte_data.turno
    )


@router.post("/cortes/{corte_id}/finalizar", response_model=CorteCajaResponse)
async def finalizar_corte_caja(
    corte_id: UUID,
    finalizar_data: CorteCajaFinalizar,
    db: AsyncSession = Depends(get_db)
):
    """Finalizar corte de caja"""
    return await CorteCajaService.finalizar_corte(
        db=db,
        corte_id=corte_id,
        total_efectivo=finalizar_data.total_efectivo,
        total_cheques=finalizar_data.total_cheques,
        total_tarjetas=finalizar_data.total_tarjetas,
        total_transferencias=finalizar_data.total_transferencias,
        observaciones=finalizar_data.observaciones,
        usuario_id=finalizar_data.usuario_id
    )


@router.get("/cortes", response_model=List[CorteCajaResponse])
async def listar_cortes(
    tenant_id: UUID = Query(...),
    caja_id: Optional[UUID] = None,
    tipo_corte: Optional[str] = None,
    fecha: Optional[date] = None,
    db: AsyncSession = Depends(get_db)
):
    """Listar cortes de caja"""
    from sqlalchemy.future import select
    from app.models.tesoreria.caja import CorteCaja
    from app.models.tesoreria.caja import Caja
    
    query = select(CorteCaja).join(Caja).where(Caja.tenant_id == tenant_id)
    
    if caja_id:
        query = query.where(CorteCaja.caja_id == caja_id)
    if tipo_corte:
        query = query.where(CorteCaja.tipo_corte == tipo_corte)
    if fecha:
        query = query.where(CorteCaja.fecha_apertura >= fecha)
    
    result = await db.execute(query.order_by(CorteCaja.fecha_apertura.desc()))
    return list(result.scalars().all())
