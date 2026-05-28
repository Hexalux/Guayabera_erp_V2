# Configuración del Entorno Virtual del Backend

Sigue estos pasos para crear y configurar correctamente tu entorno virtual para el backend de Guayabera ERP Suite.

## Opción 1: Usando el script automatizado (Recomendado)

### En Windows:
1. Ejecuta el archivo `setup_env.bat` como administrador
2. El script hará lo siguiente:
   - Eliminará cualquier entorno virtual existente
   - Creará un nuevo entorno virtual
   - Activará el entorno virtual
   - Instalará todas las dependencias desde requirements.txt

### En Linux/Mac:
1. Abre la terminal en este directorio
2. Ejecuta: `chmod +x setup_env.sh && ./setup_env.sh`
3. El script hará lo siguiente:
   - Eliminará cualquier entorno virtual existente
   - Creará un nuevo entorno virtual
   - Activará el entorno virtual
   - Instalará todas las dependencias desde requirements.txt

## Opción 2: Manualmente

### 1. Crear el entorno virtual
```bash
# En Windows
python -m venv venv

# En Linux/Mac
python3 -m venv venv
```

### 2. Activar el entorno virtual
```bash
# En Windows
venv\Scripts\activate

# En Linux/Mac
source venv/bin/activate
```

### 3. Actualizar pip
```bash
pip install --upgrade pip
```

### 4. Instalar las dependencias
```bash
pip install -r requirements.txt
```

## Verificar la instalación

Después de completar cualquiera de los métodos anteriores, puedes verificar que todo esté instalado correctamente ejecutando:

```bash
# Verificar que FastAPI esté instalado
python -c "import fastapi; print(fastapi.__version__)"

# Verificar que SQLAlchemy esté instalado
python -c "import sqlalchemy; print(sqlalchemy.__version__)"

# Verificar que las principales dependencias estén instaladas
python -c "
import fastapi, sqlalchemy, pydantic, uvicorn, jwt, passlib, celery, redis, psycopg2, alembic, pydantic_settings
print('Todas las dependencias principales están instaladas correctamente')
"
```

## Activar el entorno virtual en sesiones futuras

Cada vez que abras una nueva terminal para trabajar en el proyecto, deberás activar el entorno virtual:

```bash
# En Windows
venv\Scripts\activate

# En Linux/Mac
source venv/bin/activate
```

## Iniciar el servidor de desarrollo

Una vez que el entorno virtual esté activado y las dependencias estén instaladas, puedes iniciar el servidor:

```bash
# Desde el directorio backend/app
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

## Solución de problemas comunes

### Problema: "No module named 'uvicorn'"
Solución: Asegúrate de que el entorno virtual esté activado y que hayas instalado las dependencias con `pip install -r requirements.txt`

### Problema: Permisos en Windows al ejecutar scripts
Solución: Ejecuta PowerShell como administrador y ejecuta:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Problema: Error de instalación psycopg2 en Windows
Solución: Instala el Microsoft C++ Build Tools o instala psycopg2-binary en su lugar:
```bash
pip install psycopg2-binary
```