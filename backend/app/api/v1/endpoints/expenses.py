from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime, date, timezone

from app.core.database import get_db
from app.models.usuario import Usuario
from app.api.deps import get_current_user

# Models
from app.models.expenses import CategoriaGasto, GastoOperativo
from app.models.treasury import CuentaBancaria, TransaccionBancaria
from app.models.finance import CuentaContable

# Schemas
from app.schemas.expenses import (
    CategoriaGastoCreate, CategoriaGastoResponse,
    GastoOperativoCreate, GastoOperativoResponse, GastoOperativoPay
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

@router.get("/categories", response_model=List[CategoriaGastoResponse])
async def list_categorias(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(CategoriaGasto).where(CategoriaGasto.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    categorias = result.scalars().all()
    
    # Auto-seed MVP categories if none exist
    if not categorias:
        seed_cats = [
            CategoriaGasto(tenant_id=current_user.tenant_id, nombre="Viáticos", descripcion="Comidas, vuelos, hospedajes"),
            CategoriaGasto(tenant_id=current_user.tenant_id, nombre="Papelería y Oficina", descripcion="Suministros de oficina"),
            CategoriaGasto(tenant_id=current_user.tenant_id, nombre="Servicios", descripcion="Luz, agua, internet"),
            CategoriaGasto(tenant_id=current_user.tenant_id, nombre="Mantenimiento", descripcion="Reparaciones a maquinaria"),
        ]
        db.add_all(seed_cats)
        await db.commit()
        for c in seed_cats:
            await db.refresh(c)
        categorias = seed_cats
        
    return categorias

@router.get("/record", response_model=List[GastoOperativoResponse])
async def list_gastos(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(GastoOperativo).options(
        selectinload(GastoOperativo.categoria),
        selectinload(GastoOperativo.usuario),
        selectinload(GastoOperativo.transaccion).selectinload(TransaccionBancaria.cuenta)
    ).where(GastoOperativo.tenant_id == current_user.tenant_id).order_by(GastoOperativo.fecha.desc())
    
    result = await db.execute(stmt)
    gastos = result.scalars().all()
    
    response = []
    for g in gastos:
        response.append({
            "id": g.id,
            "tenant_id": g.tenant_id,
            "categoria_id": g.categoria_id,
            "transaccion_bancaria_id": g.transaccion_bancaria_id,
            "usuario_id": g.usuario_id,
            "concepto": g.concepto,
            "monto": g.monto,
            "fecha": g.fecha,
            "estado": g.estado,
            "comprobante_url": g.comprobante_url,
            "categoria_nombre": g.categoria.nombre if g.categoria else "",
            "usuario_nombre": g.usuario.nombre if g.usuario else "",
            "banco_origen": g.transaccion.cuenta.banco if g.transaccion and g.transaccion.cuenta else "Desconocido"
        })
    return response

@router.post("/record", response_model=GastoOperativoResponse)
async def registrar_gasto(
    req: GastoOperativoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if req.monto <= 0:
        raise HTTPException(status_code=400, detail="El monto del gasto debe ser mayor a 0.")
        
    db_gasto = GastoOperativo(
        tenant_id=current_user.tenant_id,
        categoria_id=req.categoria_id,
        usuario_id=current_user.id,
        concepto=req.concepto,
        monto=req.monto,
        estado="pendiente",
        comprobante_url=req.comprobante_url
    )
    db.add(db_gasto)
    await db.commit()
    
    # Reload for response
    stmt = select(GastoOperativo).options(
        selectinload(GastoOperativo.categoria),
        selectinload(GastoOperativo.usuario)
    ).where(GastoOperativo.id == db_gasto.id)
    result = await db.execute(stmt)
    rel_gasto = result.scalar_one()
    
    return {
        "id": rel_gasto.id,
        "tenant_id": rel_gasto.tenant_id,
        "categoria_id": rel_gasto.categoria_id,
        "transaccion_bancaria_id": rel_gasto.transaccion_bancaria_id,
        "usuario_id": rel_gasto.usuario_id,
        "concepto": rel_gasto.concepto,
        "monto": rel_gasto.monto,
        "fecha": rel_gasto.fecha,
        "estado": rel_gasto.estado,
        "comprobante_url": rel_gasto.comprobante_url,
        "categoria_nombre": rel_gasto.categoria.nombre if rel_gasto.categoria else "",
        "usuario_nombre": rel_gasto.usuario.nombre if rel_gasto.usuario else "",
        "banco_origen": None
    }

@router.put("/{id}/approve", response_model=GastoOperativoResponse)
async def aprobar_gasto(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Only admins can approve, but for MVP we assume UI handles roles
    stmt = select(GastoOperativo).where(
        GastoOperativo.id == id,
        GastoOperativo.tenant_id == current_user.tenant_id
    )
    result = await db.execute(stmt)
    gasto = result.scalar_one_or_none()
    
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto no encontrado.")
    
    if gasto.estado != "pendiente":
        raise HTTPException(status_code=400, detail="El gasto no está pendiente de aprobación.")
        
    gasto.estado = "aprobado"
    await db.commit()
    
    # Reload for response
    stmt_reload = select(GastoOperativo).options(
        selectinload(GastoOperativo.categoria),
        selectinload(GastoOperativo.usuario)
    ).where(GastoOperativo.id == gasto.id)
    res_rel = await db.execute(stmt_reload)
    rel_gasto = res_rel.scalar_one()
    
    return {
        "id": rel_gasto.id,
        "tenant_id": rel_gasto.tenant_id,
        "categoria_id": rel_gasto.categoria_id,
        "transaccion_bancaria_id": rel_gasto.transaccion_bancaria_id,
        "usuario_id": rel_gasto.usuario_id,
        "concepto": rel_gasto.concepto,
        "monto": rel_gasto.monto,
        "fecha": rel_gasto.fecha,
        "estado": rel_gasto.estado,
        "comprobante_url": rel_gasto.comprobante_url,
        "categoria_nombre": rel_gasto.categoria.nombre if rel_gasto.categoria else "",
        "usuario_nombre": rel_gasto.usuario.nombre if rel_gasto.usuario else "",
        "banco_origen": None
    }

@router.put("/{id}/pay", response_model=GastoOperativoResponse)
async def pagar_gasto(
    id: str,
    req: GastoOperativoPay,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if not db.in_transaction():
        await db.begin()
        
    try:
        stmt = select(GastoOperativo).where(
            GastoOperativo.id == id,
            GastoOperativo.tenant_id == current_user.tenant_id
        ).with_for_update()
        result = await db.execute(stmt)
        gasto = result.scalar_one_or_none()
        
        if not gasto:
            raise HTTPException(status_code=404, detail="Gasto no encontrado.")
            
        if gasto.estado != "aprobado":
            raise HTTPException(status_code=400, detail="El gasto debe estar aprobado para ser pagado.")
            
        # Bloquear cuenta bancaria
        stmt_bank = select(CuentaBancaria).where(
            CuentaBancaria.id == req.cuenta_bancaria_id,
            CuentaBancaria.tenant_id == current_user.tenant_id
        ).with_for_update()
        result_bank = await db.execute(stmt_bank)
        db_bank = result_bank.scalar_one_or_none()
        
        if not db_bank:
            raise HTTPException(status_code=404, detail="Cuenta bancaria no encontrada.")
            
        if gasto.monto > db_bank.saldo_actual:
            raise HTTPException(status_code=400, detail=f"FONDOS INSUFICIENTES: El gasto es de ${gasto.monto} pero la cuenta '{db_bank.banco}' solo tiene ${db_bank.saldo_actual}.")
            
        # Descontar banco
        db_bank.saldo_actual -= gasto.monto
        
        # Generar Transaccion (Egreso)
        db_trx = TransaccionBancaria(
            tenant_id=current_user.tenant_id,
            cuenta_id=db_bank.id,
            tipo="egreso",
            monto=gasto.monto,
            concepto=f"Gasto: {gasto.concepto}"
        )
        db.add(db_trx)
        await db.flush()
        
        # Generar Póliza Contable (Cargo 502 Gastos Operacion, Abono 102 Bancos)
        cta_gastos = await obtener_cuenta_por_codigo(db, current_user.tenant_id, "502")
        cta_bancos = await obtener_cuenta_por_codigo(db, current_user.tenant_id, "102")
        
        poliza = await create_system_poliza(
            db=db,
            tenant_id=current_user.tenant_id,
            tipo="egreso",
            fecha=date.today(),
            descripcion=f"Gasto: {gasto.concepto}",
            movimientos_data=[
                {"cuenta_id": cta_gastos, "cargo": gasto.monto, "abono": 0.0},
                {"cuenta_id": cta_bancos, "cargo": 0.0, "abono": gasto.monto}
            ]
        )
        
        db_trx.poliza_id = poliza.id
        gasto.transaccion_bancaria_id = db_trx.id
        gasto.estado = "pagado"
        await db.commit()
        
        # Reload for response
        stmt_reload = select(GastoOperativo).options(
            selectinload(GastoOperativo.categoria),
            selectinload(GastoOperativo.usuario),
            selectinload(GastoOperativo.transaccion).selectinload(TransaccionBancaria.cuenta)
        ).where(GastoOperativo.id == gasto.id)
        res_rel = await db.execute(stmt_reload)
        rel_gasto = res_rel.scalar_one()
        
        return {
            "id": rel_gasto.id,
            "tenant_id": rel_gasto.tenant_id,
            "categoria_id": rel_gasto.categoria_id,
            "transaccion_bancaria_id": rel_gasto.transaccion_bancaria_id,
            "usuario_id": rel_gasto.usuario_id,
            "concepto": rel_gasto.concepto,
            "monto": rel_gasto.monto,
            "fecha": rel_gasto.fecha,
            "estado": rel_gasto.estado,
            "comprobante_url": rel_gasto.comprobante_url,
            "categoria_nombre": rel_gasto.categoria.nombre if rel_gasto.categoria else "",
            "usuario_nombre": rel_gasto.usuario.nombre if rel_gasto.usuario else "",
            "banco_origen": rel_gasto.transaccion.cuenta.banco if rel_gasto.transaccion and rel_gasto.transaccion.cuenta else "Desconocido"
        }
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
