import uuid
from typing import Dict, Any

class PACServiceMock:
    """
    Simulador de Proveedor Autorizado de Certificación (PAC)
    Para conectar con un PAC real (Facturama, SW Sapien), reemplazar la lógica de este servicio.
    """
    
    @staticmethod
    async def timbrar_nomina(nomina_id: str, empleado_rfc: str, percepciones: float, deducciones: float) -> Dict[str, Any]:
        """
        Simula el ensamblaje del CFDI de Nómina 4.0 y su envío al PAC.
        Retorna el UUID y URLs de los archivos en caso de éxito.
        """
        # Validación básica de prueba
        if not empleado_rfc or len(empleado_rfc) < 12:
            return {
                "success": False,
                "error": "El RFC del receptor no es válido para CFDI 4.0"
            }
            
        # Simulación de respuesta exitosa del PAC
        fake_uuid = str(uuid.uuid4()).upper()
        
        return {
            "success": True,
            "data": {
                "uuid": fake_uuid,
                "url_xml": f"https://api.pacsimulado.com/descargas/cfdi/{fake_uuid}.xml",
                "url_pdf": f"https://api.pacsimulado.com/descargas/cfdi/{fake_uuid}.pdf",
                "mensaje": "Timbrado exitoso (Simulado)"
            }
        }

pac_service = PACServiceMock()
