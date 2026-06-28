"""
Servicios para Reportes Financieros y Contables
Generación de estados financieros, balanzas, libros y análisis
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import joinedload, aliased
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from decimal import Decimal
import asyncio

from app.models.contabilidad import (
    CuentaContable, AsientoContable, MovimientoAsiento, 
    CentroCosto, PeriodoContable, TipoCuenta, NaturalezaCuenta
)
from app.models.cxp import FacturaProveedor, PagoProveedor
from app.models.cxc import FacturaCliente, PagoCliente
from app.models.gastos.gasto import Gasto
from app.models.revaluacion.revaluacion import TipoCambio


class ReportesService:
    """Servicio para generación de reportes financieros"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def balance_comprobacion(
        self, 
        fecha_inicio: date, 
        fecha_fin: date,
        tenant_id: int,
        cuenta_id: Optional[int] = None,
        nivel: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Genera Balance de Comprobación
        Similar a CONTPAQi: saldos iniciales, movimientos y saldos finales
        """
        # Obtener cuentas con sus movimientos
        query = select(CuentaContable).where(
            CuentaContable.tenant_id == tenant_id,
            CuentaContable.activa == True
        )
        
        if cuenta_id:
            query = query.where(CuentaContable.id == cuenta_id)
        
        if nivel:
            query = query.where(CuentaContable.nivel <= nivel)
        
        result = await self.db.execute(query)
        cuentas = result.scalars().all()
        
        reporte = []
        total_debe_ini = Decimal('0')
        total_haber_ini = Decimal('0')
        total_debe_mov = Decimal('0')
        total_haber_mov = Decimal('0')
        total_debe_fin = Decimal('0')
        total_haber_fin = Decimal('0')
        
        for cuenta in cuentas:
            # Calcular saldos iniciales (antes de fecha_inicio)
            stmt_saldo_ini = select(
                func.sum(MovimientoAsiento.debe).label('total_debe'),
                func.sum(MovimientoAsiento.haber).label('total_haber')
            ).join(
                AsientoContable, MovimientoAsiento.asiento_id == AsientoContable.id
            ).where(
                AsientoContable.tenant_id == tenant_id,
                AsientoContable.fecha < fecha_inicio,
                AsientoContable.estado == 'registrado',
                MovimientoAsiento.cuenta_id == cuenta.id
            )
            
            result_ini = await self.db.execute(stmt_saldo_ini)
            saldo_ini = result_ini.first()
            debe_ini = Decimal(str(saldo_ini.total_debe or 0))
            haber_ini = Decimal(str(saldo_ini.total_haber or 0))
            saldo_inicial = debe_ini - haber_ini
            
            # Calcular movimientos del período
            stmt_mov = select(
                func.sum(MovimientoAsiento.debe).label('total_debe'),
                func.sum(MovimientoAsiento.haber).label('total_haber')
            ).join(
                AsientoContable, MovimientoAsiento.asiento_id == AsientoContable.id
            ).where(
                AsientoContable.tenant_id == tenant_id,
                AsientoContable.fecha >= fecha_inicio,
                AsientoContable.fecha <= fecha_fin,
                AsientoContable.estado == 'registrado',
                MovimientoAsiento.cuenta_id == cuenta.id
            )
            
            result_mov = await self.db.execute(stmt_mov)
            mov = result_mov.first()
            debe_mov = Decimal(str(mov.total_debe or 0))
            haber_mov = Decimal(str(mov.total_haber or 0))
            
            # Calcular saldo final
            saldo_final = saldo_inicial + (debe_mov - haber_mov)
            debe_fin = max(saldo_final, Decimal('0')) if cuenta.naturaleza == 'deudora' else Decimal('0')
            haber_fin = abs(min(saldo_final, Decimal('0'))) if cuenta.naturaleza == 'acreedora' else Decimal('0')
            
            if saldo_final != 0 or debe_mov > 0 or haber_mov > 0:
                reporte.append({
                    'cuenta': {
                        'codigo': cuenta.codigo,
                        'nombre': cuenta.nombre,
                        'nivel': cuenta.nivel,
                        'tipo': cuenta.tipo.value,
                        'naturaleza': cuenta.naturaleza.value
                    },
                    'saldo_inicial': float(saldo_inicial),
                    'debe_inicial': float(debe_ini),
                    'haber_inicial': float(haber_ini),
                    'movimientos': {
                        'debe': float(debe_mov),
                        'haber': float(haber_mov)
                    },
                    'saldo_final': float(saldo_final),
                    'debe_final': float(debe_fin),
                    'haber_final': float(haber_fin)
                })
                
                total_debe_ini += debe_ini
                total_haber_ini += haber_ini
                total_debe_mov += debe_mov
                total_haber_mov += haber_mov
                total_debe_fin += debe_fin
                total_haber_fin += haber_fin
        
        return {
            'reporte': 'Balance de Comprobación',
            'fecha_inicio': fecha_inicio.isoformat(),
            'fecha_fin': fecha_fin.isoformat(),
            'fecha_generacion': datetime.now().isoformat(),
            'cuentas': reporte,
            'totales': {
                'saldo_inicial': float(total_debe_ini - total_haber_ini),
                'debe_inicial': float(total_debe_ini),
                'haber_inicial': float(total_haber_ini),
                'movimientos': {
                    'debe': float(total_debe_mov),
                    'haber': float(total_haber_mov)
                },
                'saldo_final': float(total_debe_fin - total_haber_fin),
                'debe_final': float(total_debe_fin),
                'haber_final': float(total_haber_fin),
                'cuadrado': abs(total_debe_fin - total_haber_fin) < Decimal('0.01')
            }
        }
    
    async def balance_general(
        self,
        fecha_corte: date,
        tenant_id: int,
        comparar_ejercicio_anterior: bool = False
    ) -> Dict[str, Any]:
        """
        Genera Balance General (Estado de Situación Financiera)
        Estilo Odoo: agrupado por tipos de cuenta (Activo, Pasivo, Patrimonio)
        """
        tipos_balance = [TipoCuenta.activo, TipoCuenta.pasivo, TipoCuenta.patrimonio]
        
        resultado = {
            'reporte': 'Balance General',
            'fecha_corte': fecha_corte.isoformat(),
            'fecha_generacion': datetime.now().isoformat(),
            'activos': {'corriente': [], 'no_corriente': [], 'total': 0},
            'pasivos': {'corriente': [], 'no_corriente': [], 'total': 0},
            'patrimonio': {'cuentas': [], 'total': 0},
            'total_activo': 0,
            'total_pasivo_patrimonio': 0,
            'cuadrado': False
        }
        
        for tipo_cuenta in tipos_balance:
            query = select(CuentaContable).where(
                CuentaContable.tenant_id == tenant_id,
                CuentaContable.tipo == tipo_cuenta,
                CuentaContable.activa == True,
                CuentaContable.padre_id.is_(None)  # Solo cuentas de primer nivel
            )
            
            result = await self.db.execute(query)
            cuentas_padre = result.scalars().all()
            
            for cuenta_padre in cuentas_padre:
                saldo = await self._calcular_saldo_cuenta(cuenta_padre.id, fecha_corte, tenant_id)
                
                es_corriente = self._es_cuenta_corriente(cuenta_padre)
                dato = {
                    'codigo': cuenta_padre.codigo,
                    'nombre': cuenta_padre.nombre,
                    'saldo': float(saldo),
                    'nivel': cuenta_padre.nivel
                }
                
                if tipo_cuenta == TipoCuenta.activo:
                    if es_corriente:
                        resultado['activos']['corriente'].append(dato)
                    else:
                        resultado['activos']['no_corriente'].append(dato)
                    resultado['activos']['total'] += float(saldo) if saldo > 0 else 0
                    
                elif tipo_cuenta == TipoCuenta.pasivo:
                    if es_corriente:
                        resultado['pasivos']['corriente'].append(dato)
                    else:
                        resultado['pasivos']['no_corriente'].append(dato)
                    resultado['pasivos']['total'] += float(abs(saldo)) if saldo < 0 else 0
                    
                elif tipo_cuenta == TipoCuenta.patrimonio:
                    resultado['patrimonio']['cuentas'].append(dato)
                    resultado['patrimonio']['total'] += float(abs(saldo)) if saldo < 0 else 0
        
        resultado['total_activo'] = resultado['activos']['total']
        resultado['total_pasivo_patrimonio'] = resultado['pasivos']['total'] + resultado['patrimonio']['total']
        resultado['cuadrado'] = abs(resultado['total_activo'] - resultado['total_pasivo_patrimonio']) < 0.01
        
        return resultado
    
    async def estado_resultados(
        self,
        fecha_inicio: date,
        fecha_fin: date,
        tenant_id: int,
        por_centro_costo: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Genera Estado de Resultados (Pérdidas y Ganancias)
        Similar a Management Pro: con márgenes y porcentajes
        """
        resultado = {
            'reporte': 'Estado de Resultados',
            'periodo': {
                'inicio': fecha_inicio.isoformat(),
                'fin': fecha_fin.isoformat()
            },
            'fecha_generacion': datetime.now().isoformat(),
            'ingresos': {'total': 0, 'cuentas': []},
            'costos_ventas': {'total': 0, 'cuentas': []},
            'utilidad_bruta': 0,
            'gastos_operacion': {'total': 0, 'cuentas': []},
            'utilidad_operativa': 0,
            'otros_ingresos_gastos': {'total': 0, 'cuentas': []},
            'utilidad_antes_impuestos': 0,
            'impuestos': {'total': 0, 'cuentas': []},
            'utilidad_neta': 0,
            'margen_bruto': 0,
            'margen_operativo': 0,
            'margen_netto': 0
        }
        
        # Ingresos
        ingresos = await self._obtener_saldos_tipo(
            TipoCuenta.ingreso, fecha_inicio, fecha_fin, tenant_id, por_centro_costo
        )
        resultado['ingresos']['cuentas'] = ingresos
        resultado['ingresos']['total'] = sum(c['saldo'] for c in ingresos)
        
        # Costos de venta
        costos = await self._obtener_saldos_tipo(
            TipoCuenta.costo, fecha_inicio, fecha_fin, tenant_id, por_centro_costo
        )
        resultado['costos_ventas']['cuentas'] = costos
        resultado['costos_ventas']['total'] = sum(abs(c['saldo']) for c in costos)
        
        # Utilidad bruta
        resultado['utilidad_bruta'] = resultado['ingresos']['total'] - resultado['costos_ventas']['total']
        
        # Gastos de operación
        gastos_op = await self._obtener_saldos_tipo(
            TipoCuenta.gasto, fecha_inicio, fecha_fin, tenant_id, por_centro_costo
        )
        resultado['gastos_operacion']['cuentas'] = gastos_op
        resultado['gastos_operacion']['total'] = sum(abs(c['saldo']) for c in gastos_op)
        
        # Utilidad operativa
        resultado['utilidad_operativa'] = resultado['utilidad_bruta'] - resultado['gastos_operacion']['total']
        
        # Otros ingresos/gastos (cuentas de ingreso/gasto no operativas)
        # Simplificado: usamos el mismo cálculo
        resultado['otros_ingresos_gastos']['total'] = 0
        
        # Utilidad antes de impuestos
        resultado['utilidad_antes_impuestos'] = resultado['utilidad_operativa']
        
        # Impuestos (gastos de impuestos)
        impuestos = await self._obtener_saldos_tipo(
            TipoCuenta.gasto, fecha_inicio, fecha_fin, tenant_id, por_centro_costo,
            filtro_codigo='6%'  # Asumiendo que 6xxx son impuestos
        )
        resultado['impuestos']['cuentas'] = impuestos
        resultado['impuestos']['total'] = sum(abs(c['saldo']) for c in impuestos)
        
        # Utilidad neta
        resultado['utilidad_neta'] = resultado['utilidad_antes_impuestos'] - resultado['impuestos']['total']
        
        # Márgenes
        if resultado['ingresos']['total'] > 0:
            resultado['margen_bruto'] = (resultado['utilidad_bruta'] / resultado['ingresos']['total']) * 100
            resultado['margen_operativo'] = (resultado['utilidad_operativa'] / resultado['ingresos']['total']) * 100
            resultado['margen_netto'] = (resultado['utilidad_neta'] / resultado['ingresos']['total']) * 100
        
        return resultado
    
    async def libro_mayor(
        self,
        cuenta_id: int,
        fecha_inicio: date,
        fecha_fin: date,
        tenant_id: int
    ) -> Dict[str, Any]:
        """
        Genera Libro Mayor para una cuenta específica
        Detalle de todos los movimientos con referencias cruzadas
        """
        cuenta = await self.db.get(CuentaContable, cuenta_id)
        if not cuenta or cuenta.tenant_id != tenant_id:
            raise ValueError("Cuenta no encontrada")
        
        # Obtener todos los movimientos
        query = select(MovimientoAsiento).join(
            AsientoContable, MovimientoAsiento.asiento_id == AsientoContable.id
        ).where(
            MovimientoAsiento.cuenta_id == cuenta_id,
            AsientoContable.fecha >= fecha_inicio,
            AsientoContable.fecha <= fecha_fin,
            AsientoContable.tenant_id == tenant_id,
            AsientoContable.estado == 'registrado'
        ).order_by(AsientoContable.fecha, AsientoContable.numero)
        
        result = await self.db.execute(query)
        movimientos = result.scalars().all()
        
        detalle = []
        saldo_acumulado = Decimal('0')
        
        for mov in movimientos:
            saldo_acumulado += (mov.debe - mov.haber)
            detalle.append({
                'fecha': mov.asiento.fecha.isoformat(),
                'numero_asiento': mov.asiento.numero,
                'descripcion': mov.asiento.descripcion,
                'referencia': mov.asiento.referencia,
                'debe': float(mov.debe),
                'haber': float(mov.haber),
                'saldo': float(saldo_acumulado),
                'centro_costo': mov.centro_costo.nombre if mov.centro_costo else None
            })
        
        return {
            'reporte': 'Libro Mayor',
            'cuenta': {
                'codigo': cuenta.codigo,
                'nombre': cuenta.nombre,
                'tipo': cuenta.tipo.value,
                'naturaleza': cuenta.naturaleza.value
            },
            'periodo': {
                'inicio': fecha_inicio.isoformat(),
                'fin': fecha_fin.isoformat()
            },
            'fecha_generacion': datetime.now().isoformat(),
            'saldo_inicial': float(saldo_acumulado - sum(m.debe - m.haber for m in movimientos)),
            'movimientos': detalle,
            'saldo_final': float(saldo_acumulado),
            'total_movimientos': len(detalle)
        }
    
    async def antiguedad_saldos(
        self,
        tipo: str,  # 'clientes' o 'proveedores'
        fecha_corte: date,
        tenant_id: int
    ) -> Dict[str, Any]:
        """
        Reporte de Antigüedad de Saldos (CXC o CXP)
        Similar a CONTPAQi: clasificación por rangos de días
        """
        from app.models.cxc import FacturaCliente
        from app.models.cxp import FacturaProveedor
        
        rangos = [
            ('Corriente', 0, 30),
            ('31-60 días', 31, 60),
            ('61-90 días', 61, 90),
            ('Más de 90 días', 91, 9999)
        ]
        
        resultado = {
            'reporte': f'Antigüedad de Saldos - {tipo}',
            'fecha_corte': fecha_corte.isoformat(),
            'fecha_generacion': datetime.now().isoformat(),
            'rangos': {r[0]: {'total': 0, 'documentos': []} for r in rangos},
            'total_general': 0
        }
        
        if tipo == 'clientes':
            modelo = FacturaCliente
        else:
            modelo = FacturaProveedor
        
        # Obtener facturas con saldo pendiente
        query = select(modelo).where(
            modelo.tenant_id == tenant_id,
            modelo.saldo > 0,
            modelo.fecha_vencimiento <= fecha_corte
        )
        
        result = await self.db.execute(query)
        facturas = result.scalars().all()
        
        for factura in facturas:
            dias_vencido = (fecha_corte - factura.fecha_vencimiento).days
            saldo = float(factura.saldo)
            
            for nombre_rango, min_dias, max_dias in rangos:
                if min_dias <= dias_vencido <= max_dias:
                    resultado['rangos'][nombre_rango]['documentos'].append({
                        'folio': factura.folio,
                        'tercero': factura.cliente.nombre if tipo == 'clientes' else factura.proveedor.nombre,
                        'fecha_emision': factura.fecha_emision.isoformat(),
                        'fecha_vencimiento': factura.fecha_vencimiento.isoformat(),
                        'dias_vencido': dias_vencido,
                        'saldo': saldo,
                        'moneda': factura.moneda
                    })
                    resultado['rangos'][nombre_rango]['total'] += saldo
                    resultado['total_general'] += saldo
                    break
        
        return resultado
    
    async def flujo_efectivo(
        self,
        fecha_inicio: date,
        fecha_fin: date,
        tenant_id: int,
        metodo: str = 'indirecto'  # 'directo' o 'indirecto'
    ) -> Dict[str, Any]:
        """
        Estado de Flujo de Efectivo
        Método indirecto (desde utilidad neta) o directo (cobros/pagos)
        """
        resultado = {
            'reporte': 'Flujo de Efectivo',
            'metodo': metodo,
            'periodo': {
                'inicio': fecha_inicio.isoformat(),
                'fin': fecha_fin.isoformat()
            },
            'fecha_generacion': datetime.now().isoformat(),
            'actividades_operacion': {'total': 0, 'conceptos': []},
            'actividades_inversion': {'total': 0, 'conceptos': []},
            'actividades_financiamiento': {'total': 0, 'conceptos': []},
            'incremento_disminucion': 0,
            'efectivo_inicio': 0,
            'efectivo_fin': 0
        }
        
        # Obtener utilidad neta del período
        estado_resultados = await self.estado_resultados(fecha_inicio, fecha_fin, tenant_id)
        utilidad_neta = estado_resultados['utilidad_neta']
        
        if metodo == 'indirecto':
            resultado['actividades_operacion']['conceptos'].append({
                'concepto': 'Utilidad Neta',
                'monto': utilidad_neta
            })
            resultado['actividades_operacion']['total'] += utilidad_neta
            
            # Ajustes por partidas no efectivas (depreciación, etc.)
            # Simplificado: buscar gastos de depreciación
            query_depreciacion = select(func.sum(Gasto.monto)).where(
                Gasto.tenant_id == tenant_id,
                Gasto.fecha >= fecha_inicio,
                Gasto.fecha <= fecha_fin,
                Gasto.tipo_gasto == 'depreciacion'
            )
            result_dep = await self.db.execute(query_depreciacion)
            depreciacion = float(result_dep.scalar() or 0)
            
            resultado['actividades_operacion']['conceptos'].append({
                'concepto': 'Depreciación y Amortización',
                'monto': depreciacion
            })
            resultado['actividades_operacion']['total'] += depreciacion
            
            # Cambios en capital de trabajo (CXC, CXP, Inventarios)
            # Simplificado: variación neta
            resultado['actividades_operacion']['conceptos'].append({
                'concepto': 'Cambios en Capital de Trabajo',
                'monto': 0  # Calcular comparando saldos inicio/fin
            })
        
        # Actividades de inversión (compra/venta de activos fijos)
        # Actividades de financiamiento (préstamos, dividendos)
        # Estos requerirían modelos adicionales de activos y préstamos
        
        resultado['incremento_disminucion'] = (
            resultado['actividades_operacion']['total'] +
            resultado['actividades_inversion']['total'] +
            resultado['actividades_financiamiento']['total']
        )
        
        # Saldo inicial y final de efectivo (de bancos y caja)
        # Simplificado: usar saldos contables de cuentas de activo circulante
        
        return resultado
    
    async def _calcular_saldo_cuenta(
        self, 
        cuenta_id: int, 
        fecha_corte: date, 
        tenant_id: int
    ) -> Decimal:
        """Calcula el saldo de una cuenta hasta una fecha"""
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
    
    async def _obtener_saldos_tipo(
        self,
        tipo_cuenta: TipoCuenta,
        fecha_inicio: date,
        fecha_fin: date,
        tenant_id: int,
        centro_costo_id: Optional[int] = None,
        filtro_codigo: Optional[str] = None
    ) -> List[Dict]:
        """Obtiene saldos de cuentas de un tipo específico"""
        query = select(CuentaContable).where(
            CuentaContable.tenant_id == tenant_id,
            CuentaContable.tipo == tipo_cuenta,
            CuentaContable.activa == True
        )
        
        if filtro_codigo:
            # Filtro por patrón de código (ej. '6%')
            pass  # Implementar con like si es necesario
        
        result = await self.db.execute(query)
        cuentas = result.scalars().all()
        
        saldos = []
        for cuenta in cuentas:
            saldo = await self._calcular_saldo_cuenta_periodo(
                cuenta.id, fecha_inicio, fecha_fin, tenant_id, centro_costo_id
            )
            if saldo != 0:
                saldos.append({
                    'codigo': cuenta.codigo,
                    'nombre': cuenta.nombre,
                    'saldo': float(saldo),
                    'centro_costo_id': centro_costo_id
                })
        
        return saldos
    
    async def _calcular_saldo_cuenta_periodo(
        self,
        cuenta_id: int,
        fecha_inicio: date,
        fecha_fin: date,
        tenant_id: int,
        centro_costo_id: Optional[int] = None
    ) -> Decimal:
        """Calcula saldo de una cuenta en un período específico"""
        stmt = select(
            func.sum(MovimientoAsiento.debe).label('total_debe'),
            func.sum(MovimientoAsiento.haber).label('total_haber')
        ).join(
            AsientoContable, MovimientoAsiento.asiento_id == AsientoContable.id
        ).where(
            AsientoContable.tenant_id == tenant_id,
            AsientoContable.fecha >= fecha_inicio,
            AsientoContable.fecha <= fecha_fin,
            AsientoContable.estado == 'registrado',
            MovimientoAsiento.cuenta_id == cuenta_id
        )
        
        if centro_costo_id:
            stmt = stmt.where(MovimientoAsiento.centro_costo_id == centro_costo_id)
        
        result = await self.db.execute(stmt)
        saldo = result.first()
        debe = Decimal(str(saldo.total_debe or 0))
        haber = Decimal(str(saldo.total_haber or 0))
        
        return debe - haber
    
    def _es_cuenta_corriente(self, cuenta: CuentaContable) -> bool:
        """Determina si una cuenta es corriente (< 1 año)"""
        # Lógica simplificada: cuentas de nivel 2 o superior suelen ser corrientes
        # En implementación real, usar campo específico o reglas de negocio
        return cuenta.nivel >= 2 or 'circulante' in cuenta.nombre.lower()
