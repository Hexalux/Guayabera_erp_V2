# Importar modelos para que estén disponibles al importar el paquete

from app.models.usuario import Usuario
from app.models.tenant import Tenant, GrupoCorporativo
from app.models.admin import Admin
from app.models.licencia import Licencia, TipoLicencia
from app.models.token import TokenVerificacion
from app.models.inventory import CategoriaProductoTextil, ProductoTextil, Almacen, UbicacionAlmacen, LoteProducto, MovimientoInventario
from app.models.finance import CuentaContable, PolizaContable, MovimientoPoliza, Banco, MovimientoBancario
from app.models.hr import Empleado, ContratoLaboral, ControlVacaciones, Nomina
from app.models.production import OrdenProduccion, RecetaProduccion, CostoSubcontratacionMaquila
from app.models.helpdesk import TicketSoporte
from app.models.branches import Sucursal, CajaRegistradora
from app.models.sales import Cliente, VentaPOS, DetalleVentaPOS
from app.models.purchases import Proveedor, OrdenCompra, DetalleOrdenCompra, CuentaPorPagar
from app.models.treasury import CuentaBancaria, TransaccionBancaria
from app.models.cxc import CuentaPorCobrar, PagoCxC, NotaCreditoCliente
from app.models.expenses import CategoriaGasto, GastoOperativo
from app.models.sales_b2b import CotizacionVenta, DetalleCotizacion, PedidoVenta, DetallePedido, RemisionVenta, DetalleRemision

__all__ = [
    "Usuario", 
    "Tenant", 
    "Admin", 
    "GrupoCorporativo", 
    "Licencia", 
    "TipoLicencia", 
    "TokenVerificacion",
    "CategoriaProductoTextil",
    "ProductoTextil",
    "Almacen",
    "UbicacionAlmacen",
    "LoteProducto",
    "MovimientoInventario",
    "CuentaContable",
    "PolizaContable",
    "MovimientoPoliza",
    "Banco",
    "MovimientoBancario",
    "Empleado",
    "ContratoLaboral",
    "ControlVacaciones",
    "Nomina",
    "OrdenProduccion",
    "RecetaProduccion",
    "CostoSubcontratacionMaquila",
    "TicketSoporte",
    "Sucursal",
    "CajaRegistradora",
    "Cliente",
    "VentaPOS",
    "DetalleVentaPOS",
    "Proveedor",
    "OrdenCompra",
    "DetalleOrdenCompra",
    "CuentaPorPagar",
    "CuentaBancaria",
    "TransaccionBancaria",
    "CuentaPorCobrar",
    "PagoCxC",
    "NotaCreditoCliente",
    "CategoriaGasto",
    "GastoOperativo",
    "CotizacionVenta",
    "DetalleCotizacion",
    "PedidoVenta",
    "DetallePedido",
    "RemisionVenta",
    "DetalleRemision"
]