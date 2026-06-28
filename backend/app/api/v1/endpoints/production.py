from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, String, cast
from typing import List
from datetime import date

from app.core.database import get_db
from app.models.usuario import Usuario
from app.api.deps import get_current_user

# Models
from app.models.production import OrdenProduccion, RecetaProduccion, CostoSubcontratacionMaquila
from app.models.inventory import ProductoTextil, LoteProducto, MovimientoInventario

# Schemas
from app.schemas.production import (
    OrdenProduccionCreate, OrdenProduccionResponse,
    RecetaProduccionCreate, RecetaProduccionResponse,
    CostoSubcontratacionMaquilaCreate, CostoSubcontratacionMaquilaResponse,
    FinalizarOrdenRequest,
    ProyectoProduccionCreate, ProyectoProduccionResponse
)

# Integración contable
from app.services.finance_auto import create_system_poliza
from app.models.finance import CuentaContable

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
# PROYECTOS DE PRODUCCIÓN
# =================================================================
@router.get("/proyectos", response_model=List[ProyectoProduccionResponse])
async def list_proyectos(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    from app.models.production import ProyectoProduccion
    stmt = select(ProyectoProduccion).where(ProyectoProduccion.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/proyectos", response_model=ProyectoProduccionResponse, status_code=status.HTTP_201_CREATED)
async def create_proyecto(
    proyecto: ProyectoProduccionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    from app.models.production import ProyectoProduccion
    db_proyecto = ProyectoProduccion(**proyecto.model_dump(), tenant_id=current_user.tenant_id, responsable_id=current_user.id)
    db.add(db_proyecto)
    await db.commit()
    await db.refresh(db_proyecto)
    return db_proyecto

# =================================================================
# RECETAS DE PRODUCCIÓN (BOM)
# =================================================================
@router.get("/recetas", response_model=List[RecetaProduccionResponse])
async def list_recetas(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(RecetaProduccion).where(RecetaProduccion.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/recetas", response_model=RecetaProduccionResponse, status_code=status.HTTP_201_CREATED)
async def create_receta(
    receta: RecetaProduccionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    db_receta = RecetaProduccion(**receta.model_dump(), tenant_id=current_user.tenant_id)
    db.add(db_receta)
    await db.commit()
    await db.refresh(db_receta)
    return db_receta


# =================================================================
# ÓRDENES DE PRODUCCIÓN
# =================================================================
@router.get("/ordenes", response_model=List[OrdenProduccionResponse])
async def list_ordenes(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(OrdenProduccion).where(OrdenProduccion.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/ordenes", response_model=OrdenProduccionResponse, status_code=status.HTTP_201_CREATED)
async def create_orden(
    orden: OrdenProduccionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    db_orden = OrdenProduccion(**orden.model_dump(), tenant_id=current_user.tenant_id)
    db.add(db_orden)
    await db.commit()
    await db.refresh(db_orden)
    return db_orden

@router.post("/ordenes/{orden_id}/finalizar", response_model=OrdenProduccionResponse)
async def finalizar_orden(
    orden_id: str,
    req: FinalizarOrdenRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Finaliza la orden, aplica consumo manual (para este ejemplo asume que ya fue consumido el material físicamente)
    Registra costo de maquila, ingresa PT al inventario y genera Póliza de Costo de Manufactura.
    """
    # Iniciamos transacción explícita ACID si no ha empezado
    if not db.in_transaction():
        await db.begin()
        
    try:
        stmt = select(OrdenProduccion).where(
            cast(OrdenProduccion.id, String) == orden_id,
            OrdenProduccion.tenant_id == current_user.tenant_id
        ).with_for_update() # Bloqueo pesimista para evitar que dos usuarios finalicen la misma orden
        
        result = await db.execute(stmt)
        db_orden = result.scalar_one_or_none()
        
        if not db_orden:
            raise HTTPException(status_code=404, detail="Orden de producción no encontrada")
            
        if db_orden.estado == "completado":
            raise HTTPException(status_code=400, detail="La orden ya está completada")

        # 1. Registrar Costo de Maquila si lo hay
        if req.costo_maquila_adicional > 0:
            db_maquila = CostoSubcontratacionMaquila(
                orden_produccion_id=orden_id,
                maquilador_nombre=req.maquilador_nombre or "Interno",
                costo_servicio=req.costo_maquila_adicional,
                piezas_enviadas=int(db_orden.cantidad_programada),
                piezas_recibidas=int(req.cantidad_real_producida),
                tenant_id=current_user.tenant_id
            )
            db.add(db_maquila)
            db_orden.costo_maquila_externa = float(db_orden.costo_maquila_externa or 0) + req.costo_maquila_adicional
        
        # Costo base estimado de materia prima (en la vida real saldría de las salidas de almacén ligadas a la orden)
        costo_mp_estimado = req.cantidad_real_producida * 80.0  # $80 estimación por prenda
        db_orden.costo_materia_prima = costo_mp_estimado
        db_orden.costo_total = float(db_orden.costo_maquila_externa) + costo_mp_estimado
        
        # 2. Ingresar el Producto Terminado al Inventario
        # Buscar si ya existe un lote para esta orden, si no, crear uno
        numero_lote = f"LOTE-PROD-{db_orden.folio}"
        db_lote = LoteProducto(
            producto_id=db_orden.producto_final_id,
            numero_lote=numero_lote,
            cantidad=req.cantidad_real_producida,
            tenant_id=current_user.tenant_id
        )
        db.add(db_lote)
        
        # 3. Registrar Movimiento de Entrada por Producción
        await db.flush() # para obtener db_lote.id
        db_mov = MovimientoInventario(
            lote_id=db_lote.id,
            cantidad=req.cantidad_real_producida,
            tipo_movimiento="entrada",
            referencia=f"Entrada por Orden {db_orden.folio}",
            tenant_id=current_user.tenant_id
        )
        db.add(db_mov)
        
        # 4. Generar Póliza Contable de Capitalización de Producción
        cta_inv_pt = await obtener_cuenta_por_codigo(db, current_user.tenant_id, "115") # Inventario PT
        cta_inv_proceso = await obtener_cuenta_por_codigo(db, current_user.tenant_id, "115") # Asumimos misma cuenta padre por ahora
        cta_proveedores = await obtener_cuenta_por_codigo(db, current_user.tenant_id, "201") # Proveedores (para la maquila)
        
        movimientos = []
        # Cargo a Inventario de Producto Terminado por el valor total
        movimientos.append({"cuenta_id": cta_inv_pt, "cargo": db_orden.costo_total, "abono": 0.0})
        
        # Abono a Materia Prima / Inventario en proceso (descargando valor)
        movimientos.append({"cuenta_id": cta_inv_proceso, "cargo": 0.0, "abono": db_orden.costo_materia_prima})
        
        # Abono a Proveedores por la maquila externa
        if req.costo_maquila_adicional > 0:
            movimientos.append({"cuenta_id": cta_proveedores, "cargo": 0.0, "abono": float(req.costo_maquila_adicional)})
            
        await create_system_poliza(
            db=db,
            tenant_id=current_user.tenant_id,
            tipo="diario",
            fecha=date.today(),
            descripcion=f"Capitalización Orden de Producción {db_orden.folio}",
            movimientos_data=movimientos
        )
    
        # 5. Cerrar Orden
        db_orden.cantidad_producida = req.cantidad_real_producida
        db_orden.estado = "completado"
        db_orden.fecha_fin = date.today()
        
        await db.commit()
        await db.refresh(db_orden)
        
        return db_orden
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Fallo en persistencia atómica: {str(e)}")
