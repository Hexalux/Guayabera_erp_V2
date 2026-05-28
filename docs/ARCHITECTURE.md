# Arquitectura del Guayabera ERP Suite v2.0

## Introducción

Esta documentación describe la arquitectura de la versión 2.0 del Guayabera ERP Suite, enfocada especialmente en el soporte multitenant (multiempresa) y el concepto de superusuario administrador global.

## Características de la Arquitectura Multitenant

### 1. Separación de Datos

La arquitectura multitenant implementada en esta versión permite:

- **Compartición de recursos**: Múltiples empresas (tenants) comparten la misma instancia de la aplicación y la base de datos
- **Aislamiento de datos**: Cada tenant tiene sus propios datos, que están aislados de otros tenants
- **Personalización**: Cada tenant puede tener configuraciones personalizadas sin afectar a otros tenants

### 2. Identificación de Tenant

- Cada solicitud al sistema incluye un header `X-Tenant-ID` que identifica el tenant actual
- El middleware de tenant intercepta cada solicitud y establece el contexto correspondiente
- Para operaciones del superusuario, el tenant puede ser opcional

### 3. Superusuario del Sistema

El superusuario tiene las siguientes características:

- **Acceso global**: No está asociado a ningún tenant específico
- **Gestión del sistema**: Puede crear, modificar y eliminar tenants
- **Supervisión**: Puede acceder y auditar cualquier información del sistema
- **Administración**: Puede gestionar usuarios de cualquier tenant si es necesario

## Empresas Filiales y Grupos Corporativos

### 1. Modelo de Grupo Corporativo

Además del modelo de tenant individual, se ha implementado un modelo de grupo corporativo que permite:

- Agrupar varias empresas bajo un mismo grupo (por ejemplo, Grupo Tut con empresas filiales como Alexa Tut, Alexis Tut y Antonio Tut)
- Realizar operaciones entre empresas filiales del mismo grupo
- Automatizar procesos entre empresas del mismo grupo

### 2. Tipos de Operaciones entre Filiales

El sistema soporta diferentes tipos de operaciones entre empresas filiales:

- **Consigna**: Envío de productos para su venta en otra empresa filial
- **Compra/Venta**: Transacciones comerciales entre empresas filiales
- **Apartado**: Reserva de productos entre filiales
- **Préstamo**: Préstamo temporal de productos entre filiales
- **Traspaso**: Transferencia definitiva de productos entre filiales

### 3. Validación de Operaciones

Para garantizar que solo se realicen operaciones válidas entre empresas del mismo grupo:

- El sistema verifica que ambas empresas (origen y destino) pertenezcan al mismo grupo corporativo
- Se requieren al menos 2 empresas filiales para que se puedan realizar operaciones
- Se registra un historial de todas las operaciones entre filiales

## Componentes Arquitectónicos

### 1. Middleware de Tenant

El archivo `app/middleware/tenant_middleware.py` implementa:

- Lectura del header `X-Tenant-ID` en cada solicitud
- Validación de que el tenant existe y está activo
- Almacenamiento del tenant en el contexto de la solicitud

### 2. Modelos de Datos

#### Modelo GrupoCorporativo (`app/models/tenant.py`)

Representa un grupo corporativo que puede contener varias empresas filiales:

- `id`: Identificador único del grupo
- `nombre`: Nombre del grupo corporativo
- `descripcion`: Descripción del grupo

#### Modelo Tenant (`app/models/tenant.py`)

Representa una empresa/cliente en el sistema con soporte para grupos:

- `id`: Identificador único del tenant
- `name`: Nombre del tenant
- `subdomain`: Subdominio único para identificarlo
- `schema_name`: Nombre del esquema en la base de datos (futuro uso)
- `es_grupo_corporativo`: Indica si este tenant es un grupo corporativo
- `grupo_corporativo_id`: ID del grupo corporativo al que pertenece (para empresas filiales)
- `is_active`: Estado de actividad del tenant

#### Modelo Usuario (`app/models/usuario.py`)

Representa un usuario en el sistema:

- Puede pertenecer a un tenant específico o ser un superusuario
- Tiene un campo `tenant_id` que puede ser nulo para superusuarios
- Campo `tipo_usuario` para distinguir entre 'superuser' y 'normal'

#### Modelo Admin (`app/models/admin.py`)

Representa al superusuario del sistema:

- No asociado a ningún tenant
- Acceso global al sistema
- Permisos especiales para gestionar tenants y ver todos los datos

### 3. Autenticación

El proceso de autenticación (`app/api/v1/endpoints/auth.py`) diferencia entre:

- Usuarios normales: Asociados a un tenant específico
- Superusuarios: Sin tenant asociado, con acceso global

### 4. Operaciones entre Filiales

El endpoint `app/api/v1/endpoints/operaciones_filiales.py` implementa:

- Creación de operaciones entre empresas filiales del mismo grupo
- Validación de que las empresas pertenecen al mismo grupo corporativo
- Registro de diferentes tipos de operaciones (consigna, compra, venta, etc.)

## Implementación Técnica

### Identificación del Tenant

1. El cliente debe incluir el header `X-Tenant-ID` en cada solicitud
2. El middleware extrae este valor y lo valida contra la base de datos
3. El tenant se almacena en el objeto `request.state` para su uso posterior

### Control de Acceso

- Las operaciones entre filiales requieren verificación de que ambas empresas pertenecen al mismo grupo corporativo
- Los endpoints protegidos verifican que el usuario tenga permiso para acceder a los recursos del tenant actual
- Los superusuarios pueden acceder a recursos de cualquier tenant
- Los usuarios normales solo pueden acceder a recursos de su propio tenant

## Consideraciones de Seguridad

- Todas las operaciones de consulta a la base de datos deben filtrar por `tenant_id` (excepto para superusuarios)
- El token JWT contiene información sobre el tenant del usuario
- El middleware de tenant asegura que cada solicitud esté correctamente identificada
- Las operaciones entre filiales se verifican para garantizar que ambas empresas pertenecen al mismo grupo

## Ventajas de la Arquitectura

- **Eficiencia**: Menor uso de recursos comparado con instancias separadas por empresa
- **Mantenimiento**: Actualizaciones y parches se aplican a una sola instancia
- **Consistencia**: Misma funcionalidad y experiencia para todos los tenants
- **Escalabilidad**: Fácil adición de nuevos tenants
- **Flexibilidad**: Soporte para grupos corporativos y operaciones entre filiales

## Consideraciones Futuras

- Implementación de esquemas de base de datos separados por tenant
- Funcionalidades de backup y restauración por tenant
- Monitoreo y reporting a nivel de tenant
- Facturación y control de uso por tenant
- Automatización avanzada de procesos entre empresas filiales
- Reportes consolidados para grupos corporativos