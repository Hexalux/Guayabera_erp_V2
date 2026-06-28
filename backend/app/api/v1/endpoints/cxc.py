"""
API de Cuentas por Cobrar (CXC)
Fusión de CONTPAQi (robustez), Odoo (flexibilidad), Management Pro (opciones)
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.core.database import get_db
from app.services.cxc_service import CXCService
from app.schemas.cxc import (
    DocumentoCXCCreate, DocumentoXCResponse, DocumentoXCUpdate, CXCFiltro,
    CobroCreate, CobroResponse, AplicacionCXCCreate, AplicacionXCResponse,
    NotaCreditoCreate, AnticipoCreate, AnticipoResponse,
    InteresMoratorioCalculation, InteresMoratorioResponse,
    ResumenCarteraCliente, ReporteAntiguedadSaldos, EstadoCuentaCliente
)
from app.models.auth import Usuario
from app.core.security import get_current_active_user
from app.core.dependencies import get_tenant_id

router = APIRouter(prefix="/cxc", tags=["Cuentas por Cobrar"])


# ==================== DOCUMENTOS CXC ====================

@router.post("/documentos", response_model=DocumentoXCResponse, status_code=status.HTTP_201_CREATED)
async def crear_documento_cxc(
    data: DocumentoCXCCreate,
    serie: str = Query("FAC-001", description="Serie del documento"),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    usuario: Usuario = Depends(get_current_active_user)
):
    """
    Crear documento de Cuentas por Cobrar (Factura, Nota Crédito, etc.)
    
    - **tipo_documento**: factura, nota_credito, nota_debito, recibo, pagare, anticipo
    - **cliente_id**: UUID del cliente
    - **fecha_emision**: Fecha de emisión del documento
    - **fecha_vencimiento**: Fecha de vencimiento
    - **total**: Valor total del documento
    - **dias_plazo**: Días de crédito otorgados
    """
    service = CXCService(db)
    try:
        documento = await service.crear_documento(
            data=data,
            tenant_id=tenant_id,
            usuario_id=usuario.id,
            serie=serie
        )
        return documento
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/documentos", response_model=List[DocumentoXCResponse])
async def listar_documentos_cxc(
    tipo_documento: Optional[str] = Query(None),
    cliente_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    vencido: Optional[bool] = Query(None),
    limite: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Listar documentos CXC con filtros avanzados
    
    - **tipo_documento**: Filtrar por tipo de documento
    - **cliente_id**: Filtrar por cliente específico
    - **estado**: registrado, parcial, saldado, vencido, cancelado
    - **vencido**: True para mostrar solo vencidos, False para no vencidos
    """
    filtro = CXCFiltro(
        tipo_documento=tipo_documento,
        cliente_id=cliente_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        vencido=vencido
    )
    
    service = CXCService(db)
    documentos = await service.listar_documentos(
        filtro=filtro,
        tenant_id=tenant_id,
        limite=limite,
        offset=offset
    )
    return documentos


@router.get("/documentos/{documento_id}", response_model=DocumentoXCResponse)
async def obtener_documento_cxc(
    documento_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Obtener detalles de un documento CXC específico"""
    from app.models.cxc import CXCDocumento
    documento = await db.get(CXCDocumento, documento_id)
    
    if not documento or documento.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado"
        )
    
    return documento


# ==================== COBROS ====================

@router.post("/cobros", response_model=CobroResponse, status_code=status.HTTP_201_CREATED)
async def registrar_cobro(
    data: CobroCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    usuario: Usuario = Depends(get_current_active_user)
):
    """
    Registrar cobro de cliente
    
    - **cliente_id**: Cliente que realiza el pago
    - **forma_pago**: efectivo, cheque, transferencia, tarjeta
    - **total**: Valor total del cobro
    - **documentos_a_aplicar**: Lista de documentos a los que se aplicará el pago
    """
    service = CXCService(db)
    try:
        cobro = await service.registrar_cobro(
            data=data,
            tenant_id=tenant_id,
            usuario_id=usuario.id
        )
        return cobro
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/aplicaciones", response_model=AplicacionXCResponse)
async def aplicar_pago_documento(
    data: AplicacionCXCCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    usuario: Usuario = Depends(get_current_active_user)
):
    """
    Aplicar pago o nota de crédito a un documento
    
    - **documento_pago_id**: ID del pago o nota de crédito
    - **documento_aplicado_id**: ID de la factura u otro documento
    - **valor_aplicado**: Valor a aplicar
    - **tipo_aplicacion**: pago, nota_credito, anticipo, bonificacion
    """
    service = CXCService(db)
    try:
        aplicacion = await service.aplicar_pago_documento(
            documento_pago_id=data.documento_pago_id,
            documento_aplicado_id=data.documento_aplicado_id,
            valor_aplicado=data.valor_aplicado,
            tenant_id=tenant_id,
            usuario_id=usuario.id,
            tipo_aplicacion=data.tipo_aplicacion,
            observaciones=data.observaciones
        )
        return aplicacion
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== NOTAS DE CRÉDITO ====================

@router.post("/notas-credito", response_model=DocumentoXCResponse, status_code=status.HTTP_201_CREATED)
async def crear_nota_credito(
    data: NotaCreditoCreate,
    serie: str = Query("NCR-001", description="Serie para nota de crédito"),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    usuario: Usuario = Depends(get_current_active_user)
):
    """
    Crear nota de crédito
    
    Tipos: directa, bonificacion, devolucion, pre_pedido
    
    - **documento_origen_id**: Factura original (opcional)
    - **motivo**: Razón detallada de la nota de crédito
    """
    service = CXCService(db)
    try:
        nota = await service.crear_nota_credito(
            data=data,
            tenant_id=tenant_id,
            usuario_id=usuario.id,
            serie=serie
        )
        return nota
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== ANTICIPOS ====================

@router.post("/anticipos", response_model=AnticipoResponse, status_code=status.HTTP_201_CREATED)
async def registrar_anticipo(
    data: AnticipoCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    usuario: Usuario = Depends(get_current_active_user)
):
    """Registrar anticipo de cliente"""
    # En producción se implementaría como documento tipo ANTICIPO
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Funcionalidad en desarrollo"
    )


# ==================== INTERESES MORATORIOS ====================

@router.post("/intereses-moratorios/calcular", response_model=InteresMoratorioResponse)
async def calcular_intereses_moratorios(
    data: InteresMoratorioCalculation,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    usuario: Usuario = Depends(get_current_active_user)
):
    """
    Calcular intereses moratorios para un documento vencido
    
    - **documento_id**: Documento a calcular
    - **tasa_interes_anual**: Tasa anual en porcentaje
    - **dias_gracia**: Días de gracia antes de cobrar interés
    """
    service = CXCService(db)
    try:
        resultado = await service.calcular_intereses_moratorios(
            data=data,
            tenant_id=tenant_id,
            usuario_id=usuario.id
        )
        return resultado
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== REPORTES ====================

@router.get("/clientes/{cliente_id}/resumen-cartera", response_model=ResumenCarteraCliente)
async def obtener_resumen_cartera(
    cliente_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Obtener resumen de cartera de un cliente
    
    Incluye saldo total, vencido, por vencer y disponible de crédito
    """
    service = CXCService(db)
    try:
        resumen = await service.obtener_resumen_cartera(
            cliente_id=cliente_id,
            tenant_id=tenant_id
        )
        return resumen
    except Exception as e:
        if "no encontrado" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/reportes/antiguedad-saldos")
async def reporte_antiguedad_saldos(
    cliente_id: Optional[UUID] = Query(None),
    fecha_corte: date = Query(default_factory=date.today),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Reporte de antigüedad de saldos (corriente, 30, 60, 90, 120+ días)"""
    # Implementación pendiente
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Reporte en desarrollo"
    )


@router.get("/clientes/{cliente_id}/estado-cuenta", response_model=EstadoCuentaCliente)
async def estado_de_cuenta_cliente(
    cliente_id: UUID,
    fecha_corte: date = Query(default_factory=date.today),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Estado de cuenta completo de un cliente
    
    Muestra movimientos, saldos y documentos vencidos/por vencer
    """
    # Implementación simplificada
    from app.models.terceros import Tercero
    cliente = await db.get(Tercero, cliente_id)
    
    if not cliente or cliente.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    return {
        "cliente_id": str(cliente.id),
        "cliente_nombre": cliente.razon_social,
        "cliente_identificacion": cliente.identificacion,
        "fecha_corte": fecha_corte,
        "saldo_inicial": 0,
        "movimientos": [],
        "saldo_final": 0,
        "documentos_vencidos": [],
        "documentos_por_vencer": []
    }
