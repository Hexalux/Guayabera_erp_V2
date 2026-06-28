# Manual de Usuario: Sistema ERP MATS Green Energy / Guayabera

¡Bienvenido al sistema ERP! Esta guía está diseñada para enseñar a los administradores, gerentes y empleados cómo utilizar las diferentes áreas operativas del sistema. El sistema opera de manera integral, de modo que cada departamento colabora para mantener la empresa al día.

---

## Índice
1. [Introducción General](#1-introducción-general)
2. [Punto de Venta y Portal B2B (Ventas)](#2-punto-de-venta-y-portal-b2b-ventas)
3. [Inventario y Almacenes](#3-inventario-y-almacenes)
4. [Recursos Humanos y Biometría](#4-recursos-humanos-y-biometría)
5. [Finanzas y Contabilidad (Cuentas por Cobrar/Pagar)](#5-finanzas-y-contabilidad)

---

## 1. Introducción General

El sistema está construido bajo una filosofía de "Módulos", visibles en el menú lateral izquierdo de tu pantalla. Para acceder a cada función, haz clic en las pestañas correspondientes.

### Modo Oscuro y Estilo Visual
- El sistema utiliza la gama de colores oficial (Fondo Principal: `#0C0E14`, Acentos Verdes `#00A651` y Dorados `#DAA520`). Está optimizado para reducir la fatiga visual.
- Cuenta con tablas oscuras e indicadores de estado con códigos de color rápidos (Verde: Óptimo/Activo, Rojo: Alerta, Dorado: Pendiente).

---

## 2. Punto de Venta y Portal B2B (Ventas)

### Punto de Venta (B2C)
Ruta: **Ventas > Punto de Venta**
Esta pantalla está diseñada para ser rápida e intuitiva para los cajeros en tiendas físicas.
1. **Buscar y Agregar**: Puedes escanear un código de barras o seleccionar productos de la cuadrícula visual.
2. **Carrito de Compras**: Del lado derecho, verás los productos agregados, impuestos (IVA) y total.
3. **Cobro**: Da clic en el botón de "Cobrar" para registrar el pago. Automáticamente se generará un asiento contable y se restará el inventario del almacén correspondiente.

### Portal B2B (Distribuidores)
Ruta: **Ventas > Portal B2B**
Si tienes clientes tipo "Mayorista", ellos pueden iniciar sesión con su cuenta y acceder a este portal.
1. **Visor de Catálogo**: Podrán ver el catálogo y crear "Órdenes de Compra" directo a la fábrica.
2. **Estados de Cuenta**: Podrán consultar qué facturas deben y hacer sus conciliaciones sin tener que llamar a cobranza.

---

## 3. Inventario y Almacenes

El módulo de inventarios es de "Doble Entrada", lo que significa que la mercancía no desaparece mágicamente, siempre viaja de una ubicación a otra.

Rutas: **Inventarios > Movimientos / Inventario Físico / Trazabilidad**

### Movimientos de Stock
- **Transferencias Internas**: Para enviar mercancía de "Almacén Central" a "Sucursal Norte".
- **Ajustes y Mermas**: Cuando reportas una merma o producto dañado, el sistema automáticamente contabiliza la pérdida económica hacia una cuenta de Gastos, cuadrando los números con Finanzas.

### Inventario Físico (Auditorías)
Para realizar tu conteo físico:
1. Elige tu Sucursal/Ubicación.
2. Ingresa la cantidad real contada.
3. El sistema calculará la diferencia (Ajuste Positivo o Negativo) e inyectará ese ajuste en la base de datos para cuadrarlo.

### Trazabilidad de Lotes
Permite rastrear "de dónde viene y a dónde va" cada producto específico (o materia prima) mediante un diagrama de árbol visual.
1. Ingresa el número de lote y el sistema dibujará si ese material se usó en una orden de producción o se vendió a un cliente.

---

## 4. Recursos Humanos y Biometría

Ruta: **Recursos Humanos**

El módulo de RH gestiona el organigrama y permite controlar al personal de forma eficiente.

### Directorio y Expediente Digital
1. **Nuevo Empleado**: Ingresas sus datos, puesto, y muy importante, seleccionas a su **Jefe Inmediato**. 
2. **Organigrama**: El sistema dibujará gráficamente la jerarquía de la empresa basada en quién le reporta a quién.
3. **Expediente Digital**: Cada empleado tiene un espacio para subir sus PDFs obligatorios (Contrato, RFC, NSS).

### Vacaciones y Ausencias
- Aquí podrás solicitar días de vacaciones (indicando la fecha). RRHH o el Jefe directo podrá **Aprobar** o **Rechazar** la solicitud.
- Las inasistencias o faltas del empleado se registran aquí, marcando si están justificadas (no descuentan día) o no.

### Reloj Checador y Huella Digital (PWA)
Esta pantalla simula el dispositivo de asistencia en la entrada de tus tiendas o fábricas.
- **Modo Online/Offline**: Si el punto de venta se queda sin internet, el cajero puede seguir usando el Reloj Checador (con botón de Entrada / Salida). El sistema guarda en la computadora local esos datos y, en cuanto el WiFi regrese, subirá los "chequeos" pendientes sin perder nada.
- **Lector U.are.U 4500**: Mediante un pequeño agente instalado en la computadora física, el sistema puede capturar huellas dactilares y verificar la identidad antes de marcar la entrada, asegurando 100% de confiabilidad.

---

## 5. Finanzas y Contabilidad

El corazón del ERP donde todo el dinero y operaciones aterrizan. 
*Nota: La mayoría de las Pólizas Diarias (Ventas, Entradas de almacén, Mermas) se generan de forma **Automática**. Tú no tienes que teclearlas.*

### Catálogo de Cuentas
Ruta: **Configuración > Plan de Cuentas**
Un listado estilo árbol con el Código Agrupador del SAT. Permite configurar la base financiera de la empresa.

### Cuentas por Cobrar (CxC) y Facturación
Ruta: **Cuentas por Cobrar > CxC Dashboard**
- **Dashboard de Cobranza**: Un resumen de las facturas vencidas (Aging / Antigüedad de saldos) de 1-30, 31-60, y +90 días.
- Aquí podrás registrar pagos de clientes, relacionándolos con facturas específicas para matar el adeudo.

### Reportes de Antigüedad
Ruta: **Finanzas > Reportes**
Reportes tabulares donde puedes dar clic en cualquier fila para expandir los detalles y entender qué cliente debe y desde cuándo.

---

## 6. Soporte Técnico
Si notas un error de programación en alguna pantalla de carga o la PWA offline no quiere sincronizar al reconectarse a internet, intenta refrescar la pestaña presionando `F5` o `Ctrl+R`. 

Si el Lector de Huella no lee, verifica que el **Agente Biométrico Local** (`biometric_server.py`) esté corriendo en tu computadora Windows en el puerto `5000` y que la PWA no tenga un bloqueador de WebSockets.
