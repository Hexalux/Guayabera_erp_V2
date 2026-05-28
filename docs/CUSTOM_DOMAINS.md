# Configuración de Dominios Personalizados para Tenants

## Introducción

En un sistema multitenant como Guayabera ERP Suite, es común que cada tenant (empresa cliente) quiera tener su propia URL personalizada para acceder al sistema. Esta personalización puede tomar dos formas principales:

1. Subdominios personalizados (ej. `empresa1.guayaberaerp.com`)
2. Dominios personalizados (ej. `erp.empresa1.com`)

## Configuración de Subdominios Personalizados

### Ventajas
- Implementación relativamente sencilla
- No requiere configuración DNS adicional por parte del cliente
- Menos costos de infraestructura
- Facilidad de mantenimiento

### Desventajas
- Menos profesional para grandes empresas
- Limitaciones en branding

### Implementación Técnica
1. Configurar el servidor web (Nginx/Apache) para capturar subdominios con comodines (`*.guayaberaerp.com`)
2. Extraer el subdominio de la solicitud HTTP
3. Identificar el tenant correspondiente en la base de datos
4. Aplicar la lógica de aislamiento multitenant

## Configuración de Dominios Personalizados

### Ventajas
- Mayor profesionalismo y branding
- Total control del cliente sobre su URL
- Mejor percepción para grandes empresas

### Desventajas
- Implementación más compleja
- Requiere configuración DNS por parte del cliente
- Posible sobrecarga de certificados SSL
- Mayor complejidad en mantenimiento

### Implementación Técnica

#### Paso 1: Gestión de dominios en la base de datos
```python
class TenantDomain(Base):
    __tablename__ = "tenant_domains"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    domain_name = Column(String, unique=True, index=True)
    is_primary = Column(Boolean, default=False)
    verified = Column(Boolean, default=False)
    verification_token = Column(String)
```

#### Paso 2: Middleware para resolución de dominios
```python
class DomainResolutionMiddleware:
    async def dispatch(self, request: Request, call_next):
        host = request.url.hostname
        
        # Buscar el dominio en la base de datos
        tenant_domain = await get_tenant_by_domain(host)
        
        if tenant_domain:
            # Asociar el tenant con la solicitud
            request.state.tenant = tenant_domain.tenant
        else:
            # Extraer tenant del subdominio o encabezado
            tenant_id = extract_tenant_from_subdomain(host)
            request.state.tenant = await get_tenant_by_id(tenant_id)
        
        response = await call_next(request)
        return response
```

#### Paso 3: Verificación de dominios
Para garantizar que un cliente realmente posee un dominio personalizado:

1. El cliente agrega un registro TXT o un archivo en su dominio con un token generado por el sistema
2. El sistema verifica la presencia de este token
3. Marca el dominio como verificado en la base de datos

## Consideraciones Técnicas Adicionales

### Certificados SSL
- Para subdominios: Un certificado wildcard es suficiente
- Para dominios personalizados: Se requiere soporte de SSL por SNI (Server Name Indication) y posiblemente Let's Encrypt para emitir certificados individuales

### Caché y CDNs
- Las reglas de caché deben considerar el tenant
- Los recursos estáticos deben estar disponibles para todos los dominios

### Redireccionamiento
- Considerar redirecciones de HTTP a HTTPS
- Redirección de dominios www a no-www (o viceversa)
- Redirección de dominio secundario al primario

## Recomendación para Guayabera ERP Suite

Dado el enfoque de Guayabera ERP Suite en el mercado latinoamericano, especialmente en la península de Yucatán, recomendamos:

1. **Implementar primero subdominios personalizados** como característica básica
2. **Ofrecer dominios personalizados como característica premium**
3. **Proporcionar una interfaz de administración** para que los administradores de tenants puedan gestionar sus dominios personalizados
4. **Implementar un proceso de verificación automático** para dominios personalizados
5. **Considerar integración con servicios de CDN** para mejorar el rendimiento global

## Conclusión

La implementación de dominios personalizados no es técnicamente imposible ni extremadamente complicada, pero sí requiere planificación cuidadosa y consideraciones de seguridad. La complejidad aumenta considerablemente al soportar dominios personalizados en comparación con subdominios, pero la funcionalidad puede ser un factor diferenciador importante en el mercado empresarial.

Con una arquitectura bien diseñada, es posible ofrecer ambas opciones a los clientes, comenzando con subdominios y ampliando a dominios personalizados según la demanda del mercado.