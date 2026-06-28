# Sprint 1 Plan: Assessment Financiero y Trazabilidad de Inventario
**Date**: 2026-06-05T12:35:00-06:00
**Sprint Goal**: Análisis y propuesta estructural para el módulo de contabilidad, finanzas, inventario, control de stock y trazabilidad, con base en el motor de producción actual.

<div style="background-color: #0C0E14; color: #FFFFFF; padding: 20px; border-left: 5px solid #00A651; font-family: 'Inter', sans-serif;">
  <h2 style="color: #DAA520; margin-top: 0;">🏛️ Arquitectura Financiera Cuantitativa (TutConta)</h2>

  <p><strong>Assessment del Estado Actual:</strong></p>
  <p>El motor actual de inventario (PostgreSQL) y la generación de pólizas de sistema en <code>finance_auto.py</code> cumplen primitivamente con los requisitos de la partida doble. Sin embargo, para escalar a nivel corporativo y mantener la inmutabilidad transaccional requerida en la auditoría (NIIF/IFRS), debemos migrar de una arquitectura puramente reactiva a una arquitectura basada en <em>Event Sourcing</em> y bloqueos deterministas.</p>

  <p><strong>Propuesta Estructural para Contabilidad y Trazabilidad de Stock:</strong></p>
  
  <ul>
    <li><strong>1. Inmutabilidad por Diseño (Ledger Insert-Only):</strong><br/>
    Bajo ninguna circunstancia la tabla de Movimientos de Inventario o Pólizas Contables debe permitir operaciones <code>UPDATE</code> o <code>DELETE</code>. Todo ajuste de inventario (mermas, traspasos) debe generar un nuevo registro de compensación. Esto garantiza una trazabilidad <em>Forensic-Ready</em>.</li>
    
    <li><strong>2. Modelo FIFO / Promedio Ponderado Integrado:</strong><br/>
    El inventario debe calcularse sobre la marcha utilizando Redis para cacheo del <em>Moving Average Cost</em>. Cuando una orden de producción se cierra (como hicimos en el módulo MRP), el descargo de tela no debe usar un costo estático estimado, sino leer de Redis el costo promedio ponderado exacto al milisegundo de ejecución.</li>
    
    <li><strong>3. Bloqueos Explícitos (Pessimistic Locking):</strong><br/>
    Para evitar condiciones de carrera cuando múltiples sucursales descuentan la misma guayabera o consumen el mismo rollo de tela, las consultas críticas en FastAPI deben usar <code>SELECT ... FOR UPDATE</code>. Esto fuerza una ejecución secuencial a nivel de base de datos en operaciones concurrentes de inventario.</li>
    
    <li><strong>4. Trazabilidad Híbrida (SQL + NoSQL):</strong><br/>
    El <em>General Ledger</em> y los asientos de diario permanecen en PostgreSQL (asegurando el cumplimiento ACID y la igualdad de Débito == Crédito). Sin embargo, el archivo plano de la trazabilidad logística de la guayabera (ID del lote de tela, operario que la cosió, número de máquina, tiempo de ciclo) debe enviarse como un documento JSONB a MongoDB, evitando inflar innecesariamente el esquema relacional.</li>
  </ul>

  <p><strong>Evaluación de Riesgo Actual:</strong></p>
  <p>Actualmente el método <code>create_system_poliza</code> en <code>finance_auto.py</code> verifica la asimetría contable, lo cual es excelente. Sin embargo, si un fallo ocurre entre la inserción del <code>MovimientoInventario</code> y la <code>PolizaContable</code>, el sistema queda asimétrico a nivel de dominio. Recomiendo envolver toda la operación finalizadora de producción en un bloque transaccional ACID explícito (<code>async with db.begin():</code>).</p>
</div>

---

## 🔧 Backend & Infrastructure (Tony)
**Status**: GO WITH CONDITIONS ⚠️
- Secundo a TutConta en la necesidad de envolver las llamadas en transacciones ACID estrictas.
- Recomiendo implementar un middleware de manejo de errores globales en FastAPI para asegurar que cualquier excepción de base de datos dispare automáticamente un `db.rollback()`.
- La separación de la lógica contable en `finance_auto.py` es limpia, pero sugiero inyectar un servicio de Colas (Redis + Celery) para la generación de facturación electrónica masiva en el futuro, ya que bloquearemos el event loop de FastAPI si la solicitud HTTP al SAT se demora.

---

## ⚡ Frontend Stack (Alexis)
**Status**: GO ✅
- Desde el frontend, consumiremos los endpoints analíticos de TutConta mapeados sobre ApexCharts.
- Proponemos crear un "Visor de Trazabilidad 360°" (Componente React) donde el usuario ingrese el Lote de una guayabera y, en un flujo visual (Timeline de Ant Design), pueda rastrear: Entrada de Tela -> Orden de Producción -> Venta en POS.

---

## ✅ Sign-off
- [x] TutConta: Criterios de rigurosidad matemática y partida doble establecidos.
- [ ] Tony: Transacciones ACID implementadas en toda la línea de inventario/conta.
- [ ] Alexis: Componentes de Trazabilidad 360 y Dashboards Financieros validados.
- [ ] Manuel: Batería de pruebas concurrentes pasadas.
