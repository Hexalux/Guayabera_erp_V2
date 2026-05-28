# Resumen Técnico del ERP Guayabera v2.0 - Arquitectura Multitenant

## Fecha: 3 de mayo de 2026

## Introducción

Este documento resume los principales desarrollos realizados en la versión 2.0 del ERP Guayabera, con un enfoque especial en la implementación de la arquitectura multitenant y el sistema de superusuario administrador global, así como la funcionalidad de empresas filiales y el sistema de licencias.

## Características Implementadas

### 1. Arquitectura Multitenant

- **Identificación de Tenant**: Implementación de middleware para identificar el tenant actual mediante el header `X-Tenant-ID`
- **Modelo de Tenant**: Creación del modelo `Tenant` para representar cada empresa/cliente en el sistema
- **Aislamiento de Datos**: Implementación de mecanismos para garantizar la separación de datos entre tenants
- **Contexto de Tenant**: Variables de contexto para almacenar el tenant actual durante la ejecución de solicitudes

### 2. Grupos Corporativos y Empresas Filiales

- **Modelo Grupo Corporativo**: Creación del modelo `GrupoCorporativo` para agrupar empresas filiales
- **Relación entre Empresas**: Implementación de la relación entre empresas filiales y su grupo corporativo
- **Operaciones entre Filiales**: Desarrollo de funcionalidades para realizar operaciones entre empresas del mismo grupo (consigna, compra, venta, apartado, préstamo)
- **Validación de Operaciones**: Implementación de reglas para garantizar que solo se realicen operaciones entre empresas del mismo grupo corporativo

### 3. Sistema de Login y Registro

- **Registro de Usuarios**: Implementación de un flujo de registro con verificación por correo electrónico
- **Confirmación de Cuenta**: Sistema de tokens únicos para activar cuentas después del registro
- **Login Seguro**: Autenticación JWT con tokens que incluyen información del tenant
- **Verificación de Licencia**: Validación de licencia activa antes de permitir el acceso al sistema

### 4. Sistema de Licencias

- **Tipos de Licencia**: Implementación de diferentes tipos de licencias (prueba, mensual, seis meses, anual)
- **Licencia de Prueba**: Licencia gratuita de 90 días para nuevos usuarios
- **Gestión de Licencias**: Módulo para que el super admin pueda generar y gestionar licencias
- **Renovación y Compra**: Sistema para que los usuarios puedan comprar nuevas licencias
- **Códigos de Licencia**: Generación de códigos únicos para las licencias

### 5. Recuperación de Contraseña

- **Solicitud de Recuperación**: Sistema para solicitar recuperación de contraseña mediante correo electrónico
- **Tokens de Un Solo Uso**: Implementación de tokens temporales y de un solo uso para la recuperación
- **Mensaje Profesional**: Mensajes claros que indican al usuario revisar la carpeta de correo no deseado
- **Seguridad Mejorada**: Tokens que expiran después de un periodo corto de tiempo

### 6. Superusuario del Sistema

- **Usuario Global**: Implementación del modelo `Admin` para representar al superusuario del sistema
- **Acceso Global**: El superusuario no está asociado a ningún tenant específico y tiene acceso global al sistema
- **Gestión de Tenants**: Capacidad para crear, modificar y eliminar tenants
- **Supervisión**: Posibilidad de auditar y supervisar todas las operaciones del sistema

### 7. Tipos de Operaciones entre Filiales

- **Consigna**: Sistema para enviar productos para su venta en otra empresa filial
- **Compra/Venta**: Transacciones comerciales entre empresas filiales
- **Apartado**: Reserva de productos entre filiales
- **Préstamo**: Préstamo temporal de productos entre filiales
- **Traspaso**: Transferencia definitiva de productos entre filiales

### 8. Autenticación y Autorización

- **Diferenciación de Usuarios**: Sistema capaz de distinguir entre usuarios normales (asociados a un tenant) y superusuarios (sin tenant asociado)
- **Tokens JWT**: Implementación de tokens JWT que incluyen información sobre el tipo de usuario y el tenant
- **Control de Acceso**: Verificación de que los usuarios solo accedan a recursos del tenant correspondiente
- **Validación de Operaciones**: Control de que las operaciones entre filiales solo se realicen entre empresas del mismo grupo

### 9. Estructura de Proyecto

- **Organización Modular**: Estructura de directorios claramente definida para facilitar el mantenimiento
- **Documentación**: Documentación completa sobre la arquitectura multitenant y las operaciones entre filiales
- **Configuración**: Configuración centralizada en `app/core/config.py`

## Componentes Principales

### Backend (FastAPI)

- **Middleware de Tenant**: Interceptor que valida y establece el tenant para cada solicitud
- **Modelos de Datos**: Implementación de modelos para `Tenant`, `Usuario`, `Admin`, `Licencia`, `TipoLicencia` y `TokenVerificacion`
- **Endpoints API**: Rutas para gestión de tenants, usuarios, autenticación, operaciones entre filiales y licencias
- **Esquemas Pydantic**: Validación de datos de entrada y salida

### Seguridad

- **Hash de Contraseñas**: Uso de bcrypt para almacenar contraseñas de forma segura
- **Tokens JWT**: Autenticación segura con tokens firmados
- **Control de Acceso**: Verificación de permisos basada en el tipo de usuario y tenant
- **Validación de Grupos**: Asegura que solo se realicen operaciones entre empresas del mismo grupo
- **Tokens de Verificación**: Implementación de tokens temporales y de un solo uso para registro y recuperación de contraseñas

### Infraestructura

- **Docker Compose**: Configuración de contenedores para desarrollo
- **PostgreSQL**: Base de datos relacional con soporte para múltiples tenants
- **Redis**: Caché y soporte para tareas asíncronas

## Beneficios de la Nueva Arquitectura

1. **Eficiencia**: Compartición de recursos entre múltiples empresas
2. **Escalabilidad**: Capacidad para agregar nuevos tenants sin afectar a otros
3. **Seguridad**: Aislamiento completo de datos entre tenants
4. **Gestión Centralizada**: Administración unificada de múltiples empresas
5. **Flexibilidad Corporativa**: Soporte para estructuras corporativas complejas con empresas filiales
6. **Automatización**: Procesos automatizados entre empresas del mismo grupo
7. **Monetización**: Sistema flexible de licencias que permite diferentes modelos de negocio

## Próximos Pasos

1. **Implementación de Esquemas Separados**: Considerar el uso de esquemas de base de datos separados por tenant para mayor aislamiento
2. **Funcionalidades de Monitoreo**: Implementar herramientas para supervisar el uso y rendimiento por tenant
3. **Integración de Pagos**: Conectar el sistema de compra de licencias con pasarelas de pago reales
4. **Extensión de Funcionalidades**: Incorporar módulos completos (inventarios, ventas, producción, etc.) adaptados a la arquitectura multitenant
5. **Automatización Avanzada**: Desarrollar reglas de negocio para automatizar completamente las operaciones entre filiales
6. **Reportes Consolidados**: Implementar reportes que muestren información consolidada para grupos corporativos
7. **Notificaciones por Email**: Implementar un sistema completo de notificaciones por correo electrónico con plantillas personalizables

## Resolución de Incidencias

### Corrección de Error 500 en `/api/v1/auth/register-superuser`
Durante la inicialización del sistema se detectó un error 500 Internal Server Error al intentar crear el primer superusuario global mediante Postman. 
La causa raíz fue un error de mapeo de SQLAlchemy en los modelos de licencias: `sqlalchemy.exc.InvalidRequestError: Mapper 'Mapper[TipoLicencia(tipos_licencia)]' has no property 'licencias_asignadas'`.
Se solucionó agregando la relación `licencias_asignadas = relationship("Licencia", back_populates="tipo_licencia")` al modelo `TipoLicencia` en `app/models/licencia.py`, permitiendo que el inicializador de la base de datos complete su configuración y el endpoint procese correctamente la petición (retornando 400 Bad Request en lugar de 500, en el caso de que el superusuario ya exista).

## Conclusión

La versión 2.0 del ERP Guayabera implementa una sólida arquitectura multitenant que permite servir a múltiples empresas desde una única instancia del sistema, manteniendo la seguridad y privacidad de los datos de cada tenant. La implementación del superusuario global facilita la administración del sistema y la supervisión de todas las operaciones. Además, la funcionalidad de grupos corporativos y empresas filiales permite automatizar operaciones entre empresas relacionadas, mejorando la eficiencia operativa para estructuras corporativas complejas. El sistema de licencias flexible permite diferentes modelos de negocio y periodos de prueba, facilitando la adopción del sistema por nuevos clientes.