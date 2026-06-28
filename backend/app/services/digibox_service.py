import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DigiboxService:
    """
    Cliente para la API de Digibox (PAC) - Timbrado JSON v3
    """
    
    def __init__(self, user: str, password: str, is_production: bool = False):
        self.user = user
        self.password = password
        
        if is_production:
            self.base_url = "https://timbrado.digibox.com.mx"
        else:
            self.base_url = "https://testtimbrado.digibox.com.mx"
            
        self._token: Optional[str] = None
        
    async def _authenticate(self) -> str:
        """Obtiene el token de autenticación"""
        url = f"{self.base_url}/api/autenticacion/autenticarbasico"
        headers = {
            "usuario": self.user,
            "password": self.password
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers)
            
            if response.status_code == 200:
                self._token = response.text.strip('"')  # Retorna el token como string
                return self._token
            else:
                logger.error(f"Error de autenticación Digibox: {response.text}")
                raise Exception(f"Fallo al autenticar con el PAC: {response.text}")
                
    async def timbrar_nomina(self, nomina_id: str, empleado_rfc: str, percepciones: float, deducciones: float, cfdi_json_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía el JSON estructurado del CFDI 4.0 al PAC para su Timbrado y Sellado.
        """
        if not self._token:
            await self._authenticate()
            
        url = f"{self.base_url}/apisellado/timbradojson/v3"
        headers = {
            "token": self._token,
            "formato": "pdf" # Solicita que devuelva también el PDF (opcional, según doc, valores: png, jpg, pdf, etc.)
        }
        
        # En una implementación real, aquí va el Payload JSON estructurado bajo las reglas de Digibox
        # Para la prueba, enviamos el payload que debe construir el backend.
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=cfdi_json_payload)
                
                if response.status_code == 200:
                    # El response.json() debería ser un array: [0] -> XML, [1] -> QR/PDF, [2] -> Method
                    data = response.json()
                    
                    return {
                        "success": True,
                        "data": {
                            "uuid": "UUID-EXTRAIDO-DEL-XML", # Requiere parsear el XML retornado para sacar el UUID
                            "xml_b64": data[0],
                            "pdf_b64": data[1] if len(data) > 1 else None,
                            "mensaje": "Timbrado exitoso"
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": response.json().get("ExceptionMessage", response.text)
                    }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
