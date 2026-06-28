from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, String, cast
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime, date, timezone
import uuid

from app.core.database import get_db
from app.models.usuario import Usuario
from app.api.deps import get_current_user

# Models
from app.models.sales_b2b import (
    CotizacionVenta, DetalleCotizacion,
    PedidoVenta, DetallePedido,
    RemisionVenta, DetalleRemision
)
from app.models.sales import Cliente
from app.models.cxc import CuentaPorCobrar
from app.models.finance import CuentaContable
from app.models.inventory import LoteProducto, MovimientoInventario

# Schemas
from app.schemas.sales_b2b import (
    CotizacionVentaCreate, CotizacionVentaResponse,
    PedidoVentaResponse,
    RemisionVentaResponse
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

# ================= COTIZACIONES =================

@router.get("/cotizaciones", response_model=List[CotizacionVentaResponse])
async def list_cotizaciones(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(CotizacionVenta).options(
        selectinload(CotizacionVenta.cliente),
        selectinload(CotizacionVenta.vendedor),
        selectinload(CotizacionVenta.detalles).selectinload(DetalleCotizacion.producto)
    ).where(CotizacionVenta.tenant_id == current_user.tenant_id).order_by(CotizacionVenta.fecha_emision.desc())
    
    result = await db.execute(stmt)
    cotizaciones = result.scalars().all()
    
    response = []
    for c in cotizaciones:
        dets = []
        for d in c.detalles:
            dets.append({
                "id": d.id,
                "producto_textil_id": d.producto_textil_id,
                "cantidad": d.cantidad,
                "precio_unitario": d.precio_unitario,
                "subtotal": d.subtotal,
                "producto_nombre": d.producto.nombre if d.producto else ""
            })
            
        response.append({
            "id": c.id,
            "folio": c.folio,
            "cliente_id": c.cliente_id,
            "vendedor_id": c.vendedor_id,
            "fecha_emision": c.fecha_emision,
            "fecha_vigencia": c.fecha_vigencia,
            "subtotal": c.subtotal,
            "iva": c.iva,
            "total": c.total,
            "estado": c.estado,
            "notas": c.notas,
            "cliente_nombre": c.cliente.nombre_comercial if c.cliente else "",
            "vendedor_nombre": c.vendedor.nombre if c.vendedor else "",
            "detalles": dets
        })
    return response

@router.post("/cotizaciones", response_model=CotizacionVentaResponse)
async def create_cotizacion(
    req: CotizacionVentaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if not req.detalles:
        raise HTTPException(status_code=400, detail="La cotización debe tener al menos un producto.")
        
    folio = f"COT-{uuid.uuid4().hex[:6].upper()}"
    
    db_cot = CotizacionVenta(
        tenant_id=current_user.tenant_id,
        folio=folio,
        cliente_id=req.cliente_id,
        vendedor_id=current_user.id,
        fecha_vigencia=req.fecha_vigencia,
        notas=req.notas,
        subtotal=0.0,
        iva=0.0,
        total=0.0
    )
    db.add(db_cot)
    await db.flush()
    
    subtotal = 0.0
    for d in req.detalles:
        sub = d.cantidad * d.precio_unitario
        subtotal += sub
        db_det = DetalleCotizacion(
            tenant_id=current_user.tenant_id,
            cotizacion_id=db_cot.id,
            producto_textil_id=d.producto_textil_id,
            cantidad=d.cantidad,
            precio_unitario=d.precio_unitario,
            subtotal=sub
        )
        db.add(db_det)
        
    db_cot.subtotal = subtotal
    db_cot.iva = subtotal * 0.16
    db_cot.total = subtotal + db_cot.iva
    
    await db.commit()
    
    # Reload
    stmt_reload = select(CotizacionVenta).options(
        selectinload(CotizacionVenta.cliente),
        selectinload(CotizacionVenta.vendedor),
        selectinload(CotizacionVenta.detalles).selectinload(DetalleCotizacion.producto)
    ).where(CotizacionVenta.id == db_cot.id)
    res_rel = await db.execute(stmt_reload)
    rel_cot = res_rel.scalar_one()
    
    return {
        "id": rel_cot.id,
        "folio": rel_cot.folio,
        "cliente_id": rel_cot.cliente_id,
        "vendedor_id": rel_cot.vendedor_id,
        "fecha_emision": rel_cot.fecha_emision,
        "fecha_vigencia": rel_cot.fecha_vigencia,
        "subtotal": rel_cot.subtotal,
        "iva": rel_cot.iva,
        "total": rel_cot.total,
        "estado": rel_cot.estado,
        "notas": rel_cot.notas,
        "cliente_nombre": rel_cot.cliente.nombre_comercial if rel_cot.cliente else "",
        "vendedor_nombre": rel_cot.vendedor.nombre if rel_cot.vendedor else "",
        "detalles": [{
            "id": d.id,
            "producto_textil_id": d.producto_textil_id,
            "cantidad": d.cantidad,
            "precio_unitario": d.precio_unitario,
            "subtotal": d.subtotal,
            "producto_nombre": d.producto.nombre if d.producto else ""
        } for d in rel_cot.detalles]
    }

# ================= PEDIDOS =================

@router.post("/cotizaciones/{id}/convertir-pedido", response_model=PedidoVentaResponse)
async def convertir_cotizacion_a_pedido(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if not db.in_transaction():
        await db.begin()
        
    try:
        stmt_cot = select(CotizacionVenta).options(
            selectinload(CotizacionVenta.detalles)
        ).where(
            cast(CotizacionVenta.id, String) == id,
            CotizacionVenta.tenant_id == current_user.tenant_id
        ).with_for_update()
        res_cot = await db.execute(stmt_cot)
        db_cot = res_cot.scalar_one_or_none()
        
        if not db_cot:
            raise HTTPException(status_code=404, detail="Cotización no encontrada")
            
        if db_cot.estado != "borrador" and db_cot.estado != "enviada":
            raise HTTPException(status_code=400, detail="Cotización ya fue procesada.")
            
        db_cot.estado = "aceptada"
        
        folio_ped = f"PED-{uuid.uuid4().hex[:6].upper()}"
        db_ped = PedidoVenta(
            tenant_id=current_user.tenant_id,
            folio=folio_ped,
            cotizacion_id=db_cot.id,
            cliente_id=db_cot.cliente_id,
            vendedor_id=current_user.id,
            subtotal=db_cot.subtotal,
            iva=db_cot.iva,
            total=db_cot.total
        )
        db.add(db_ped)
        await db.flush()
        
        for d in db_cot.detalles:
            db_det = DetallePedido(
                tenant_id=current_user.tenant_id,
                pedido_id=db_ped.id,
                producto_textil_id=d.producto_textil_id,
                cantidad_solicitada=d.cantidad,
                cantidad_remisionada=0,
                precio_unitario=d.precio_unitario,
                subtotal=d.subtotal
            )
            db.add(db_det)
            
        await db.commit()
        
        stmt_reload = select(PedidoVenta).options(
            selectinload(PedidoVenta.cliente),
            selectinload(PedidoVenta.detalles).selectinload(DetallePedido.producto)
        ).where(PedidoVenta.id == db_ped.id)
        res_rel = await db.execute(stmt_reload)
        rel_ped = res_rel.scalar_one()
        
        return {
            "id": rel_ped.id,
            "folio": rel_ped.folio,
            "cotizacion_id": rel_ped.cotizacion_id,
            "cliente_id": rel_ped.cliente_id,
            "fecha_pedido": rel_ped.fecha_pedido,
            "fecha_entrega_esperada": rel_ped.fecha_entrega_esperada,
            "subtotal": rel_ped.subtotal,
            "iva": rel_ped.iva,
            "total": rel_ped.total,
            "estado": rel_ped.estado,
            "notas": rel_ped.notas,
            "cliente_nombre": rel_ped.cliente.nombre_comercial if rel_ped.cliente else "",
            "detalles": [{
                "id": dp.id,
                "producto_textil_id": dp.producto_textil_id,
                "cantidad_solicitada": dp.cantidad_solicitada,
                "cantidad_remisionada": dp.cantidad_remisionada,
                "precio_unitario": dp.precio_unitario,
                "subtotal": dp.subtotal,
                "producto_nombre": dp.producto.nombre if dp.producto else ""
            } for dp in rel_ped.detalles]
        }
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pedidos", response_model=List[PedidoVentaResponse])
async def list_pedidos(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(PedidoVenta).options(
        selectinload(PedidoVenta.cliente),
        selectinload(PedidoVenta.detalles).selectinload(DetallePedido.producto)
    ).where(PedidoVenta.tenant_id == current_user.tenant_id).order_by(PedidoVenta.fecha_pedido.desc())
    
    result = await db.execute(stmt)
    pedidos = result.scalars().all()
    
    response = []
    for p in pedidos:
        response.append({
            "id": p.id,
            "folio": p.folio,
            "cotizacion_id": p.cotizacion_id,
            "cliente_id": p.cliente_id,
            "fecha_pedido": p.fecha_pedido,
            "fecha_entrega_esperada": p.fecha_entrega_esperada,
            "subtotal": p.subtotal,
            "iva": p.iva,
            "total": p.total,
            "estado": p.estado,
            "notas": p.notas,
            "cliente_nombre": p.cliente.nombre_comercial if p.cliente else "",
            "detalles": [{
                "id": dp.id,
                "producto_textil_id": dp.producto_textil_id,
                "cantidad_solicitada": dp.cantidad_solicitada,
                "cantidad_remisionada": dp.cantidad_remisionada,
                "precio_unitario": dp.precio_unitario,
                "subtotal": dp.subtotal,
                "producto_nombre": dp.producto.nombre if dp.producto else ""
            } for dp in p.detalles]
        })
    return response

# ================= REMISIONES =================

@router.post("/pedidos/{id}/remisionar", response_model=RemisionVentaResponse)
async def remisionar_pedido(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Surtir el pedido.
    Reduce inventario (LIFO/FIFO básico por Lote disponible).
    Genera CxC (Deuda del cliente).
    Genera Póliza Contable (TutConta).
    """
    if not db.in_transaction():
        await db.begin()
        
    try:
        # 1. Bloquear Pedido
        stmt_ped = select(PedidoVenta).options(
            selectinload(PedidoVenta.cliente),
            selectinload(PedidoVenta.detalles)
        ).where(
            cast(PedidoVenta.id, String) == id,
            PedidoVenta.tenant_id == current_user.tenant_id
        ).with_for_update()
        res_ped = await db.execute(stmt_ped)
        db_ped = res_ped.scalar_one_or_none()
        
        if not db_ped:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
            
        if db_ped.estado == "remisionado_total":
            raise HTTPException(status_code=400, detail="Este pedido ya fue surtido totalmente.")
            
        folio_rem = f"REM-{uuid.uuid4().hex[:6].upper()}"
        
        db_rem = RemisionVenta(
            tenant_id=current_user.tenant_id,
            folio=folio_rem,
            pedido_id=db_ped.id,
            cliente_id=db_ped.cliente_id,
            vendedor_id=current_user.id,
            subtotal=db_ped.subtotal,
            iva=db_ped.iva,
            total=db_ped.total
        )
        db.add(db_rem)
        await db.flush()
        
        # 2. Descontar Inventario y Llenar Detalles de Remisión
        costo_total_ventas = 0.0
        
        for d in db_ped.detalles:
            faltante = d.cantidad_solicitada - d.cantidad_remisionada
            if faltante <= 0:
                continue
                
            # Buscar Lotes disponibles de este producto
            stmt_lotes = select(LoteProducto).where(
                LoteProducto.producto_id == d.producto_textil_id,
                LoteProducto.estado == "disponible",
                LoteProducto.cantidad > 0,
                LoteProducto.tenant_id == current_user.tenant_id
            ).with_for_update()
            
            res_lotes = await db.execute(stmt_lotes)
            lotes = res_lotes.scalars().all()
            
            piezas_surtidas = 0
            
            for lote in lotes:
                if faltante <= 0:
                    break
                
                extraer = min(lote.cantidad, faltante)
                lote.cantidad -= extraer
                faltante -= extraer
                piezas_surtidas += extraer
                costo_total_ventas += (extraer * lote.costo_unitario)
                
                # Movimiento de Salida
                db_mov = MovimientoInventario(
                    tenant_id=current_user.tenant_id,
                    lote_id=lote.id,
                    cantidad=extraer,
                    tipo_movimiento="salida",
                    referencia=f"Remisión {folio_rem}"
                )
                db.add(db_mov)
                
            if piezas_surtidas > 0:
                d.cantidad_remisionada += piezas_surtidas
                sub = piezas_surtidas * d.precio_unitario
                
                db_det_rem = DetalleRemision(
                    tenant_id=current_user.tenant_id,
                    remision_id=db_rem.id,
                    detalle_pedido_id=d.id,
                    producto_textil_id=d.producto_textil_id,
                    cantidad=piezas_surtidas,
                    precio_unitario=d.precio_unitario,
                    subtotal=sub
                )
                db.add(db_det_rem)
                
        # Validar si se surtió algo
        if costo_total_ventas == 0:
            raise HTTPException(status_code=400, detail="NO HAY INVENTARIO SUFICIENTE para surtir ninguna pieza de este pedido.")
            
        db_ped.estado = "remisionado_total" # Asumimos surtido total en MVP B2B simple
        
        # 3. Generar Cuenta por Cobrar (Deuda)
        dias_cred = db_ped.cliente.dias_credito if db_ped.cliente and db_ped.cliente.dias_credito else 0
        fecha_venc = datetime.now(timezone.utc)
        
        db_cxc = CuentaPorCobrar(
            tenant_id=current_user.tenant_id,
            cliente_id=db_ped.cliente_id,
            monto_original=db_ped.total,
            saldo_pendiente=db_ped.total,
            fecha_vencimiento=fecha_venc,
            origen="remision",
            referencia_origen=db_rem.id
        )
        db.add(db_cxc)
        await db.flush()
        
        db_rem.cuenta_por_cobrar_id = db_cxc.id
        
        # 4. Generar Pólizas Contables (TutConta)
        # Ingreso/Venta: Cargo a Clientes, Abono a Ingresos, Abono a IVA.
        # Costo: Cargo a Costo de Ventas, Abono a Inventario.
        cta_clientes = await obtener_cuenta_por_codigo(db, current_user.tenant_id, "105")
        cta_ingresos = await obtener_cuenta_por_codigo(db, current_user.tenant_id, "401")
        cta_iva = await obtener_cuenta_por_codigo(db, current_user.tenant_id, "208")
        
        cta_costo = await obtener_cuenta_por_codigo(db, current_user.tenant_id, "501")
        cta_inventario = await obtener_cuenta_por_codigo(db, current_user.tenant_id, "115")
        
        poliza = await create_system_poliza(
            db=db,
            tenant_id=current_user.tenant_id,
            tipo="diario", # Diario porque no entra dinero al banco aún
            fecha=date.today(),
            descripcion=f"Remisión Venta B2B {folio_rem}",
            movimientos_data=[
                # Venta
                {"cuenta_id": cta_clientes, "cargo": db_ped.total, "abono": 0.0},
                {"cuenta_id": cta_ingresos, "cargo": 0.0, "abono": db_ped.subtotal},
                {"cuenta_id": cta_iva, "cargo": 0.0, "abono": db_ped.iva},
                # Costo
                {"cuenta_id": cta_costo, "cargo": costo_total_ventas, "abono": 0.0},
                {"cuenta_id": cta_inventario, "cargo": 0.0, "abono": costo_total_ventas}
            ]
        )
        
        db_rem.poliza_id = poliza.id
        
        await db.commit()
        
        # Reload Remisión para el response
        stmt_rel_rem = select(RemisionVenta).options(
            selectinload(RemisionVenta.cliente),
            selectinload(RemisionVenta.detalles).selectinload(DetalleRemision.producto)
        ).where(RemisionVenta.id == db_rem.id)
        res_rel_rem = await db.execute(stmt_rel_rem)
        rel_rem = res_rel_rem.scalar_one()
        
        return {
            "id": rel_rem.id,
            "folio": rel_rem.folio,
            "pedido_id": rel_rem.pedido_id,
            "cliente_id": rel_rem.cliente_id,
            "fecha_emision": rel_rem.fecha_emision,
            "subtotal": rel_rem.subtotal,
            "iva": rel_rem.iva,
            "total": rel_rem.total,
            "estado": rel_rem.estado,
            "cliente_nombre": rel_rem.cliente.nombre_comercial if rel_rem.cliente else "",
            "cuenta_por_cobrar_id": rel_rem.cuenta_por_cobrar_id,
            "poliza_id": rel_rem.poliza_id,
            "detalles": [{
                "id": dr.id,
                "producto_textil_id": dr.producto_textil_id,
                "cantidad": dr.cantidad,
                "precio_unitario": dr.precio_unitario,
                "subtotal": dr.subtotal,
                "producto_nombre": dr.producto.nombre if dr.producto else ""
            } for dr in rel_rem.detalles]
        }
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/remisiones", response_model=List[RemisionVentaResponse])
async def list_remisiones(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(RemisionVenta).options(
        selectinload(RemisionVenta.cliente),
        selectinload(RemisionVenta.detalles).selectinload(DetalleRemision.producto)
    ).where(RemisionVenta.tenant_id == current_user.tenant_id).order_by(RemisionVenta.fecha_emision.desc())
    
    result = await db.execute(stmt)
    remisiones = result.scalars().all()
    
    response = []
    for r in remisiones:
        response.append({
            "id": r.id,
            "folio": r.folio,
            "pedido_id": r.pedido_id,
            "cliente_id": r.cliente_id,
            "fecha_emision": r.fecha_emision,
            "subtotal": r.subtotal,
            "iva": r.iva,
            "total": r.total,
            "estado": r.estado,
            "cliente_nombre": r.cliente.nombre_comercial if r.cliente else "",
            "cuenta_por_cobrar_id": r.cuenta_por_cobrar_id,
            "poliza_id": r.poliza_id,
            "detalles": [{
                "id": dr.id,
                "producto_textil_id": dr.producto_textil_id,
                "cantidad": dr.cantidad,
                "precio_unitario": dr.precio_unitario,
                "subtotal": dr.subtotal,
                "producto_nombre": dr.producto.nombre if dr.producto else ""
            } for dr in r.detalles]
        })
    return response
