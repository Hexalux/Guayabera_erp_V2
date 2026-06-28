from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import List, Dict, Any
from datetime import date

from app.core.database import get_db
from app.models.usuario import Usuario
from app.api.deps import get_current_user

from app.models.finance import CuentaContable, PolizaContable, MovimientoPoliza
from app.models.cxc import CuentaPorCobrar
from app.models.purchases import CuentaPorPagar
from app.models.tenant import Tenant
from datetime import datetime, timezone
from pydantic import BaseModel

router = APIRouter()

# ==========================================
# BALANCE GENERAL (ACTIVO, PASIVO, CAPITAL)
# ==========================================
@router.get("/reports/balance-general")
async def get_balance_general(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Calcula el Balance General sumando movimientos (o saldos iniciales + movimientos).
    Por ahora MVP suma los movimientos históricos de cada cuenta de tipo activo, pasivo y capital.
    Activo: Naturaleza deudora (Saldo = Cargos - Abonos)
    Pasivo/Capital: Naturaleza acreedora (Saldo = Abonos - Cargos)
    """
    stmt = select(CuentaContable).options(
        selectinload(CuentaContable.movimientos)
    ).where(
        CuentaContable.tenant_id == current_user.tenant_id,
        CuentaContable.tipo.in_(["activo", "pasivo", "capital"])
    )
    res = await db.execute(stmt)
    cuentas = res.scalars().all()
    
    activos = []
    pasivos = []
    capital = []
    
    total_activos = 0.0
    total_pasivos = 0.0
    total_capital = 0.0
    
    for cta in cuentas:
        cargos = sum([float(m.cargo) for m in cta.movimientos])
        abonos = sum([float(m.abono) for m in cta.movimientos])
        
        if cta.naturaleza == "deudora":
            saldo = cargos - abonos
        else:
            saldo = abonos - cargos
            
        # Para el reporte, solo incluimos si el saldo es distinto de 0 o es agrupadora
        data = {
            "id": cta.id,
            "codigo": cta.codigo,
            "nombre": cta.nombre,
            "saldo": saldo,
            "nivel": cta.nivel
        }
        
        if cta.tipo == "activo":
            activos.append(data)
            total_activos += saldo
        elif cta.tipo == "pasivo":
            pasivos.append(data)
            total_pasivos += saldo
        elif cta.tipo == "capital":
            capital.append(data)
            total_capital += saldo
            
    # Ordenar por código
    activos.sort(key=lambda x: x["codigo"])
    pasivos.sort(key=lambda x: x["codigo"])
    capital.sort(key=lambda x: x["codigo"])
    
    return {
        "activos": {"cuentas": activos, "total": total_activos},
        "pasivos": {"cuentas": pasivos, "total": total_pasivos},
        "capital": {"cuentas": capital, "total": total_capital},
        "ecuacion_contable": total_activos == (total_pasivos + total_capital)
    }

# ==========================================
# ESTADO DE RESULTADOS (P&L)
# ==========================================
@router.get("/reports/estado-resultados")
async def get_estado_resultados(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Calcula el Estado de Resultados (Ingresos, Costos, Gastos).
    Ingresos: Acreedora (Abonos - Cargos)
    Costos/Gastos: Deudora (Cargos - Abonos)
    """
    stmt = select(CuentaContable).options(
        selectinload(CuentaContable.movimientos)
    ).where(
        CuentaContable.tenant_id == current_user.tenant_id,
        CuentaContable.tipo.in_(["ingresos", "costos", "gastos"])
    )
    res = await db.execute(stmt)
    cuentas = res.scalars().all()
    
    ingresos = []
    costos = []
    gastos = []
    
    total_ingresos = 0.0
    total_costos = 0.0
    total_gastos = 0.0
    
    for cta in cuentas:
        cargos = sum([float(m.cargo) for m in cta.movimientos])
        abonos = sum([float(m.abono) for m in cta.movimientos])
        
        if cta.naturaleza == "deudora":
            saldo = cargos - abonos
        else:
            saldo = abonos - cargos
            
        data = {
            "id": cta.id,
            "codigo": cta.codigo,
            "nombre": cta.nombre,
            "saldo": saldo,
            "nivel": cta.nivel
        }
        
        if cta.tipo == "ingresos":
            ingresos.append(data)
            total_ingresos += saldo
        elif cta.tipo == "costos":
            costos.append(data)
            total_costos += saldo
        elif cta.tipo == "gastos":
            gastos.append(data)
            total_gastos += saldo
            
    ingresos.sort(key=lambda x: x["codigo"])
    costos.sort(key=lambda x: x["codigo"])
    gastos.sort(key=lambda x: x["codigo"])
    
    utilidad_bruta = total_ingresos - total_costos
    utilidad_neta = utilidad_bruta - total_gastos
    
    return {
        "ingresos": {"cuentas": ingresos, "total": total_ingresos},
        "costos": {"cuentas": costos, "total": total_costos},
        "gastos": {"cuentas": gastos, "total": total_gastos},
        "utilidad_bruta": utilidad_bruta,
        "utilidad_neta": utilidad_neta
    }

# ==========================================
# AUDITORÍA DE DIARIO (PÓLIZAS)
# ==========================================
@router.get("/journal")
async def list_polizas(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista las pólizas contables y sus asientos (Auditoría de Diario).
    """
    stmt = select(PolizaContable).options(
        selectinload(PolizaContable.movimientos).selectinload(MovimientoPoliza.cuenta)
    ).where(PolizaContable.tenant_id == current_user.tenant_id).order_by(PolizaContable.fecha.desc(), PolizaContable.numero.desc())
    
    res = await db.execute(stmt)
    polizas = res.scalars().all()
    
    response = []
    for p in polizas:
        movs = []
        for m in p.movimientos:
            movs.append({
                "id": m.id,
                "cuenta_codigo": m.cuenta.codigo if m.cuenta else "",
                "cuenta_nombre": m.cuenta.nombre if m.cuenta else "",
                "cargo": float(m.cargo),
                "abono": float(m.abono),
                "concepto": m.concepto
            })
            
        response.append({
            "id": p.id,
            "numero": p.numero,
            "tipo": p.tipo,
            "fecha": p.fecha,
            "descripcion": p.descripcion,
            "estado": p.estado,
            "total_cargos": float(p.total_cargos),
            "total_abonos": float(p.total_abonos),
            "movimientos": movs
        })
        
    return response

# ==========================================
# REPORTE DE CARTERA VENCIDA (AGING REPORT)
# ==========================================
@router.get("/reports/aging")
async def get_aging_report(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Calcula la antigüedad de saldos de CxC (Clientes) y CxP (Proveedores).
    Buckets: Al corriente, 1-30, 31-60, 61-90, 90+ días.
    """
    now = datetime.now(timezone.utc)
    
    # CxC
    stmt_cxc = select(CuentaPorCobrar).options(
        selectinload(CuentaPorCobrar.cliente)
    ).where(
        CuentaPorCobrar.tenant_id == current_user.tenant_id,
        CuentaPorCobrar.saldo_pendiente > 0
    )
    res_cxc = await db.execute(stmt_cxc)
    cxc_list = res_cxc.scalars().all()
    
    cxc_aging = {"current": 0.0, "days_30": 0.0, "days_60": 0.0, "days_90": 0.0, "older": 0.0, "total": 0.0}
    cxc_details = []
    
    for cxc in cxc_list:
        # Asegurar que fecha_vencimiento sea aware
        venc = cxc.fecha_vencimiento
        if venc.tzinfo is None:
            venc = venc.replace(tzinfo=timezone.utc)
            
        days_overdue = (now - venc).days
        saldo = float(cxc.saldo_pendiente)
        cxc_aging["total"] += saldo
        
        if days_overdue <= 0:
            cxc_aging["current"] += saldo
            bucket = "current"
        elif days_overdue <= 30:
            cxc_aging["days_30"] += saldo
            bucket = "30_days"
        elif days_overdue <= 60:
            cxc_aging["days_60"] += saldo
            bucket = "60_days"
        elif days_overdue <= 90:
            cxc_aging["days_90"] += saldo
            bucket = "90_days"
        else:
            cxc_aging["older"] += saldo
            bucket = "older"
            
        cxc_details.append({
            "id": cxc.id,
            "entidad": cxc.cliente.nombre if cxc.cliente else "Desconocido",
            "documento": f"Venta POS {cxc.venta_id[:8]}",
            "fecha_vencimiento": venc.isoformat(),
            "dias_vencido": max(0, days_overdue),
            "saldo": saldo,
            "bucket": bucket
        })
        
    # CxP
    stmt_cxp = select(CuentaPorPagar).options(
        selectinload(CuentaPorPagar.proveedor)
    ).where(
        CuentaPorPagar.tenant_id == current_user.tenant_id,
        CuentaPorPagar.saldo_pendiente > 0
    )
    res_cxp = await db.execute(stmt_cxp)
    cxp_list = res_cxp.scalars().all()
    
    cxp_aging = {"current": 0.0, "days_30": 0.0, "days_60": 0.0, "days_90": 0.0, "older": 0.0, "total": 0.0}
    cxp_details = []
    
    for cxp in cxp_list:
        venc = cxp.fecha_vencimiento
        if venc.tzinfo is None:
            venc = venc.replace(tzinfo=timezone.utc)
            
        days_overdue = (now - venc).days
        saldo = float(cxp.saldo_pendiente)
        cxp_aging["total"] += saldo
        
        if days_overdue <= 0:
            cxp_aging["current"] += saldo
            bucket = "current"
        elif days_overdue <= 30:
            cxp_aging["days_30"] += saldo
            bucket = "30_days"
        elif days_overdue <= 60:
            cxp_aging["days_60"] += saldo
            bucket = "60_days"
        elif days_overdue <= 90:
            cxp_aging["days_90"] += saldo
            bucket = "90_days"
        else:
            cxp_aging["older"] += saldo
            bucket = "older"
            
        cxp_details.append({
            "id": cxp.id,
            "entidad": cxp.proveedor.razon_social if cxp.proveedor else "Desconocido",
            "documento": f"OC {cxp.orden_compra_id[:8]}",
            "fecha_vencimiento": venc.isoformat(),
            "dias_vencido": max(0, days_overdue),
            "saldo": saldo,
            "bucket": bucket
        })
        
    return {
        "cxc": {
            "summary": cxc_aging,
            "details": cxc_details
        },
        "cxp": {
            "summary": cxp_aging,
            "details": cxp_details
        }
    }

# ==========================================
# CONFIGURACIÓN: FECHAS DE CIERRE CONTABLE
# ==========================================

class CierreContableConfig(BaseModel):
    fecha_cierre: str | None = None

@router.get("/settings/cierre")
async def get_cierre_contable(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(Tenant).where(Tenant.id == current_user.tenant_id)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
        
    return {
        "fecha_cierre_contable": tenant.fecha_cierre_contable.isoformat() if tenant.fecha_cierre_contable else None
    }

@router.post("/settings/cierre")
async def update_cierre_contable(
    config: CierreContableConfig,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(Tenant).where(Tenant.id == current_user.tenant_id)
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
        
    if config.fecha_cierre:
        try:
            dt = datetime.fromisoformat(config.fecha_cierre)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            tenant.fecha_cierre_contable = dt
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido")
    else:
        tenant.fecha_cierre_contable = None
        
    await db.commit()
    return {"message": "Fecha de cierre actualizada", "fecha_cierre_contable": tenant.fecha_cierre_contable}
