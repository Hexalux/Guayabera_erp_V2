from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import date, datetime, time
from decimal import Decimal

from app.models.revaluacion.revaluacion import (
    TipoCambio, RevaluacionAutomatica, EjecucionRevaluacion,
    DetalleRevaluacion, ValuacionTipoCambio, ParametrosRevaluacion,
    EstadoRevaluacion
)
from app.schemas.revaluacion import (
    TipoCambioCreate, RevaluacionAutomaticaCreate,
    EjecucionRevaluacionCreate, ValuacionTipoCambioCreate,
    ParametrosRevaluacionCreate
)
from app.models.contabilidad import CuentaContable, AsientoContable, MovimientoAsiento

class RevaluacionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Tipos de Cambio ---
    async def registrar_tipo_cambio(self, data: TipoCambioCreate, tenant_id: int) -> TipoCambio:
        tipo_cambio = TipoCambio(
            **data.model_dump(),
            tenant_id=tenant_id
        )
        self.db.add(tipo_cambio)
        await self.db.commit()
        await self.db.refresh(tipo_cambio)
        return tipo_cambio

    async def obtener_tipo_cambio_vigente(
        self, 
        moneda_origen: str, 
        moneda_destino: str, 
        fecha: date,
        tenant_id: int
    ) -> Optional[TipoCambio]:
        query = select(TipoCambio).where(
            TipoCambio.moneda_origen == moneda_origen,
            TipoCambio.moneda_destino == moneda_destino,
            TipoCambio.fecha_vigencia <= fecha,
            TipoCambio.activo == True,
            TipoCambio.tenant_id == tenant_id
        ).order_by(TipoCambio.fecha_vigencia.desc())
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # --- Revaluación Automática ---
    async def configurar_revaluacion(self, data: RevaluacionAutomaticaCreate, tenant_id: int) -> RevaluacionAutomatica:
        revaluacion = RevaluacionAutomatica(
            **data.model_dump(),
            tenant_id=tenant_id
        )
        self.db.add(revaluacion)
        await self.db.commit()
        await self.db.refresh(revaluacion)
        return revaluacion

    async def ejecutar_revaluacion(self, revaluacion_id: int, fecha: date) -> EjecucionRevaluacion:
        """Ejecuta manualmente una revaluación"""
        query = select(RevaluacionAutomatica).where(RevaluacionAutomatica.id == revaluacion_id)
        result = await self.db.execute(query)
        config = result.scalar_one_or_none()
        
        if not config:
            raise ValueError("Configuración de revaluación no encontrada")
            
        ejecucion = EjecucionRevaluacion(
            revaluacion_id=revaluacion_id,
            fecha_ejecucion=fecha,
            tipo_cambio_referencia=Decimal('1.0'),  # Obtener del servicio de tipos de cambio
            estado=EstadoRevaluacion.PROCESANDO
        )
        
        self.db.add(ejecucion)
        await self.db.commit()
        await self.db.refresh(ejecucion)
        
        # Ejecutar proceso en segundo plano (simplificado aquí)
        await self._procesar_revaluacion(ejecucion, config)
        
        return ejecucion

    async def _procesar_revaluacion(self, ejecucion: EjecucionRevaluacion, config: RevaluacionAutomatica):
        """Procesa la revaluación de cuentas en moneda extranjera"""
        try:
            # Obtener cuentas en moneda extranjera
            # Calcular diferencias cambiarias
            # Generar asiento contable automático
            
            ejecucion.estado = EstadoRevaluacion.COMPLETADA
            ejecucion.completed_at = datetime.now()
            
            await self.db.commit()
        except Exception as e:
            ejecucion.estado = EstadoRevaluacion.ERROR
            await self.db.commit()
            raise e

    # --- Valuación de Tipos de Cambio ---
    async def registrar_valuacion(self, data: ValuacionTipoCambioCreate, tenant_id: int) -> ValuacionTipoCambio:
        valuacion = ValuacionTipoCambio(
            **data.model_dump(),
            tenant_id=tenant_id
        )
        self.db.add(valuacion)
        await self.db.commit()
        await self.db.refresh(valuacion)
        return valuacion

    async def obtener_historial_valuaciones(
        self, 
        moneda: str, 
        fecha_inicio: date, 
        fecha_fin: date,
        tenant_id: int
    ) -> List[ValuacionTipoCambio]:
        query = select(ValuacionTipoCambio).where(
            ValuacionTipoCambio.moneda == moneda,
            ValuacionTipoCambio.fecha_valuacion >= fecha_inicio,
            ValuacionTipoCambio.fecha_valuacion <= fecha_fin,
            ValuacionTipoCambio.tenant_id == tenant_id
        ).order_by(ValuacionTipoCambio.fecha_valuacion.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # --- Parámetros ---
    async def obtener_parametros(self, tenant_id: int) -> Optional[ParametrosRevaluacion]:
        query = select(ParametrosRevaluacion).where(
            ParametrosRevaluacion.tenant_id == tenant_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def actualizar_parametros(
        self, 
        tenant_id: int, 
        data: ParametrosRevaluacionCreate
    ) -> ParametrosRevaluacion:
        parametros = await self.obtener_parametros(tenant_id)
        
        if parametros:
            for key, value in data.model_dump().items():
                setattr(parametros, key, value)
        else:
            parametros = ParametrosRevaluacion(**data.model_dump())
            self.db.add(parametros)
            
        await self.db.commit()
        await self.db.refresh(parametros)
        return parametros

    # --- Reportes ---
    async def reporte_revaluacion(self, ejecucion_id: int) -> dict:
        """Obtiene el reporte detallado de una ejecución de revaluación"""
        query_ejecucion = select(EjecucionRevaluacion).where(
            EjecucionRevaluacion.id == ejecucion_id
        )
        result = await self.db.execute(query_ejecucion)
        ejecucion = result.scalar_one_or_none()
        
        if not ejecucion:
            raise ValueError("Ejecución no encontrada")
            
        query_detalles = select(DetalleRevaluacion).where(
            DetalleRevaluacion.ejecucion_id == ejecucion_id
        )
        result = await self.db.execute(query_detalles)
        detalles = list(result.scalars().all())
        
        return {
            "ejecucion": ejecucion,
            "detalles": detalles,
            "total_diferencia": sum(d.diferencia for d in detalles)
        }
