from sqlalchemy.ext.asyncio import AsyncSession
from app.models.finance import PolizaContable, MovimientoPoliza
from app.schemas.finance import PolizaContableCreate, MovimientoPolizaCreate
from datetime import date
from typing import List

async def create_system_poliza(
    db: AsyncSession, 
    tenant_id: str, 
    tipo: str, 
    fecha: date, 
    descripcion: str, 
    movimientos_data: List[dict]
) -> PolizaContable:
    """
    Crea una póliza contable de manera programática (desde otros módulos como Inventario).
    
    movimientos_data debe ser una lista de diccionarios:
    [
      {"cuenta_id": "uuid-1", "cargo": 100.0, "abono": 0.0, "concepto": "Entrada almacén"},
      {"cuenta_id": "uuid-2", "cargo": 0.0, "abono": 100.0, "concepto": "Entrada almacén"}
    ]
    """
    total_cargos = sum(m.get("cargo", 0.0) for m in movimientos_data)
    total_abonos = sum(m.get("abono", 0.0) for m in movimientos_data)
    
    # Validación estricta del cuadre (incluso para el sistema automático)
    if abs(total_cargos - total_abonos) > 0.01:
        raise ValueError(f"La póliza de sistema no cuadra. Cargos: {total_cargos}, Abonos: {total_abonos}")
        
    # Asignar un número auto-incremental (simplificado, idealmente requeriría una secuencia por tenant y tipo)
    # Aquí podríamos hacer un query para obtener el MAX(numero) del tenant + 1
    from sqlalchemy import select, func
    stmt = select(func.max(PolizaContable.numero)).where(
        PolizaContable.tenant_id == tenant_id,
        PolizaContable.tipo == tipo
    )
    result = await db.execute(stmt)
    max_num = result.scalar_one_or_none()
    nuevo_numero = (max_num or 0) + 1

    # Crear póliza
    poliza = PolizaContable(
        numero=nuevo_numero,
        tipo=tipo,
        fecha=fecha,
        descripcion=descripcion,
        estado="aprobada",  # Las de sistema nacen aprobadas
        tenant_id=tenant_id,
        total_cargos=total_cargos,
        total_abonos=total_abonos
    )
    db.add(poliza)
    await db.flush() # flush para obtener poliza.id
    
    # Crear movimientos
    for m in movimientos_data:
        movimiento = MovimientoPoliza(
            poliza_id=poliza.id,
            cuenta_id=m["cuenta_id"],
            tenant_id=tenant_id,
            cargo=m.get("cargo", 0.0),
            abono=m.get("abono", 0.0),
            concepto=m.get("concepto", descripcion),
            referencia=m.get("referencia")
        )
        db.add(movimiento)
        
    # Dejamos que el invocador (el endpoint de inventario/producción) haga el commit
    await db.flush()
    
    return poliza
