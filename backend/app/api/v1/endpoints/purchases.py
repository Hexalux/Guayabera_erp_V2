from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, String, cast
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime, date, timedelta, timezone
import uuid

from app.core.database import get_db
from app.models.usuario import Usuario
from app.api.deps import get_current_user

# Models
from app.models.purchases import Proveedor, OrdenCompra, DetalleOrdenCompra, CuentaPorPagar, PagoCxP
from app.models.treasury import CuentaBancaria, TransaccionBancaria
from app.models.inventory import LoteProducto, MovimientoInventario, ProductoTextil
from app.models.finance import CuentaContable

# Schemas
from app.schemas.purchases import (
    ProveedorCreate, ProveedorResponse,
    OrdenCompraCreate, OrdenCompraResponse,
    CuentaPorPagarResponse, PagoCxPCreate, PagoCxPResponse,
    ListaPrecioProveedorCreate, ListaPrecioProveedorResponse
)

# Integración contable
from app.services.finance_auto import create_system_poliza

router = APIRouter()

async def obtener_cuenta_por_codigo(db: AsyncSession, tenant_id: str, codigo: str) -> str:
    stmt = select(CuentaContable).where(
        CuentaContable.tenant_id == tenant_id,
        CuentaContable.codigo == codigo
    )
    result = await db.execute(stmt)
    cuenta = result.scalar_one_or_none()
    if not cuenta:
        raise ValueError(f"No se encontró la cuenta contable {codigo}")
    return str(cuenta.id)

# =================================================================
# PROVEEDORES
# =================================================================
@router.get("/proveedores", response_model=List[ProveedorResponse])
async def list_proveedores(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(Proveedor).where(Proveedor.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/proveedores", response_model=ProveedorResponse, status_code=status.HTTP_201_CREATED)
async def create_proveedor(
    proveedor: ProveedorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    db_prov = Proveedor(**proveedor.model_dump(), tenant_id=current_user.tenant_id)
    db.add(db_prov)
    await db.commit()
    await db.refresh(db_prov)
    return db_prov

@router.get("/proveedores/{proveedor_id}/precios", response_model=List[ListaPrecioProveedorResponse])
async def list_precios_proveedor(
    proveedor_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    from app.models.purchases import ListaPrecioProveedor
    stmt = select(ListaPrecioProveedor).where(
        ListaPrecioProveedor.proveedor_id == proveedor_id,
        ListaPrecioProveedor.tenant_id == current_user.tenant_id
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/proveedores/{proveedor_id}/precios", response_model=ListaPrecioProveedorResponse, status_code=status.HTTP_201_CREATED)
async def create_precio_proveedor(
    proveedor_id: str,
    req: ListaPrecioProveedorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    from app.models.purchases import ListaPrecioProveedor
    db_precio = ListaPrecioProveedor(**req.model_dump(), tenant_id=current_user.tenant_id)
    db.add(db_precio)
    await db.commit()
    await db.refresh(db_precio)
    return db_precio

# =================================================================
# ORDENES DE COMPRA
# =================================================================
@router.get("/ordenes", response_model=List[OrdenCompraResponse])
async def list_ordenes(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(OrdenCompra).where(
        OrdenCompra.tenant_id == current_user.tenant_id
    ).options(selectinload(OrdenCompra.detalles))
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/ordenes", response_model=OrdenCompraResponse, status_code=status.HTTP_201_CREATED)
async def create_orden_compra(
    req: OrdenCompraCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if not req.detalles:
        raise HTTPException(status_code=400, detail="La orden no tiene productos.")

    folio_oc = f"OC-{uuid.uuid4().hex[:6].upper()}"
    
    db_oc = OrdenCompra(
        tenant_id=current_user.tenant_id,
        folio=folio_oc,
        proveedor_id=req.proveedor_id,
        comprador_id=current_user.id,
        notas=req.notas,
        estado="rfq",
        subtotal=0.0,
        iva=0.0,
        total=0.0
    )
    db.add(db_oc)
    await db.flush()
    
    subtotal = 0.0
    for det in req.detalles:
        sub = det.cantidad_solicitada * det.precio_unitario
        subtotal += sub
        db_det = DetalleOrdenCompra(
            tenant_id=current_user.tenant_id,
            orden_id=db_oc.id,
            producto_textil_id=det.producto_textil_id,
            cantidad_solicitada=det.cantidad_solicitada,
            precio_unitario=det.precio_unitario,
            subtotal=sub
        )
        db.add(db_det)
        
    db_oc.subtotal = subtotal
    db_oc.iva = subtotal * 0.16
    db_oc.total = subtotal + db_oc.iva
    
    await db.commit()
    
    stmt_reload = select(OrdenCompra).where(OrdenCompra.id == db_oc.id).options(selectinload(OrdenCompra.detalles))
    result_reload = await db.execute(stmt_reload)
    return result_reload.scalar_one()

@router.post("/ordenes/{orden_id}/confirmar", status_code=status.HTTP_200_OK)
async def confirmar_rfq(
    orden_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(OrdenCompra).where(
        cast(OrdenCompra.id, String) == orden_id,
        OrdenCompra.tenant_id == current_user.tenant_id
    )
    result = await db.execute(stmt)
    db_oc = result.scalar_one_or_none()
    
    if not db_oc:
        raise HTTPException(status_code=404, detail="Orden de Compra no encontrada.")
        
    if db_oc.estado != "rfq":
        raise HTTPException(status_code=400, detail="Solo se pueden confirmar RFQs en estado 'rfq'.")
        
    db_oc.estado = "emitida"
    await db.commit()
    return {"mensaje": "Orden de compra confirmada y emitida al proveedor."}

# =================================================================
# RECEPCIÓN Y PROVISIÓN (ACID)
# =================================================================
@router.post("/ordenes/{orden_id}/recibir", status_code=status.HTTP_200_OK)
async def recibir_orden_compra(
    orden_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if not db.in_transaction():
        await db.begin()
        
    try:
        # Bloqueamos la OC para evitar recepciones dobles
        stmt = select(OrdenCompra).where(
            cast(OrdenCompra.id, String) == orden_id,
            OrdenCompra.tenant_id == current_user.tenant_id
        ).with_for_update().options(selectinload(OrdenCompra.detalles))
        
        result = await db.execute(stmt)
        db_oc = result.scalar_one_or_none()
        
        if not db_oc:
            raise HTTPException(status_code=404, detail="Orden de Compra no encontrada.")
            
        if db_oc.estado == "recibida":
            raise HTTPException(status_code=400, detail="Esta orden ya fue recibida anteriormente.")
            
        if db_oc.estado == "rfq":
            raise HTTPException(status_code=400, detail="No puedes recibir un RFQ. Primero confírmalo.")
            
        # Obtener el proveedor para calcular días de crédito
        stmt_prov = select(Proveedor).where(Proveedor.id == db_oc.proveedor_id)
        res_prov = await db.execute(stmt_prov)
        proveedor = res_prov.scalar_one()
            
        # 1. Ingresar mercancía al Inventario
        for det in db_oc.detalles:
            det.cantidad_recibida = det.cantidad_solicitada # Recibimos todo por MVP
            
            # Crear un Lote de Producto nuevo por esta recepción
            numero_lote = f"LOTE-COMPRA-{uuid.uuid4().hex[:6].upper()}"
            nuevo_lote = LoteProducto(
                tenant_id=current_user.tenant_id,
                producto_id=det.producto_textil_id,
                numero_lote=numero_lote,
                cantidad=det.cantidad_recibida,
                costo_unitario=det.precio_unitario,
                estado="disponible",
                ubicacion_id=None # Se asignaría a una rampa de recibo
            )
            db.add(nuevo_lote)
            await db.flush()
            
            # Kardex
            db_mov = MovimientoInventario(
                tenant_id=current_user.tenant_id,
                lote_id=nuevo_lote.id,
                cantidad=det.cantidad_recibida,
                tipo_movimiento="entrada",
                referencia=f"Recepción OC {db_oc.folio}"
            )
            db.add(db_mov)
            
        db_oc.estado = "recibida"
        db_oc.fecha_recepcion = datetime.now(timezone.utc)
        
        # 2. Generar Cuenta por Pagar (CxP)
        fecha_venc = datetime.now(timezone.utc) + timedelta(days=proveedor.dias_credito)
        db_cxp = CuentaPorPagar(
            tenant_id=current_user.tenant_id,
            orden_compra_id=db_oc.id,
            proveedor_id=db_oc.proveedor_id,
            monto_original=db_oc.total,
            saldo_pendiente=db_oc.total,
            fecha_vencimiento=fecha_venc
        )
        db.add(db_cxp)
        
        # 3. Póliza de Provisión de Compras (TutConta)
        # Cargamos a Inventario y a IVA Acreditable Pendiente. Abonamos a Proveedores.
        cta_inventario = await obtener_cuenta_por_codigo(db, current_user.tenant_id, "115") # Inventario Materia Prima
        cta_iva_pendiente = await obtener_cuenta_por_codigo(db, current_user.tenant_id, "118") # IVA Acreditable o Pendiente de Pago
        cta_proveedores = await obtener_cuenta_por_codigo(db, current_user.tenant_id, "201") # Proveedores
        
        await create_system_poliza(
            db=db,
            tenant_id=current_user.tenant_id,
            tipo="diario",
            fecha=date.today(),
            descripcion=f"Provisión de Compra OC {db_oc.folio} - {proveedor.razon_social}",
            movimientos_data=[
                {"cuenta_id": cta_inventario, "cargo": db_oc.subtotal, "abono": 0.0},
                {"cuenta_id": cta_iva_pendiente, "cargo": db_oc.iva, "abono": 0.0},
                {"cuenta_id": cta_proveedores, "cargo": 0.0, "abono": db_oc.total}
            ]
        )
        
        await db.commit()
        return {"mensaje": "Mercancía recibida, inventario actualizado y póliza contable de provisión generada exitosamente."}
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Fallo crítico al recibir orden de compra: {str(e)}")

# =================================================================
# CUENTAS POR PAGAR (CXP) - SPRINT 3
# =================================================================
@router.get("/cxp/saldos", response_model=List[CuentaPorPagarResponse])
async def list_cxp(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(CuentaPorPagar).options(
        selectinload(CuentaPorPagar.proveedor),
        selectinload(CuentaPorPagar.orden_compra)
    ).where(CuentaPorPagar.tenant_id == current_user.tenant_id)
    
    result = await db.execute(stmt)
    cxp_list = result.scalars().all()
    
    response = []
    for cxp in cxp_list:
        response.append({
            "id": cxp.id,
            "tenant_id": cxp.tenant_id,
            "orden_compra_id": cxp.orden_compra_id,
            "proveedor_id": cxp.proveedor_id,
            "proveedor_nombre": cxp.proveedor.razon_social if cxp.proveedor else "",
            "folio_orden": cxp.orden_compra.folio if cxp.orden_compra else "",
            "monto_original": cxp.monto_original,
            "monto_pagado": cxp.monto_pagado,
            "saldo_pendiente": cxp.saldo_pendiente,
            "fecha_emision": cxp.fecha_emision,
            "fecha_vencimiento": cxp.fecha_vencimiento,
            "estado": cxp.estado
        })
    return response

@router.post("/cxp/pagar", response_model=PagoCxPResponse)
async def registrar_pago_cxp(
    req: PagoCxPCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if req.monto <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser mayor a 0.")
        
    if not db.in_transaction():
        await db.begin()
        
    try:
        # 1. Bloquear CxP
        stmt_cxp = select(CuentaPorPagar).options(
            selectinload(CuentaPorPagar.proveedor)
        ).where(
            CuentaPorPagar.id == req.cuenta_por_pagar_id,
            CuentaPorPagar.tenant_id == current_user.tenant_id
        ).with_for_update()
        result_cxp = await db.execute(stmt_cxp)
        db_cxp = result_cxp.scalar_one_or_none()
        
        if not db_cxp:
            raise HTTPException(status_code=404, detail="Cuenta por pagar no encontrada.")
            
        if req.monto > db_cxp.saldo_pendiente:
            raise HTTPException(status_code=400, detail=f"El monto supera el saldo pendiente de ${db_cxp.saldo_pendiente}.")
            
        # 2. Bloquear Cuenta Bancaria (Control estricto de fondos)
        stmt_bank = select(CuentaBancaria).where(
            CuentaBancaria.id == req.cuenta_bancaria_id,
            CuentaBancaria.tenant_id == current_user.tenant_id
        ).with_for_update()
        result_bank = await db.execute(stmt_bank)
        db_bank = result_bank.scalar_one_or_none()
        
        if not db_bank:
            raise HTTPException(status_code=404, detail="Cuenta bancaria no encontrada.")
            
        if req.monto > db_bank.saldo_actual:
            raise HTTPException(status_code=400, detail=f"FONDOS INSUFICIENTES: Intentas pagar ${req.monto} pero la cuenta bancaria '{db_bank.banco}' solo tiene ${db_bank.saldo_actual}.")
            
        # 3. Aplicar pago a la deuda
        db_cxp.monto_pagado += req.monto
        db_cxp.saldo_pendiente -= req.monto
        if db_cxp.saldo_pendiente <= 0:
            db_cxp.estado = "pagada"
        elif db_cxp.monto_pagado > 0:
            db_cxp.estado = "parcial"
            
        # Extraer dinero del banco
        db_bank.saldo_actual -= req.monto
        
        # 4. Registrar Transacción Bancaria (Egreso)
        db_trx = TransaccionBancaria(
            tenant_id=current_user.tenant_id,
            cuenta_id=db_bank.id,
            tipo="egreso",
            monto=req.monto,
            referencia=req.referencia,
            concepto=f"Pago a Proveedor: {db_cxp.proveedor.razon_social if db_cxp.proveedor else ''}"
        )
        db.add(db_trx)
        await db.flush()
        
        # 5. Registrar Pago CxP
        db_pago = PagoCxP(
            tenant_id=current_user.tenant_id,
            cuenta_por_pagar_id=db_cxp.id,
            transaccion_bancaria_id=db_trx.id,
            monto=req.monto,
            referencia=req.referencia
        )
        db.add(db_pago)
        await db.flush()
        
        # 6. Generar Póliza Contable (TutConta)
        # Cargo a Proveedores (201). Abono a Bancos (102).
        cta_proveedores = await obtener_cuenta_por_codigo(db, current_user.tenant_id, "201")
        cta_bancos = await obtener_cuenta_por_codigo(db, current_user.tenant_id, "102")
        
        poliza = await create_system_poliza(
            db=db,
            tenant_id=current_user.tenant_id,
            tipo="egreso",
            fecha=date.today(),
            descripcion=f"Pago OC a {db_cxp.proveedor.razon_social if db_cxp.proveedor else ''}",
            movimientos_data=[
                {"cuenta_id": cta_proveedores, "cargo": req.monto, "abono": 0.0},
                {"cuenta_id": cta_bancos, "cargo": 0.0, "abono": req.monto}
            ]
        )
        
        db_trx.poliza_id = poliza.id
        await db.commit()
        await db.refresh(db_pago)
        return db_pago
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en transacción CxP: {str(e)}")
