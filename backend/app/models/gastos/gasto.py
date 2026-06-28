"""
Guayabera ERP Suite v2.0 - Sprint 7: Control de Gastos
Fusión de CONTPAQi (robustez), Odoo (flexibilidad) y Management Pro (opciones)
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Boolean, Text, Date
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class TipoGasto(str, enum.Enum):
    OPERATIVO = "operativo"
    ADMINISTRATIVO = "administrativo"
    VENTAS = "ventas"
    VIAJE = "viaje"
    NOMINA = "nomina"
    DEPRECIACION = "depreciacion"
    OTRO = "otro"


class EstadoGasto(str, enum.Enum):
    BORRADOR = "borrador"
    REGISTRADO = "registrado"
    AUTORIZADO = "autorizado"
    CONTABILIZADO = "contabilizado"
    CANCELADO = "cancelado"


class CategoriaGasto(Base):
    """Catálogo de categorías de gastos (tabla de gastos)"""
    __tablename__ = "categorias_gasto"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    codigo = Column(String(20), nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    
    # Clasificación contable
    cuenta_contable_id = Column(Integer, ForeignKey("cuentas_contables.id"))
    tipo_gasto = Column(SQLEnum(TipoGasto), default=TipoGasto.OPERATIVO)
    
    # Presupuesto
    presupuesto_mensual = Column(Float, default=0.0)
    presupuesto_anual = Column(Float, default=0.0)
    
    # Control
    activo = Column(Boolean, default=True)
    requiere_autorizacion = Column(Boolean, default=False)
    nivel_autorizacion = Column(Integer, default=1)
    
    # Auditoría
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    
    # Relaciones
    gastos = relationship("Gasto", back_populates="categoria")
    hijos = relationship("CategoriaGasto", remote_side="CategoriaGasto.id")


class Gasto(Base):
    """Registro individual de gastos"""
    __tablename__ = "gastos"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias_gasto.id"), nullable=False)
    
    # Datos del gasto
    numero_gasto = Column(String(50), unique=True, nullable=False)
    fecha_gasto = Column(Date, nullable=False)
    fecha_registro = Column(Date, nullable=False)
    descripcion = Column(Text, nullable=False)
    
    # Proveedor o beneficiario
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"))
    empleado_id = Column(Integer, ForeignKey("usuarios.id"))
    tercero_nombre = Column(String(200))  # Para gastos sin proveedor registrado
    
    # Montos
    subtotal = Column(Float, nullable=False, default=0.0)
    iva_trasladado = Column(Float, default=0.0)
    iva_retenido = Column(Float, default=0.0)
    isr_retenido = Column(Float, default=0.0)
    otros_impuestos = Column(Float, default=0.0)
    total = Column(Float, nullable=False, default=0.0)
    
    # Documento de respaldo
    tipo_comprobante = Column(String(50))  # Factura, Ticket, Recibo
    serie_comprobante = Column(String(20))
    folio_comprobante = Column(String(20))
    uuid_fiscal = Column(String(36))
    archivo_comprobante = Column(String(255))  # Ruta del PDF/XML
    
    # Centro de costo
    centro_costo_id = Column(Integer, ForeignKey("centros_costo.id"))
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"))
    
    # Estado y autorización
    estado = Column(SQLEnum(EstadoGasto), default=EstadoGasto.BORRADOR)
    requiere_autorizacion = Column(Boolean, default=False)
    autorizado = Column(Boolean, default=False)
    autorizado_por = Column(Integer, ForeignKey("usuarios.id"))
    fecha_autorizacion = Column(DateTime)
    
    # Contabilidad
    poliza_generada = Column(Boolean, default=False)
    asiento_contable_id = Column(Integer, ForeignKey("asientos_contables.id"))
    
    # Observaciones
    observaciones = Column(Text)
    referencia = Column(String(100))
    
    # Auditoría
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    
    # Relaciones
    categoria = relationship("CategoriaGasto", back_populates="gastos")


class GastoViaje(Base):
    """Gastos específicos de viaje (viáticos, hospedaje, transporte)"""
    __tablename__ = "gastos_viaje"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Datos del viaje
    numero_viaje = Column(String(50), unique=True, nullable=False)
    empleado_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    descripcion = Column(Text, nullable=False)
    
    # Fechas
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    destino = Column(String(200))
    
    # Montos
    anticipo_recibido = Column(Float, default=0.0)
    total_gastos = Column(Float, default=0.0)
    saldo_a_favor_empleado = Column(Float, default=0.0)
    saldo_a_favor_empresa = Column(Float, default=0.0)
    
    # Estado
    estado = Column(SQLEnum(EstadoGasto), default=EstadoGasto.BORRADOR)
    cerrado = Column(Boolean, default=False)
    fecha_cierre = Column(DateTime)
    
    # Auditoría
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    
    # Relaciones
    gastos_detalle = relationship("GastoViajeDetalle", back_populates="viaje", cascade="all, delete-orphan")


class GastoViajeDetalle(Base):
    """Detalle de gastos individuales dentro de un viaje"""
    __tablename__ = "gastos_viaje_detalle"
    
    id = Column(Integer, primary_key=True, index=True)
    viaje_id = Column(Integer, ForeignKey("gastos_viaje.id"), nullable=False)
    
    # Datos del gasto
    fecha_gasto = Column(Date, nullable=False)
    tipo_gasto = Column(String(50), nullable=False)  # Alimento, Hospedaje, Transporte, etc.
    descripcion = Column(Text, nullable=False)
    
    # Montos
    monto = Column(Float, nullable=False, default=0.0)
    iva_incluido = Column(Float, default=0.0)
    
    # Comprobante
    tiene_comprobante = Column(Boolean, default=False)
    archivo_comprobante = Column(String(255))
    observaciones = Column(Text)
    
    # Auditoría
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    
    # Relaciones
    viaje = relationship("GastoViaje", back_populates="gastos_detalle")


class NominaGasto(Base):
    """Registro de nómina como gasto"""
    __tablename__ = "nomina_gastos"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Periodo
    periodo_inicio = Column(Date, nullable=False)
    periodo_fin = Column(Date, nullable=False)
    fecha_pago = Column(Date, nullable=False)
    
    # Montos
    total_sueldos = Column(Float, default=0.0)
    total_horas_extras = Column(Float, default=0.0)
    total_bonos = Column(Float, default=0.0)
    total_deducciones = Column(Float, default=0.0)
    total_isr_retener = Column(Float, default=0.0)
    total_imss = Column(Float, default=0.0)
    total_patronal = Column(Float, default=0.0)
    total_neto = Column(Float, default=0.0)
    
    # Contabilidad
    poliza_generada = Column(Boolean, default=False)
    asiento_contable_id = Column(Integer, ForeignKey("asientos_contables.id"))
    
    # Estado
    procesado = Column(Boolean, default=False)
    
    # Auditoría
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))


class DepreciacionActivo(Base):
    """Depreciación de activos fijos"""
    __tablename__ = "depreciacion_activos"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Activo
    activo_fijo_id = Column(Integer, ForeignKey("activos_fijos.id"), nullable=False)
    descripcion_activo = Column(String(200), nullable=False)
    
    # Configuración depreciación
    metodo_depreciacion = Column(String(50), default="linea_recta")  # Línea recta, saldo decreciente
    vida_util_meses = Column(Integer, nullable=False)
    valor_residual = Column(Float, default=0.0)
    porcentaje_depreciacion = Column(Float, nullable=False)
    
    # Valores
    costo_original = Column(Float, nullable=False)
    depreciacion_acumulada = Column(Float, default=0.0)
    valor_libros = Column(Float, default=0.0)
    
    # Periodo actual
    periodo_depreciacion = Column(Date)  # Mes/año de la depreciación
    depreciacion_periodo = Column(Float, default=0.0)
    
    # Contabilidad
    cuenta_depreciacion = Column(String(20))
    cuenta_gasto_depreciacion = Column(String(20))
    poliza_generada = Column(Boolean, default=False)
    asiento_contable_id = Column(Integer, ForeignKey("asientos_contables.id"))
    
    # Estado
    activo = Column(Boolean, default=True)
    completamente_depreciado = Column(Boolean, default=False)
    
    # Auditoría
    fecha_compra = Column(Date)
    fecha_inicio_depreciacion = Column(Date)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))


class ReclasificacionGasto(Base):
    """Reclasificación de gastos entre cuentas o centros de costo"""
    __tablename__ = "reclasificaciones_gasto"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Datos
    numero_reclasificacion = Column(String(50), unique=True, nullable=False)
    fecha_reclasificacion = Column(Date, nullable=False)
    descripcion = Column(Text, nullable=False)
    
    # Origen
    gasto_origen_id = Column(Integer, ForeignKey("gastos.id"), nullable=False)
    cuenta_contable_origen_id = Column(Integer, ForeignKey("cuentas_contables.id"))
    centro_costo_origen_id = Column(Integer, ForeignKey("centros_costo.id"))
    
    # Destino
    cuenta_contable_destino_id = Column(Integer, ForeignKey("cuentas_contables.id"), nullable=False)
    centro_costo_destino_id = Column(Integer, ForeignKey("centros_costo.id"), nullable=False)
    
    # Monto
    monto_reclasificar = Column(Float, nullable=False)
    
    # Justificación
    justificacion = Column(Text, nullable=False)
    
    # Autorización
    autorizado = Column(Boolean, default=False)
    autorizado_por = Column(Integer, ForeignKey("usuarios.id"))
    fecha_autorizacion = Column(DateTime)
    
    # Contabilidad
    poliza_generada = Column(Boolean, default=False)
    asiento_contable_id = Column(Integer, ForeignKey("asientos_contables.id"))
    
    # Auditoría
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))


class PresupuestoGasto(Base):
    """Presupuesto anual/mensual de gastos"""
    __tablename__ = "presupuestos_gasto"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias_gasto.id"), nullable=False)
    centro_costo_id = Column(Integer, ForeignKey("centros_costo.id"))
    
    # Periodo
    anio = Column(Integer, nullable=False)
    mes = Column(Integer)  # Null para presupuesto anual
    
    # Montos
    presupuesto_aprobado = Column(Float, nullable=False, default=0.0)
    presupuesto_ejecutado = Column(Float, default=0.0)
    presupuesto_disponible = Column(Float, default=0.0)
    
    # Variaciones
    variacion_absoluta = Column(Float, default=0.0)
    variacion_porcentual = Column(Float, default=0.0)
    
    # Estado
    activo = Column(Boolean, default=True)
    
    # Auditoría
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))


class ParametrosGastos(Base):
    """Parámetros de configuración del módulo de gastos"""
    __tablename__ = "parametros_gastos"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, unique=True)
    
    # Configuración general
    prefijo_gasto = Column(String(10), default="GAS")
    consecutivo_gasto = Column(Integer, default=1)
    
    # Autorizaciones
    monto_maximo_sin_autorizacion = Column(Float, default=1000.0)
    requiere_comprobante_mayor_a = Column(Float, default=500.0)
    
    # Contabilidad automática
    generar_poliza_automatica = Column(Boolean, default=True)
    cuenta_gastos_generica = Column(String(20))
    cuenta_iva_acreditable = Column(String(20))
    cuenta_proveedores = Column(String(20))
    
    # Viajes
    limite_viaticos_diarios = Column(Float, default=500.0)
    limite_hospedaje_diario = Column(Float, default=1500.0)
    
    # Auditoría
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    actualizado_por = Column(Integer, ForeignKey("usuarios.id"))
