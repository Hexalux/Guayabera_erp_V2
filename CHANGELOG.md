# Changelog

Todos los cambios notables en el proyecto Guayabera ERP Suite v2.0 serán documentados en este archivo.

## [2.0.0] - TBD

### Fixed
- Error 500 (Internal Server Error) en el endpoint `/api/v1/auth/register-superuser` provocado por un manejo asíncrono incorrecto de `scalars()` al verificar superusuarios existentes.

### Added
- Arquitectura multitenant desde el inicio del proyecto
- Superusuario administrador global del sistema
- Sistema de gestión de tenants (empresas)
- Estructura de base de datos multitenant
- Middleware para identificación de tenant
- Autenticación y autorización adaptadas al modelo multitenant
- Documentación inicial del sistema

### Changed
- Rediseño completo de la arquitectura para soportar multiempresa
- Actualización de modelos de datos para incluir tenant_id
- Revisión de la estrategia de seguridad para soportar multiempresa
- Reorganización de la estructura de carpetas para mejor escalabilidad

### Removed
- Configuración monolítica de la versión anterior
- Estructura de usuarios sin distinción de tenant
- Control de acceso sin consideración de multiempresa

## [1.0.0] - 2026-04

Versión original del Guayabera ERP Suite (desarrollo previo a la v2.0).