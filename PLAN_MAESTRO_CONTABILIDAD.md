# Plan Maestro: Sistema Contable y de Finanzas - Guayabera ERP Suite v2.0

## Visión del Sistema

Fusionar lo mejor de tres sistemas líderes:
- **CONTPAQi**: Robustez en manejo fiscal, validaciones estrictas, reportes contables completos
- **Odoo**: Flexibilidad modular, diseño UX moderno, automatización inteligente
- **Management Pro**: Opciones avanzadas de configuración, múltiples métodos de pago, control detallado

---

## Estado Actual (Sprint 1 Completado ✓)

### Implementado
- ✅ Modelos base: CuentaContable, CentroCosto, PeriodoContable, AsientoContable, MovimientoAsiento
- ✅ Jerarquías y multi-moneda
- ✅ Control de períodos cerrados
- ✅ Validación de cuadratura (débito = crédito)
- ✅ API REST para CRUD básico
- ✅ Balance de comprobación inicial

---

## Roadmap Detallado por Sprints

### **SPRINT 2: Terceros Unificados** (2 semanas)
**Inspiración**: CONTPAQi (datos fiscales completos) + Odoo (relaciones flexibles)

#### Funcionalidades
1. **Modelo Unificado de Terceros**
   - Tipo: cliente, proveedor, empleado, otro
   - Datos fiscales: RUC/CI, razón social, nombre comercial
   - Límites de crédito y plazos de pago
   - Múltiples direcciones y contactos
   - Cuentas contables predeterminadas por tercero

2. **Historial Crediticio**
   - Comportamiento de pago
   - Calificación automática
   - Alertas de riesgo

3. **Vinculación Contable**
   - Campos `tercero_id` y `tipo_tercero` en MovimientoAsiento
   - Reportes por tercero

#### Archivos a Crear
- `app/models/terceros.py`
- `app/schemas/terceros.py`
- `app/services/terceros_service.py`
- `app/api/v1/endpoints/terceros.py`

#### Endpoints
```
POST   /api/v1/terceros
GET    /api/v1/terceros
GET    /api/v1/terceros/{id}
PUT    /api/v1/terceros/{id}
DELETE /api/v1/terceros/{id}
GET    /api/v1/terceros/{id}/estado-cuenta
GET    /api/v1/terceros/{id}/historial-credito
```

---

### **SPRINT 3: Cuentas por Cobrar (CXC)** (3 semanas)
**Inspiración**: CONTPAQi (manejo de documentos) + Management Pro (múltiples formas de cobro)

#### A. Captura de Cuentas por Cobrar
- Facturas manuales y automáticas (desde módulo ventas)
- Series y folios configurables
- Impuestos desglosados (IVA, ICE, etc.)
- Vinculación automática a asientos contables

#### B. Gestión de Cobros
- **Registrar cobro**: Parcial o total, múltiple forma de pago
- **Cancelar cobro**: Con reversa automática de asiento
- **Generar comprobante de pago**: Recibos oficiales
- **Reportes**: Comprobantes de pago parcial

#### C. Notas de Crédito
- **Nota directa**: Por errores en facturación
- **Bonificación múltiple**: Aplicar a varias facturas
- **Por devolución**: Vinculada a inventario
- **De pre-pedido**: Anticipos no aplicados
- **Aplicación**: Manual o automática
- **Reportes**: Análisis anual de notas de crédito

#### D. Estado de Cuenta y Cartera
- Estado de cuenta de clientes (PDF/Excel)
- Reporte analítico de cartera
- Relación de cobranza:
  - Elaborar relación
  - Descargar relación
  - Generar recibo de caja masivo
- Descarga de cartera:
  - Aplicar recibos de caja (crédito)
  - Cobros masivos
  - Aplicar anticipos
  - Depuración de saldos

#### E. Documentos y Pagarés
- Generación de pagarés
- Control de vencimientos
- Reportes de documentos vencidos

#### F. Contra Recibos e Intereses
- Captura de contra recibos
- **Intereses moratorios**:
  - Generación automática por días de atraso
  - Tasas configurables
  - Reportes de intereses generados

#### G. Comprobación Fiscal
- Comprobación de compras (A0G02)
- Comprobación de gastos
- Aplicar pago desde CXP

#### H. Reportes CXC (20+ reportes)
1. Cuentas por cobrar
2. Análisis de cuentas por cobrar
3. Estado de cuenta de clientes
4. Cobranza
5. Documentos vencidos a una fecha
6. Impuestos cobrados
7. Auxiliar de documentos
8. Análisis de factura
9. Anticipos
10. Anticipos con saldo a una fecha
11. Cartera
12. Cobranza y anticipos
13. Ventas saldadas
14. Comisiones
15. Días promedio de cobranza
16. Análisis de días de cobranza
17. Comprobación de compras
18. Antigüedad de saldos
19. Rotación de cartera
20. Proyección de cobros

#### Archivos a Crear
- `app/models/cxc.py` (DocumentoCXC, Cobro, NotaCredito, Pagaré, InteresMoratorio)
- `app/schemas/cxc.py`
- `app/services/cxc_service.py`
- `app/api/v1/endpoints/cxc.py`
- `app/services/reportes_cxc.py`

---

### **SPRINT 4: Cuentas por Pagar (CXP)** (3 semanas)
**Inspiración**: CONTPAQi (control de obligaciones) + Odoo (flujos de aprobación)

#### A. Captura de Cuentas por Pagar
- Facturas de proveedores manuales/automáticas
- Retenciones automáticas
- Vinculación a centros de costo

#### B. Pagos a Proveedores
- Registrar pago (parcial/total)
- Cancelar pago con reversa
- Múltiples formas de pago
- Pagos masivos

#### C. Notas de Crédito de Proveedor
- Condiciones comerciales
- Lista de descuentos
- Notas directas, por bonificación, por devolución
- Aplicación manual/automática
- Reportes

#### D. Autorización de Pagos
- Flujos de aprobación multinivel
- Límites por usuario
- Notificaciones

#### E. Anticipos y Pagarés
- Aplicación de anticipos
- Generación de pagarés
- Control de vencimientos

#### F. Operaciones Cruzadas
- Depuración de saldos
- Aplicar pago desde CXC (compensaciones)

#### G. Reportes CXP (15+ reportes)
1. Análisis de cuentas por pagar
2. Cuentas por pagar a una fecha
3. Estado de cuenta de proveedores
4. Pagos realizados
5. Anticipos a proveedores
6. Anticipos a una fecha
7. Impuestos sobre compras
8. Impuestos acreditables
9. Antigüedad de saldos
10. Flujo de pagos proyectado
11. Proveedores principales
12. Compras por proveedor
13. Retenciones practicadas
14. Pagos pendientes
15. Análisis de descuentos

#### Archivos a Crear
- `app/models/cxp.py` (DocumentoCXP, Pago, NotaCreditoProveedor, Anticipo)
- `app/schemas/cxp.py`
- `app/services/cxp_service.py`
- `app/api/v1/endpoints/cxp.py`
- `app/services/autorizacion_pagos.py`

---

### **SPRINT 5: Tesorería - Caja** (2 semanas)
**Inspiración**: Management Pro (control de puntos de venta) + CONTPAQi (arqueos)

#### A. Recibos de Caja
- Elaborar recibos
- Depositar recibos
- Series consecutivas
- Múltiples tipos de ingreso

#### B. Liquidaciones
- Liquidación de sucursal
- Liquidación de vendedores (contado)
- Recepción de valores
- Arqueos ciegas

#### C. Punto de Venta
- Recepción de valores de cajeros
- Corte general de cajas
- Apertura/cierre de turno
- Fondo fijo

#### D. Reportes de Caja
- Arqueo de punto de venta
- Recepción de valores
- Cortes de caja (por turno, diario, personalizado)
- Recibos de caja emitidos
- Depósitos a bancos
- Ventas de contado aplicadas

#### Archivos a Crear
- `app/models/tesoreria/caja.py` (ReciboCaja, LiquidacionSucursal, LiquidacionVendedor, ArqueoCaja)
- `app/schemas/tesoreria/caja.py`
- `app/services/tesoreria/caja_service.py`
- `app/api/v1/endpoints/tesoreria/caja.py`

---

### **SPRINT 6: Tesorería - Bancos** (2 semanas)
**Inspiración**: CONTPAQi (control de cheques) + Odoo (conciliación)

#### A. Control de Cheques
- Solicitud de cheques
- Elaboración de cheques
- Aplicación de cheques
- Reingreso de cheques
- Captura de cheques rebotados
- Reportes:
  - Cheques emitidos
  - Cheques posfechados
  - Cheques rebotados

#### B. Movimientos Bancarios
- Registrar movimiento (depósito, retención, transferencia)
- Conciliación automática/semi-automática
- Importación de estados de cuenta (CSV, Excel)

#### C. Mantenimiento de Cuentas
- Configuración de cuentas bancarias
- Saldos libro vs banco
- Múltiples monedas por cuenta

#### D. Reportes de Bancos
- Concentrado de bancos
- Ingresos detallados
- Detallado de bancos
- Ingreso por cobranza y anticipos
- Movimientos de banco
- Conciliación bancaria

#### Archivos a Crear
- `app/models/tesoreria/bancos.py` (CuentaBancaria, Cheque, MovimientoBancario, Conciliacion)
- `app/schemas/tesoreria/bancos.py`
- `app/services/tesoreria/bancos_service.py`
- `app/api/v1/endpoints/tesoreria/bancos.py`

---

### **SPRINT 7: Control de Gastos** (2 semanas)
**Inspiración**: Management Pro (clasificación detallada) + CONTPAQi (depreciación)

#### A. Registro de Gastos
- Captura de gastos operativos
- Clasificación por tipo
- Centros de costo
- Comprobantes fiscales digitales

#### B. Reclasificación de Gastos
- Movimientos entre cuentas
- Justificación de cambios
- Auditoría de cambios

#### C. Nómina Integrada
- Registro de nómina
- Asientos automáticos
- Provisiones

#### D. Activos Fijos
- Alta de activos
- **Depreciación automática**:
  - Métodos: línea recta, acelerada
  - Tablas preconfiguradas
  - Asientos mensuales automáticos
- Baja de activos
- Reportes de depreciación

#### E. Gastos de Viaje
- Registro por viaje
- Viáticos
- Comprobantes
- Aprobaciones

#### F. Presupuesto de Gastos
- Presupuesto anual/mensual
- Control presupuestario
- Alertas de excedentes

#### G. Reportes de Gastos
1. Gastos del período
2. Gastos anuales comparativos
3. Auxiliar de gastos
4. Tabla de gastos
5. Gastos de operación
6. Depreciación de activos
7. Presupuesto vs real
8. Gastos por centro de costo
9. Gastos por proveedor
10. Gastos de viaje detallados

#### Archivos a Crear
- `app/models/gastos.py` (Gasto, ActivoFijo, Depreciacion, Nomina, GastoViaje, PresupuestoGasto)
- `app/schemas/gastos.py`
- `app/services/gastos_service.py`
- `app/services/depreciacion_service.py`
- `app/api/v1/endpoints/gastos.py`

---

### **SPRINT 8: Revaluación Cambiaria** (1 semana)
**Inspiración**: CONTPAQi (manejo multi-moneda robusto)

#### A. Tipos de Cambio
- Registro diario de tipos de cambio
- Fuentes automáticas (API BCE, SAT, etc.)
- Tipos históricos

#### B. Revaluación Automática
- **Revaluación de tipos de cambio**:
  - Cálculo automático de diferencias cambiarias
  - Asientos de ajuste por tenencia
  - Ganancias/pérdidas cambiarias
- Valuación de portafolio

#### C. Reportes de Revaluación
- Revaluación de tipos de cambio
- Valuación de tipos de cambio
- Utilidad/pérdida cambiaria por cuenta
- Impacto en resultados

#### Archivos a Crear
- `app/models/revaluacion.py` (TipoCambio, RevaluacionAutomatica)
- `app/schemas/revaluacion.py`
- `app/services/revaluacion_service.py`
- `app/api/v1/endpoints/revaluacion.py`

---

### **SPRINT 9: Contabilidad Electrónica e Impuestos** (3 semanas)
**Inspiración**: CONTPAQi (reportes fiscales) + Odoo (conexión XML)

#### A. Pólizas Contables Avanzadas
- Captura de pólizas con plantillas
- Pólizas recurrentes
- Pólizas de cierre automático
- Conexión contable desde otros módulos

#### B. Impuestos
- Configuración de impuestos (IVA, ISR, retenciones)
- Cálculo automático en documentos
- **Cancelación de impuestos**
- Acumulación por período

#### C. DIOT (Declaración Informativa de Operaciones con Terceros)
- **Generación de DIOT** automática
- Validación de datos
- Exportación a formato oficial
- **Reporte de DIOT**

#### D. Constancias de Retenciones
- Generación de constancias
- Información de pagos
- Envío a autoridades

#### E. Exportación Contabilidad Electrónica
- Formato XML oficial
- Balanza de comprobación XML
- Catálogo de cuentas estandarizado

#### Archivos a Crear
- `app/models/contabilidad_electronica.py` (PolizaAvanzada, Impuesto, DIOT, ConstanciaRetencion)
- `app/schemas/contabilidad_electronica.py`
- `app/services/contabilidad_electronica_service.py`
- `app/services/impuestos_service.py`
- `app/api/v1/endpoints/contabilidad_electronica.py`

---

### **SPRINT 10: Reportes Financieros Ejecutivos** (3 semanas)
**Inspiración**: Management Pro (reportes gerenciales) + Odoo (dashboards)

#### A. Estados Financieros Básicos
1. **Balance General**
   - Clásico y vertical
   - De 12 períodos
   - Comparativo año anterior
   - Por empresa (multi-compañía)

2. **Estado de Resultados**
   - Tabla dinámica
   - De 12 períodos
   - Por centro de costo (CECO)
   - Margen de contribución

3. **Análisis de Resultados**
   - Análisis administrativo
   - Análisis de proyectos
   - Análisis por empresa
   - Variaciones presupuestales

#### B. Flujo de Efectivo
- **Flujo de efectivo** estándar
- **Flujo de efectivo detallado** (método directo/indirecto)
- **Flujo de efectivo anual**
- **Flujo de efectivo por empresa**
- Proyecciones

#### C. Libros Contables
- Auxiliar contable (por cuenta, por fecha, por tercero)
- Balanza de comprobación
- Balanza de comprobación 12 períodos
- Libro de mayor
- Libro de diario
- Libro mayor condensado

#### D. Reportes Especiales
- Documentos sin contabilizar
- Pólizas del período
- Utilidad y pérdida cambiaria
- Razones financieras
- Punto de equilibrio

#### E. Dashboard Ejecutivo
- KPIs financieros en tiempo real
- Gráficos de tendencias
- Alertas de desviaciones
- Personalizable por usuario

#### Archivos a Crear
- `app/services/reportes_financieros.py`
- `app/api/v1/endpoints/reportes_financieros.py`
- `app/utils/calculos_financieros.py`
- Frontend: componentes de dashboard

---

### **SPRINT 11: Automatizaciones e Integraciones** (2 semanas)
**Inspiración**: Odoo (automatización inteligente)

#### A. Asientos Automáticos
- Desde ventas (facturación)
- Desde compras (recepción)
- Desde inventarios (movimientos)
- Desde nómina
- Desde tesorería

#### B. Procesos Programados
- Depreciación mensual automática
- Revaluación cambiaria diaria/semanal
- Cierre de períodos programado
- Generación de intereses moratorios

#### C. Integraciones Externas
- Bancos (API para importación de movimientos)
- Autoridades fiscales (envío automático de reportes)
- Pasarelas de pago
- Sistemas de facturación electrónica

#### D. Workflows Aprobación
- Líneas de aprobación configurables
- Notificaciones por email
- Escalamiento automático

---

### **SPRINT 12: Características Avanzadas UX** (2 semanas)
**Inspiración**: Odoo (diseño) + Management Pro (opciones)

#### A. Mejoras de UX
- Búsqueda global inteligente
- Favoritos y accesos rápidos
- Vistas personalizadas por usuario
- Atajos de teclado
- Modo oscuro/claro

#### B. Plantillas y Configuración
- Plantillas de asientos frecuentes
- Plan de cuentas preconfigurado por industria
- Configuración wizard inicial
- Importación masiva de datos (Excel, CSV)

#### C. Multi-Compañía Avanzado
- Consolidación de estados financieros
- Eliminación de operaciones intercompañía
- Monedas diferentes por compañía
- Horarios fiscales distintos

#### D. Auditoría y Seguridad
- Log completo de auditoría
- Trazabilidad de cambios
- Roles y permisos granulares
- Firmas digitales en pólizas

---

## Resumen de Entregables por Módulo

### Módulo CXC (40+ funcionalidades)
- [x] Captura de documentos
- [x] Cobros múltiples
- [x] Notas de crédito (5 tipos)
- [x] Estados de cuenta
- [x] Relaciones de cobranza
- [x] Pagarés y documentos
- [x] Intereses moratorios
- [x] 20+ reportes especializados

### Módulo CXP (35+ funcionalidades)
- [x] Captura de facturas
- [x] Pagos a proveedores
- [x] Notas de crédito proveedor
- [x] Autorizaciones
- [x] Anticipos
- [x] Compensaciones CXC-CXP
- [x] 15+ reportes

### Tesorería (30+ funcionalidades)
- [x] Caja: recibos, liquidaciones, arqueos
- [x] Bancos: cheques, conciliaciones
- [x] Control de puntos de venta
- [x] 15+ reportes de tesorería

### Control de Gastos (25+ funcionalidades)
- [x] Registro y reclasificación
- [x] Activos fijos y depreciación
- [x] Nómina integrada
- [x] Gastos de viaje
- [x] Presupuestos
- [x] 10+ reportes

### Contabilidad Electrónica (20+ funcionalidades)
- [x] Pólizas avanzadas
- [x] Impuestos y retenciones
- [x] DIOT
- [x] Constancias
- [x] Exportación XML
- [x] 10+ libros contables

### Reportes Financieros (25+ reportes)
- [x] Balance General (múltiples formatos)
- [x] Estado de Resultados
- [x] Flujo de Efectivo
- [x] Análisis de resultados
- [x] Dashboard ejecutivo

---

## Cronograma Estimado

| Sprint | Duración | Módulo | Prioridad |
|--------|----------|--------|-----------|
| 2 | 2 sem | Terceros | 🔴 Alta |
| 3 | 3 sem | CXC | 🔴 Alta |
| 4 | 3 sem | CXP | 🔴 Alta |
| 5 | 2 sem | Caja | 🟡 Media |
| 6 | 2 sem | Bancos | 🟡 Media |
| 7 | 2 sem | Gastos | 🟡 Media |
| 8 | 1 sem | Revaluación | 🟢 Baja |
| 9 | 3 sem | Cont. Electrónica | 🔴 Alta |
| 10 | 3 sem | Reportes | 🔴 Alta |
| 11 | 2 sem | Automatizaciones | 🟡 Media |
| 12 | 2 sem | UX Avanzado | 🟢 Baja |

**Total estimado**: 25 semanas (~6 meses)

---

## Próximos Pasos Inmediatos

1. **Validar este plan** con el equipo
2. **Priorizar sprints** según necesidades del negocio
3. **Comenzar Sprint 2**: Terceros Unificados
4. **Configurar ambiente de desarrollo** con las nuevas rutas
5. **Diseñar UI/UX** inspirado en Odoo para los nuevos módulos

---

## Bibliotecas Adicionales Requeridas

```txt
# Ya existentes (no se requieren adicionales para ahora)
sqlalchemy>=2.0.23
fastapi>=0.104.1
pydantic>=2.6.0
asyncpg>=0.29.0

# Para futuras funcionalidades (agregar cuando corresponda)
openpyxl>=3.1.2          # Manejo de Excel para reportes
pandas>=2.0.3            # Análisis de datos para reportes avanzados
weasyprint>=60.1         # Generación de PDFs profesionales
xmltodict>=0.13.0        # Manejo de XML para contabilidad electrónica
qrcode>=7.4.2            # Códigos QR en comprobantes
celery>=5.3.4            # Tareas asíncronas para procesos programados
redis>=4.6.0             # Cola de mensajes para Celery
httpx>=0.25.2            # Cliente HTTP para APIs externas
```

---

## Métricas de Éxito

- ✅ 100% de funcionalidades de CONTPAQi cubiertas en módulos fiscales
- ✅ 90% de flexibilidad de Odoo en configuración y UX
- ✅ 95% de opciones de Management Pro implementadas
- ✅ Tiempo de generación de reportes < 3 segundos
- ✅ Soporte para 100+ usuarios concurrentes
- ✅ 99.9% uptime en producción

---

**Documento creado**: Diciembre 2024  
**Versión**: 1.0  
**Próxima revisión**: Al finalizar Sprint 3
