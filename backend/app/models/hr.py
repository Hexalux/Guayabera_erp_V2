from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, Numeric, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class Departamento(Base):
    """Departamentos de la empresa"""
    __tablename__ = "rh_departamentos"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    nombre: str = Column(String(100), nullable=False)
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=True)
    
    empleados = relationship("Empleado", back_populates="departamento")

class Empleado(Base):
    """Gestión de Empleados y Expediente Digital"""
    __tablename__ = "rh_empleados"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    codigo: str = Column(String(50), unique=True, nullable=False, index=True)
    nombre_completo: str = Column(String(300), nullable=False)
    email: str = Column(String(150), nullable=True)
    telefono: str = Column(String(50), nullable=True)
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=True)

    # Organigrama
    puesto: str = Column(String(150), nullable=True)
    departamento_id: str = Column(String, ForeignKey("rh_departamentos.id"), nullable=True)
    jefe_id: str = Column(String, ForeignKey("rh_empleados.id"), nullable=True)

    # Identificación Oficial
    rfc: str = Column(String(13), unique=True, index=True, nullable=True)
    curp: str = Column(String(18), unique=True, index=True, nullable=True)
    nss: str = Column(String(11), unique=True, nullable=True)

    # Biometría y Asistencia
    huella_template: str = Column(Text, nullable=True) # Plantilla ISO/ANSI en Base64
    requiere_asistencia: bool = Column(Boolean, default=True)

    # Rutas a Documentos digitalizados
    archivo_contrato: str = Column(String(500), nullable=True)
    archivo_nacimiento: str = Column(String(500), nullable=True)
    archivo_curp: str = Column(String(500), nullable=True)

    is_active: bool = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    contratos = relationship("ContratoLaboral", back_populates="empleado")
    vacaciones = relationship("ControlVacaciones", back_populates="empleado")
    nominas = relationship("Nomina", back_populates="empleado")
    inasistencias = relationship("Inasistencia", back_populates="empleado")
    asistencias = relationship("RegistroAsistencia", back_populates="empleado")

    departamento = relationship("Departamento", back_populates="empleados")
    jefe = relationship("Empleado", remote_side=[id], backref="subordinados")


class SATCatalogoPercepcion(Base):
    """Catálogo SAT de Percepciones c_TipoPercepcion (CFDI 4.0)"""
    __tablename__ = "sat_catalogo_percepciones"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    clave: str = Column(String(3), unique=True, nullable=False, index=True) # ej. 001
    descripcion: str = Column(String(200), nullable=False) # ej. Sueldos, Salarios
    
    is_active: bool = Column(Boolean, default=True)


class SATCatalogoDeduccion(Base):
    """Catálogo SAT de Deducciones c_TipoDeduccion (CFDI 4.0)"""
    __tablename__ = "sat_catalogo_deducciones"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    clave: str = Column(String(3), unique=True, nullable=False, index=True) # ej. 001
    descripcion: str = Column(String(200), nullable=False) # ej. Seguridad social
    
    is_active: bool = Column(Boolean, default=True)


class ParametroFiscal(Base):
    """Parámetros fiscales generales (UMA, Salarios Mínimos)"""
    __tablename__ = "hr_parametros_fiscales"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    anio: int = Column(Integer, nullable=False, unique=True)
    uma: float = Column(Numeric(10, 2), nullable=False)
    smi: float = Column(Numeric(10, 2), nullable=False) # Salario Mínimo General
    is_active: bool = Column(Boolean, default=True)


class TablaISR(Base):
    """Tablas de tarifas de ISR vigentes por año y periodicidad"""
    __tablename__ = "hr_tablas_isr"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    anio: int = Column(Integer, nullable=False, index=True)
    periodicidad: str = Column(String(50), nullable=False) # Ej. '04' (Quincenal), '05' (Mensual)
    
    limite_inferior: float = Column(Numeric(12, 2), nullable=False)
    limite_superior: float = Column(Numeric(12, 2), nullable=False)
    cuota_fija: float = Column(Numeric(12, 2), nullable=False)
    porcentaje: float = Column(Numeric(6, 4), nullable=False) # Porcentaje aplicable sobre excedente
    
    is_active: bool = Column(Boolean, default=True)


class ContratoLaboral(Base):
    """Contratos de trabajo y condiciones salariales"""
    __tablename__ = "rh_contratos"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    empleado_id: str = Column(String, ForeignKey("rh_empleados.id"), nullable=False)
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=True)

    tipo_contrato: str = Column(String(100), default="indeterminado")  # ej. 01 (SAT c_TipoContrato)
    tipo_jornada_id: str = Column(String(50), nullable=True) # ej. 01 - Diurna (SAT c_TipoJornada)
    periodicidad_pago_id: str = Column(String(50), nullable=True) # ej. 04 - Quincenal (SAT c_PeriodicidadPago)
    
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=True)
    
    salario_diario: float = Column(Numeric(12, 2), nullable=False)
    salario_diario_integrado: float = Column(Numeric(12, 2), nullable=True) # SDI (IMSS)
    salario_base_cotizacion: float = Column(Numeric(12, 2), nullable=True) # SBC
    
    dias_laborables: int = Column(Integer, default=6) # 1 a 6 días a la semana

    is_active: bool = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    empleado = relationship("Empleado", back_populates="contratos")


class ControlVacaciones(Base):
    """Solicitudes y balance de vacaciones de los empleados"""
    __tablename__ = "rh_vacaciones"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    empleado_id: str = Column(String, ForeignKey("rh_empleados.id"), nullable=False)
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=True)

    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    dias_solicitados: int = Column(Integer, nullable=False)
    estado: str = Column(String(50), default="pendiente")  # pendiente, aprobada, rechazada

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    empleado = relationship("Empleado", back_populates="vacaciones")


class Nomina(Base):
    """Cálculo y timbrado de Nómina electrónica (CFDI)"""
    __tablename__ = "rh_nominas"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    empleado_id: str = Column(String, ForeignKey("rh_empleados.id"), nullable=False)
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=True)

    fecha_pago = Column(Date, nullable=False)
    total_percepciones: float = Column(Numeric(12, 2), default=0.00)
    total_deducciones: float = Column(Numeric(12, 2), default=0.00)
    neto_pagado: float = Column(Numeric(12, 2), default=0.00)

    # Datos fiscales CFDI
    uuid_cfdi: str = Column(String(100), nullable=True)
    url_xml: str = Column(String, nullable=True)
    url_pdf: str = Column(String, nullable=True)
    estado_timbrado: str = Column(String, default="PENDIENTE") # PENDIENTE, TIMBRADO, ERROR, CANCELADO

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    empleado = relationship("Empleado", back_populates="nominas")

class Inasistencia(Base):
    """Registro de faltas y ausencias"""
    __tablename__ = "rh_inasistencias"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    empleado_id: str = Column(String, ForeignKey("rh_empleados.id"), nullable=False)
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=True)

    fecha = Column(Date, nullable=False)
    motivo: str = Column(String(200), nullable=True)
    justificada: bool = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    empleado = relationship("Empleado", back_populates="inasistencias")

class NoticiaHR(Base):
    """Tablón de anuncios y noticias de RRHH"""
    __tablename__ = "rh_noticias"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=True)
    
    titulo: str = Column(String(200), nullable=False)
    contenido: str = Column(Text, nullable=False)
    autor: str = Column(String(100), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RegistroAsistencia(Base):
    """Registro de entradas y salidas de empleados (biométrico)"""
    __tablename__ = "rh_registro_asistencia"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    empleado_id: str = Column(String, ForeignKey("rh_empleados.id"), nullable=False)
    tenant_id: str = Column(String, ForeignKey('tenants.id'), nullable=True)

    tipo: str = Column(String(50), nullable=False) # 'entrada', 'salida'
    metodo: str = Column(String(50), nullable=False) # 'biometrico', 'manual'
    offline_sync: bool = Column(Boolean, default=False)
    fecha_hora = Column(DateTime(timezone=True), server_default=func.now())
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    empleado = relationship("Empleado", back_populates="asistencias")
