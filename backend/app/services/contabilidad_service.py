from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import logging

from app.models.contabilidad import (
    CuentaContable, CentroCosto, PeriodoContable, 
    AsientoContable, MovimientoAsiento, NaturalezaCuenta
)
from app.schemas.contabilidad import (
    CuentaContableCreate, CuentaContableUpdate,
    CentroCostoCreate, CentroCostoUpdate,
    PeriodoContableCreate, PeriodoContableUpdate,
    AsientoContableCreate, AsientoContableUpdate,
    FiltroCuentasContables, FiltroAsientosContables
)

logger = logging.getLogger(__name__)


class ContabilidadService:
    """Servicio para operaciones de contabilidad"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==================== CUENTAS CONTABLES ====================
    
    async def crear_cuenta(self, cuenta_data: CuentaContableCreate, tenant_id: str, user_id: str) -> CuentaContable:
        """Crear una nueva cuenta contable"""
        cuenta = CuentaContable(
            **cuenta_data.dict(),
            tenant_id=tenant_id,
            created_by=user_id
        )
        
        if cuenta_data.parent_id:
            parent = await self.db.get(CuentaContable, cuenta_data.parent_id)
            if not parent or parent.tenant_id != tenant_id:
                raise ValueError("La cuenta padre no existe o no pertenece a este tenant")
            cuenta.nivel = parent.nivel + 1
        
        self.db.add(cuenta)
        await self.db.commit()
        await self.db.refresh(cuenta)
        return cuenta
    
    async def obtener_cuentas(
        self, 
        tenant_id: str, 
        filtro: Optional[FiltroCuentasContables] = None
    ) -> List[CuentaContable]:
        """Obtener lista de cuentas contables con filtros"""
        query = select(CuentaContable).where(CuentaContable.tenant_id == tenant_id)
        
        if filtro:
            if filtro.tipo_cuenta:
                query = query.where(CuentaContable.tipo_cuenta == filtro.tipo_cuenta)
            if filtro.es_activa is not None:
                query = query.where(CuentaContable.es_activa == filtro.es_activa)
            if filtro.parent_id:
                query = query.where(CuentaContable.parent_id == filtro.parent_id)
            if filtro.busca_codigo:
                query = query.where(CuentaContable.codigo.ilike(f"%{filtro.busca_codigo}%"))
            if filtro.busca_nombre:
                query = query.where(CuentaContable.nombre.ilike(f"%{filtro.busca_nombre}%"))
        
        query = query.order_by(CuentaContable.codigo)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def obtener_cuenta_por_id(self, cuenta_id: str, tenant_id: str) -> Optional[CuentaContable]:
        """Obtener una cuenta por ID"""
        query = select(CuentaContable).where(
            CuentaContable.id == cuenta_id,
            CuentaContable.tenant_id == tenant_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def actualizar_cuenta(self, cuenta_id: str, tenant_id: str, update_data: CuentaContableUpdate) -> Optional[CuentaContable]:
        """Actualizar una cuenta contable"""
        cuenta = await self.obtener_cuenta_por_id(cuenta_id, tenant_id)
        if not cuenta:
            return None
        
        update_dict = {k: v for k, v in update_data.dict(exclude_unset=True).items() if v is not None}
        for field, value in update_dict.items():
            setattr(cuenta, field, value)
        
        await self.db.commit()
        await self.db.refresh(cuenta)
        return cuenta
    
    async def eliminar_cuenta(self, cuenta_id: str, tenant_id: str) -> bool:
        """Eliminar una cuenta contable (solo si no tiene movimientos)"""
        cuenta = await self.obtener_cuenta_por_id(cuenta_id, tenant_id)
        if not cuenta:
            return False
        
        query = select(func.count()).select_from(MovimientoAsiento).where(
            MovimientoAsiento.cuenta_id == cuenta_id
        )
        result = await self.db.execute(query)
        count = result.scalar()
        
        if count > 0:
            raise ValueError("No se puede eliminar una cuenta con movimientos registrados")
        
        await self.db.delete(cuenta)
        await self.db.commit()
        return True
    
    # ==================== CENTROS DE COSTO ====================
    
    async def crear_centro_costo(self, centro_data: CentroCostoCreate, tenant_id: str) -> CentroCosto:
        """Crear un nuevo centro de costo"""
        centro = CentroCosto(**centro_data.dict(), tenant_id=tenant_id)
        
        if centro_data.parent_id:
            parent = await self.db.get(CentroCosto, centro_data.parent_id)
            if not parent or parent.tenant_id != tenant_id:
                raise ValueError("El centro de costo padre no existe")
            centro.nivel = parent.nivel + 1
        
        self.db.add(centro)
        await self.db.commit()
        await self.db.refresh(centro)
        return centro
    
    async def obtener_centros_costo(self, tenant_id: str, es_activo: bool = True) -> List[CentroCosto]:
        """Obtener centros de costo"""
        query = select(CentroCosto).where(
            CentroCosto.tenant_id == tenant_id,
            CentroCosto.es_activo == es_activo
        ).order_by(CentroCosto.codigo)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    # ==================== PERÍODOS CONTABLES ====================
    
    async def crear_periodo(self, periodo_data: PeriodoContableCreate, tenant_id: str) -> PeriodoContable:
        """Crear un nuevo período contable"""
        periodo = PeriodoContable(**periodo_data.dict(), tenant_id=tenant_id)
        self.db.add(periodo)
        await self.db.commit()
        await self.db.refresh(periodo)
        return periodo
    
    async def obtener_periodos(self, tenant_id: str) -> List[PeriodoContable]:
        """Obtener períodos contables"""
        query = select(PeriodoContable).where(
            PeriodoContable.tenant_id == tenant_id
        ).order_by(PeriodoContable.fecha_inicio.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def cerrar_periodo(self, periodo_id: str, tenant_id: str, user_id: str) -> bool:
        """Cerrar un período contable"""
        periodo = await self.db.get(PeriodoContable, periodo_id)
        if not periodo or periodo.tenant_id != tenant_id:
            return False
        
        periodo.esta_cerrado = True
        periodo.cerrado_por = user_id
        periodo.cerrado_en = datetime.utcnow()
        
        await self.db.commit()
        return True
    
    # ==================== ASIENTOS CONTABLES ====================
    
    async def crear_asiento(self, asiento_data: AsientoContableCreate, tenant_id: str, user_id: str) -> AsientoContable:
        """Crear un nuevo asiento contable con sus movimientos"""
        periodo = await self.db.get(PeriodoContable, asiento_data.periodo_id)
        if not periodo or periodo.tenant_id != tenant_id:
            raise ValueError("El período contable no existe")
        
        if periodo.esta_cerrado:
            raise ValueError("No se pueden crear asientos en un período cerrado")
        
        total_debito = sum(m.debito for m in asiento_data.movimientos)
        total_credito = sum(m.credito for m in asiento_data.movimientos)
        
        if total_debito != total_credito:
            raise ValueError(f"El asiento no cuadra. Débito: {total_debito}, Crédito: {total_credito}")
        
        query = select(func.max(AsientoContable.numero)).where(
            AsientoContable.tenant_id == tenant_id,
            AsientoContable.periodo_id == asiento_data.periodo_id
        )
        result = await self.db.execute(query)
        max_numero = result.scalar() or 0
        siguiente_numero = max_numero + 1
        
        estado_val = asiento_data.estado.value if hasattr(asiento_data.estado, 'value') else asiento_data.estado
        
        asiento = AsientoContable(
            numero=siguiente_numero,
            codigo_asiento=f"AS-{periodo.nombre}-{siguiente_numero:04d}",
            fecha=asiento_data.fecha,
            periodo_id=asiento_data.periodo_id,
            descripcion=asiento_data.descripcion,
            tipo_asiento=asiento_data.tipo_asiento,
            estado=estado_val,
            referencia_externa=asiento_data.referencia_externa,
            moneda=asiento_data.moneda,
            tasa_cambio=asiento_data.tasa_cambio,
            total_debito=total_debito,
            total_credito=total_credito,
            tenant_id=tenant_id,
            creado_por=user_id
        )
        
        self.db.add(asiento)
        await self.db.flush()
        
        for idx, mov_data in enumerate(asiento_data.movimientos):
            movimiento = MovimientoAsiento(
                asiento_id=asiento.id,
                cuenta_id=mov_data.cuenta_id,
                debito=mov_data.debito,
                credito=mov_data.credito,
                centro_costo_id=mov_data.centro_costo_id,
                tercero_id=mov_data.tercero_id,
                tipo_tercero=mov_data.tipo_tercero,
                descripcion=mov_data.descripcion,
                moneda=mov_data.moneda,
                tasa_cambio=mov_data.tasa_cambio,
                valor_original=mov_data.valor_original,
                orden=idx
            )
            self.db.add(movimiento)
        
        await self.db.commit()
        await self.db.refresh(asiento)
        return asiento
    
    async def obtener_asientos(
        self,
        tenant_id: str,
        filtro: Optional[FiltroAsientosContables] = None
    ) -> List[AsientoContable]:
        """Obtener asientos contables con filtros"""
        query = select(AsientoContable).where(
            AsientoContable.tenant_id == tenant_id
        ).options(
            selectinload(AsientoContable.movimientos).selectinload(MovimientoAsiento.cuenta)
        )
        
        if filtro:
            if filtro.fecha_desde:
                query = query.where(AsientoContable.fecha >= filtro.fecha_desde)
            if filtro.fecha_hasta:
                query = query.where(AsientoContable.fecha <= filtro.fecha_hasta)
            if filtro.periodo_id:
                query = query.where(AsientoContable.periodo_id == filtro.periodo_id)
            if filtro.estado:
                estado_val = filtro.estado.value if hasattr(filtro.estado, 'value') else filtro.estado
                query = query.where(AsientoContable.estado == estado_val)
        
        query = query.order_by(AsientoContable.fecha.desc(), AsientoContable.numero.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def obtener_asiento_por_id(self, asiento_id: str, tenant_id: str) -> Optional[AsientoContable]:
        """Obtener un asiento por ID con sus movimientos"""
        query = select(AsientoContable).where(
            AsientoContable.id == asiento_id,
            AsientoContable.tenant_id == tenant_id
        ).options(
            selectinload(AsientoContable.movimientos).selectinload(MovimientoAsiento.cuenta)
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def registrar_asiento(self, asiento_id: str, tenant_id: str, user_id: str) -> Optional[AsientoContable]:
        """Registrar un asiento"""
        asiento = await self.obtener_asiento_por_id(asiento_id, tenant_id)
        if not asiento or asiento.estado != "borrador":
            return None
        
        asiento.estado = "registrado"
        asiento.registrado_por = user_id
        asiento.registrado_en = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(asiento)
        return asiento
    
    async def anular_asiento(self, asiento_id: str, tenant_id: str, user_id: str) -> Optional[AsientoContable]:
        """Anular un asiento registrado"""
        asiento = await self.obtener_asiento_por_id(asiento_id, tenant_id)
        if not asiento or asiento.estado != "registrado":
            return None
        
        asiento.estado = "anulado"
        await self.db.commit()
        await self.db.refresh(asiento)
        return asiento
    
    # ==================== REPORTES ====================
    
    async def obtener_balance_comprobacion(
        self,
        tenant_id: str,
        fecha_desde: datetime,
        fecha_hasta: datetime,
        periodo_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generar balance de comprobación"""
        cuentas_query = select(CuentaContable).where(
            CuentaContable.tenant_id == tenant_id,
            CuentaContable.es_activa == True,
            CuentaContable.es_movimiento == True
        )
        cuentas_result = await self.db.execute(cuentas_query)
        cuentas = list(cuentas_result.scalars().all())
        
        items = []
        total_debito = Decimal('0')
        total_credito = Decimal('0')
        
        for cuenta in cuentas:
            query = select(
                func.sum(MovimientoAsiento.debito),
                func.sum(MovimientoAsiento.credito)
            ).join(
                AsientoContable, MovimientoAsiento.asiento_id == AsientoContable.id
            ).where(
                MovimientoAsiento.cuenta_id == cuenta.id,
                AsientoContable.tenant_id == tenant_id,
                AsientoContable.fecha >= fecha_desde,
                AsientoContable.fecha <= fecha_hasta,
                AsientoContable.estado == "registrado"
            )
            
            if periodo_id:
                query = query.where(AsientoContable.periodo_id == periodo_id)
            
            result = await self.db.execute(query)
            row = result.first()
            
            movimientos_debito = row[0] or Decimal('0')
            movimientos_credito = row[1] or Decimal('0')
            
            if cuenta.naturaleza == NaturalezaCuenta.DEUDORA:
                saldo_final_debito = movimientos_debito - movimientos_credito
                saldo_final_credito = Decimal('0')
                if saldo_final_debito < 0:
                    saldo_final_credito = abs(saldo_final_debito)
                    saldo_final_debito = Decimal('0')
            else:
                saldo_final_credito = movimientos_credito - movimientos_debito
                saldo_final_debito = Decimal('0')
                if saldo_final_credito < 0:
                    saldo_final_debito = abs(saldo_final_credito)
                    saldo_final_credito = Decimal('0')
            
            items.append({
                "cuenta_id": cuenta.id,
                "codigo": cuenta.codigo,
                "nombre": cuenta.nombre,
                "tipo_cuenta": cuenta.tipo_cuenta,
                "saldo_inicial_debito": Decimal('0'),
                "saldo_inicial_credito": Decimal('0'),
                "movimientos_debito": movimientos_debito,
                "movimientos_credito": movimientos_credito,
                "saldo_final_debito": saldo_final_debito,
                "saldo_final_credito": saldo_final_credito
            })
            
            total_debito += saldo_final_debito
            total_credito += saldo_final_credito
        
        return {
            "periodo_id": periodo_id,
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
            "items": items,
            "total_debito": total_debito,
            "total_credito": total_credito,
            "cuadra": total_debito == total_credito
        }
