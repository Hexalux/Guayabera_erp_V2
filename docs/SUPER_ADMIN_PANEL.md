# Documentación del Panel de Administración Superior (Super Admin)

## Introducción

El panel de administración superior es una funcionalidad clave dentro del sistema Guayabera ERP Suite que permite a los super administradores gestionar de forma centralizada todos los tenants, corporaciones y licencias del sistema. A diferencia de otros usuarios, el super admin opera fuera del alcance de cualquier tenant específico, manteniendo un control total sobre la infraestructura general del sistema.

## Características Principales

### 1. Gestión de Tenants
- Creación de nuevos tenants con nombre, subdominio, correo de contacto y descripción
- Activación y desactivación de tenants según sea necesario
- Visualización de todos los tenants del sistema en una sola interfaz

### 2. Agrupación Corporativa
- Creación de corporaciones para agrupar tenants relacionados
- Asignación de tenants a corporaciones específicas
- Gestión de estructuras corporativas complejas

### 3. Sistema de Invitación Segura
- Envío de invitaciones por correo electrónico a administradores de tenants
- Generación de enlaces de un solo uso para creación de contraseñas
- Tokens de verificación con tiempo de expiración (24 horas)

### 4. Gestión de Licencias
- Creación y administración de licencias por tiempo, número de usuarios y empresas
- Asignación de licencias a tenants específicos
- Monitoreo del estado de las licencias

## Arquitectura Técnica

### Backend
- **Endpoints API**: `/admin/` - Ruta dedicada para funcionalidades de super admin
- **Autenticación**: Sistema JWT con verificación de rol de super admin
- **Modelos de Datos**:
  - `Tenant`: Representa cada organización cliente
  - `TenantCorporation`: Agrupación de tenants relacionados
  - `Licencia`: Control de acceso basado en diferentes parámetros
  - `TokenVerificacion`: Tokens de un solo uso para invitaciones

### Frontend
- **Componente**: `SuperAdminDashboard.tsx` - Interfaz completa de gestión
- **Rutas Protegidas**: Sistema de rutas restringidas solo a super admins
- **Interfaz de Usuario**: Diseño responsive con Ant Design en español

## Seguridad

### Control de Acceso
- Autenticación JWT obligatoria
- Verificación de rol específico ("superuser" o "superadmin")
- Separación completa de datos entre tenants y super admin

### Validaciones
- Verificación de unicidad para tenants y corporaciones
- Validación de tokens de invitación con expiración
- Control de integridad referencial entre entidades

## Componentes Clave

### Backend
1. `backend/app/api/v1/endpoints/admin.py`
   - Endpoints para gestión de tenants, corporaciones y licencias
   - Funciones para invitación de administradores
   - Operaciones de activación/desactivación

2. `backend/app/api/deps.py`
   - Función `get_current_admin` para verificación de permisos

### Frontend
1. `frontend/src/components/SuperAdminDashboard.tsx`
   - Interfaz de gestión integral
   - Formularios para creación de tenants y corporaciones
   - Tablas interactivas con acciones

2. `frontend/src/components/ProtectedRoute.tsx`
   - Sistema de rutas protegidas por rol

3. `frontend/src/services/authService.ts`
   - Funciones API para todas las operaciones de super admin

## Flujo de Trabajo Típico

1. **Creación de Tenant**:
   - Super admin ingresa datos del nuevo tenant
   - Sistema crea tenant con esquema de base de datos separado
   - Se asignan licencias iniciales

2. **Invitación de Administrador**:
   - Super admin selecciona tenant y proporciona correo
   - Sistema genera token único y envía correo de invitación
   - Administrador accede al enlace y crea su contraseña
   - Administrador puede acceder al panel de su tenant específico

3. **Gestión Corporativa**:
   - Super admin crea corporación para agrupar tenants
   - Se asignan tenants a la corporación correspondiente
   - Se pueden aplicar políticas comunes a grupos de tenants

4. **Gestión de Licencias**:
   - Creación de licencias con características específicas
   - Asignación a tenants según necesidades
   - Monitoreo del estado y expiración

## Consideraciones Importantes

- El super admin no pertenece a ningún tenant específico
- Todos los datos de tenants están aislados entre sí
- Las operaciones del super admin afectan directamente la infraestructura del sistema
- Los tenants no tienen acceso al panel de super admin
- La seguridad se mantiene mediante controles de autenticación rigurosos

## Beneficios del Sistema

- Centralización del control del sistema
- Flexibilidad para crear y gestionar múltiples tenants
- Escalabilidad para crecer horizontalmente
- Seguridad robusta con separación de datos
- Gestión eficiente de clientes corporativos

Este panel representa una solución completa para la administración de sistemas multitenant con capacidad de crecimiento y mantenimiento a largo plazo.