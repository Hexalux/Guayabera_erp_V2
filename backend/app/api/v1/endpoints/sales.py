from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, String, cast
from typing import List
from datetime import date, datetime, timezone
import uuid

from app.core.database import get_db
from app.models.usuario import Usuario
from app.api.deps import get_current_user

# Models
from app.models.sales import Cliente, VentaPOS, DetalleVentaPOS, SesionCaja
from app.models.inventory import LoteProducto, MovimientoInventario
from app.models.finance import CuentaContable
from app.models.cxc import CuentaPorCobrar

# Schemas
from app.schemas.sales import (
    ClienteCreate, ClienteResponse,
    VentaPOSCreate, VentaPOSResponse,
    SesionCajaCreate, SesionCajaResponse, SesionCajaClose,
    OrdenVentaCreate, OrdenVentaResponse
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
# CLIENTES
# =================================================================
@router.get("/clientes", response_model=List[ClienteResponse])
async def list_clientes(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(Cliente).where(Cliente.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/clientes", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
async def create_cliente(
    cliente: ClienteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    db_cliente = Cliente(**cliente.model_dump(), tenant_id=current_user.tenant_id)
    db.add(db_cliente)
    await db.commit()
    await db.refresh(db_cliente)
    return db_cliente

# =================================================================
# ORDENES DE VENTA (COTIZACIONES)
# =================================================================
@router.get("/ordenes", response_model=List[OrdenVentaResponse])
async def list_ordenes_venta(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    from app.models.sales import OrdenVenta
    from sqlalchemy.orm import selectinload
    stmt = select(OrdenVenta).where(OrdenVenta.tenant_id == current_user.tenant_id).options(selectinload(OrdenVenta.detalles))
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/ordenes", response_model=OrdenVentaResponse, status_code=status.HTTP_201_CREATED)
async def create_orden_venta(
    orden: OrdenVentaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    from app.models.sales import OrdenVenta, DetalleOrdenVenta
    import uuid
    
    # Generar folio único
    folio_orden = f"OV-{uuid.uuid4().hex[:6].upper()}"
    
    db_orden = OrdenVenta(
        tenant_id=current_user.tenant_id,
        folio=folio_orden,
        fecha_validez=orden.fecha_validez,
        cliente_id=orden.cliente_id,
        vendedor_id=current_user.id,
        estado="borrador",
        notas=orden.notas,
        terminos_pago=orden.terminos_pago,
        subtotal=0.0,
        iva=0.0,
        total=0.0
    )
    db.add(db_orden)
    await db.flush()
    
    subtotal_orden = 0.0
    for det in orden.detalles:
        subtotal_linea = det.cantidad * det.precio_unitario * (1 - (det.descuento_porcentaje / 100))
        subtotal_orden += subtotal_linea
        
        db_det = DetalleOrdenVenta(
            tenant_id=current_user.tenant_id,
            orden_id=db_orden.id,
            producto_textil_id=det.producto_textil_id,
            cantidad=det.cantidad,
            precio_unitario=det.precio_unitario,
            descuento_porcentaje=det.descuento_porcentaje,
            subtotal=subtotal_linea
        )
        db.add(db_det)
        
    db_orden.subtotal = subtotal_orden
    db_orden.iva = subtotal_orden * 0.16
    db_orden.total = subtotal_orden + db_orden.iva
    
    await db.commit()
    await db.refresh(db_orden)
    
    # Reload for details
    from sqlalchemy.orm import selectinload
    stmt = select(OrdenVenta).where(OrdenVenta.id == db_orden.id).options(selectinload(OrdenVenta.detalles))
    res = await db.execute(stmt)
    return res.scalar_one()

@router.post("/ordenes/{orden_id}/confirmar", response_model=OrdenVentaResponse)
async def confirmar_orden_venta(
    orden_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    from app.models.sales import OrdenVenta
    from sqlalchemy.orm import selectinload
    stmt = select(OrdenVenta).where(OrdenVenta.id == orden_id, OrdenVenta.tenant_id == current_user.tenant_id).options(selectinload(OrdenVenta.detalles))
    result = await db.execute(stmt)
    db_orden = result.scalar_one_or_none()
    
    if not db_orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    if db_orden.estado != "borrador":
        raise HTTPException(status_code=400, detail=f"No se puede confirmar una orden en estado {db_orden.estado}")
        
    db_orden.estado = "confirmada"
    await db.commit()
    await db.refresh(db_orden)
    return db_orden

@router.get("/ordenes/{orden_id}", response_model=OrdenVentaResponse)
async def get_orden_venta(
    orden_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    from app.models.sales import OrdenVenta
    from sqlalchemy.orm import selectinload
    stmt = select(OrdenVenta).where(OrdenVenta.id == orden_id, OrdenVenta.tenant_id == current_user.tenant_id).options(selectinload(OrdenVenta.detalles))
    result = await db.execute(stmt)
    db_orden = result.scalar_one_or_none()
    if not db_orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    return db_orden

@router.put("/ordenes/{orden_id}", response_model=OrdenVentaResponse)
async def update_orden_venta(
    orden_id: str,
    orden: OrdenVentaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    from app.models.sales import OrdenVenta, DetalleOrdenVenta
    from sqlalchemy.orm import selectinload
    from sqlalchemy import delete
    
    stmt = select(OrdenVenta).where(OrdenVenta.id == orden_id, OrdenVenta.tenant_id == current_user.tenant_id).options(selectinload(OrdenVenta.detalles))
    result = await db.execute(stmt)
    db_orden = result.scalar_one_or_none()
    if not db_orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    if db_orden.estado != "borrador":
        raise HTTPException(status_code=400, detail="Solo se pueden modificar órdenes en estado borrador.")
        
    db_orden.fecha_validez = orden.fecha_validez
    db_orden.cliente_id = orden.cliente_id
    db_orden.notas = orden.notas
    db_orden.terminos_pago = orden.terminos_pago
    
    await db.execute(delete(DetalleOrdenVenta).where(DetalleOrdenVenta.orden_id == orden_id))
    
    subtotal_orden = 0.0
    for det in orden.detalles:
        subtotal_linea = det.cantidad * det.precio_unitario * (1 - (det.descuento_porcentaje / 100))
        subtotal_orden += subtotal_linea
        
        db_det = DetalleOrdenVenta(
            tenant_id=current_user.tenant_id,
            orden_id=db_orden.id,
            producto_textil_id=det.producto_textil_id,
            cantidad=det.cantidad,
            precio_unitario=det.precio_unitario,
            descuento_porcentaje=det.descuento_porcentaje,
            subtotal=subtotal_linea
        )
        db.add(db_det)
        
    db_orden.subtotal = subtotal_orden
    db_orden.iva = subtotal_orden * 0.16
    db_orden.total = subtotal_orden + db_orden.iva
    
    await db.commit()
    await db.refresh(db_orden)
    
    stmt = select(OrdenVenta).where(OrdenVenta.id == db_orden.id).options(selectinload(OrdenVenta.detalles))
    res = await db.execute(stmt)
    return res.scalar_one()

@router.delete("/ordenes/{orden_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_orden_venta(
    orden_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    from app.models.sales import OrdenVenta
    stmt = select(OrdenVenta).where(OrdenVenta.id == orden_id, OrdenVenta.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    db_orden = result.scalar_one_or_none()
    if not db_orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    if db_orden.estado != "borrador":
        raise HTTPException(status_code=400, detail="Solo se pueden eliminar órdenes en estado borrador.")
        
    await db.delete(db_orden)
    await db.commit()
    return None


# =================================================================
# SESIONES DE CAJA
# =================================================================
@router.get("/sesiones", response_model=List[SesionCajaResponse])
async def list_sesiones(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(SesionCaja).where(SesionCaja.tenant_id == current_user.tenant_id).order_by(SesionCaja.fecha_apertura.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/sesiones/activa", response_model=SesionCajaResponse)
async def get_active_sesion(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(SesionCaja).where(
        SesionCaja.tenant_id == current_user.tenant_id,
        SesionCaja.cajero_id == current_user.id,
        SesionCaja.estado == "abierta"
    )
    result = await db.execute(stmt)
    sesion = result.scalar_one_or_none()
    if not sesion:
        raise HTTPException(status_code=404, detail="No hay sesión de caja abierta para este cajero.")
    return sesion

@router.post("/sesiones/open", response_model=SesionCajaResponse, status_code=status.HTTP_201_CREATED)
async def open_sesion(
    sesion_req: SesionCajaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Verificar si ya hay una abierta para el cajero
    stmt = select(SesionCaja).where(SesionCaja.cajero_id == current_user.id, SesionCaja.estado == "abierta")
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ya tienes una sesión de caja abierta.")
        
    db_sesion = SesionCaja(**sesion_req.model_dump(), cajero_id=current_user.id, tenant_id=current_user.tenant_id)
    db.add(db_sesion)
    await db.commit()
    await db.refresh(db_sesion)
    return db_sesion

@router.post("/sesiones/{id}/close", response_model=SesionCajaResponse)
async def close_sesion(
    id: str,
    close_req: SesionCajaClose,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(SesionCaja).where(SesionCaja.id == id, SesionCaja.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    db_sesion = result.scalar_one_or_none()
    
    if not db_sesion:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    if db_sesion.estado == "cerrada":
        raise HTTPException(status_code=400, detail="La sesión ya está cerrada")
        
    db_sesion.fecha_cierre = datetime.now(timezone.utc)
    db_sesion.estado = "cerrada"
    db_sesion.total_efectivo = close_req.total_efectivo
    db_sesion.total_tarjeta = close_req.total_tarjeta
    if close_req.notas:
        db_sesion.notas = (db_sesion.notas or "") + "\nCierre: " + close_req.notas
        
    # Calcular diferencia teórica vs declarada (Simplificado para MVP)
    # En un sistema completo sumaríamos las ventas en efectivo y tarjeta a fondo_inicial
    db_sesion.diferencia = 0.0 

    await db.commit()
    await db.refresh(db_sesion)
    return db_sesion


# =================================================================
# PUNTO DE VENTA (POS)
# =================================================================
@router.get("/pos", response_model=List[VentaPOSResponse])
async def list_ventas(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(VentaPOS).where(VentaPOS.tenant_id == current_user.tenant_id).order_by(VentaPOS.fecha_venta.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/pos", response_model=VentaPOSResponse, status_code=status.HTTP_201_CREATED)
async def process_pos_sale(
    venta_req: VentaPOSCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Procesa una venta de mostrador (POS).
    Descuenta inventario con ACID y genera Póliza de Ingreso y Costo de Ventas automáticamente.
    """
    if not venta_req.detalles:
        raise HTTPException(status_code=400, detail="El carrito está vacío.")

    # Iniciamos transacción explícita ACID
    if not db.in_transaction():
        await db.begin()
        
    try:
        if venta_req.metodo_pago == "CRÉDITO" and not venta_req.cliente_id:
            raise HTTPException(status_code=400, detail="Las ventas a crédito requieren un Cliente registrado.")

        # Generar folio único (en la vida real puede ser un correlativo en base de datos)
        folio_ticket = f"TK-{uuid.uuid4().hex[:6].upper()}"
        
        # Buscar sesión activa si aplica
        stmt_sesion = select(SesionCaja).where(SesionCaja.cajero_id == current_user.id, SesionCaja.estado == "abierta")
        res_sesion = await db.execute(stmt_sesion)
        sesion_activa = res_sesion.scalar_one_or_none()
        
        db_venta = VentaPOS(
            tenant_id=current_user.tenant_id,
            folio=folio_ticket,
            cliente_id=venta_req.cliente_id if venta_req.cliente_id else None,
            vendedor_id=current_user.id,
            sesion_id=sesion_activa.id if sesion_activa else None,
            metodo_pago=venta_req.metodo_pago,
            notas=venta_req.notas,
            subtotal=0.0,
            iva=0.0,
            total=0.0
        )
        db.add(db_venta)
        await db.flush() # Para obtener ID de la venta
        
        subtotal_venta = 0.0
        costo_total_ventas = 0.0 # Para la póliza de costo de ventas
        
        for det in venta_req.detalles:
            # 1. Obtener Lote para actualizar cantidad con Pessimistic Locking (TutConta)
            stmt = select(LoteProducto).where(
                cast(LoteProducto.id, String) == det.lote_id, 
                LoteProducto.tenant_id == current_user.tenant_id
            ).with_for_update() # Bloqueo determinista
            
            result = await db.execute(stmt)
            db_lote = result.scalar_one_or_none()
            
            if not db_lote:
                raise HTTPException(status_code=404, detail=f"Lote {det.lote_id} no encontrado")
                
            if float(db_lote.cantidad) < det.cantidad:
                raise HTTPException(status_code=400, detail=f"Stock insuficiente en el lote {db_lote.numero_lote}. Solicitado: {det.cantidad}, Disponible: {db_lote.cantidad}")
            
            # Descontar inventario
            db_lote.cantidad = float(db_lote.cantidad) - det.cantidad
            
            # Asumimos que el costo unitario está en algún lado. Aquí haríamos un promedio o tomaríamos el del lote.
            # Por simplicidad del MVP, usaremos $100 fijo o un cálculo estimado.
            costo_unitario_estimado = 80.0 
            costo_total_ventas += det.cantidad * costo_unitario_estimado
            
            subtotal_linea = det.cantidad * det.precio_unitario
            subtotal_venta += subtotal_linea
            
            # Crear detalle de venta
            db_det = DetalleVentaPOS(
                tenant_id=current_user.tenant_id,
                venta_id=db_venta.id,
                lote_id=db_lote.id,
                cantidad=det.cantidad,
                precio_unitario=det.precio_unitario,
                subtotal=subtotal_linea
            )
            db.add(db_det)
            
            # Registrar movimiento de inventario (Kardex)
            db_mov = MovimientoInventario(
                lote_id=db_lote.id,
                cantidad=det.cantidad,
                tipo_movimiento="salida",
                referencia=f"Venta POS {folio_ticket}",
                tenant_id=current_user.tenant_id
            )
            db.add(db_mov)
            
        # Calcular impuestos y totales
        db_venta.subtotal = subtotal_venta
        db_venta.iva = subtotal_venta * 0.16 # IVA México
        db_venta.total = db_venta.subtotal + db_venta.iva
        
        # Generar pólizas
        if venta_req.metodo_pago == "CRÉDITO":
            cta_cargo_venta = await obtener_cuenta_por_codigo(db, current_user.tenant_id, "103") # Clientes (CxC)
        else:
            cta_cargo_venta = await obtener_cuenta_por_codigo(db, current_user.tenant_id, "101" if venta_req.metodo_pago == "EFECTIVO" else "102")
            
        cta_ingresos = await obtener_cuenta_por_codigo(db, current_user.tenant_id, "401") # Ingresos
        cta_iva = await obtener_cuenta_por_codigo(db, current_user.tenant_id, "208") # Impuestos retenidos/trasladados
        cta_costo = await obtener_cuenta_por_codigo(db, current_user.tenant_id, "501") # Costo de ventas
        cta_inventario = await obtener_cuenta_por_codigo(db, current_user.tenant_id, "115") # Inventario PT
        
        # Póliza 1: Ingreso por Ventas (o generación de CxC)
        await create_system_poliza(
            db=db,
            tenant_id=current_user.tenant_id,
            tipo="diario" if venta_req.metodo_pago == "CRÉDITO" else "ingreso",
            fecha=date.today(),
            descripcion=f"Venta POS Ticket {folio_ticket} - {venta_req.metodo_pago}",
            movimientos_data=[
                {"cuenta_id": cta_cargo_venta, "cargo": db_venta.total, "abono": 0.0},
                {"cuenta_id": cta_ingresos, "cargo": 0.0, "abono": db_venta.subtotal},
                {"cuenta_id": cta_iva, "cargo": 0.0, "abono": db_venta.iva}
            ]
        )
        
        # Si es a crédito, generamos la CxC en el módulo correspondiente
        if venta_req.metodo_pago == "CRÉDITO":
            from datetime import timedelta
            db_cxc = CuentaPorCobrar(
                tenant_id=current_user.tenant_id,
                venta_id=db_venta.id,
                cliente_id=venta_req.cliente_id,
                monto_original=db_venta.total,
                saldo_pendiente=db_venta.total,
                fecha_vencimiento=datetime.now(timezone.utc) + timedelta(days=30) # MVP: 30 días de crédito por defecto
            )
            db.add(db_cxc)
        
        # Póliza 2: Costo de Ventas
        await create_system_poliza(
            db=db,
            tenant_id=current_user.tenant_id,
            tipo="diario",
            fecha=date.today(),
            descripcion=f"Costo de Venta Ticket {folio_ticket}",
            movimientos_data=[
                {"cuenta_id": cta_costo, "cargo": costo_total_ventas, "abono": 0.0},
                {"cuenta_id": cta_inventario, "cargo": 0.0, "abono": costo_total_ventas}
            ]
        )

        await db.commit()
        await db.refresh(db_venta)
        
        # Necesitamos recargar las relaciones para Pydantic (detalles)
        stmt_reload = select(VentaPOS).where(VentaPOS.id == db_venta.id)
        result_reload = await db.execute(stmt_reload)
        db_venta_full = result_reload.scalar_one()
        
        return db_venta_full
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Fallo en transacción POS: {str(e)}")

@router.get("/reportes/dashboard")
async def get_sales_report_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    from sqlalchemy import func
    from app.models.usuario import Usuario
    from app.models.inventory import ProductoTextil
    
    # Total ventas
    stmt_total = select(func.sum(VentaPOS.total)).where(
        VentaPOS.tenant_id == current_user.tenant_id,
        VentaPOS.estado == "completada"
    )
    res_total = await db.execute(stmt_total)
    total_monto = res_total.scalar() or 0.0

    # Ventas por vendedor
    stmt_vendedores = select(
        Usuario.nombre,
        func.sum(VentaPOS.total).label("monto")
    ).join(
        VentaPOS, VentaPOS.vendedor_id == Usuario.id
    ).where(
        VentaPOS.tenant_id == current_user.tenant_id,
        VentaPOS.estado == "completada"
    ).group_by(Usuario.nombre)
    res_vendedores = await db.execute(stmt_vendedores)
    vendedores_data = [{"nombre": r[0], "monto": r[1]} for r in res_vendedores.all()]

    # Ventas por producto (Top 5)
    stmt_productos = select(
        ProductoTextil.nombre,
        func.sum(DetalleVentaPOS.cantidad).label("cantidad"),
        func.sum(DetalleVentaPOS.subtotal).label("monto")
    ).join(
        DetalleVentaPOS, DetalleVentaPOS.venta_id == VentaPOS.id
    ).join(
        LoteProducto, LoteProducto.id == DetalleVentaPOS.lote_id
    ).join(
        ProductoTextil, ProductoTextil.id == LoteProducto.producto_id
    ).where(
        VentaPOS.tenant_id == current_user.tenant_id,
        VentaPOS.estado == "completada"
    ).group_by(ProductoTextil.nombre).order_by(func.sum(DetalleVentaPOS.subtotal).desc()).limit(5)
    res_productos = await db.execute(stmt_productos)
    productos_data = [{"nombre": r[0], "cantidad": r[1], "monto": r[2]} for r in res_productos.all()]

    # Ventas por cliente
    stmt_clientes = select(
        Cliente.razon_social,
        func.sum(VentaPOS.total).label("monto")
    ).join(
        VentaPOS, VentaPOS.cliente_id == Cliente.id
    ).where(
        VentaPOS.tenant_id == current_user.tenant_id,
        VentaPOS.estado == "completada"
    ).group_by(Cliente.razon_social).order_by(func.sum(VentaPOS.total).desc()).limit(5)
    res_clientes = await db.execute(stmt_clientes)
    clientes_data = [{"cliente": r[0], "monto": r[1]} for r in res_clientes.all()]

    return {
        "total_monto": total_monto,
        "vendedores": vendedores_data,
        "productos": productos_data,
        "clientes": clientes_data
    }

from typing import Optional
from pydantic import BaseModel

class ConfiguracionVentaUpdate(BaseModel):
    encabezado_ticket: Optional[str] = None
    pie_ticket: Optional[str] = None
    permite_credito: Optional[bool] = None
    metodos_pago_permitidos: Optional[str] = None
    equipos_ventas: Optional[str] = None

@router.get("/configuracion")
async def get_configuracion_ventas(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    from app.models.sales import ConfiguracionVenta
    stmt = select(ConfiguracionVenta).where(ConfiguracionVenta.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()
    
    if not config:
        config = ConfiguracionVenta(tenant_id=current_user.tenant_id)
        db.add(config)
        await db.commit()
        await db.refresh(config)
        
    return config

@router.put("/configuracion")
async def update_configuracion_ventas(
    config_req: ConfiguracionVentaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    from app.models.sales import ConfiguracionVenta
    stmt = select(ConfiguracionVenta).where(ConfiguracionVenta.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()
    
    if not config:
        config = ConfiguracionVenta(tenant_id=current_user.tenant_id)
        db.add(config)
        await db.flush()
        
    if config_req.encabezado_ticket is not None:
        config.encabezado_ticket = config_req.encabezado_ticket
    if config_req.pie_ticket is not None:
        config.pie_ticket = config_req.pie_ticket
    if config_req.permite_credito is not None:
        config.permite_credito = config_req.permite_credito
    if config_req.metodos_pago_permitidos is not None:
        config.metodos_pago_permitidos = config_req.metodos_pago_permitidos
    if config_req.equipos_ventas is not None:
        config.equipos_ventas = config_req.equipos_ventas
        
    await db.commit()
    await db.refresh(config)
    return config
