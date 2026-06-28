from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal

from app.models.gastos.gasto import (
    CategoriaGasto, Gasto, GastoViaje, GastoViajeDetalle,
    NominaGasto, DepreciacionActivo, ReclasificacionGasto,
    PresupuestoGasto, EstadoGasto
)
from app.schemas.gastos import (
    CategoriaGastoCreate, GastoCreate, GastoViajeCreate,
    GastoViajeDetalleCreate, NominaGastoCreate, DepreciacionActivoCreate,
    PresupuestoGastoCreate
)

class GastosService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Categorías ---
    async def crear_categoria(self, data: CategoriaGastoCreate, tenant_id: int) -> CategoriaGasto:
        categoria = CategoriaGasto(
            **data.model_dump(),
            tenant_id=tenant_id
        )
        self.db.add(categoria)
        await self.db.commit()
        await self.db.refresh(categoria)
        return categoria

    async def obtener_categorias(self, tenant_id: int, activo: bool = True) -> List[CategoriaGasto]:
        query = select(CategoriaGasto).where(
            CategoriaGasto.tenant_id == tenant_id,
            CategoriaGasto.activo == activo
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # --- Gastos ---
    async def registrar_gasto(self, data: GastoCreate, tenant_id: int, usuario_id: int) -> Gasto:
        gasto = Gasto(
            **data.model_dump(),
            creado_por=usuario_id,
            tenant_id=tenant_id
        )
        self.db.add(gasto)
        await self.db.commit()
        await self.db.refresh(gasto)
        return gasto

    async def aprobar_gasto(self, gasto_id: int, usuario_id: int) -> Gasto:
        query = select(Gasto).where(Gasto.id == gasto_id)
        result = await self.db.execute(query)
        gasto = result.scalar_one_or_none()
        
        if not gasto:
            raise ValueError("Gasto no encontrado")
            
        gasto.estado = EstadoGasto.APROBADO
        gasto.aprobado_por = usuario_id
        
        await self.db.commit()
        await self.db.refresh(gasto)
        return gasto

    # --- Gastos de Viaje ---
    async def crear_gasto_viaje(self, data: GastoViajeCreate, tenant_id: int) -> GastoViaje:
        gasto_viaje = GastoViaje(
            **data.model_dump(),
            tenant_id=tenant_id
        )
        self.db.add(gasto_viaje)
        await self.db.commit()
        await self.db.refresh(gasto_viaje)
        return gasto_viaje

    async def agregar_detalle_viaje(self, data: GastoViajeDetalleCreate) -> GastoViajeDetalle:
        detalle = GastoViajeDetalle(**data.model_dump())
        self.db.add(detalle)
        
        # Actualizar total del viaje
        query = select(func.sum(GastoViajeDetalle.monto)).where(
            GastoViajeDetalle.gasto_viaje_id == data.gasto_viaje_id
        )
        result = await self.db.execute(query)
        total = result.scalar() or 0
        
        viaje_query = select(GastoViaje).where(GastoViaje.id == data.gasto_viaje_id)
        viaje_result = await self.db.execute(viaje_query)
        viaje = viaje_result.scalar_one()
        viaje.total_gastos = total
        
        await self.db.commit()
        await self.db.refresh(detalle)
        return detalle

    # --- Nómina ---
    async def registrar_nomina(self, data: NominaGastoCreate, tenant_id: int) -> NominaGasto:
        nomina = NominaGasto(
            **data.model_dump(),
            tenant_id=tenant_id
        )
        self.db.add(nomina)
        await self.db.commit()
        await self.db.refresh(nomina)
        return nomina

    # --- Depreciación ---
    async def registrar_depreciacion(self, data: DepreciacionActivoCreate, tenant_id: int) -> DepreciacionActivo:
        activo = DepreciacionActivo(
            **data.model_dump(),
            valor_libros=data.valor_original,
            depreciacion_acumulada=0,
            tenant_id=tenant_id
        )
        self.db.add(activo)
        await self.db.commit()
        await self.db.refresh(activo)
        return activo

    async def calcular_depreciacion_mensual(self, activo_id: int) -> Decimal:
        """Calcula la depreciación mensual por línea recta"""
        query = select(DepreciacionActivo).where(DepreciacionActivo.id == activo_id)
        result = await self.db.execute(query)
        activo = result.scalar_one_or_none()
        
        if not activo:
            raise ValueError("Activo no encontrado")
            
        if activo.metodo_depreciacion == "linea_recta":
            base_depreciable = activo.valor_original - activo.valor_residual
            depreciacion_mensual = base_depreciable / activo.vida_util_meses
        else:
            # Implementar otros métodos
            depreciacion_mensual = Decimal(0)
            
        return depreciacion_mensual

    # --- Presupuesto ---
    async def crear_presupuesto(self, data: PresupuestoGastoCreate, tenant_id: int) -> PresupuestoGasto:
        presupuesto = PresupuestoGasto(
            **data.model_dump(),
            variacion=0,
            tenant_id=tenant_id
        )
        self.db.add(presupuesto)
        await self.db.commit()
        await self.db.refresh(presupuesto)
        return presupuesto

    async def obtener_reporte_gastos(
        self, 
        tenant_id: int, 
        fecha_inicio: date, 
        fecha_fin: date,
        categoria_id: Optional[int] = None
    ) -> List[dict]:
        """Reporte analítico de gastos"""
        query = select(
            Gasto.descripcion,
            Gasto.fecha,
            Gasto.monto,
            Gasto.estado,
            CategoriaGasto.nombre.label('categoria')
        ).join(
            CategoriaGasto, Gasto.categoria_id == CategoriaGasto.id, isouter=True
        ).where(
            Gasto.tenant_id == tenant_id,
            Gasto.fecha >= fecha_inicio,
            Gasto.fecha <= fecha_fin
        )
        
        if categoria_id:
            query = query.where(Gasto.categoria_id == categoria_id)
            
        result = await self.db.execute(query)
        return [dict(row._mapping) for row in result]
