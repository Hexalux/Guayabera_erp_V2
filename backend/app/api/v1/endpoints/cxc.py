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
from app.models.cxc import CuentaPorCobrar, PagoCxC, NotaCreditoCliente
from app.models.sales import Cliente, VentaPOS
from app.models.treasury import CuentaBancaria, TransaccionBancaria
from app.models.finance import CuentaContable

# Schemas
from app.schemas.cxc import (
    CuentaPorCobrarResponse, PagoCxCCreate, PagoCxCResponse,
    NotaCreditoClienteCreate, NotaCreditoClienteResponse
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

@router.get("/saldos", response_model=List[CuentaPorCobrarResponse])
async def list_cxc(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(CuentaPorCobrar).options(
        selectinload(CuentaPorCobrar.cliente),
        selectinload(CuentaPorCobrar.venta)
    ).where(CuentaPorCobrar.tenant_id == current_user.tenant_id)
    
    result = await db.execute(stmt)
    cxc_list = result.scalars().all()
    
    response = []
    for cxc in cxc_list:
        response.append({
            "id": cxc.id,
            "venta_id": cxc.venta_id,
            "cliente_id": cxc.cliente_id,
            "cliente_nombre": cxc.cliente.razon_social if cxc.cliente else "Público General",
            "folio_venta": cxc.venta.folio if cxc.venta else "",
            "monto_original": cxc.monto_original,
            "saldo_pendiente": cxc.saldo_pendiente,
            "fecha_emision": cxc.fecha_emision,
            "fecha_vencimiento": cxc.fecha_vencimiento,
            "estado": cxc.estado
        })
    return response

@router.post("/pagar", response_model=PagoCxCResponse)
async def registrar_pago_cxc(
    req: PagoCxCCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if req.monto <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser mayor a 0.")
        
    if not db.in_transaction():
        await db.begin()
        
    try:
        # 1. Bloquear CxC
        stmt_cxc = select(CuentaPorCobrar).options(
            selectinload(CuentaPorCobrar.cliente)
        ).where(
            CuentaPorCobrar.id == req.cuenta_por_cobrar_id,
            CuentaPorCobrar.tenant_id == current_user.tenant_id
        ).with_for_update()
        result_cxc = await db.execute(stmt_cxc)
        db_cxc = result_cxc.scalar_one_or_none()
        
        if not db_cxc:
            raise HTTPException(status_code=404, detail="Cuenta por cobrar no encontrada.")
            
        if req.monto > db_cxc.saldo_pendiente:
            raise HTTPException(status_code=400, detail=f"El monto supera el saldo pendiente de ${db_cxc.saldo_pendiente}.")
            
        # 2. Bloquear Cuenta Bancaria
        stmt_bank = select(CuentaBancaria).where(
            CuentaBancaria.id == req.cuenta_bancaria_id,
            CuentaBancaria.tenant_id == current_user.tenant_id
        ).with_for_update()
        result_bank = await db.execute(stmt_bank)
        db_bank = result_bank.scalar_one_or_none()
        
        if not db_bank:
            raise HTTPException(status_code=404, detail="Cuenta bancaria no encontrada.")
            
        # 3. Aplicar pago
        db_cxc.saldo_pendiente -= req.monto
        if db_cxc.saldo_pendiente <= 0:
            db_cxc.estado = "pagada"
            
        db_bank.saldo_actual += req.monto
        
        # 4. Registrar Transacción Bancaria
        db_trx = TransaccionBancaria(
            tenant_id=current_user.tenant_id,
            cuenta_id=db_bank.id,
            tipo="ingreso",
            monto=req.monto,
            referencia=req.referencia,
            concepto=f"Cobro a Cliente: {db_cxc.cliente.razon_social if db_cxc.cliente else 'General'}"
        )
        db.add(db_trx)
        await db.flush()
        
        # 5. Registrar Pago CxC
        db_pago = PagoCxC(
            tenant_id=current_user.tenant_id,
            cuenta_por_cobrar_id=db_cxc.id,
            transaccion_bancaria_id=db_trx.id,
            monto=req.monto,
            referencia=req.referencia
        )
        db.add(db_pago)
        await db.flush()
        
        # 6. Generar Póliza Contable (TutConta)
        # Cargo a Bancos (102). Abono a Clientes (103).
        cta_bancos = await obtener_cuenta_por_codigo(db, current_user.tenant_id, "102")
        cta_clientes = await obtener_cuenta_por_codigo(db, current_user.tenant_id, "103")
        
        poliza = await create_system_poliza(
            db=db,
            tenant_id=current_user.tenant_id,
            tipo="ingreso",
            fecha=date.today(),
            descripcion=f"Cobro factura {req.cuenta_por_cobrar_id[-4:]} - Cliente {db_cxc.cliente.razon_social if db_cxc.cliente else ''}",
            movimientos_data=[
                {"cuenta_id": cta_bancos, "cargo": req.monto, "abono": 0.0},
                {"cuenta_id": cta_clientes, "cargo": 0.0, "abono": req.monto}
            ]
        )
        
        db_trx.poliza_id = poliza.id
        await db.commit()
        await db.refresh(db_pago)
        return db_pago
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
