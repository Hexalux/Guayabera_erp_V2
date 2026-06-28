"""
Endpoints para Reportes Financieros y Contables
Generación de estados financieros, balanzas, libros y análisis
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import Optional

from app.core.database import get_db
from app.services.reportes.reportes_service import ReportesService
from app.schemas.reportes import (
    RequestBalanceComprobacion, RequestBalanceGeneral,
    RequestEstadoResultados, RequestLibroMayor,
    RequestAntiguedadSaldos, RequestFlujoEfectivo,
    ResponseBalanceComprobacion, ResponseBalanceGeneral,
    ResponseEstadoResultados, ResponseLibroMayor,
    ResponseAntiguedadSaldos, ResponseFlujoEfectivo
)
from app.models.usuario import Usuario
from app.api.v1.dependencies import get_current_user

router = APIRouter(prefix="/reportes", tags=["Reportes Financieros"])


@router.get("/balance-comprobacion", response_model=ResponseBalanceComprobacion)
async def obtener_balance_comprobacion(
    fecha_inicio: date = Query(..., description="Fecha de inicio"),
    fecha_fin: date = Query(..., description="Fecha de fin"),
    cuenta_id: Optional[int] = Query(None, description="Filtrar por cuenta"),
    nivel: Optional[int] = Query(None, ge=1, le=10, description="Nivel máximo"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Genera Balance de Comprobación
    
    Muestra saldos iniciales, movimientos del período y saldos finales
    de todas las cuentas o una específica. Similar a CONTPAQi.
    
    - **fecha_inicio**: Inicio del período contable
    - **fecha_fin**: Fin del período contable
    - **cuenta_id**: Opcional, filtrar por una cuenta específica
    - **nivel**: Opcional, límite de profundidad en jerarquía
    """
    service = ReportesService(db)
    
    try:
        resultado = await service.balance_comprobacion(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            tenant_id=current_user.tenant_id,
            cuenta_id=cuenta_id,
            nivel=nivel
        )
        return resultado
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/balance-general", response_model=ResponseBalanceGeneral)
async def obtener_balance_general(
    fecha_corte: date = Query(..., description="Fecha de corte del balance"),
    comparar_anterior: bool = Query(False, description="Comparar con año anterior"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Genera Balance General (Estado de Situación Financiera)
    
    Presenta Activos, Pasivos y Patrimonio clasificados como
    corrientes y no corrientes. Estilo Odoo.
    
    - **fecha_corte**: Fecha de corte para el balance
    - **comparar_anterior**: Opcional, incluir columna comparativa
    """
    service = ReportesService(db)
    
    try:
        resultado = await service.balance_general(
            fecha_corte=fecha_corte,
            tenant_id=current_user.tenant_id,
            comparar_ejercicio_anterior=comparar_anterior
        )
        return resultado
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/estado-resultados", response_model=ResponseEstadoResultados)
async def obtener_estado_resultados(
    fecha_inicio: date = Query(..., description="Fecha de inicio"),
    fecha_fin: date = Query(..., description="Fecha de fin"),
    centro_costo_id: Optional[int] = Query(None, description="Filtrar por CECO"),
    mostrar_margenes: bool = Query(True, description="Mostrar márgenes %"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Genera Estado de Resultados (Pérdidas y Ganancias)
    
    Muestra ingresos, costos, gastos y utilidades con márgenes
    porcentuales. Similar a Management Pro.
    
    - **fecha_inicio**: Inicio del período
    - **fecha_fin**: Fin del período
    - **centro_costo_id**: Opcional, filtrar por centro de costo
    - **mostrar_margenes**: Incluir cálculos de margen bruto, operativo y neto
    """
    service = ReportesService(db)
    
    try:
        resultado = await service.estado_resultados(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            tenant_id=current_user.tenant_id,
            por_centro_costo=centro_costo_id
        )
        return resultado
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/libro-mayor/{cuenta_id}", response_model=ResponseLibroMayor)
async def obtener_libro_mayor(
    cuenta_id: int,
    fecha_inicio: date = Query(..., description="Fecha de inicio"),
    fecha_fin: date = Query(..., description="Fecha de fin"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Genera Libro Mayor para una cuenta específica
    
    Detalle cronológico de todos los movimientos con saldos acumulados.
    Esencial para auditoría y análisis de cuentas.
    
    - **cuenta_id**: ID de la cuenta contable
    - **fecha_inicio**: Inicio del período
    - **fecha_fin**: Fin del período
    """
    service = ReportesService(db)
    
    try:
        resultado = await service.libro_mayor(
            cuenta_id=cuenta_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            tenant_id=current_user.tenant_id
        )
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/antiguedad-saldos", response_model=ResponseAntiguedadSaldos)
async def obtener_antiguedad_saldos(
    tipo: str = Query(..., description="'clientes' o 'proveedores'"),
    fecha_corte: date = Query(..., description="Fecha de corte"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Genera Reporte de Antigüedad de Saldos
    
    Clasifica documentos vencidos por rangos de días (corriente, 31-60, 61-90, +90).
    Crucial para gestión de cobranza y pagos. Similar a CONTPAQi.
    
    - **tipo**: 'clientes' para CXC o 'proveedores' para CXP
    - **fecha_corte**: Fecha para calcular antigüedad
    """
    service = ReportesService(db)
    
    try:
        resultado = await service.antiguedad_saldos(
            tipo=tipo,
            fecha_corte=fecha_corte,
            tenant_id=current_user.tenant_id
        )
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/flujo-efectivo", response_model=ResponseFlujoEfectivo)
async def obtener_flujo_efectivo(
    fecha_inicio: date = Query(..., description="Fecha de inicio"),
    fecha_fin: date = Query(..., description="Fecha de fin"),
    metodo: str = Query('indirecto', description="'directo' o 'indirecto'"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Genera Estado de Flujo de Efectivo
    
    Muestra origen y uso de efectivo en actividades de operación,
    inversión y financiamiento. Método indirecto o directo.
    
    - **fecha_inicio**: Inicio del período
    - **fecha_fin**: Fin del período
    - **metodo**: 'indirecto' (desde utilidad neta) o 'directo' (cobros/pagos)
    """
    service = ReportesService(db)
    
    try:
        resultado = await service.flujo_efectivo(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            tenant_id=current_user.tenant_id,
            metodo=metodo
        )
        return resultado
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/resumen-ejecutivo")
async def obtener_resumen_ejecutivo(
    fecha_corte: date = Query(..., description="Fecha de corte"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene Resumen Ejecutivo de Indicadores Financieros
    
    KPIs principales: liquidez, endeudamiento, rentabilidad, rotación.
    Útil para toma de decisiones gerenciales.
    """
    # Implementación futura de KPIs
    return {
        "mensaje": "Funcionalidad en desarrollo",
        "fecha_corte": fecha_corte.isoformat()
    }
