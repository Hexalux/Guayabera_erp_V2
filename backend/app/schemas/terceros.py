"""
Esquemas Pydantic para Terceros Unificados
Soporta Clientes, Proveedores, Empleados y Otros
Fusión de CONTPAQi (datos fiscales), Odoo (flexibilidad), Management Pro (opciones)
"""
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from uuid import UUID
from enum import Enum


class TipoTercero(str, Enum):
    CLIENTE = "cliente"
    PROVEEDOR = "proveedor"
    EMPLEADO = "empleado"
    ACCIONISTA = "accionista"
    OTRO = "otro"


class TipoDocumento(str, Enum):
    RUC = "ruc"
    CEDULA = "cedula"
    PASAPORTE = "pasaporte"
    NIT = "nit"
    OTRO = "otro"


class RegimenFiscal(str, Enum):
    GENERAL = "general"
    RIMPE = "rimpe"
    POPULAR = "popular"
    EXENTO = "exento"


# ==================== SCHEMAS BASE ====================

class DireccionBase(BaseModel):
    calle_principal: str = Field(..., min_length=3, max_length=200)
    calle_secundaria: Optional[str] = Field(None, max_length=200)
    numero: Optional[str] = Field(None, max_length=20)
    referencia: Optional[str] = Field(None, max_length=300)
    ciudad: str = Field(..., min_length=2, max_length=100)
    provincia: str = Field(..., min_length=2, max_length=100)
    codigo_postal: Optional[str] = Field(None, max_length=20)
    pais: str = Field(default="Ecuador", max_length=100)


class ContactoBase(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=150)
    cargo: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=20)
    celular: Optional[str] = Field(None, max_length=20)
    es_principal: bool = False


class TerceroBase(BaseModel):
    tipo_tercero: TipoTercero
    identificacion: str = Field(..., min_length=5, max_length=20)
    tipo_documento: TipoDocumento
    razon_social: str = Field(..., min_length=3, max_length=200)
    nombre_comercial: Optional[str] = Field(None, max_length=200)
    regimen_fiscal: RegimenFiscal = RegimenFiscal.GENERAL
    fecha_nacimiento_constitucion: Optional[date] = None
    
    # Datos de contacto principal
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=20)
    celular: Optional[str] = Field(None, max_length=20)
    sitio_web: Optional[str] = Field(None, max_length=200)
    
    # Dirección principal
    direccion: Optional[DireccionBase] = None
    
    # Configuración financiera
    moneda_default: str = Field(default="USD", max_length=3)
    limite_credito: Optional[float] = Field(None, ge=0)
    dias_plazo: int = Field(default=0, ge=0, le=365)
    descuento_default: float = Field(default=0.0, ge=0, le=100)
    
    # Cuentas contables vinculadas (automáticas o manuales)
    cuenta_cobrar_pagar: Optional[str] = Field(None, max_length=20)
    cuenta_anticipos: Optional[str] = Field(None, max_length=20)
    cuenta_ingresos_gastos: Optional[str] = Field(None, max_length=20)
    
    # Estado
    activo: bool = True
    observaciones: Optional[str] = Field(None, max_length=1000)


class TerceroCreate(TerceroBase):
    contactos: Optional[List[ContactoBase]] = []
    direcciones: Optional[List[DireccionBase]] = []
    
    @validator('identificacion')
    def validar_identificacion(cls, v, values):
        if not v:
            return v
        # Validación básica según tipo de documento
        tipo_doc = values.get('tipo_documento')
        if tipo_doc == TipoDocumento.CEDULA and len(v) != 10:
            raise ValueError('La cédula debe tener 10 dígitos')
        if tipo_doc == TipoDocumento.RUC and len(v) != 13:
            raise ValueError('El RUC debe tener 13 dígitos')
        return v


class TerceroUpdate(BaseModel):
    razon_social: Optional[str] = Field(None, min_length=3, max_length=200)
    nombre_comercial: Optional[str] = Field(None, max_length=200)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=20)
    celular: Optional[str] = Field(None, max_length=20)
    limite_credito: Optional[float] = Field(None, ge=0)
    dias_plazo: Optional[int] = Field(None, ge=0, le=365)
    descuento_default: Optional[float] = Field(None, ge=0, le=100)
    activo: Optional[bool] = None
    observaciones: Optional[str] = Field(None, max_length=1000)


class TerceroResponse(TerceroBase):
    id: UUID
    tenant_id: UUID
    codigo: str
    saldo_pendiente: float = 0.0
    saldo_vencido: float = 0.0
    ultima_compra_venta: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== SCHEMAS ESPECÍFICOS ====================

class ClienteCreate(TerceroCreate):
    tipo_tercero: TipoTercero = TipoTercero.CLIENTE
    agente_vendedor_default: Optional[UUID] = None
    zona_geografica: Optional[str] = Field(None, max_length=100)
    ruta_reparto: Optional[str] = Field(None, max_length=100)
    acepta_notas_credito_electronicas: bool = True
    enviar_estado_cuenta_email: bool = False


class ProveedorCreate(TerceroCreate):
    tipo_tercero: TipoTercero = TipoTercero.PROVEEDOR
    categoria_proveedor: Optional[str] = Field(None, max_length=100)
    pais_origen: Optional[str] = Field(default="Ecuador", max_length=100)
    requiere_orden_compra: bool = False
    evaluar_calidad: bool = False


class TerceroFiltro(BaseModel):
    tipo_tercero: Optional[TipoTercero] = None
    identificacion: Optional[str] = None
    razon_social: Optional[str] = None
    activo: Optional[bool] = True
    ciudad: Optional[str] = None
    provincia: Optional[str] = None


# ==================== SCHEMAS PARA REPORTES ====================

class ResumenTerceroReporte(BaseModel):
    id: UUID
    codigo: str
    razon_social: str
    identificacion: str
    tipo_tercero: TipoTercero
    total_documentos: int
    saldo_total: float
    saldo_vencido: float
    saldo_por_vencer: float
    limite_credito: Optional[float]
    disponible_credito: Optional[float]
    ultimo_movimiento: Optional[datetime]


class EstadoCuentaTercero(BaseModel):
    tercero_id: UUID
    razon_social: str
    identificacion: str
    fecha_corte: date
    saldo_inicial: float
    movimientos: List[Dict[str, Any]]
    saldo_final: float
    documentos_vencidos: List[Dict[str, Any]]
    documentos_por_vencer: List[Dict[str, Any]]
