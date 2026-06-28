"""
Servicios para el módulo de Tesorería - Caja
Inspirado en CONTPAQi (robustez), Odoo (flexibilidad) y Management Pro (opciones)
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import HTTPException

# Importación lazy para evitar circular import
def get_caja_models():
    from app.models.tesoreria import caja
    return caja


class AppException(Exception):
    """Excepción personalizada para la aplicación"""
    pass


class CajaService:
    """Gestión de Cajas y Puntos de Venta"""
    
    @staticmethod
    async def crear_caja(
        db: AsyncSession,
        tenant_id: UUID,
        nombre: str,
        codigo: str,
        sucursal_id: Optional[UUID] = None,
        responsable_id: Optional[UUID] = None,
        moneda: str = "USD",
        activo: bool = True
    ) -> Any:
        """Crear una nueva caja"""
        # Verificar unicidad de código por tenant
        result = await db.execute(
            select(Caja).where(
                Caja.codigo == codigo,
                Caja.tenant_id == tenant_id
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise AppException(f"Ya existe una caja con código {codigo}")
        
        caja = Caja(
            tenant_id=tenant_id,
            nombre=nombre,
            codigo=codigo,
            sucursal_id=sucursal_id,
            responsable_id=responsable_id,
            moneda=moneda,
            activo=activo,
            saldo_actual=0.0
        )
        db.add(caja)
        await db.commit()
        await db.refresh(caja)
        return caja
    
    @staticmethod
    async def obtener_cajas(
        db: AsyncSession,
        tenant_id: UUID,
        sucursal_id: Optional[UUID] = None,
        activo: Optional[bool] = None
    ) -> List[Any]:
        """Obtener todas las cajas filtradas"""
        query = select(Caja).where(Caja.tenant_id == tenant_id)
        
        if sucursal_id:
            query = query.where(Caja.sucursal_id == sucursal_id)
        if activo is not None:
            query = query.where(Caja.activo == activo)
        
        result = await db.execute(query.order_by(Caja.nombre))
        return list(result.scalars().all())
    
    @staticmethod
    async def actualizar_saldo(
        db: AsyncSession,
        caja_id: UUID,
        monto: float,
        tipo_movimiento: str,
        descripcion: str,
        usuario_id: UUID
    ) -> Any:
        """Actualizar saldo de caja con validación"""
        result = await db.execute(select(Caja).where(Caja.id == caja_id))
        caja = result.scalar_one_or_none()
        if not caja:
            raise AppException("Caja no encontrada")
        
        if tipo_movimiento == "EGRESO" and caja.saldo_actual < abs(monto):
            raise AppException(f"Saldo insuficiente. Saldo actual: {caja.saldo_actual}")
        
        if tipo_movimiento == "INGRESO":
            caja.saldo_actual += monto
        else:
            caja.saldo_actual -= abs(monto)
        
        # Registrar movimiento
        movimiento = TipoMovimientoCaja(
            caja_id=caja_id,
            tipo=tipo_movimiento,
            monto=abs(monto),
            descripcion=descripcion,
            usuario_id=usuario_id,
            saldo_anterior=caja.saldo_actual - (monto if tipo_movimiento == "INGRESO" else -abs(monto)),
            saldo_nuevo=caja.saldo_actual
        )
        db.add(movimiento)
        await db.commit()
        await db.refresh(caja)
        return caja


class ReciboCajaService:
    """Gestión de Recibos de Caja - Estilo CONTPAQi con series consecutivas"""
    
    @staticmethod
    async def crear_recibo(
        db: AsyncSession,
        tenant_id: UUID,
        caja_id: UUID,
        serie: str,
        cliente_id: Optional[UUID] = None,
        concepto: str = "",
        monto: float = 0.0,
        forma_pago: str = "EFECTIVO",  # EFECTIVO, CHEQUE, TRANSFERENCIA, TARJETA
        referencia: str = "",
        aplicar_a_cxc: bool = False,
        factura_id: Optional[UUID] = None
    ) -> Any:
        """Crear recibo de caja con numeración automática"""
        # Obtener último consecutivo de la serie
        result = await db.execute(
            select(ReciboCaja)
            .where(ReciboCaja.tenant_id == tenant_id)
            .where(ReciboCaja.caja_id == caja_id)
            .where(ReciboCaja.serie == serie)
            .order_by(ReciboCaja.consecutivo.desc())
            .limit(1)
        )
        ultimo_recibo = result.scalar_one_or_none()
        consecutivo = (ultimo_recibo.consecutivo + 1) if ultimo_recibo else 1
        
        recibo = ReciboCaja(
            tenant_id=tenant_id,
            caja_id=caja_id,
            serie=serie,
            consecutivo=consecutivo,
            cliente_id=cliente_id,
            concepto=concepto,
            monto=monto,
            forma_pago=forma_pago,
            referencia=referencia,
            aplicar_a_cxc=aplicar_a_cxc,
            factura_id=factura_id,
            estado="ACTIVO"
        )
        db.add(recibo)
        
        # Actualizar saldo de caja
        caja_service = CajaService()
        await caja_service.actualizar_saldo(
            db=db,
            caja_id=caja_id,
            monto=monto,
            tipo_movimiento="INGRESO",
            descripcion=f"Recibo {serie}-{consecutivo}: {concepto}",
            usuario_id=UUID(int=0)  # TODO: Pasar usuario real
        )
        
        await db.commit()
        await db.refresh(recibo)
        return recibo
    
    @staticmethod
    async def anular_recibo(
        db: AsyncSession,
        recibo_id: UUID,
        motivo: str,
        usuario_id: UUID
    ) -> Any:
        """Anular recibo de caja"""
        result = await db.execute(select(ReciboCaja).where(ReciboCaja.id == recibo_id))
        recibo = result.scalar_one_or_none()
        if not recibo:
            raise AppException("Recibo no encontrado")
        
        if recibo.estado != "ACTIVO":
            raise AppException(f"El recibo ya está {recibo.estado}")
        
        recibo.estado = "ANULADO"
        recibo.motivo_anulacion = motivo
        recibo.usuario_anulo = usuario_id
        recibo.fecha_anulacion = datetime.utcnow()
        
        # Revertir saldo de caja
        caja_service = CajaService()
        await caja_service.actualizar_saldo(
            db=db,
            caja_id=recibo.caja_id,
            monto=recibo.monto,
            tipo_movimiento="EGRESO",
            descripcion=f"Anulación recibo {recibo.serie}-{recibo.consecutivo}: {motivo}",
            usuario_id=usuario_id
        )
        
        await db.commit()
        return recibo
    
    @staticmethod
    async def depositar_recibos(
        db: AsyncSession,
        tenant_id: UUID,
        caja_id: UUID,
        banco_id: UUID,
        recibos_ids: List[UUID],
        numero_deposito: str,
        fecha_deposito: date,
        usuario_id: UUID
    ) -> Dict[str, Any]:
        """Depositar múltiples recibos de caja al banco"""
        total = 0.0
        for recibo_id in recibos_ids:
            result = await db.execute(select(ReciboCaja).where(ReciboCaja.id == recibo_id))
            recibo = result.scalar_one_or_none()
            if recibo and recibo.caja_id == caja_id and recibo.estado == "ACTIVO":
                total += recibo.monto
        
        if total == 0:
            raise AppException("No hay recibos válidos para depositar")
        
        # Reducir saldo de caja
        caja_service = CajaService()
        await caja_service.actualizar_saldo(
            db=db,
            caja_id=caja_id,
            monto=total,
            tipo_movimiento="EGRESO",
            descripcion=f"Depósito bancario {numero_deposito}",
            usuario_id=usuario_id
        )
        
        # TODO: Crear registro en módulo de bancos
        # El saldo se aumentará en la cuenta bancaria correspondiente
        
        return {"total_depositado": total, "numero_deposito": numero_deposito}


class LiquidacionSucursalService:
    """Liquidación diaria de sucursales"""
    
    @staticmethod
    async def crear_liquidacion(
        db: AsyncSession,
        tenant_id: UUID,
        sucursal_id: UUID,
        fecha: date,
        usuario_id: UUID
    ) -> Any:
        """Crear liquidación de sucursal"""
        # Verificar que no exista ya para esa fecha
        result = await db.execute(
            select(LiquidacionSucursal).where(
                LiquidacionSucursal.tenant_id == tenant_id,
                LiquidacionSucursal.sucursal_id == sucursal_id,
                LiquidacionSucursal.fecha == fecha
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise AppException(f"Ya existe liquidación para {fecha}")
        
        # Sumar todos los movimientos de cajas de la sucursal
        # Esto requiere join con Cajas y Movimientos
        # Implementación simplificada
        liquidacion = LiquidacionSucursal(
            tenant_id=tenant_id,
            sucursal_id=sucursal_id,
            fecha=fecha,
            efectivo=0.0,
            cheques=0.0,
            tarjetas=0.0,
            transferencias=0.0,
            total=0.0,
            estado="BORRADOR"
        )
        db.add(liquidacion)
        await db.commit()
        await db.refresh(liquidacion)
        return liquidacion
    
    @staticmethod
    async def calcular_totales(
        db: AsyncSession,
        liquidacion_id: UUID
    ) -> Any:
        """Calcular totales de la liquidación"""
        result = await db.execute(
            select(LiquidacionSucursal).where(LiquidacionSucursal.id == liquidacion_id)
        )
        liquidacion = result.scalar_one_or_none()
        if not liquidacion:
            raise AppException("Liquidación no encontrada")
        
        # TODO: Calcular sumas reales desde movimientos de caja
        # Por ahora, cálculo placeholder
        liquidacion.total = liquidacion.efectivo + liquidacion.cheques + liquidacion.tarjetas + liquidacion.transferencias
        liquidacion.estado = "CALCULADA"
        
        await db.commit()
        await db.refresh(liquidacion)
        return liquidacion


class LiquidacionVendedorService:
    """Liquidación de vendedores con cálculo de comisiones"""
    
    @staticmethod
    async def crear_liquidacion(
        db: AsyncSession,
        tenant_id: UUID,
        vendedor_id: UUID,
        fecha_inicio: date,
        fecha_fin: date,
        usuario_id: UUID
    ) -> Any:
        """Crear liquidación de vendedor"""
        liquidacion = LiquidacionVendedor(
            tenant_id=tenant_id,
            vendedor_id=vendedor_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            ventas_contado=0.0,
            ventas_credito=0.0,
            cobros_realizados=0.0,
            comisiones_devengadas=0.0,
            anticipo_comisiones=0.0,
            neto_pagar=0.0,
            estado="BORRADOR"
        )
        db.add(liquidacion)
        await db.commit()
        await db.refresh(liquidacion)
        return liquidacion
    
    @staticmethod
    async def calcular_comisiones(
        db: AsyncSession,
        liquidacion_id: UUID,
        porcentaje_comision: float = 0.0
    ) -> Any:
        """Calcular comisiones del vendedor"""
        result = await db.execute(
            select(LiquidacionVendedor).where(LiquidacionVendedor.id == liquidacion_id)
        )
        liquidacion = result.scalar_one_or_none()
        if not liquidacion:
            raise AppException("Liquidación no encontrada")
        
        # TODO: Calcular desde ventas reales
        # Placeholder
        base_comision = liquidacion.ventas_contado + liquidacion.cobros_realizados
        liquidacion.comisiones_devengadas = base_comision * (porcentaje_comision / 100)
        liquidacion.neto_pagar = liquidacion.comisiones_devengadas - liquidacion.anticipo_comisiones
        liquidacion.estado = "CALCULADA"
        
        await db.commit()
        await db.refresh(liquidacion)
        return liquidacion


class RecepcionValoresService:
    """Recepción de valores (cheques, pagarés)"""
    
    @staticmethod
    async def registrar_valor(
        db: AsyncSession,
        tenant_id: UUID,
        caja_id: UUID,
        tipo_valor: str,  # CHEQUE, PAGARE, TARJETA
        numero: str,
        banco_librador: str,
        monto: float,
        fecha_emision: date,
        fecha_vencimiento: Optional[date] = None,
        cliente_id: Optional[UUID] = None,
        observations: str = ""
    ) -> Any:
        """Registrar recepción de valor"""
        valor = RecepcionValores(
            tenant_id=tenant_id,
            caja_id=caja_id,
            tipo_valor=tipo_valor,
            numero=numero,
            banco_librador=banco_librador,
            monto=monto,
            fecha_emision=fecha_emision,
            fecha_vencimiento=fecha_vencimiento,
            cliente_id=cliente_id,
            observations=observations,
            estado="RECIBIDO"
        )
        db.add(valor)
        await db.commit()
        await db.refresh(valor)
        return valor
    
    @staticmethod
    async def rebotar_valor(
        db: AsyncSession,
        valor_id: UUID,
        motivo: str,
        usuario_id: UUID
    ) -> Any:
        """Marcar valor como rebotado"""
        result = await db.execute(select(RecepcionValores).where(RecepcionValores.id == valor_id))
        valor = result.scalar_one_or_none()
        if not valor:
            raise AppException("Valor no encontrado")
        
        valor.estado = "REBOTADO"
        valor.motivo_rebote = motivo
        valor.usuario_reboto = usuario_id
        valor.fecha_rebote = datetime.utcnow()
        
        await db.commit()
        await db.refresh(valor)
        return valor


class ArqueoCajaService:
    """Arqueos de caja (cortes ciegos)"""
    
    @staticmethod
    async def crear_arqueo(
        db: AsyncSession,
        caja_id: UUID,
        usuario_id: UUID,
        fecha_corte: datetime,
        turno: str = "MATUTINO"  # MATUTINO, VESPERTINO, NOCTURNO
    ) -> Any:
        """Crear arqueo de caja"""
        arqueo = ArqueoCaja(
            caja_id=caja_id,
            usuario_id=usuario_id,
            fecha_corte=fecha_corte,
            turno=turno,
            efectivo_contado=0.0,
            cheques_monto=0.0,
            tarjetas_monto=0.0,
            otros_monto=0.0,
            total_sistema=0.0,
            diferencia=0.0,
            estado="ABIERTO"
        )
        db.add(arqueo)
        await db.commit()
        await db.refresh(arqueo)
        return arqueo
    
    @staticmethod
    async def cerrar_arqueo(
        db: AsyncSession,
        arqueo_id: UUID,
        usuario_id: UUID
    ) -> Any:
        """Cerrar arqueo calculando diferencias"""
        result = await db.execute(select(ArqueoCaja).where(ArqueoCaja.id == arqueo_id))
        arqueo = result.scalar_one_or_none()
        if not arqueo:
            raise AppException("Arqueo no encontrado")
        
        total_contado = (
            arqueo.efectivo_contado + 
            arqueo.cheques_monto + 
            arqueo.tarjetas_monto + 
            arqueo.otros_monto
        )
        
        arqueo.diferencia = total_contado - arqueo.total_sistema
        arqueo.estado = "CERRADO"
        arqueo.usuario_cierre = usuario_id
        arqueo.fecha_cierre = datetime.utcnow()
        
        await db.commit()
        await db.refresh(arqueo)
        return arqueo


class CorteCajaService:
    """Cortes de caja parciales o por turno"""
    
    @staticmethod
    async def crear_corte(
        db: AsyncSession,
        caja_id: UUID,
        usuario_id: UUID,
        tipo_corte: str = "PARCIAL",  # PARCIAL, TURNO, DIARIO, GENERAL
        turno: Optional[str] = None
    ) -> Any:
        """Crear corte de caja"""
        corte = CorteCaja(
            caja_id=caja_id,
            usuario_id=usuario_id,
            tipo_corte=tipo_corte,
            turno=turno,
            estado="EN_PROCESO"
        )
        db.add(corte)
        await db.commit()
        await db.refresh(corte)
        return corte
    
    @staticmethod
    async def finalizar_corte(
        db: AsyncSession,
        corte_id: UUID,
        total_efectivo: float,
        total_cheques: float,
        total_tarjetas: float,
        total_transferencias: float,
        observaciones: str = "",
        usuario_id: UUID = None
    ) -> Any:
        """Finalizar corte de caja"""
        result = await db.execute(select(CorteCaja).where(CorteCaja.id == corte_id))
        corte = result.scalar_one_or_none()
        if not corte:
            raise AppException("Corte no encontrado")
        
        corte.total_efectivo = total_efectivo
        corte.total_cheques = total_cheques
        corte.total_tarjetas = total_tarjetas
        corte.total_transferencias = total_transferencias
        corte.total_general = total_efectivo + total_cheques + total_tarjetas + total_transferencias
        corte.observaciones = observaciones
        corte.usuario_cierre = usuario_id
        corte.estado = "CERRADO"
        corte.fecha_cierre = datetime.utcnow()
        
        await db.commit()
        await db.refresh(corte)
        return corte
