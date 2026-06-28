"""
Guayabera ERP Suite v2.0 - Sprint 8: Revaluación de Tipos de Cambio
Fusión de CONTPAQi (robustez), Odoo (flexibilidad) y Management Pro (opciones)
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Date
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class TipoCambio(Base):
    """Tipos de cambio diarios (peso mexicano vs otras monedas)"""
    __tablename__ = "tipos_cambio"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Moneda
    moneda_origen = Column(String(3), nullable=False, default="USD")  # USD, EUR, etc.
    moneda_destino = Column(String(3), nullable=False, default="MXN")
    
    # Fecha y valores
    fecha = Column(Date, nullable=False)
    tipo_cambio = Column(Float, nullable=False)  # Valor de la moneda extranjera en MN
    
    # Fuente (BANXICO, SAT, manual)
    fuente = Column(String(50), default="manual")
    
    # Auditoría
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    
    # Índice único para evitar duplicados
    __table_args__ = (
        {'sqlite_autoincrement': True}  # Para SQLite, ajustar para PostgreSQL
    )


class RevaluacionAutomatica(Base):
    """Configuración de revaluación automática de saldos en moneda extranjera"""
    __tablename__ = "revaluaciones_automaticas"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Configuración
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    
    # Frecuencia (diaria, semanal, mensual, al cierre)
    frecuencia = Column(String(20), default="mensual")
    dia_ejecucion = Column(Integer)  # Día del mes para ejecución automática
    
    # Cuentas a revaluar
    incluir_clientes = Column(Boolean, default=True)
    incluir_proveedores = Column(Boolean, default=True)
    incluir_bancos = Column(Boolean, default=True)
    cuentas_personalizadas = Column(String(500))  # Lista de cuentas separadas por coma
    
    # Contabilidad
    cuenta_gasto_cambiario = Column(String(20))  # Cuenta para pérdidas cambiarias
    cuenta_ingreso_cambiario = Column(String(20))  # Cuenta para ganancias cambiarias
    centro_costo_id = Column(Integer, ForeignKey("centros_costo.id"))
    
    # Estado
    activo = Column(Boolean, default=True)
    ultima_ejecucion = Column(DateTime)
    proxima_ejecucion = Column(Date)
    
    # Auditoría
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))


class EjecucionRevaluacion(Base):
    """Historial de ejecuciones de revaluación"""
    __tablename__ = "ejecuciones_revaluacion"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    configuracion_id = Column(Integer, ForeignKey("revaluaciones_automaticas.id"))
    
    # Fecha de ejecución
    fecha_ejecucion = Column(DateTime, nullable=False, default=datetime.utcnow)
    fecha_corte = Column(Date, nullable=False)  # Fecha de corte para la revaluación
    
    # Tipo de cambio utilizado
    tipo_cambio_anterior = Column(Float)
    tipo_cambio_nuevo = Column(Float, nullable=False)
    moneda = Column(String(3), nullable=False)
    
    # Resultados
    total_saldos_revaluados = Column(Float, default=0.0)
    perdida_cambiaria = Column(Float, default=0.0)
    ganancia_cambiaria = Column(Float, default=0.0)
    resultado_neto = Column(Float, default=0.0)  # Positivo = ganancia, negativo = pérdida
    
    # Contabilidad
    poliza_generada = Column(Boolean, default=False)
    asiento_contable_id = Column(Integer, ForeignKey("asientos_contables.id"))
    numero_poliza = Column(String(50))
    
    # Estado
    estado = Column(String(20), default="procesado")  # procesado, cancelado, error
    observaciones = Column(Text)
    
    # Auditoría
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    
    # Relaciones
    detalles = relationship("DetalleRevaluacion", back_populates="ejecucion", cascade="all, delete-orphan")


class DetalleRevaluacion(Base):
    """Detalle de cada cuenta/partida revaluada"""
    __tablename__ = "detalles_revaluacion"
    
    id = Column(Integer, primary_key=True, index=True)
    ejecucion_id = Column(Integer, ForeignKey("ejecuciones_revaluacion.id"), nullable=False)
    
    # Identificación de la partida
    tipo_documento = Column(String(50))  # factura, pago, saldo banco, etc.
    documento_id = Column(Integer)  # ID del documento original
    numero_documento = Column(String(50))
    
    # Tercero
    tercero_tipo = Column(String(20))  # cliente, proveedor
    tercero_id = Column(Integer)
    tercero_nombre = Column(String(200))
    
    # Cuentas contables
    cuenta_contable_id = Column(Integer, ForeignKey("cuentas_contables.id"))
    centro_costo_id = Column(Integer, ForeignKey("centros_costo.id"))
    
    # Saldos
    saldo_moneda_extranjera = Column(Float, nullable=False, default=0.0)
    tipo_cambio_original = Column(Float, nullable=False)
    tipo_cambio_nuevo = Column(Float, nullable=False)
    
    # Valores
    saldo_mn_anterior = Column(Float, default=0.0)
    saldo_mn_nuevo = Column(Float, default=0.0)
    diferencia_cambiaria = Column(Float, default=0.0)  # Positivo = ganancia, negativo = pérdida
    
    # Auditoría
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    ejecucion = relationship("EjecucionRevaluacion", back_populates="detalles")


class ValuacionTipoCambio(Base):
    """Valuación de tipos de cambio para reportes históricos"""
    __tablename__ = "valuaciones_tipo_cambio"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Periodo de valuación
    fecha_valuacion = Column(Date, nullable=False)
    moneda = Column(String(3), nullable=False)
    
    # Valores
    tipo_cambio_compra = Column(Float)
    tipo_cambio_venta = Column(Float)
    tipo_cambio_promedio = Column(Float)
    
    # Fuente oficial (SAT, BANXICO)
    fuente_oficial = Column(String(50))
    valor_oficial = Column(Float)
    
    # Diferencia
    diferencia_porcentual = Column(Float, default=0.0)
    
    # Auditoría
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))


class ParametrosRevaluacion(Base):
    """Parámetros de configuración del módulo de revaluación"""
    __tablename__ = "parametros_revaluacion"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, unique=True)
    
    # Configuración general
    moneda_base = Column(String(3), default="MXN")
    monedas_extranjeras_habilitadas = Column(String(100), default="USD,EUR")
    
    # Fuente de tipos de cambio
    fuente_principal = Column(String(50), default="manual")  # manual, sat, banxico
    url_sat = Column(String(255), default="https://www.sat.gob.mx/app/externos/index.html")
    
    # Revaluación automática
    ejecutar_al_cierre_mes = Column(Boolean, default=True)
    generar_poliza_automatica = Column(Boolean, default=True)
    
    # Cuentas contables por defecto
    cuenta_perdida_cambiaria = Column(String(20))
    cuenta_ganancia_cambiaria = Column(String(20))
    
    # Redondeo
    decimales_tipo_cambio = Column(Integer, default=4)
    decimales_moneda = Column(Integer, default=2)
    
    # Auditoría
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    actualizado_por = Column(Integer, ForeignKey("usuarios.id"))
