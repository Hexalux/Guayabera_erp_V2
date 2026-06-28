from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, String, cast
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime, date, timezone

from app.core.database import get_db
from app.models.usuario import Usuario
from app.api.deps import get_current_user

# Models
from app.models.treasury import CuentaBancaria, TransaccionBancaria
from app.models.finance import CuentaContable

# Schemas
from app.schemas.treasury import (
    CuentaBancariaCreate, CuentaBancariaResponse,
    TransaccionBancariaCreate, TransaccionBancariaResponse
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
# CUENTAS BANCARIAS
# =================================================================
@router.get("/accounts", response_model=List[CuentaBancariaResponse])
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(CuentaBancaria).where(CuentaBancaria.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/accounts", response_model=CuentaBancariaResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    req: CuentaBancariaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    db_acc = CuentaBancaria(**req.model_dump(), tenant_id=current_user.tenant_id, saldo_actual=0.0)
    db.add(db_acc)
    await db.commit()
    await db.refresh(db_acc)
    return db_acc


# =================================================================
# TRANSACCIONES (INGRESO / EGRESO) CON PESSIMISTIC LOCKING
# =================================================================
@router.post("/transactions/ingreso", response_model=TransaccionBancariaResponse)
async def registrar_ingreso(
    req: TransaccionBancariaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if req.monto <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser mayor a 0.")
        
    if not db.in_transaction():
        await db.begin()
        
    try:
        # 1. Bloquear cuenta
        stmt = select(CuentaBancaria).where(
            CuentaBancaria.id == req.cuenta_id,
            CuentaBancaria.tenant_id == current_user.tenant_id
        ).with_for_update()
        result = await db.execute(stmt)
        db_acc = result.scalar_one_or_none()
        
        if not db_acc:
            raise HTTPException(status_code=404, detail="Cuenta bancaria no encontrada.")
            
        # 2. Modificar saldo
        db_acc.saldo_actual += req.monto
        
        # 3. Registrar Transacción
        db_trx = TransaccionBancaria(
            tenant_id=current_user.tenant_id,
            cuenta_id=db_acc.id,
            tipo="ingreso",
            monto=req.monto,
            referencia=req.referencia,
            concepto=req.concepto,
            metodo_pago=req.metodo_pago,
            estado_cheque=req.estado_cheque if req.metodo_pago == 'cheque' else None
        )
        db.add(db_trx)
        await db.flush()
        
        # 4. Póliza Contable (TutConta)
        # Cargo a Bancos (102). Abono a Capital/Aportaciones (301) por defecto al no haber origen CxC
        cta_bancos = await obtener_cuenta_por_codigo(db, current_user.tenant_id, "102")
        cta_origen = await obtener_cuenta_por_codigo(db, current_user.tenant_id, "301") # Aportaciones futuras
        
        poliza = await create_system_poliza(
            db=db,
            tenant_id=current_user.tenant_id,
            tipo="ingreso",
            fecha=date.today(),
            descripcion=f"Ingreso a {db_acc.banco} - {req.concepto}",
            movimientos_data=[
                {"cuenta_id": cta_bancos, "cargo": req.monto, "abono": 0.0},
                {"cuenta_id": cta_origen, "cargo": 0.0, "abono": req.monto}
            ]
        )
        
        db_trx.poliza_id = poliza.id
        await db.commit()
        await db.refresh(db_trx)
        return db_trx
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transactions/egreso", response_model=TransaccionBancariaResponse)
async def registrar_egreso(
    req: TransaccionBancariaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if req.monto <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser mayor a 0.")
        
    if not db.in_transaction():
        await db.begin()
        
    try:
        # 1. Bloquear cuenta
        stmt = select(CuentaBancaria).where(
            CuentaBancaria.id == req.cuenta_id,
            CuentaBancaria.tenant_id == current_user.tenant_id
        ).with_for_update()
        result = await db.execute(stmt)
        db_acc = result.scalar_one_or_none()
        
        if not db_acc:
            raise HTTPException(status_code=404, detail="Cuenta bancaria no encontrada.")
            
        # 2. Modificar saldo
        if db_acc.saldo_actual < req.monto:
            raise HTTPException(status_code=400, detail="Fondos insuficientes en la cuenta.")
            
        db_acc.saldo_actual -= req.monto
        
        # 3. Registrar Transacción
        db_trx = TransaccionBancaria(
            tenant_id=current_user.tenant_id,
            cuenta_id=db_acc.id,
            tipo="egreso",
            monto=req.monto,
            referencia=req.referencia,
            concepto=req.concepto,
            metodo_pago=req.metodo_pago,
            estado_cheque=req.estado_cheque if req.metodo_pago == 'cheque' else None
        )
        db.add(db_trx)
        await db.flush()
        
        # 4. Póliza Contable (TutConta)
        # Abono a Bancos (102). Cargo a Gastos o Proveedores, usamos Proveedores (201) por defecto para el MVP
        cta_bancos = await obtener_cuenta_por_codigo(db, current_user.tenant_id, "102")
        cta_destino = await obtener_cuenta_por_codigo(db, current_user.tenant_id, "201")
        
        poliza = await create_system_poliza(
            db=db,
            tenant_id=current_user.tenant_id,
            tipo="egreso",
            fecha=date.today(),
            descripcion=f"Egreso de {db_acc.banco} - {req.concepto}",
            movimientos_data=[
                {"cuenta_id": cta_destino, "cargo": req.monto, "abono": 0.0},
                {"cuenta_id": cta_bancos, "cargo": 0.0, "abono": req.monto}
            ]
        )
        
        db_trx.poliza_id = poliza.id
        await db.commit()
        await db.refresh(db_trx)
        return db_trx
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# =================================================================
# HISTORIAL Y CONCILIACIÓN
# =================================================================
@router.get("/transactions", response_model=List[TransaccionBancariaResponse])
async def list_transactions(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    limit: int = 100
):
    stmt = select(TransaccionBancaria).where(
        TransaccionBancaria.tenant_id == current_user.tenant_id
    ).order_by(TransaccionBancaria.fecha.desc()).limit(limit)
    
    result = await db.execute(stmt)
    return result.scalars().all()

from pydantic import BaseModel
class EstadoChequeUpdate(BaseModel):
    estado: str

@router.put("/transactions/{id}/estado", response_model=TransaccionBancariaResponse)
async def update_check_status(
    id: str,
    req: EstadoChequeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(TransaccionBancaria).where(
        TransaccionBancaria.id == id,
        TransaccionBancaria.tenant_id == current_user.tenant_id
    )
    result = await db.execute(stmt)
    trx = result.scalar_one_or_none()
    
    if not trx:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
        
    if trx.metodo_pago != 'cheque':
        raise HTTPException(status_code=400, detail="La transacción no es un cheque")
        
    trx.estado_cheque = req.estado
    await db.commit()
    await db.refresh(trx)
    return trx
