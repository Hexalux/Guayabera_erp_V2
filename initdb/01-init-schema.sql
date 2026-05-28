-- Script de inicialización de la base de datos para Guayabera ERP v2.0
-- Este script crea todas las tablas necesarias para el sistema multitenant

-- Crear extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Crear esquema para el sistema base
CREATE SCHEMA IF NOT EXISTS public;

-- Tabla para grupos corporativos
CREATE TABLE IF NOT EXISTS grupos_corporativos (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla para tenants (empresas)
CREATE TABLE IF NOT EXISTS tenants (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    name VARCHAR(255) NOT NULL,
    subdomain VARCHAR(255) UNIQUE NOT NULL,
    schema_name VARCHAR(255) UNIQUE NOT NULL,
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    descripcion TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    es_grupo_corporativo BOOLEAN DEFAULT FALSE,
    grupo_corporativo_id VARCHAR(36) REFERENCES grupos_corporativos(id)
);

-- Tabla para tipos de licencia
CREATE TABLE IF NOT EXISTS tipos_licencia (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    duracion_dias INTEGER NOT NULL,
    precio DECIMAL(10, 2),
    es_prueba BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla para licencias
CREATE TABLE IF NOT EXISTS licencias (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    tipo_licencia_id VARCHAR(36) NOT NULL REFERENCES tipos_licencia(id),
    codigo VARCHAR(50) UNIQUE NOT NULL,
    fecha_inicio TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    fecha_fin TIMESTAMP WITH TIME ZONE NOT NULL,
    activa BOOLEAN DEFAULT TRUE,
    usada BOOLEAN DEFAULT FALSE,
    notas TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla para administradores del sistema (superusuarios)
CREATE TABLE IF NOT EXISTS admins (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    email VARCHAR(255) UNIQUE NOT NULL,
    nombre_completo VARCHAR(255),
    hashed_password VARCHAR(255) NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla para usuarios regulares
CREATE TABLE IF NOT EXISTS usuarios (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    email VARCHAR(255) UNIQUE NOT NULL,
    nombre_completo VARCHAR(255),
    hashed_password VARCHAR(255) NOT NULL,
    tipo_usuario VARCHAR(20) DEFAULT 'normal',
    is_active BOOLEAN DEFAULT TRUE,
    tenant_id VARCHAR(36) REFERENCES tenants(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla para tokens de verificación
CREATE TABLE IF NOT EXISTS tokens_verificacion (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    usuario_id VARCHAR(36) REFERENCES usuarios(id),
    admin_id VARCHAR(36) REFERENCES admins(id),
    tipo_token VARCHAR(50) NOT NULL,  -- 'registro', 'recuperacion', 'invitacion_tenant_admin'
    token VARCHAR(255) UNIQUE NOT NULL,
    usado BOOLEAN DEFAULT FALSE,
    expira_en TIMESTAMP WITH TIME ZONE NOT NULL,
    tenant_id VARCHAR(36) REFERENCES tenants(id),
    destinatario_email VARCHAR(255),
    nombre_completo VARCHAR(255),
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE tokens_verificacion
    ALTER COLUMN tipo_token TYPE VARCHAR(50),
    ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(36) REFERENCES tenants(id),
    ADD COLUMN IF NOT EXISTS destinatario_email VARCHAR(255),
    ADD COLUMN IF NOT EXISTS nombre_completo VARCHAR(255);

-- Crear índices para mejorar el rendimiento
CREATE INDEX IF NOT EXISTS idx_tenants_subdomain ON tenants(subdomain);
CREATE INDEX IF NOT EXISTS idx_tenants_schema_name ON tenants(schema_name);
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
CREATE INDEX IF NOT EXISTS idx_usuarios_tenant_id ON usuarios(tenant_id);
CREATE INDEX IF NOT EXISTS idx_licencias_tenant_id ON licencias(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tokens_token ON tokens_verificacion(token);
CREATE INDEX IF NOT EXISTS idx_licencias_codigo ON licencias(codigo);

-- Insertar tipos de licencia predeterminados
INSERT INTO tipos_licencia (nombre, descripcion, duracion_dias, precio, es_prueba) 
SELECT 'Prueba 90 días', 'Licencia de prueba para nuevos usuarios', 90, NULL, TRUE
WHERE NOT EXISTS (SELECT 1 FROM tipos_licencia WHERE nombre = 'Prueba 90 días');

INSERT INTO tipos_licencia (nombre, descripcion, duracion_dias, precio, es_prueba) 
SELECT 'Mensual', 'Licencia mensual para uso continuo', 30, 49.99, FALSE
WHERE NOT EXISTS (SELECT 1 FROM tipos_licencia WHERE nombre = 'Mensual');

INSERT INTO tipos_licencia (nombre, descripcion, duracion_dias, precio, es_prueba) 
SELECT '6 Meses', 'Licencia semestral con descuento', 180, 249.99, FALSE
WHERE NOT EXISTS (SELECT 1 FROM tipos_licencia WHERE nombre = '6 Meses');

INSERT INTO tipos_licencia (nombre, descripcion, duracion_dias, precio, es_prueba) 
SELECT 'Anual', 'Licencia anual con mayor descuento', 365, 449.99, FALSE
WHERE NOT EXISTS (SELECT 1 FROM tipos_licencia WHERE nombre = 'Anual');

-- Insertar superusuario por defecto
INSERT INTO admins (email, nombre_completo, hashed_password, is_verified) 
SELECT 'admin@guayabera-erp.com', 'Super Administrador', '$2b$12$E9PVoslhSFJDhBab4tOK/e2wQIrTE2/4S4I8iknq6lu6UG5rQ8lrO', TRUE  -- Contraseña: admin123
WHERE NOT EXISTS (SELECT 1 FROM admins WHERE email = 'admin@guayabera-erp.com');
