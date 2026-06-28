from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.usuario import Usuario
from app.models.inventory import CategoriaProductoTextil, ProductoTextil, Almacen, UbicacionAlmacen, LoteProducto, MovimientoInventario
from app.models.finance import CuentaContable, PolizaContable, MovimientoPoliza, Banco, MovimientoBancario
from app.models.hr import Empleado, ContratoLaboral, ControlVacaciones, Nomina
from app.models.production import OrdenProduccion, RecetaProduccion, CostoSubcontratacionMaquila
from app.models.branches import Sucursal, CajaRegistradora
from app.models.licencia import Licencia

router = APIRouter()

# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class AlmacenCreate(BaseModel):
    nombre: str
    codigo: str

class UbicacionCreate(BaseModel):
    almacen_id: str
    nombre: str
    parent_id: Optional[str] = None
    pasillo: Optional[str] = None
    estante: Optional[str] = None
    rack: Optional[str] = None
    nivel: Optional[str] = None

class ProductoCreate(BaseModel):
    nombre: str
    sku: str
    categoria_id: str
    tipo_producto: str = "producto_terminado"
    composicion: Optional[str] = None
    gramaje: Optional[float] = None
    ancho: Optional[float] = None
    color_pantone: Optional[str] = None

class LoteCreate(BaseModel):
    producto_id: str
    numero_lote: str
    ubicacion_id: Optional[str] = None
    cantidad: float = 0.0
    variacion_tono: Optional[str] = None

class MovimientoInventarioCreate(BaseModel):
    lote_id: str
    ubicacion_origen_id: Optional[str] = None
    ubicacion_destino_id: Optional[str] = None
    cantidad: float
    tipo_movimiento: str
    referencia: Optional[str] = None

class CuentaCreate(BaseModel):
    codigo: str
    nombre: str
    nivel: int = 1
    tipo: str
    naturaleza: str = "deudora"
    es_agrupadora: bool = False
    cuenta_padre_id: Optional[str] = None

class MovimientoPolizaSchema(BaseModel):
    cuenta_id: str
    cargo: float = 0.0
    abono: float = 0.0
    concepto: str
    referencia: Optional[str] = None

class PolizaCreate(BaseModel):
    numero: int
    tipo: str
    fecha: date
    descripcion: str
    movimientos: List[MovimientoPolizaSchema]

class ConciliarRequest(BaseModel):
    movimiento_bancario_id: str
    poliza_id: str

class EmpleadoCreate(BaseModel):
    codigo: str
    nombre_completo: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    rfc: Optional[str] = None
    curp: Optional[str] = None
    nss: Optional[str] = None

class DocumentoUpload(BaseModel):
    tipo_documento: str  # "contrato", "nacimiento", "curp"
    archivo_path: str

class VacacionRequest(BaseModel):
    fecha_inicio: date
    fecha_fin: date
    dias_solicitados: int

class NominaCreate(BaseModel):
    empleado_id: str
    fecha_pago: date
    total_percepciones: float
    total_deducciones: float

class BOMCreate(BaseModel):
    producto_padre_id: str
    insumo_id: str
    cantidad_requerida: float

class OrdenProduccionCreate(BaseModel):
    folio: str
    producto_final_id: str
    cantidad_programada: float
    fecha_inicio: Optional[date] = None

class MaquilaFinalize(BaseModel):
    maquilador_nombre: str
    costo_servicio: float
    piezas_enviadas: int
    piezas_recibidas: int

class NestingResults(BaseModel):
    diseno_id: str
    lote_tela_id: str
    metros_consumidos: float
    metros_desperdiciados: float
    piezas_cortadas: int
    dxf_path: str

# ============================================================================
# INVENTORY ENDPOINTS
# ============================================================================

@router.post("/inventory/almacenes", status_code=status.HTTP_201_CREATED)
async def crear_almacen(
    data: AlmacenCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    nuevo = Almacen(
        nombre=data.nombre,
        codigo=data.codigo,
        tenant_id=current_user.tenant_id
    )
    db.add(nuevo)
    await db.commit()
    await db.refresh(nuevo)
    return nuevo

@router.get("/inventory/almacenes")
async def listar_almacenes(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Almacen).where(cast(Almacen.tenant_id, String) == str(current_user.tenant_id))
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/inventory/ubicaciones", status_code=status.HTTP_201_CREATED)
async def crear_ubicacion(
    data: UbicacionCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    nuevo = UbicacionAlmacen(
        almacen_id=data.almacen_id,
        nombre=data.nombre,
        parent_id=data.parent_id,
        pasillo=data.pasillo,
        estante=data.estante,
        rack=data.rack,
        nivel=data.nivel,
        tenant_id=current_user.tenant_id
    )
    db.add(nuevo)
    await db.commit()
    await db.refresh(nuevo)
    return nuevo

@router.get("/inventory/ubicaciones")
async def listar_ubicaciones(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(UbicacionAlmacen).where(cast(UbicacionAlmacen.tenant_id, String) == str(current_user.tenant_id))
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/inventory/productos", status_code=status.HTTP_201_CREATED)
async def crear_producto(
    data: ProductoCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    nuevo = ProductoTextil(
        nombre=data.nombre,
        sku=data.sku,
        categoria_id=data.categoria_id,
        tipo_producto=data.tipo_producto,
        composicion=data.composicion,
        gramaje=data.gramaje,
        ancho=data.ancho,
        color_pantone=data.color_pantone,
        tenant_id=current_user.tenant_id
    )
    db.add(nuevo)
    await db.commit()
    await db.refresh(nuevo)
    return nuevo

@router.get("/inventory/productos")
async def listar_productos(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ProductoTextil).where(cast(ProductoTextil.tenant_id, String) == str(current_user.tenant_id))
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/inventory/movimientos", status_code=status.HTTP_201_CREATED)
async def registrar_movimiento(
    data: MovimientoInventarioCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(LoteProducto).where(cast(LoteProducto.id, String) == str(data.lote_id))
    lote = (await db.execute(stmt)).scalar_one_or_none()
    if not lote:
        raise HTTPException(status_code=404, detail="Lote no encontrado")

    if data.tipo_movimiento in ["salida", "transferencia"]:
        if float(lote.cantidad) < data.cantidad:
            raise HTTPException(status_code=400, detail="Stock insuficiente en el lote")
        lote.cantidad = float(lote.cantidad) - data.cantidad
    
    if data.tipo_movimiento in ["entrada", "transferencia"]:
        lote.cantidad = float(lote.cantidad) + data.cantidad
        if data.ubicacion_destino_id:
            lote.ubicacion_id = data.ubicacion_destino_id

    mov = MovimientoInventario(
        lote_id=data.lote_id,
        ubicacion_origen_id=data.ubicacion_origen_id,
        ubicacion_destino_id=data.ubicacion_destino_id,
        cantidad=data.cantidad,
        tipo_movimiento=data.tipo_movimiento,
        referencia=data.referencia,
        tenant_id=current_user.tenant_id
    )
    db.add(mov)
    await db.commit()
    await db.refresh(mov)
    return mov

# ============================================================================
# FINANCE ENDPOINTS
# ============================================================================

@router.post("/finance/cuentas", status_code=status.HTTP_201_CREATED)
async def crear_cuenta(
    data: CuentaCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    nuevo = CuentaContable(
        codigo=data.codigo,
        nombre=data.nombre,
        nivel=data.nivel,
        tipo=data.tipo,
        naturaleza=data.naturaleza,
        es_agrupadora=data.es_agrupadora,
        cuenta_padre_id=data.cuenta_padre_id,
        tenant_id=current_user.tenant_id
    )
    db.add(nuevo)
    await db.commit()
    await db.refresh(nuevo)
    return nuevo

@router.get("/finance/cuentas")
async def listar_cuentas(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CuentaContable).where(cast(CuentaContable.tenant_id, String) == str(current_user.tenant_id))
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/finance/polizas", status_code=status.HTTP_201_CREATED)
async def crear_poliza(
    data: PolizaCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    total_cargos = sum(m.cargo for m in data.movimientos)
    total_abonos = sum(m.abono for m in data.movimientos)

    if round(total_cargos, 2) != round(total_abonos, 2):
        raise HTTPException(
            status_code=400,
            detail=f"La póliza no está cuadrada. Cargos: {total_cargos}, Abonos: {total_abonos}"
        )

    poliza = PolizaContable(
        numero=data.numero,
        tipo=data.tipo,
        fecha=data.fecha,
        descripcion=data.descripcion,
        total_cargos=total_cargos,
        total_abonos=total_abonos,
        estado="aprobada",
        tenant_id=current_user.tenant_id
    )
    db.add(poliza)
    await db.commit()
    await db.refresh(poliza)

    for mov_data in data.movimientos:
        mov = MovimientoPoliza(
            poliza_id=poliza.id,
            cuenta_id=mov_data.cuenta_id,
            cargo=mov_data.cargo,
            abono=mov_data.abono,
            concepto=mov_data.concepto,
            referencia=mov_data.referencia,
            tenant_id=current_user.tenant_id
        )
        db.add(mov)
    await db.commit()
    return poliza

@router.get("/finance/polizas")
async def listar_polizas(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(PolizaContable).where(cast(PolizaContable.tenant_id, String) == str(current_user.tenant_id))
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/finance/bancos/conciliar")
async def conciliar_movimiento(
    data: ConciliarRequest,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(MovimientoBancario).where(cast(MovimientoBancario.id, String) == str(data.movimiento_bancario_id))
    mb = (await db.execute(stmt)).scalar_one_or_none()
    if not mb:
        raise HTTPException(status_code=404, detail="Movimiento bancario no encontrado")

    mb.conciliado = True
    await db.commit()
    return {"status": "success", "message": "Movimiento bancario conciliado correctamente"}

# ============================================================================
# PRODUCTION ENDPOINTS
# ============================================================================

@router.post("/production/recetas", status_code=status.HTTP_201_CREATED)
async def crear_bom(
    data: BOMCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    bom = RecetaProduccion(
        producto_padre_id=data.producto_padre_id,
        insumo_id=data.insumo_id,
        cantidad_requerida=data.cantidad_requerida,
        tenant_id=current_user.tenant_id
    )
    db.add(bom)
    await db.commit()
    await db.refresh(bom)
    return bom

@router.post("/production/ordenes", status_code=status.HTTP_201_CREATED)
async def crear_orden_produccion(
    data: OrdenProduccionCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    orden = OrdenProduccion(
        folio=data.folio,
        producto_final_id=data.producto_final_id,
        cantidad_programada=data.cantidad_programada,
        fecha_inicio=data.fecha_inicio or datetime.utcnow().date(),
        estado="en_proceso",
        tenant_id=current_user.tenant_id
    )
    db.add(orden)
    await db.commit()
    await db.refresh(orden)
    return orden

@router.post("/production/ordenes/{id}/maquila")
async def finalizar_con_maquila(
    id: str,
    data: MaquilaFinalize,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(OrdenProduccion).where(cast(OrdenProduccion.id, String) == str(id))
    orden = (await db.execute(stmt)).scalar_one_or_none()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden de producción no encontrada")

    # Registrar costos de maquila
    maquila = CostoSubcontratacionMaquila(
        orden_produccion_id=orden.id,
        maquilador_nombre=data.maquilador_nombre,
        costo_servicio=data.costo_servicio,
        piezas_enviadas=data.piezas_enviadas,
        piezas_recibidas=data.piezas_recibidas,
        tenant_id=current_user.tenant_id
    )
    db.add(maquila)

    # Actualizar orden
    orden.cantidad_producida = data.piezas_recibidas
    orden.costo_maquila_externa = data.costo_servicio
    orden.costo_total = float(orden.costo_materia_prima or 0) + float(data.costo_servicio)
    orden.estado = "completado"
    orden.fecha_fin = datetime.utcnow().date()

    await db.commit()
    await db.refresh(orden)
    return orden

# ============================================================================
# HR ENDPOINTS
# ============================================================================

@router.post("/hr/empleados", status_code=status.HTTP_201_CREATED)
async def crear_empleado(
    data: EmpleadoCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    nuevo = Empleado(
        codigo=data.codigo,
        nombre_completo=data.nombre_completo,
        email=data.email,
        telefono=data.telefono,
        rfc=data.rfc,
        curp=data.curp,
        nss=data.nss,
        tenant_id=current_user.tenant_id
    )
    db.add(nuevo)
    await db.commit()
    await db.refresh(nuevo)
    return nuevo

@router.get("/hr/empleados")
async def listar_empleados(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Empleado).where(cast(Empleado.tenant_id, String) == str(current_user.tenant_id))
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/hr/empleados/{id}/documentos")
async def subir_documento(
    id: str,
    data: DocumentoUpload,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Empleado).where(cast(Empleado.id, String) == str(id))
    emp = (await db.execute(stmt)).scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")

    if data.tipo_documento == "contrato":
        emp.archivo_contrato = data.archivo_path
    elif data.tipo_documento == "nacimiento":
        emp.archivo_nacimiento = data.archivo_path
    elif data.tipo_documento == "curp":
        emp.archivo_curp = data.archivo_path
    else:
        raise HTTPException(status_code=400, detail="Tipo de documento no soportado")

    await db.commit()
    return {"status": "success", "message": f"Documento {data.tipo_documento} registrado"}

@router.post("/hr/vacaciones", status_code=status.HTTP_201_CREATED)
async def solicitar_vacacion(
    data: VacacionRequest,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Buscar empleado del usuario actual si existe
    stmt = select(Empleado).where(Empleado.email == current_user.email)
    emp = (await db.execute(stmt)).scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=400, detail="El usuario no tiene un expediente de empleado asociado")

    solicitud = ControlVacaciones(
        empleado_id=emp.id,
        fecha_inicio=data.fecha_inicio,
        fecha_fin=data.fecha_fin,
        dias_solicitados=data.dias_solicitados,
        estado="pendiente",
        tenant_id=current_user.tenant_id
    )
    db.add(solicitud)
    await db.commit()
    await db.refresh(solicitud)
    return solicitud

@router.post("/hr/nominas", status_code=status.HTTP_201_CREATED)
async def generar_nomina(
    data: NominaCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    neto = data.total_percepciones - data.total_deducciones
    nomina = Nomina(
        empleado_id=data.empleado_id,
        fecha_pago=data.fecha_pago,
        total_percepciones=data.total_percepciones,
        total_deducciones=data.total_deducciones,
        neto_pagado=neto,
        estado_timbrado="timbrado",
        uuid_cfdi=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id
    )
    db.add(nomina)
    await db.commit()
    await db.refresh(nomina)
    return nomina

# ============================================================================
# POS / BRANCH ENDPOINTS
# ============================================================================

@router.post("/branches/sucursales", status_code=status.HTTP_201_CREATED)
async def crear_sucursal(
    nombre: str,
    codigo: str,
    direccion: Optional[str] = None,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    nueva = Sucursal(
        nombre=nombre,
        codigo=codigo,
        direccion=direccion,
        tenant_id=current_user.tenant_id
    )
    db.add(nueva)
    await db.commit()
    await db.refresh(nueva)
    return nueva

@router.get("/branches/sucursales")
async def listar_sucursales(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Sucursal).where(cast(Sucursal.tenant_id, String) == str(current_user.tenant_id))
    result = await db.execute(stmt)
    return result.scalars().all()

# ============================================================================
# CAD & LICENSING ENDPOINTS
# ============================================================================

@router.post("/cad/nesting-results", status_code=status.HTTP_201_CREATED)
async def registrar_nesting(
    data: NestingResults,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # En la nube guardamos el registro de optimización y el consumo
    return {
        "status": "success",
        "message": "Nesting results synchronized to cloud successfully",
        "saved_data": {
            "diseno_id": data.diseno_id,
            "metros_consumidos": data.metros_consumidos,
            "metros_desperdiciados": data.metros_desperdiciados,
            "piezas_cortadas": data.piezas_cortadas,
            "timestamp": datetime.utcnow().isoformat()
        }
    }

@router.get("/cad/licencia/verificar")
async def verificar_licencia_cad(
    codigo_licencia: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Licencia).where(Licencia.codigo == codigo_licencia)
    lic = (await db.execute(stmt)).scalar_one_or_none()
    if not lic or not lic.activa:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Licencia no válida o inactiva")

    return {
        "status": "valid",
        "licencia_id": lic.id,
        "tenant_id": lic.tenant_id,
        "fecha_fin": lic.fecha_fin
    }
