# Guayabera ERP Suite - Versión 2.0

## Descripción General

Guayabera ERP Suite v2.0 es una plataforma avanzada de planificación de recursos empresariales con arquitectura multitenant, diseñada específicamente para la industria textil y manufacturera. Esta nueva versión implementa un sistema de multiempresa con un superusuario administrador que gestiona todo el sistema.

## Características de la Arquitectura Multitenant

### Superusuario del Sistema
- Usuario administrador global con acceso a todo el sistema
- No pertenece a ninguna empresa específica
- Responsable de la gestión del sistema, creación de tenants y administración general
- Capacidad para supervisar y auditar todas las empresas del sistema

### Arquitectura de Multiempresa
- Completa separación de datos entre empresas
- Recursos compartidos con aislamiento garantizado
- Escalabilidad horizontal para agregar nuevas empresas
- Configuración centralizada y gestión descentralizada

### Seguridad y Acceso
- Autenticación y autorización jerárquica
- Control de acceso basado en roles (RBAC) por tenant
- Auditoría completa de todas las operaciones
- Encriptación de datos sensible

## Tecnologías Utilizadas

### Backend
- **Framework Web**: FastAPI (Python 3.11+)
- **ORM**: SQLAlchemy con soporte para PostgreSQL
- **Autenticación**: JWT (JSON Web Tokens) con soporte para multiempresa
- **Validación de Datos**: Pydantic
- **Cache**: Redis
- **Tareas Asíncronas**: Celery

### Frontend
- **Framework**: React 18+
- **Lenguaje**: TypeScript
- **UI Framework**: Ant Design
- **Estado**: Redux Toolkit

### Infraestructura
- **Base de Datos**: PostgreSQL 15+
- **Contenedores**: Docker & Docker Compose
- **Seguridad**: Let's Encrypt para SSL

## Estructura del Proyecto

```
guayabera-erp-v2/
├── backend/                 # API FastAPI multitenant
│   ├── app/
│   │   ├── api/v1/         # Endpoints por módulo
│   │   ├── core/           # Config, seguridad, BD multitenant
│   │   ├── crud/           # Operaciones de BD
│   │   ├── models/         # Modelos SQLAlchemy multitenant
│   │   ├── schemas/        # Schemas Pydantic
│   │   ├── services/       # Servicios multitenant
│   │   ├── middleware/     # Middlewares
│   │   ├── utils/          # Utilidades
│   │   └── main.py
│   └── requirements.txt
├── frontend/               # React (en desarrollo)
├── database/               # Migraciones Alembic multitenant
├── docker/                 # Dockerfiles
└── docs/                   # Documentación
```

## Módulos Planificados

1. **Autenticación Multitenant**
2. **Gestión de Tenants**
3. **Usuarios y Permisos**
4. **Catálogos Maestros**
5. **Contabilidad**
6. **Inventarios**
7. **Ventas**
8. **Compras**
9. **Producción**
10. **Recursos Humanos**
11. **CRM**
12. **Business Intelligence**

## Instalación y Ejecución

Siga las instrucciones en [INSTALL.md](./docs/INSTALL.md) para configurar el entorno de desarrollo.

## Documentación

- [Instalación](./docs/INSTALL.md)
- [Arquitectura](./docs/ARCHITECTURE.md)
- [API Reference](./docs/API.md)
- [Migración](./docs/MIGRATION.md)

## Contribución

Consulte [CONTRIBUTING.md](./docs/CONTRIBUTING.md) para conocer cómo contribuir al proyecto.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - vea el archivo [LICENSE](./LICENSE) para más detalles.