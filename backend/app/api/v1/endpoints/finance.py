from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from app.api import deps
from app.models.usuario import Usuario
from app.models.finance import CuentaContable, PolizaContable, MovimientoPoliza
from app.models.tenant import Tenant
from app.schemas.finance import (
    CuentaContableCreate, CuentaContableUpdate, CuentaContableOut,
    PolizaContableCreate, PolizaContableOut, MovimientoPolizaCreate, MovimientoPolizaOut
)
from datetime import timezone

router = APIRouter()

# -----------------
# CUENTAS CONTABLES
# -----------------

@router.get("/cuentas", response_model=List[CuentaContableOut])
async def read_cuentas(
    db: AsyncSession = Depends(deps.get_db),
    current_user: Usuario = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Obtener lista de cuentas contables del tenant.
    """
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="Usuario no pertenece a un tenant")

    stmt = select(CuentaContable).where(
        CuentaContable.tenant_id == current_user.tenant_id,
        CuentaContable.is_active == True
    ).order_by(CuentaContable.codigo).offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    cuentas = result.scalars().all()
    return cuentas

@router.post("/cuentas", response_model=CuentaContableOut)
async def create_cuenta(
    *,
    db: AsyncSession = Depends(deps.get_db),
    cuenta_in: CuentaContableCreate,
    current_user: Usuario = Depends(deps.get_current_user),
) -> Any:
    """
    Crear nueva cuenta contable.
    """
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="Usuario no pertenece a un tenant")

    # Verificar si el código ya existe
    stmt = select(CuentaContable).where(
        CuentaContable.tenant_id == current_user.tenant_id,
        CuentaContable.codigo == cuenta_in.codigo
    )
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Ya existe una cuenta con este código")

    cuenta = CuentaContable(
        **cuenta_in.dict(),
        tenant_id=current_user.tenant_id
    )
    db.add(cuenta)
    await db.commit()
    await db.refresh(cuenta)
    return cuenta


# -----------------
# POLIZAS CONTABLES
# -----------------

@router.get("/polizas", response_model=List[PolizaContableOut])
async def read_polizas(
    db: AsyncSession = Depends(deps.get_db),
    current_user: Usuario = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Obtener lista de pólizas contables del tenant.
    """
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="Usuario no pertenece a un tenant")

    stmt = select(PolizaContable).where(
        PolizaContable.tenant_id == current_user.tenant_id
    ).order_by(PolizaContable.fecha.desc(), PolizaContable.numero.desc()).offset(skip).limit(limit)
    
    # Eager load missing? For now we just return them, we might need to load movimientos
    # from sqlalchemy.orm import selectinload
    # stmt = stmt.options(selectinload(PolizaContable.movimientos))
    
    result = await db.execute(stmt)
    polizas = result.scalars().all()
    return polizas

@router.post("/polizas", response_model=PolizaContableOut)
async def create_poliza(
    *,
    db: AsyncSession = Depends(deps.get_db),
    poliza_in: PolizaContableCreate,
    current_user: Usuario = Depends(deps.get_current_user),
) -> Any:
    """
    Crear nueva póliza contable con sus movimientos.
    """
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="Usuario no pertenece a un tenant")

    # Validar fecha de cierre contable
    stmt_tenant = select(Tenant).where(Tenant.id == current_user.tenant_id)
    res_tenant = await db.execute(stmt_tenant)
    tenant = res_tenant.scalar_one_or_none()
    
    if tenant and tenant.fecha_cierre_contable:
        # Asegurar datetime aware
        poliza_dt = datetime.combine(poliza_in.fecha, datetime.min.time()).replace(tzinfo=timezone.utc)
        if poliza_dt <= tenant.fecha_cierre_contable:
            raise HTTPException(status_code=400, detail="No se pueden crear pólizas en un periodo contable cerrado.")

    # Calcular totales
    total_cargos = sum(m.cargo for m in poliza_in.movimientos)
    total_abonos = sum(m.abono for m in poliza_in.movimientos)

    # Validar cuadre si no es borrador
    if poliza_in.estado != 'borrador':
        if abs(total_cargos - total_abonos) > 0.01:
            raise HTTPException(status_code=400, detail="La póliza debe estar cuadrada para no ser borrador.")

    # Crear póliza
    poliza = PolizaContable(
        numero=poliza_in.numero,
        tipo=poliza_in.tipo,
        fecha=poliza_in.fecha,
        descripcion=poliza_in.descripcion,
        estado=poliza_in.estado,
        tenant_id=current_user.tenant_id,
        total_cargos=total_cargos,
        total_abonos=total_abonos
    )
    db.add(poliza)
    await db.flush() # Para obtener poliza.id

    # Crear movimientos
    for mov_in in poliza_in.movimientos:
        movimiento = MovimientoPoliza(
            poliza_id=poliza.id,
            cuenta_id=mov_in.cuenta_id,
            tenant_id=current_user.tenant_id,
            cargo=mov_in.cargo,
            abono=mov_in.abono,
            concepto=mov_in.concepto,
            referencia=mov_in.referencia
        )
        db.add(movimiento)

    await db.commit()
    await db.refresh(poliza)
    return poliza
