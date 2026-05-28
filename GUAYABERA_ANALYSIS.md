# Análisis Comparativo: Guayabera ERP v1 vs v2
## Y Plan de Acción para Sprints Futuros

**Fecha:** Mayo 21, 2026  
**Productor:** Remy (AI Orchestration)  
**Estado:** Análisis Completo

---

## 📊 ESTADO ACTUAL DEL PROYECTO

### Versión 1 (guayabera-erp) - ORIGINAL
**Estado:** ❌ No funcional  
**Razones de fallos:**
- Arquitectura monolítica y altamente acoplada
- Múltiples módulos sin testing unitario
- Inconsistencias en tipos de datos (UUID vs INTEGER)
- Modelos duplicados (ConfiguracionCorreo en múltiples lugares)
- Migraciones deficientes o incompletas
- Frontend Ant Design v4 incompatible con React 18
- Dependencias sin resolver

**Componentes Implementados:**
- ✅ 10+ módulos CRUD completos (HR, Finanzas, Inventario, Ventas, etc.)
- ✅ API REST con 50+ endpoints
- ✅ Integración bancaria (esqueleto)
- ✅ Sistema de notificaciones
- ❌ Tests: No existen
- ❌ CI/CD: No configurado

### Versión 2 (guayabera-erp-v2) - REFACTORIZADA
**Estado:** ✅ Funcional (parcial)  
**Avances clave:**
- Arquitectura multi-tenant limpia
- Autenticación superusuario global
- Backend minimalista pero estable
- Frontend compilable con Ant Design v5
- Docker Compose configurado
- Base de datos con migraciones

**Componentes Implementados:**
- ✅ Autenticación y autorización (JWT)
- ✅ Modelos básicos (Empresa, Usuario, Tenant)
- ⚠️ Módulos principales incompletos (solo 3 endpoints base)
- ❌ Lógica de negocio: Mínima
- ❌ Tests: No existen
- ❌ Migraciones Alembic: No configuradas

---

## 🔍 ANÁLISIS DETALLADO

### Backend

#### v1 Fortalezas:
- Diseño modular completo (10 módulos de negocio)
- CRUD operations bien estructuradas
- Models y schemas coherentes
- Servicios de integración avanzados

#### v1 Debilidades:
- Errores de compilación fundamentales
- Sin tests unitarios/integración
- Migraciones conflictivas
- Falta de documentación en código

#### v2 Fortalezas:
- Arquitectura multi-tenant robusta
- Código limpio y enfocado
- Fácil de extender
- Punto de partida sólido

#### v2 Debilidades:
- Muy incompleto (solo auth + base de datos)
- Falta mayoría de lógica de negocio
- Sin integración bancaria
- Sin servicios avanzados (OCR, IA, etc.)

### Frontend

#### v1 Problemas:
- Ant Design v4 + React 18 incompatibles
- TypeScript sin strict mode
- Componentes sin tests
- Sin stories (Storybook)

#### v2 Estado:
- Actualizado a Ant Design v5
- React 18 compatible
- TypeScript configurado
- Pero muy básico (solo login + CRUD mínimo)

### Testing & QA

**Ambas versiones:** ❌ Carencia crítica  
- No hay tests unitarios
- No hay tests de integración
- No hay tests E2E
- No hay cobertura de código

---

## 💡 RECOMENDACIONES COMO PRODUCTOR

### ¿Cuál versión usar de base?

**RESPUESTA: v2 + Portear módulos de v1**

**Razonamiento:**
1. v2 tiene arquitectura multi-tenant correcta
2. v1 tiene lógica de negocio probada
3. v2 está compilando (v1 no)
4. Es más rápido pulir v2 que debuggear v1

### Estrategia de Migración

**Fase 1: Estabilización (2 sprints)**
- Completar migraciones Alembic en v2
- Portar servicios críticos de v1 (1-2 módulos)
- Setup testing framework completo
- CI/CD básico

**Fase 2: Funcionalidad Core (3-4 sprints)**
- Portar 5-6 módulos principales (HR, Finanzas, Inventario, Ventas, Compras)
- Implementar tests (50% cobertura mínimo)
- Documentación de API (OpenAPI/Swagger)

**Fase 3: Integraciones (2 sprints)**
- Integración bancaria operacional
- Notificaciones avanzadas
- Webhooks

**Fase 4: Frontend (2 sprints)**
- Layouts y componentes base
- Páginas CRUD para módulos
- Tests E2E

---

## 🎯 PLAN DE SPRINTS INICIALES

### Sprint 1: Backend Foundation (1 semana)
**Objetivos:**
- Migraciones Alembic configuradas y testables
- Modelos principales portados (Empresa, Usuario, Producto)
- CRUD básico operacional

**Tareas:**
1. Setup Alembic en v2
2. Crear modelos de Inventario/Productos
3. Servicios CRUD para productos
4. Routers API para productos
5. Health check endpoint

**Success Criteria:**
- `pytest tests/` pasa
- `alembic upgrade head` sin errores
- GET/POST /api/v1/products funciona

---

### Sprint 2: Testing Infrastructure (1 semana)
**Objetivos:**
- Framework pytest configurado
- Tests unitarios básicos (25% cobertura)
- GitHub Actions CI/CD

**Tareas:**
1. Instalar pytest, pytest-cov, faker
2. Escribir tests para auth (login/register)
3. Escribir tests para CRUD productos
4. Configurar GitHub Actions
5. Coverage report automático

**Success Criteria:**
- 25% cobertura de código
- CI/CD verde en main
- Tests pasan en paralelo

---

### Sprint 3: Modularización de v1 (1.5 semanas)
**Objetivos:**
- Portar Finanzas y RH desde v1
- Mantener compatibilidad multi-tenant
- Completar integraciones básicas

**Tareas:**
1. Analizar módulos Finanzas y RH de v1
2. Adaptar a arquitectura v2
3. Crear migraciones correspondientes
4. Tests unitarios
5. Documentar cambios

**Success Criteria:**
- Finanzas y RH funcionan en v2
- Tests pasan
- No regresiones en módulos anteriores

---

### Sprint 4: Frontend Fundacional (1.5 semanas)
**Objetivos:**
- Layout principal con identidad de marca
- Páginas CRUD operacionales
- TypeScript strict mode

**Tareas:**
1. Setup Storybook
2. Componentes base (Layout, Nav, Form)
3. Páginas CRUD (Productos, Clientes, etc.)
4. Autenticación en frontend
5. Tests E2E (Cypress)

**Success Criteria:**
- Componentes en Storybook
- Login → Dashboard funciona
- Tests E2E pasan

---

## ⚠️ RIESGOS IDENTIFICADOS

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|------------|--------|-----------|
| v1 tiene lógica no documentada | Alta | Alto | Code review exhaustivo |
| Multi-tenant complexity | Media | Alto | Aislamiento tests por tenant |
| TypeScript strict migration | Media | Medio | Relajar gradualmente |
| Database migrations conflict | Baja | Alto | Backup antes de migrate |
| Auth JWT token expiry | Baja | Medio | Refresh token implement |

---

## 📋 TAREAS INMEDIATAS (Próximos 3 días)

1. **Crear PROJECT_BRIEF.md** en raíz (sección 7-8 configuración v2)
2. **Setup GitHub Issues** con etiquetas (bug, feature, sprint-N)
3. **Crear docs/sprint-1/plan.md** detallado
4. **Configurar pytest** en v2/backend
5. **Primera reunión de equipo** (brainstorm roles: Product, Eng, QA)

---

## ✅ PRÓXIMOS PASOS

1. Confirmar estrategia con equipo dev
2. Comenzar Sprint 1 inmediatamente
3. Hacer daily standups (15 min)
4. Actualizar progress.md diariamente

**Prioridades:**
- ✅ Estabilidad > Características
- ✅ Tests > Código sin tests
- ✅ Documentación > Código no documentado
- ✅ Incrementos pequeños > Cambios grandes

---

*Este análisis será la base para los próximos sprints.*
