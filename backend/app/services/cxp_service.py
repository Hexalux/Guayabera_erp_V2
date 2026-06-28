from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import joinedload
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal

from app.models.cxp import (
    Proveedor, FacturaProveedor, PagoProveedor, 
    NotaCreditoProveedor, RetencionProveedor, AnticipoProveedor,
    AplicacionPagoFactura, MovimientoFacturaProveedor, EstadoFactura, EstadoPago
)
from app.schemas.cxp import (
    ProveedorCreate, ProveedorUpdate, FacturaProveedorCreate,
    PagoProveedorCreate, NotaCreditoProveedorCreate, RetencionProveedorCreate
)
from app.models.contabilidad import AsientoContable, PeriodoContable

class CXPService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Proveedores ---
    async def crear_proveedor(self, data: ProveedorCreate, tenant_id: int) -> Proveedor:
        proveedor = Proveedor(
            **data.model_dump(),
            tenant_id=tenant_id
        )
        self.db.add(proveedor)
        await self.db.commit()
        await self.db.refresh(proveedor)
        return proveedor

    async def obtener_proveedores(self, tenant_id: int, activo: bool = True) -> List[Proveedor]:
        query = select(Proveedor).where(
            Proveedor.tenant_id == tenant_id,
            Proveedor.activo == activo
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # --- Facturas de Proveedor ---
    async def registrar_factura(self, data: FacturaProveedorCreate, tenant_id: int) -> FacturaProveedor:
        # Validar que el período esté abierto
        periodo_abierto = await self._verificar_periodo_abierto(data.fecha_emision, tenant_id)
        if not periodo_abierto:
            raise ValueError(f"El período {data.fecha_emision.strftime('%Y-%m')} está cerrado")

        factura = FacturaProveedor(
            **data.model_dump(),
            estado=EstadoFactura.PENDIENTE,
            saldo_pendiente=data.total,
            tenant_id=tenant_id
        )
        
        # Registrar movimiento inicial
        movimiento = MovimientoFacturaProveedor(
            factura_id=factura.id,
            tipo_movimiento="REGISTRO",
            monto=data.total,
            saldo_resultante=data.total,
            fecha=data.fecha_emision
        )
        
        self.db.add(factura)
        self.db.add(movimiento)
        await self.db.commit()
        await self.db.refresh(factura)
        
        # Generar póliza contable automática si se configura
        # await self._generar_poliza_factura(factura)
        
        return factura

    async def aplicar_pago_factura(self, factura_id: int, pago_id: int, monto_aplicado: Decimal) -> AplicacionPagoFactura:
        factura = await self._obtener_factura(factura_id)
        pago = await self._obtener_pago(pago_id)
        
        if factura.saldo_pendiente < monto_aplicado:
            raise ValueError("Monto aplicado mayor al saldo pendiente")
        
        aplicacion = AplicacionPagoFactura(
            factura_id=factura_id,
            pago_id=pago_id,
            monto_aplicado=monto_aplicado
        )
        
        # Actualizar saldo de factura
        factura.saldo_pendiente -= monto_aplicado
        if factura.saldo_pendiente == 0:
            factura.estado = EstadoFactura.PAGADA
        else:
            factura.estado = EstadoFactura.PARCIAL
            
        # Registrar movimiento
        movimiento = MovimientoFacturaProveedor(
            factura_id=factura_id,
            tipo_movimiento="PAGO_PARCIAL" if factura.estado != EstadoFactura.PAGADA else "PAGO_TOTAL",
            monto=-monto_aplicado,
            saldo_resultante=factura.saldo_pendiente,
            fecha=datetime.now().date()
        )
        
        self.db.add(aplicacion)
        self.db.add(movimiento)
        await self.db.commit()
        
        return aplicacion

    async def registrar_pago(self, data: PagoProveedorCreate, tenant_id: int) -> PagoProveedor:
        pago = PagoProveedor(
            **data.model_dump(exclude=['facturas_a_pagar']),
            estado=EstadoPago.AUTORIZADO if not data.es_anticipo else EstadoPago.PAGADO,
            tenant_id=tenant_id
        )
        
        self.db.add(pago)
        await self.db.commit()
        await self.db.refresh(pago)
        
        # Si hay facturas seleccionadas, aplicar pagos
        if data.facturas_a_pagar and not data.es_anticipo:
            monto_total = data.monto
            for factura_id in data.facturas_a_pagar:
                # Calcular monto proporcional o secuencial
                # Simplificado: aplica secuencialmente hasta agotar monto
                pass
                
        return pago

    async def registrar_nota_credito(self, data: NotaCreditoProveedorCreate, tenant_id: int) -> NotaCreditoProveedor:
        nota = NotaCreditoProveedor(
            **data.model_dump(),
            aplicada=False,
            tenant_id=tenant_id
        )
        self.db.add(nota)
        await self.db.commit()
        await self.db.refresh(nota)
        return nota

    async def registrar_retencion(self, data: RetencionProveedorCreate, tenant_id: int) -> RetencionProveedor:
        retencion = RetencionProveedor(
            **data.model_dump(),
            tenant_id=tenant_id
        )
        self.db.add(retencion)
        await self.db.commit()
        await self.db.refresh(retencion)
        return retencion

    # --- Reportes y Consultas ---
    async def obtener_cuentas_por_pagar(self, tenant_id: int, fecha_corte: Optional[date] = None) -> dict:
        """Obtiene el resumen de CXP"""
        if not fecha_corte:
            fecha_corte = date.today()
            
        query = select(
            Proveedor.nombre,
            func.sum(FacturaProveedor.saldo_pendiente).label('total_pendiente')
        ).join(
            FacturaProveedor, Proveedor.id == FacturaProveedor.proveedor_id
        ).where(
            Proveedor.tenant_id == tenant_id,
            FacturaProveedor.fecha_vencimiento <= fecha_corte,
            FacturaProveedor.saldo_pendiente > 0
        ).group_by(Proveedor.nombre)
        
        result = await self.db.execute(query)
        return result.fetchall()

    async def _obtener_factura(self, factura_id: int) -> FacturaProveedor:
        query = select(FacturaProveedor).where(FacturaProveedor.id == factura_id)
        result = await self.db.execute(query)
        factura = result.scalar_one_or_none()
        if not factura:
            raise ValueError("Factura no encontrada")
        return factura

    async def _obtener_pago(self, pago_id: int) -> PagoProveedor:
        query = select(PagoProveedor).where(PagoProveedor.id == pago_id)
        result = await self.db.execute(query)
        pago = result.scalar_one_or_none()
        if not pago:
            raise ValueError("Pago no encontrado")
        return pago

    async def _verificar_periodo_abierto(self, fecha: date, tenant_id: int) -> bool:
        """Verifica si el período contable está abierto"""
        # Implementación simplificada - debería buscar en tabla PeriodoContable
        return True
