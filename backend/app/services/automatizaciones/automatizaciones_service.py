"""
Servicios de Automatización de Procesos Contables y Financieros
Incluye: asientos automáticos, conciliación bancaria automática, 
generación de pólizas, procesos batch programados
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import joinedload
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
from decimal import Decimal
import asyncio
import logging

from app.models.contabilidad import (
    AsientoContable, MovimientoAsiento, CuentaContable,
    PeriodoContable, TipoCuenta, NaturalezaCuenta
)
from app.models.cxc import FacturaCliente, PagoCliente
from app.models.cxp import FacturaProveedor, PagoProveedor
from app.models.gastos.gasto import Gasto, DepreciacionActivo
from app.models.revaluacion.revaluacion import TipoCambio, RevaluacionAutomatica

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AutomatizacionesService:
    """Servicio para automatización de procesos contables"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generar_asientos_automaticos_cxc(self, tenant_id: int) -> Dict[str, Any]:
        """
        Genera asientos contables automáticos para facturas y pagos de clientes
        Similar a CONTPAQi: conexión contable automática
        """
        resultados = {
            'facturas_procesadas': 0,
            'pagos_procesados': 0,
            'asientos_generados': [],
            'errores': []
        }
        
        # Obtener facturas sin registro contable
        query_facturas = select(FacturaCliente).where(
            FacturaCliente.tenant_id == tenant_id,
            FacturaCliente.registro_contable == False
        )
        result = await self.db.execute(query_facturas)
        facturas = result.scalars().all()
        
        for factura in facturas:
            try:
                # Verificar período abierto
                periodo = await self._verificar_periodo_abierto(factura.fecha_emision, tenant_id)
                if not periodo:
                    resultados['errores'].append(f"Factura {factura.folio}: período cerrado")
                    continue
                
                # Generar asiento de venta
                asiento = AsientoContable(
                    tenant_id=tenant_id,
                    numero=await self._generar_numero_asiento(tenant_id),
                    fecha=factura.fecha_emision,
                    periodo_id=periodo.id,
                    descripcion=f"Venta por factura {factura.folio}",
                    tipo='venta',
                    referencia=f'FACT-{factura.folio}',
                    estado='registrado',
                    total_debe=factura.total,
                    total_haber=factura.total
                )
                
                self.db.add(asiento)
                await self.db.flush()
                
                # Movimientos del asiento
                # Cargo a Clientes
                cuenta_cliente = await self._obtener_cuenta_por_tipo(TipoCuenta.activo, 'Clientes', tenant_id)
                mov_cliente = MovimientoAsiento(
                    asiento_id=asiento.id,
                    cuenta_id=cuenta_cliente.id if cuenta_cliente else 1,
                    debe=factura.total,
                    haber=Decimal('0'),
                    centro_costo_id=factura.centro_costo_id
                )
                
                # Abono a Ingresos
                cuenta_ingreso = await self._obtener_cuenta_por_tipo(TipoCuenta.ingreso, 'Ventas', tenant_id)
                mov_ingreso = MovimientoAsiento(
                    asiento_id=asiento.id,
                    cuenta_id=cuenta_ingreso.id if cuenta_ingreso else 1,
                    debe=Decimal('0'),
                    haber=factura.subtotal,
                    centro_costo_id=factura.centro_costo_id
                )
                
                # Abono a IVA Acreditable (si aplica)
                if factura.impuesto > 0:
                    cuenta_iva = await self._obtener_cuenta_por_tipo(TipoCuenta.pasivo, 'IVA', tenant_id)
                    mov_iva = MovimientoAsiento(
                        asiento_id=asiento.id,
                        cuenta_id=cuenta_iva.id if cuenta_iva else 1,
                        debe=Decimal('0'),
                        haber=factura.impuesto,
                        centro_costo_id=factura.centro_costo_id
                    )
                    self.db.add(mov_iva)
                
                self.db.add_all([mov_cliente, mov_ingreso])
                
                # Marcar factura como registrada
                factura.registro_contable = True
                factura.asiento_id = asiento.id
                
                resultados['facturas_procesadas'] += 1
                resultados['asientos_generados'].append({
                    'tipo': 'venta',
                    'folio': factura.folio,
                    'numero_asiento': asiento.numero
                })
                
            except Exception as e:
                logger.error(f"Error procesando factura {factura.folio}: {str(e)}")
                resultados['errores'].append(f"Factura {factura.folio}: {str(e)}")
        
        await self.db.commit()
        return resultados
    
    async def generar_asientos_automaticos_cxp(self, tenant_id: int) -> Dict[str, Any]:
        """
        Genera asientos contables automáticos para facturas y pagos de proveedores
        """
        resultados = {
            'facturas_procesadas': 0,
            'pagos_procesados': 0,
            'asientos_generados': [],
            'errores': []
        }
        
        # Obtener facturas de proveedores sin registro contable
        query_facturas = select(FacturaProveedor).where(
            FacturaProveedor.tenant_id == tenant_id,
            FacturaProveedor.registro_contable == False
        )
        result = await self.db.execute(query_facturas)
        facturas = result.scalars().all()
        
        for factura in facturas:
            try:
                periodo = await self._verificar_periodo_abierto(factura.fecha_emision, tenant_id)
                if not periodo:
                    resultados['errores'].append(f"Factura Proveedor {factura.folio}: período cerrado")
                    continue
                
                # Generar asiento de compra/gasto
                asiento = AsientoContable(
                    tenant_id=tenant_id,
                    numero=await self._generar_numero_asiento(tenant_id),
                    fecha=factura.fecha_emision,
                    periodo_id=periodo.id,
                    descripcion=f"Compra/Gasto por factura {factura.folio}",
                    tipo='compra',
                    referencia=f'PROV-{factura.folio}',
                    estado='registrado',
                    total_debe=factura.total,
                    total_haber=factura.total
                )
                
                self.db.add(asiento)
                await self.db.flush()
                
                # Cargo a Gasto o Activo
                cuenta_gasto = await self._obtener_cuenta_por_tipo(TipoCuenta.gasto, 'Compras', tenant_id)
                mov_gasto = MovimientoAsiento(
                    asiento_id=asiento.id,
                    cuenta_id=cuenta_gasto.id if cuenta_gasto else 1,
                    debe=factura.subtotal,
                    haber=Decimal('0'),
                    centro_costo_id=factura.centro_costo_id
                )
                
                # Cargo a IVA Acreditable
                cuenta_iva = await self._obtener_cuenta_por_tipo(TipoCuenta.activo, 'IVA Acreditable', tenant_id)
                mov_iva = MovimientoAsiento(
                    asiento_id=asiento.id,
                    cuenta_id=cuenta_iva.id if cuenta_iva else 1,
                    debe=factura.impuesto,
                    haber=Decimal('0'),
                    centro_costo_id=factura.centro_costo_id
                )
                
                # Abono a Proveedores
                cuenta_proveedor = await self._obtener_cuenta_por_tipo(TipoCuenta.pasivo, 'Proveedores', tenant_id)
                mov_proveedor = MovimientoAsiento(
                    asiento_id=asiento.id,
                    cuenta_id=cuenta_proveedor.id if cuenta_proveedor else 1,
                    debe=Decimal('0'),
                    haber=factura.total,
                    centro_costo_id=factura.centro_costo_id
                )
                
                self.db.add_all([mov_gasto, mov_iva, mov_proveedor])
                
                factura.registro_contable = True
                factura.asiento_id = asiento.id
                
                resultados['facturas_procesadas'] += 1
                resultados['asientos_generados'].append({
                    'tipo': 'compra',
                    'folio': factura.folio,
                    'numero_asiento': asiento.numero
                })
                
            except Exception as e:
                logger.error(f"Error procesando factura proveedor {factura.folio}: {str(e)}")
                resultados['errores'].append(f"Factura {factura.folio}: {str(e)}")
        
        await self.db.commit()
        return resultados
    
    async def generar_depreciacion_mensual(
        self, 
        tenant_id: int, 
        periodo: str  # Formato AAAA-MM
    ) -> Dict[str, Any]:
        """
        Genera automáticamente los asientos de depreciación del mes
        Similar a Management Pro: cálculo automático de depreciación
        """
        resultados = {
            'activos_procesados': 0,
            'depreciacion_total': Decimal('0'),
            'asiento_generado': None,
            'errores': []
        }
        
        try:
            # Parsear período
            anio, mes = map(int, periodo.split('-'))
            fecha_depreciacion = date(anio, mes, 28)  # Último día del mes
            
            # Verificar período abierto
            periodo_contable = await self._verificar_periodo_abierto(fecha_depreciacion, tenant_id)
            if not periodo_contable:
                return {'error': f'Período {periodo} está cerrado'}
            
            # Obtener activos fijos con depreciación pendiente
            query_activos = select(DepreciacionActivo).where(
                DepreciacionActivo.tenant_id == tenant_id,
                DepreciacionActivo.fecha_inicio <= fecha_depreciacion,
                (DepreciacionActivo.fecha_fin.is_(None) | 
                 (DepreciacionActivo.fecha_fin > fecha_depreciacion))
            )
            
            result = await self.db.execute(query_activos)
            activos = result.scalars().all()
            
            if not activos:
                return {'mensaje': 'No hay activos para depreciar en este período'}
            
            # Calcular depreciación total del mes
            total_depreciacion = sum(a.depreciacion_mensual for a in activos)
            
            if total_depreciacion == 0:
                return {'mensaje': 'La depreciación total es cero'}
            
            # Generar asiento de depreciación
            asiento = AsientoContable(
                tenant_id=tenant_id,
                numero=await self._generar_numero_asiento(tenant_id),
                fecha=fecha_depreciacion,
                periodo_id=periodo_contable.id,
                descripcion=f"Depreciación del mes {periodo}",
                tipo='depreciacion',
                referencia=f'DEPR-{periodo}',
                estado='registrado',
                total_debe=total_depreciacion,
                total_haber=total_depreciacion
            )
            
            self.db.add(asiento)
            await self.db.flush()
            
            # Cargo a Gasto por Depreciación
            cuenta_gasto_depr = await self._obtener_cuenta_por_codigo('6105', tenant_id)
            if cuenta_gasto_depr:
                mov_gasto = MovimientoAsiento(
                    asiento_id=asiento.id,
                    cuenta_id=cuenta_gasto_depr.id,
                    debe=total_depreciacion,
                    haber=Decimal('0')
                )
                self.db.add(mov_gasto)
            
            # Abono a Depreciación Acumulada (cuenta de activo acreditora)
            cuenta_depr_acum = await self._obtener_cuenta_por_codigo('1190', tenant_id)
            if cuenta_depr_acum:
                mov_acum = MovimientoAsiento(
                    asiento_id=asiento.id,
                    cuenta_id=cuenta_depr_acum.id,
                    debe=Decimal('0'),
                    haber=total_depreciacion
                )
                self.db.add(mov_acum)
            
            # Actualizar activos con depreciación aplicada
            for activo in activos:
                activo.depreciacion_acumulada += activo.depreciacion_mensual
                activo.valor_en_libros -= activo.depreciacion_mensual
                activo.ultima_depreciacion = fecha_depreciacion
            
            await self.db.commit()
            
            resultados['activos_procesados'] = len(activos)
            resultados['depreciacion_total'] = total_depreciacion
            resultados['asiento_generado'] = asiento.numero
            
            return resultados
            
        except Exception as e:
            logger.error(f"Error generando depreciación: {str(e)}")
            resultados['errores'].append(str(e))
            await self.db.rollback()
            return resultados
    
    async def ejecutar_revaluacion_cambiaria(
        self,
        tenant_id: int,
        fecha_corte: date,
        tipo_cambio_oficial: Decimal
    ) -> Dict[str, Any]:
        """
        Ejecuta revaluación cambiaria automática de cuentas en moneda extranjera
        Similar a CONTPAQi: ajuste por diferencia cambiaria
        """
        resultados = {
            'cuentas_revaluadas': 0,
            'diferencia_cambiaria': Decimal('0'),
            'asiento_generado': None,
            'errores': []
        }
        
        try:
            # Obtener configuración de revaluación automática
            query_config = select(RevaluacionAutomatica).where(
                RevaluacionAutomatica.tenant_id == tenant_id,
                RevaluacionAutomatica.activa == True
            )
            result = await self.db.execute(query_config)
            config = result.scalars().first()
            
            if not config:
                return {'mensaje': 'No hay configuración de revaluación automática'}
            
            # Obtener cuentas en moneda extranjera con saldo
            # (Implementación simplificada - en producción usar filtro específico)
            query_cuentas = select(CuentaContable).where(
                CuentaContable.tenant_id == tenant_id,
                CuentaContable.moneda != 'MXN'
            )
            result = await self.db.execute(query_cuentas)
            cuentas = result.scalars().all()
            
            if not cuentas:
                return {'mensaje': 'No hay cuentas en moneda extranjera'}
            
            # Calcular diferencias cambiarias
            total_diferencia = Decimal('0')
            movimientos_revaluacion = []
            
            for cuenta in cuentas:
                # Obtener saldo en moneda extranjera
                saldo = await self._calcular_saldo_cuenta(cuenta.id, fecha_corte, tenant_id)
                
                if saldo != 0:
                    # Obtener tipo de cambio histórico (simplificado)
                    tipo_cambio_historico = Decimal('17.50')  # Valor ejemplo
                    
                    # Calcular diferencia
                    diferencia = saldo * (tipo_cambio_oficial - tipo_cambio_historico)
                    total_diferencia += diferencia
                    
                    if diferencia != 0:
                        movimientos_revaluacion.append({
                            'cuenta': cuenta.codigo,
                            'saldo_original': float(saldo),
                            'diferencia': float(diferencia)
                        })
            
            if total_diferencia == 0:
                return {'mensaje': 'No hay diferencia cambiaria significativa'}
            
            # Generar asiento de ajuste cambiario
            asiento = AsientoContable(
                tenant_id=tenant_id,
                numero=await self._generar_numero_asiento(tenant_id),
                fecha=fecha_corte,
                descripcion=f"Revaluación cambiaria al {fecha_corte.isoformat()}",
                tipo='revaluacion',
                referencia=f'REVAL-{fecha_corte.isoformat()}',
                estado='registrado',
                total_debe=abs(total_diferencia),
                total_haber=abs(total_diferencia)
            )
            
            self.db.add(asiento)
            await self.db.flush()
            
            # Generar movimientos según sea pérdida o ganancia
            if total_diferencia > 0:
                # Ganancia cambiaria (abono a ingreso)
                cuenta_ingreso = await self._obtener_cuenta_por_codigo('7200', tenant_id)
                if cuenta_ingreso:
                    mov = MovimientoAsiento(
                        asiento_id=asiento.id,
                        cuenta_id=cuenta_ingreso.id,
                        debe=Decimal('0'),
                        haber=abs(total_diferencia)
                    )
                    self.db.add(mov)
            else:
                # Pérdida cambiaria (cargo a gasto)
                cuenta_gasto = await self._obtener_cuenta_por_codigo('6300', tenant_id)
                if cuenta_gasto:
                    mov = MovimientoAsiento(
                        asiento_id=asiento.id,
                        cuenta_id=cuenta_gasto.id,
                        debe=abs(total_diferencia),
                        haber=Decimal('0')
                    )
                    self.db.add(mov)
            
            await self.db.commit()
            
            resultados['cuentas_revaluadas'] = len(movimientos_revaluacion)
            resultados['diferencia_cambiaria'] = total_diferencia
            resultados['asiento_generado'] = asiento.numero
            resultados['detalle'] = movimientos_revaluacion
            
            return resultados
            
        except Exception as e:
            logger.error(f"Error en revaluación cambiaria: {str(e)}")
            resultados['errores'].append(str(e))
            await self.db.rollback()
            return resultados
    
    async def cerrar_periodo_automatico(
        self,
        tenant_id: int,
        periodo_id: int
    ) -> Dict[str, Any]:
        """
        Cierra período contable automáticamente con validaciones
        """
        resultados = {
            'validaciones': [],
            'asientos_cierre': [],
            'periodo_cerrado': False,
            'errores': []
        }
        
        try:
            # Obtener período
            periodo = await self.db.get(PeriodoContable, periodo_id)
            if not periodo or periodo.tenant_id != tenant_id:
                return {'error': 'Período no encontrado'}
            
            if periodo.estado == 'cerrado':
                return {'mensaje': 'El período ya está cerrado'}
            
            # Validaciones previas al cierre
            # 1. Verificar que todos los asientos estén registrados
            query_asientos_pendientes = select(AsientoContable).where(
                AsientoContable.tenant_id == tenant_id,
                AsientoContable.periodo_id == periodo_id,
                AsientoContable.estado == 'borrador'
            )
            result = await self.db.execute(query_asientos_pendientes)
            asientos_borrador = result.scalars().all()
            
            if asientos_borrador:
                resultados['validaciones'].append({
                    'tipo': 'advertencia',
                    'mensaje': f'{len(asientos_borrador)} asientos en borrador'
                })
            
            # 2. Generar asientos de cierre (ingresos y gastos a Resultados del Ejercicio)
            # Calcular saldo de cuentas de resultados
            utilidad_ejercicio = await self._calcular_utilidad_periodo(
                periodo.fecha_inicio, periodo.fecha_fin, tenant_id
            )
            
            if utilidad_ejercicio != 0:
                # Generar asiento de cierre
                asiento_cierre = AsientoContable(
                    tenant_id=tenant_id,
                    numero=await self._generar_numero_asiento(tenant_id),
                    fecha=periodo.fecha_fin,
                    periodo_id=periodo_id,
                    descripcion=f"Cierre del período {periodo.nombre}",
                    tipo='cierre',
                    referencia=f'CIERRE-{periodo.nombre}',
                    estado='registrado',
                    total_debe=abs(utilidad_ejercicio),
                    total_haber=abs(utilidad_ejercicio)
                )
                
                self.db.add(asiento_cierre)
                await self.db.flush()
                
                resultados['asientos_cierre'].append(asiento_cierre.numero)
            
            # 3. Cambiar estado del período a cerrado
            periodo.estado = 'cerrado'
            periodo.fecha_cierre = datetime.now()
            
            await self.db.commit()
            
            resultados['periodo_cerrado'] = True
            resultados['utilidad_ejercicio'] = float(utilidad_ejercicio)
            
            return resultados
            
        except Exception as e:
            logger.error(f"Error cerrando período: {str(e)}")
            resultados['errores'].append(str(e))
            await self.db.rollback()
            return resultados
    
    # Métodos auxiliares
    
    async def _verificar_periodo_abierto(self, fecha: date, tenant_id: int) -> Optional[PeriodoContable]:
        """Verifica si hay un período abierto para la fecha dada"""
        query = select(PeriodoContable).where(
            PeriodoContable.tenant_id == tenant_id,
            PeriodoContable.fecha_inicio <= fecha,
            PeriodoContable.fecha_fin >= fecha,
            PeriodoContable.estado == 'abierto'
        )
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def _generar_numero_asiento(self, tenant_id: int) -> str:
        """Genera número consecutivo para asiento"""
        # Implementación simplificada
        from datetime import datetime
        return f"A-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    async def _obtener_cuenta_por_tipo(
        self, 
        tipo: TipoCuenta, 
        busqueda: str,
        tenant_id: int
    ) -> Optional[CuentaContable]:
        """Obtiene una cuenta por tipo y nombre"""
        query = select(CuentaContable).where(
            CuentaContable.tenant_id == tenant_id,
            CuentaContable.tipo == tipo,
            CuentaContable.nombre.ilike(f'%{busqueda}%')
        )
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def _obtener_cuenta_por_codigo(
        self, 
        codigo: str, 
        tenant_id: int
    ) -> Optional[CuentaContable]:
        """Obtiene cuenta por código exacto o parcial"""
        query = select(CuentaContable).where(
            CuentaContable.tenant_id == tenant_id,
            CuentaContable.codigo == codigo
        )
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def _calcular_saldo_cuenta(
        self, 
        cuenta_id: int, 
        fecha_corte: date, 
        tenant_id: int
    ) -> Decimal:
        """Calcula saldo de una cuenta hasta una fecha"""
        from sqlalchemy import select, func
        
        stmt = select(
            func.sum(MovimientoAsiento.debe).label('total_debe'),
            func.sum(MovimientoAsiento.haber).label('total_haber')
        ).join(
            AsientoContable, MovimientoAsiento.asiento_id == AsientoContable.id
        ).where(
            AsientoContable.tenant_id == tenant_id,
            AsientoContable.fecha <= fecha_corte,
            AsientoContable.estado == 'registrado',
            MovimientoAsiento.cuenta_id == cuenta_id
        )
        
        result = await self.db.execute(stmt)
        saldo = result.first()
        debe = Decimal(str(saldo.total_debe or 0))
        haber = Decimal(str(saldo.total_haber or 0))
        
        return debe - haber
    
    async def _calcular_utilidad_periodo(
        self,
        fecha_inicio: date,
        fecha_fin: date,
        tenant_id: int
    ) -> Decimal:
        """Calcula utilidad del período (ingresos - gastos)"""
        from sqlalchemy import select, func
        
        # Sumar ingresos
        stmt_ingresos = select(func.sum(MovimientoAsiento.haber)).join(
            AsientoContable, MovimientoAsiento.asiento_id == AsientoContable.id
        ).join(
            CuentaContable, MovimientoAsiento.cuenta_id == CuentaContable.id
        ).where(
            AsientoContable.tenant_id == tenant_id,
            AsientoContable.fecha >= fecha_inicio,
            AsientoContable.fecha <= fecha_fin,
            AsientoContable.estado == 'registrado',
            CuentaContable.tipo == TipoCuenta.ingreso
        )
        
        result = await self.db.execute(stmt_ingresos)
        total_ingresos = Decimal(str(result.scalar() or 0))
        
        # Sumar gastos
        stmt_gastos = select(func.sum(MovimientoAsiento.debe)).join(
            AsientoContable, MovimientoAsiento.asiento_id == AsientoContable.id
        ).join(
            CuentaContable, MovimientoAsiento.cuenta_id == CuentaContable.id
        ).where(
            AsientoContable.tenant_id == tenant_id,
            AsientoContable.fecha >= fecha_inicio,
            AsientoContable.fecha <= fecha_fin,
            AsientoContable.estado == 'registrado',
            CuentaContable.tipo == TipoCuenta.gasto
        )
        
        result = await self.db.execute(stmt_gastos)
        total_gastos = Decimal(str(result.scalar() or 0))
        
        return total_ingresos - total_gastos
