from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData, text
from typing import AsyncGenerator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Metadata object para controlar nuestro esquema de base de datos
metadata = MetaData(schema="public")

# Configurar motor asincrónico
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Crear un generador local de sesiones
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async_session_maker = AsyncSessionLocal

# Base para modelos
Base = declarative_base(metadata=metadata)

# Importaciones de modelos después de crear la Base para evitar problemas de importación circular
from app.models.usuario import Usuario  # noqa: F401
from app.models.tenant import Tenant  # noqa: F401
from app.models.admin import Admin  # noqa: F401
from app.models.licencia import Licencia, TipoLicencia  # noqa: F401
from app.models.token import TokenVerificacion  # noqa: F401
from app.models.inventory import CategoriaProductoTextil, ProductoTextil, Almacen, UbicacionAlmacen, LoteProducto, MovimientoInventario  # noqa: F401
from app.models.finance import CuentaContable, PolizaContable, MovimientoPoliza, Banco, MovimientoBancario  # noqa: F401
from app.models.hr import Empleado, ContratoLaboral, ControlVacaciones, Nomina  # noqa: F401
from app.models.production import OrdenProduccion, RecetaProduccion, CostoSubcontratacionMaquila  # noqa: F401
from app.models.helpdesk import TicketSoporte  # noqa: F401
from app.models.branches import Sucursal, CajaRegistradora  # noqa: F401


async def init_db():
    """Inicializa la base de datos creando todas las tablas."""
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        await conn.execute(text("ALTER TABLE tenants DROP CONSTRAINT IF EXISTS tenants_grupo_corporativo_id_fkey"))
        await conn.execute(text("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS fecha_cierre_contable TIMESTAMP WITH TIME ZONE"))
        await conn.execute(text("ALTER TABLE transacciones_bancarias ADD COLUMN IF NOT EXISTS metodo_pago VARCHAR NOT NULL DEFAULT 'transferencia'"))
        await conn.execute(text("ALTER TABLE transacciones_bancarias ADD COLUMN IF NOT EXISTS estado_cheque VARCHAR"))
        await conn.execute(text("ALTER TABLE rh_empleados ADD COLUMN IF NOT EXISTS puesto VARCHAR(150)"))
        await conn.execute(text("ALTER TABLE rh_empleados ADD COLUMN IF NOT EXISTS departamento_id VARCHAR"))
        await conn.execute(text("ALTER TABLE rh_empleados ADD COLUMN IF NOT EXISTS jefe_id VARCHAR"))
        await conn.execute(text("ALTER TABLE rh_empleados ADD COLUMN IF NOT EXISTS huella_template TEXT"))
        await conn.execute(text("ALTER TABLE rh_empleados ADD COLUMN IF NOT EXISTS requiere_asistencia BOOLEAN DEFAULT TRUE"))
        await conn.execute(text("ALTER TABLE licencias DROP CONSTRAINT IF EXISTS licencias_tenant_id_fkey"))
        await conn.execute(text("ALTER TABLE licencias DROP CONSTRAINT IF EXISTS licencias_tipo_licencia_id_fkey"))
        await conn.execute(text("ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS usuarios_tenant_id_fkey"))
        
        # Sprint 12: Ventas y Sesiones
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS pos_sesiones (
                id VARCHAR PRIMARY KEY,
                tenant_id VARCHAR NOT NULL,
                cajero_id VARCHAR NOT NULL,
                fecha_apertura TIMESTAMP NOT NULL,
                fecha_cierre TIMESTAMP,
                fondo_inicial FLOAT DEFAULT 0.0,
                total_efectivo FLOAT DEFAULT 0.0,
                total_tarjeta FLOAT DEFAULT 0.0,
                diferencia FLOAT DEFAULT 0.0,
                estado VARCHAR DEFAULT 'abierta',
                notas TEXT
            )
        """))
        await conn.execute(text("ALTER TABLE ventas_pos ADD COLUMN IF NOT EXISTS sesion_id VARCHAR"))
        
        # Sprint 13: Compras e Inventario
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS inv_unidades_medida (
                id VARCHAR PRIMARY KEY,
                tenant_id VARCHAR,
                nombre VARCHAR(50) NOT NULL,
                abreviatura VARCHAR(10) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE
            )
        """))
        await conn.execute(text("ALTER TABLE inv_productos ADD COLUMN IF NOT EXISTS unidad_medida_id VARCHAR"))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS prov_listas_precio (
                id VARCHAR PRIMARY KEY,
                tenant_id VARCHAR NOT NULL,
                proveedor_id VARCHAR NOT NULL,
                producto_textil_id VARCHAR NOT NULL,
                codigo_proveedor VARCHAR,
                precio FLOAT NOT NULL,
                moneda VARCHAR DEFAULT 'MXN',
                factor_conversion FLOAT DEFAULT 1.0
            )
        """))
        
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS mrp_proyectos (
                id VARCHAR PRIMARY KEY,
                tenant_id VARCHAR NOT NULL,
                nombre VARCHAR NOT NULL,
                descripcion TEXT,
                estado VARCHAR DEFAULT 'planificacion',
                fecha_inicio DATE,
                fecha_entrega DATE,
                responsable_id VARCHAR,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))

        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ventas_ordenes (
                id VARCHAR PRIMARY KEY,
                tenant_id VARCHAR NOT NULL,
                folio VARCHAR UNIQUE NOT NULL,
                fecha_emision TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                fecha_validez TIMESTAMP WITH TIME ZONE,
                cliente_id VARCHAR NOT NULL,
                vendedor_id VARCHAR NOT NULL,
                estado VARCHAR DEFAULT 'borrador',
                subtotal FLOAT DEFAULT 0.0,
                iva FLOAT DEFAULT 0.0,
                total FLOAT DEFAULT 0.0,
                notas TEXT,
                terminos_pago VARCHAR
            )
        """))

        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS detalles_orden_venta (
                id VARCHAR PRIMARY KEY,
                tenant_id VARCHAR NOT NULL,
                orden_id VARCHAR NOT NULL,
                producto_textil_id VARCHAR NOT NULL,
                cantidad FLOAT NOT NULL,
                precio_unitario FLOAT NOT NULL,
                descuento_porcentaje FLOAT DEFAULT 0.0,
                subtotal FLOAT NOT NULL
            )
        """))

        await conn.execute(text("ALTER TABLE ordenes_compra ADD COLUMN IF NOT EXISTS estado VARCHAR DEFAULT 'rfq'"))
        await conn.execute(text("ALTER TABLE prov_listas_precio ADD COLUMN IF NOT EXISTS factor_conversion FLOAT DEFAULT 1.0"))
        await conn.execute(text("ALTER TABLE tokens_verificacion DROP CONSTRAINT IF EXISTS tokens_verificacion_usuario_id_fkey"))
        await conn.execute(text("ALTER TABLE tokens_verificacion DROP CONSTRAINT IF EXISTS tokens_verificacion_admin_id_fkey"))
        await conn.execute(text("ALTER TABLE tokens_verificacion DROP CONSTRAINT IF EXISTS tokens_verificacion_tenant_id_fkey"))
        await conn.execute(text("ALTER TABLE grupos_corporativos ALTER COLUMN id TYPE VARCHAR(36) USING id::text"))
        await conn.execute(text("ALTER TABLE grupos_corporativos ALTER COLUMN id SET DEFAULT uuid_generate_v4()::text"))
        await conn.execute(text("ALTER TABLE tenants ALTER COLUMN id TYPE VARCHAR(36) USING id::text"))
        await conn.execute(text("ALTER TABLE tenants ALTER COLUMN id SET DEFAULT uuid_generate_v4()::text"))
        await conn.execute(text("ALTER TABLE tenants ALTER COLUMN grupo_corporativo_id TYPE VARCHAR(36) USING grupo_corporativo_id::text"))
        await conn.execute(text("ALTER TABLE tipos_licencia ALTER COLUMN id TYPE VARCHAR(36) USING id::text"))
        await conn.execute(text("ALTER TABLE tipos_licencia ALTER COLUMN id SET DEFAULT uuid_generate_v4()::text"))
        await conn.execute(text("ALTER TABLE licencias ALTER COLUMN id TYPE VARCHAR(36) USING id::text"))
        await conn.execute(text("ALTER TABLE licencias ALTER COLUMN id SET DEFAULT uuid_generate_v4()::text"))
        await conn.execute(text("ALTER TABLE licencias ALTER COLUMN tenant_id TYPE VARCHAR(36) USING tenant_id::text"))
        await conn.execute(text("ALTER TABLE licencias ALTER COLUMN tipo_licencia_id TYPE VARCHAR(36) USING tipo_licencia_id::text"))
        await conn.execute(text("ALTER TABLE admins ALTER COLUMN id TYPE VARCHAR(36) USING id::text"))
        await conn.execute(text("ALTER TABLE admins ALTER COLUMN id SET DEFAULT uuid_generate_v4()::text"))
        await conn.execute(text("ALTER TABLE usuarios ALTER COLUMN id TYPE VARCHAR(36) USING id::text"))
        await conn.execute(text("ALTER TABLE usuarios ALTER COLUMN id SET DEFAULT uuid_generate_v4()::text"))
        await conn.execute(text("ALTER TABLE usuarios ALTER COLUMN tenant_id TYPE VARCHAR(36) USING tenant_id::text"))
        await conn.execute(text("ALTER TABLE tokens_verificacion ALTER COLUMN id TYPE VARCHAR(36) USING id::text"))
        await conn.execute(text("ALTER TABLE tokens_verificacion ALTER COLUMN id SET DEFAULT uuid_generate_v4()::text"))
        await conn.execute(text("ALTER TABLE tokens_verificacion ALTER COLUMN usuario_id TYPE VARCHAR(36) USING usuario_id::text"))
        await conn.execute(text("ALTER TABLE tokens_verificacion ALTER COLUMN admin_id TYPE VARCHAR(36) USING admin_id::text"))
        await conn.execute(text("ALTER TABLE tokens_verificacion ALTER COLUMN tipo_token TYPE VARCHAR(50)"))
        await conn.execute(text("ALTER TABLE tokens_verificacion ADD COLUMN IF NOT EXISTS tenant_id VARCHAR"))
        await conn.execute(text("ALTER TABLE tokens_verificacion ALTER COLUMN tenant_id TYPE VARCHAR(36) USING tenant_id::text"))
        await conn.execute(text("ALTER TABLE tokens_verificacion ADD COLUMN IF NOT EXISTS destinatario_email VARCHAR"))
        await conn.execute(text("ALTER TABLE tokens_verificacion ADD COLUMN IF NOT EXISTS nombre_completo VARCHAR"))
        await conn.execute(text("ALTER TABLE admins ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE"))
        await conn.execute(text("UPDATE admins SET is_active = TRUE WHERE is_active IS NULL"))
        await conn.execute(text("ALTER TABLE grupos_corporativos ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE"))
        await conn.execute(text("UPDATE grupos_corporativos SET is_active = TRUE WHERE is_active IS NULL"))
        await conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'tenants_grupo_corporativo_id_fkey') THEN
                    ALTER TABLE tenants ADD CONSTRAINT tenants_grupo_corporativo_id_fkey
                    FOREIGN KEY (grupo_corporativo_id) REFERENCES grupos_corporativos(id);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'licencias_tenant_id_fkey') THEN
                    ALTER TABLE licencias ADD CONSTRAINT licencias_tenant_id_fkey
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'licencias_tipo_licencia_id_fkey') THEN
                    ALTER TABLE licencias ADD CONSTRAINT licencias_tipo_licencia_id_fkey
                    FOREIGN KEY (tipo_licencia_id) REFERENCES tipos_licencia(id);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'usuarios_tenant_id_fkey') THEN
                    ALTER TABLE usuarios ADD CONSTRAINT usuarios_tenant_id_fkey
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'tokens_verificacion_usuario_id_fkey') THEN
                    ALTER TABLE tokens_verificacion ADD CONSTRAINT tokens_verificacion_usuario_id_fkey
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'tokens_verificacion_admin_id_fkey') THEN
                    ALTER TABLE tokens_verificacion ADD CONSTRAINT tokens_verificacion_admin_id_fkey
                    FOREIGN KEY (admin_id) REFERENCES admins(id);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'tokens_verificacion_tenant_id_fkey') THEN
                    ALTER TABLE tokens_verificacion ADD CONSTRAINT tokens_verificacion_tenant_id_fkey
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id);
                END IF;
            END $$;
        """))
        
    logger.info("Base de datos inicializada correctamente")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Obtiene una sesión de base de datos para dependencias de FastAPI.
    
    Yields:
        db_session: Sesión de base de datos
    """
    async with AsyncSessionLocal() as session:
        yield session

# Alias for backwards compatibility with existing endpoints
get_db = get_db_session
