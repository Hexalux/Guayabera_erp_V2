from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime
import enum


class TipoRecibo(enum.Enum):
    """Tipos de recibos de caja"""
    INGRESO = "ingreso"
    EGRESO = "egreso"
    TRASPASO = "traspaso"


class EstadoLiquidacion(enum.Enum):
    """Estados de liquidación"""
    ABIERTA = "abierta"
    EN_PROCESO = "en_proceso"
    CERRADA = "cerrada"
    CUADRADA = "cuadrada"
    DESCUADRADA = "descuadrada"


class TipoMovimientoCaja(enum.Enum):
    """Tipos de movimiento de caja"""
    VENTA = "venta"
    COBRO = "cobro"
    PAGO = "pago"
    DEPOSITO = "deposito"
    RETIRO = "retiro"
    TRASPASO = "traspaso"
    AJUSTE = "ajuste"
    INTERNO = "interno"


class Caja(Base):
    """
    Modelo para representar Cajas o Puntos de Venta
    Soporta múltiples cajas por tenant
    """
    __tablename__ = "cajas"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    tenant_id: str = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Identificación
    codigo: str = Column(String(50), nullable=False, index=True)
    nombre: str = Column(String(200), nullable=False)
    descripcion: str = Column(Text, nullable=True)
    
    # Configuración
    es_principal: bool = Column(Boolean, default=False)
    es_activa: bool = Column(Boolean, default=True)
    moneda: str = Column(String(3), default="USD")
    
    # Límites y controles
    monto_maximo: Numeric = Column(Numeric(19, 4), nullable=True)
    requiere_autorizacion_retiro: bool = Column(Boolean, default=True)
    monto_autorizacion: Numeric = Column(Numeric(19, 4), default=0)
    
    # Fondo fijo
    tiene_fondo_fijo: bool = Column(Boolean, default=False)
    monto_fondo_fijo: Numeric = Column(Numeric(19, 4), default=0)
    
    # Auditoría
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    creado_por: str = Column(String, nullable=True)
    
    # Relaciones
    tenant = relationship("Tenant", backref="cajas")
    recibos = relationship("ReciboCaja", back_populates="caja")
    liquidaciones = relationship("LiquidacionSucursal", back_populates="caja")
    arqueos = relationship("ArqueoCaja", back_populates="caja")

    def __repr__(self):
        return f"<Caja(codigo='{self.codigo}', nombre='{self.nombre}')>"


class ReciboCaja(Base):
    """
    Modelo para representar Recibos de Caja
    Similar a CONTPAQi con series consecutivas
    """
    __tablename__ = "recibos_caja"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    tenant_id: str = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    caja_id: str = Column(String, ForeignKey("cajas.id"), nullable=False, index=True)
    
    # Numeración
    serie: str = Column(String(10), nullable=False, index=True)
    numero: int = Column(Integer, nullable=False, index=True)
    numero_completo: str = Column(String(50), nullable=False)  # ej: FAC-001-0000123
    
    # Tipo y concepto
    tipo_recibo: TipoRecibo = Column(SQLEnum(TipoRecibo), nullable=False)
    concepto: str = Column(String(200), nullable=False)
    descripcion: str = Column(Text, nullable=True)
    
    # Montos
    monto: Numeric = Column(Numeric(19, 4), nullable=False)
    impuestos: Numeric = Column(Numeric(19, 4), default=0)
    total: Numeric = Column(Numeric(19, 4), nullable=False)
    moneda: str = Column(String(3), default="USD")
    tasa_cambio: Numeric = Column(Numeric(19, 6), default=1.0)
    
    # Forma de pago
    forma_pago: str = Column(String(50), nullable=False)  # efectivo, tarjeta, transferencia, etc.
    referencia_pago: str = Column(String(100), nullable=True)  # No. cheque, autorización, etc.
    
    # Tercero (cliente, proveedor, empleado)
    tercero_id: str = Column(String, ForeignKey("terceros.id"), nullable=True, index=True)
    tipo_tercero: str = Column(String(20), nullable=True)  # cliente, proveedor, empleado, otro
    nombre_tercero: str = Column(String(200), nullable=True)
    
    # Estado
    estado: str = Column(String(20), default="emitido")  # emitido, cancelado, aplicado
    es_aplicado: bool = Column(Boolean, default=False)
    
    # Vínculo contable
    asiento_id: str = Column(String, ForeignKey("asientos_contables.id"), nullable=True)
    
    # Auditoría
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    emitido_por: str = Column(String, nullable=True)
    cancelado_por: str = Column(String, nullable=True)
    cancelado_en: datetime = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones
    caja = relationship("Caja", back_populates="recibos")
    tenant = relationship("Tenant", backref="recibos_caja")
    tercero = relationship("Tercero", backref="recibos_caja")

    def __repr__(self):
        return f"<ReciboCaja(numero_completo='{self.numero_completo}', monto={self.monto})>"


class LiquidacionSucursal(Base):
    """
    Modelo para representar Liquidaciones de Sucursal
    Agrupa movimientos de un período
    """
    __tablename__ = "liquidaciones_sucursal"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    tenant_id: str = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    caja_id: str = Column(String, ForeignKey("cajas.id"), nullable=False, index=True)
    
    # Período
    fecha_inicio: datetime = Column(DateTime, nullable=False)
    fecha_fin: datetime = Column(DateTime, nullable=False)
    
    # Totales
    total_ventas: Numeric = Column(Numeric(19, 4), default=0)
    total_cobros: Numeric = Column(Numeric(19, 4), default=0)
    total_pagos: Numeric = Column(Numeric(19, 4), default=0)
    total_retiros: Numeric = Column(Numeric(19, 4), default=0)
    total_depositos: Numeric = Column(Numeric(19, 4), default=0)
    
    # Desglose por forma de pago
    efectivo: Numeric = Column(Numeric(19, 4), default=0)
    tarjetas: Numeric = Column(Numeric(19, 4), default=0)
    transferencias: Numeric = Column(Numeric(19, 4), default=0)
    cheques: Numeric = Column(Numeric(19, 4), default=0)
    otros: Numeric = Column(Numeric(19, 4), default=0)
    
    # Estado
    estado: EstadoLiquidacion = Column(SQLEnum(EstadoLiquidacion), default=EstadoLiquidacion.ABIERTA)
    
    # Diferencias
    diferencia: Numeric = Column(Numeric(19, 4), default=0)
    observaciones: str = Column(Text, nullable=True)
    
    # Auditoría
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    elaborado_por: str = Column(String, nullable=True)
    revisado_por: str = Column(String, nullable=True)
    aprobado_por: str = Column(String, nullable=True)
    
    # Relaciones
    caja = relationship("Caja", back_populates="liquidaciones")
    tenant = relationship("Tenant", backref="liquidaciones_sucursal")

    def __repr__(self):
        return f"<LiquidacionSucursal(fecha_inicio={self.fecha_inicio}, estado={self.estado})>"


class LiquidacionVendedor(Base):
    """
    Modelo para representar Liquidaciones de Vendedores
    Control de ventas y cobros por vendedor
    """
    __tablename__ = "liquidaciones_vendedor"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    tenant_id: str = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Vendedor
    vendedor_id: str = Column(String, ForeignKey("terceros.id"), nullable=False, index=True)
    
    # Período
    fecha_inicio: datetime = Column(DateTime, nullable=False)
    fecha_fin: datetime = Column(DateTime, nullable=False)
    
    # Totales
    total_ventas_contado: Numeric = Column(Numeric(19, 4), default=0)
    total_ventas_credito: Numeric = Column(Numeric(19, 4), default=0)
    total_cobros: Numeric = Column(Numeric(19, 4), default=0)
    total_devoluciones: Numeric = Column(Numeric(19, 4), default=0)
    
    # Comisiones
    porcentaje_comision: Numeric = Column(Numeric(5, 2), default=0)
    monto_comision: Numeric = Column(Numeric(19, 4), default=0)
    
    # Estado
    estado: str = Column(String(20), default="pendiente")  # pendiente, revisada, aprobada, pagada
    
    # Auditoría
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    elaborado_por: str = Column(String, nullable=True)
    
    # Relaciones
    tenant = relationship("Tenant", backref="liquidaciones_vendedor")
    vendedor = relationship("Tercero", backref="liquidaciones_vendedor")

    def __repr__(self):
        return f"<LiquidacionVendedor(vendedor_id={self.vendedor_id}, periodo={self.fecha_inicio})>"


class RecepcionValores(Base):
    """
    Modelo para representar Recepción de Valores
    Control de documentos recibidos (cheques, pagarés, etc.)
    """
    __tablename__ = "recepcion_valores"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    tenant_id: str = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    caja_id: str = Column(String, ForeignKey("cajas.id"), nullable=True, index=True)
    
    # Tipo de valor
    tipo_valor: str = Column(String(50), nullable=False)  # cheque, pagare, transferencia, otro
    numero_documento: str = Column(String(100), nullable=False, index=True)
    
    # Datos del documento
    banco: str = Column(String(200), nullable=True)
    cuenta: str = Column(String(50), nullable=True)
    monto: Numeric = Column(Numeric(19, 4), nullable=False)
    moneda: str = Column(String(3), default="USD")
    fecha_emision: datetime = Column(DateTime, nullable=True)
    fecha_vencimiento: datetime = Column(DateTime, nullable=True)
    
    # Cliente/Proveedor
    tercero_id: str = Column(String, ForeignKey("terceros.id"), nullable=True, index=True)
    nombre_tercero: str = Column(String(200), nullable=False)
    
    # Estado
    estado: str = Column(String(20), default="recibido")  # recibido, depositado, cobrado, rebotado, devuelto
    
    # Aplicación
    aplicado_a: str = Column(String(100), nullable=True)  # factura, documento
    fecha_aplicacion: datetime = Column(DateTime, nullable=True)
    
    # Auditoría
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    recibido_por: str = Column(String, nullable=True)
    
    # Relaciones
    caja = relationship("Caja", backref="recepcion_valores")
    tenant = relationship("Tenant", backref="recepcion_valores")
    tercero = relationship("Tercero", backref="recepcion_valores")

    def __repr__(self):
        return f"<RecepcionValores(tipo={self.tipo_valor}, numero={self.numero_documento})>"


class ArqueoCaja(Base):
    """
    Modelo para representar Arqueos de Caja
    Similar a CONTPAQi con corte ciego
    """
    __tablename__ = "arqueos_caja"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    tenant_id: str = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    caja_id: str = Column(String, ForeignKey("cajas.id"), nullable=False, index=True)
    
    # Período del arqueo
    fecha_inicio: datetime = Column(DateTime, nullable=False)
    fecha_fin: datetime = Column(DateTime, nullable=False)
    fecha_arqueo: datetime = Column(DateTime, server_default=func.now())
    
    # Sistema (lo que debería haber)
    saldo_inicial_sistema: Numeric = Column(Numeric(19, 4), default=0)
    total_ingresos_sistema: Numeric = Column(Numeric(19, 4), default=0)
    total_egresos_sistema: Numeric = Column(Numeric(19, 4), default=0)
    saldo_final_sistema: Numeric = Column(Numeric(19, 4), default=0)
    
    # Físico (lo que el cajero reporta - corte ciego)
    efectivo_fisico: Numeric = Column(Numeric(19, 4), default=0)
    tarjetas_fisico: Numeric = Column(Numeric(19, 4), default=0)
    cheques_fisico: Numeric = Column(Numeric(19, 4), default=0)
    otros_fisico: Numeric = Column(Numeric(19, 4), default=0)
    total_fisico: Numeric = Column(Numeric(19, 4), default=0)
    
    # Diferencia
    diferencia: Numeric = Column(Numeric(19, 4), default=0)
    tipo_diferencia: str = Column(String(20), nullable=True)  # faltante, sobrante, cuadrado
    
    # Desglose de efectivo (billetes y monedas)
    desglose_efectivo: Text = Column(Text, nullable=True)  # JSON con denominaciones
    
    # Observaciones
    observaciones: str = Column(Text, nullable=True)
    justificacion_diferencia: str = Column(Text, nullable=True)
    
    # Estado
    estado: str = Column(String(20), default="abierto")  # abierto, cerrado, revisado, aprobado
    
    # Auditoría
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en: datetime = Column(DateTime(timezone=True), onupdate=func.now())
    realizado_por: str = Column(String, nullable=True)
    revisado_por: str = Column(String, nullable=True)
    aprobado_por: str = Column(String, nullable=True)
    
    # Relaciones
    caja = relationship("Caja", back_populates="arqueos")
    tenant = relationship("Tenant", backref="arqueos_caja")

    def __repr__(self):
        return f"<ArqueoCaja(caja_id={self.caja_id}, fecha={self.fecha_arqueo})>"


class CorteCaja(Base):
    """
    Modelo para representar Cortes de Caja
    Cortes parciales o generales
    """
    __tablename__ = "cortes_caja"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    tenant_id: str = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    caja_id: str = Column(String, ForeignKey("cajas.id"), nullable=False, index=True)
    
    # Tipo de corte
    tipo_corte: str = Column(String(50), nullable=False)  # parcial, turno, diario, general
    numero_corte: int = Column(Integer, nullable=False, index=True)
    
    # Período
    fecha_inicio: datetime = Column(DateTime, nullable=False)
    fecha_fin: datetime = Column(DateTime, nullable=False)
    
    # Totales
    total_ingresos: Numeric = Column(Numeric(19, 4), default=0)
    total_egresos: Numeric = Column(Numeric(19, 4), default=0)
    saldo_final: Numeric = Column(Numeric(19, 4), default=0)
    
    # Por forma de pago
    efectivo: Numeric = Column(Numeric(19, 4), default=0)
    tarjetas: Numeric = Column(Numeric(19, 4), default=0)
    transferencias: Numeric = Column(Numeric(19, 4), default=0)
    cheques: Numeric = Column(Numeric(19, 4), default=0)
    
    # Estado
    estado: str = Column(String(20), default="cerrado")  # abierto, cerrado, impreso
    
    # Auditoría
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    realizado_por: str = Column(String, nullable=True)
    
    # Relaciones
    caja = relationship("Caja", backref="cortes_caja")
    tenant = relationship("Tenant", backref="cortes_caja")

    def __repr__(self):
        return f"<CorteCaja(tipo={self.tipo_corte}, numero={self.numero_corte})>"
