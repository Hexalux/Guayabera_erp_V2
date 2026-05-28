# Manual de instalacion y arranque desde cero

Este manual describe como levantar Guayabera ERP v2 desde un entorno limpio usando Docker, y tambien incluye una ruta opcional para desarrollo local.

## 1. Requisitos

Instala o verifica que tengas:

- Git
- Docker Desktop con Docker Compose
- Node.js 18 o superior, solo si vas a correr el frontend fuera de Docker
- Python 3.11, solo si vas a correr el backend fuera de Docker

## 2. Entrar al proyecto

Desde PowerShell:

```powershell
cd C:\Users\Choripapa\Documents\Proyectos\Guayabera-QWEN\guayabera-erp-v2
```

## 3. Variables principales

El proyecto ya incluye archivos `.env` para desarrollo local:

- Backend: `backend/.env`
- Frontend: `frontend/.env`

Valores importantes:

```text
Backend API: http://localhost:8000
Frontend: http://localhost:3000
PostgreSQL local: localhost:5435
Redis local: localhost:6381
API base para frontend: http://localhost:8000/api/v1
```

Usuario inicial de superadministrador:

```text
Email: admin@guayabera-erp.com
Password: admin123
```

## 4. Levantar todo con Docker

Para un primer arranque normal:

```powershell
docker compose up -d --build
```

Revisa que los contenedores esten arriba:

```powershell
docker compose ps
```

Servicios esperados:

- `guayabera-erp-v2-db`
- `guayabera-erp-v2-redis`
- `guayabera-erp-v2-backend`
- `guayabera-erp-v2-frontend`

## 5. Arranque completamente limpio

Usa esto cuando quieras borrar la base de datos de desarrollo y recrear todo desde cero.

Advertencia: `docker compose down -v` elimina los volumenes, incluyendo los datos de PostgreSQL.

```powershell
docker compose down -v
docker compose build --no-cache backend frontend
docker compose up -d
```

Si solo quieres reiniciar sin borrar datos:

```powershell
docker compose down
docker compose up -d --build
```

## 6. URLs utiles

Cuando todo este arriba:

- Frontend: http://localhost:3000
- Backend health check: http://localhost:8000/health
- Swagger / API docs: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/api/v1/openapi.json

## 7. Verificar login del superadministrador

Desde PowerShell:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/v1/auth/login `
  -ContentType 'application/json' `
  -Body '{"email":"admin@guayabera-erp.com","password":"admin123"}'
```

La respuesta correcta debe incluir:

```text
access_token
token_type
user
```

Despues abre el frontend:

```text
http://localhost:3000
```

Inicia sesion con:

```text
admin@guayabera-erp.com / admin123
```

## 8. Ver logs

Backend:

```powershell
docker compose logs -f backend
```

Frontend:

```powershell
docker compose logs -f frontend
```

Base de datos:

```powershell
docker compose logs -f postgres
```

Redis:

```powershell
docker compose logs -f redis
```

## 9. Problemas comunes

### El frontend muestra `Cannot read properties of undefined (reading 'data')`

Esto suele indicar que el navegador o el contenedor esta usando una version vieja del frontend.

Ejecuta:

```powershell
docker compose build --no-cache frontend
docker compose up -d --force-recreate frontend
```

Luego recarga el navegador con cache limpia.

### Docker falla con `ERESOLVE` entre `react-scripts` y TypeScript

`react-scripts@5.0.1` es compatible con TypeScript 4.x. El proyecto debe mantenerse con:

```text
typescript: ^4.9.5
```

Si aparece un error como `peerOptional typescript "^3.2.1 || ^4" from react-scripts@5.0.1`, reinstala dependencias y reconstruye:

```powershell
cd C:\Users\Choripapa\Documents\Proyectos\Guayabera-QWEN\guayabera-erp-v2\frontend
npm install

cd C:\Users\Choripapa\Documents\Proyectos\Guayabera-QWEN\guayabera-erp-v2
docker compose build frontend
docker compose up -d frontend
```

Si agregaste o cambiaste dependencias del frontend y Docker sigue usando `node_modules` viejo, recrea el volumen anonimo del servicio:

```powershell
docker compose up -d --build --force-recreate -V frontend
```

### Error relacionado con `bcrypt` o `passlib`

El backend debe usar `bcrypt==4.0.1`, definido en `backend/requirements.txt`.

Reconstruye el backend sin cache:

```powershell
docker compose build --no-cache backend
docker compose up -d --force-recreate backend
```

### Login falla aunque los contenedores estan arriba

Primero prueba el login directo contra la API:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/v1/auth/login `
  -ContentType 'application/json' `
  -Body '{"email":"admin@guayabera-erp.com","password":"admin123"}'
```

Si falla, revisa logs del backend:

```powershell
docker compose logs -f backend
```

Si sospechas que la base de datos quedo con datos antiguos, reinicia desde cero:

```powershell
docker compose down -v
docker compose up -d --build
```

### Puertos ocupados

El proyecto usa estos puertos:

- Frontend: `3000`
- Backend: `8000`
- PostgreSQL: `5435`
- Redis: `6381`

Para revisar si estan ocupados:

```powershell
netstat -ano | Select-String ':3000|:8000|:5435|:6381'
```

### El frontend apunta a otro backend

Verifica `frontend/.env`:

```text
REACT_APP_API_URL=http://localhost:8000/api/v1
```

Despues de cambiar variables de React, reinicia el frontend:

```powershell
docker compose restart frontend
```

## 10. Desarrollo local opcional

Esta ruta es util cuando quieres correr PostgreSQL y Redis en Docker, pero backend/frontend directo en tu maquina.

### 10.1 Levantar solo PostgreSQL y Redis

```powershell
docker compose up -d postgres redis
```

### 10.2 Backend local

```powershell
cd C:\Users\Choripapa\Documents\Proyectos\Guayabera-QWEN\guayabera-erp-v2\backend
```

Si ya existe el entorno virtual:

```powershell
.\venv\Scripts\Activate.ps1
```

Si no existe:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Instala dependencias:

```powershell
pip install -r requirements.txt
```

Arranca el backend:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 10.3 Frontend local

En otra terminal:

```powershell
cd C:\Users\Choripapa\Documents\Proyectos\Guayabera-QWEN\guayabera-erp-v2\frontend
npm install
npm start
```

El frontend quedara disponible en:

```text
http://localhost:3000
```

## 11. Comandos de verificacion antes de migrar modulos

Backend:

```powershell
cd C:\Users\Choripapa\Documents\Proyectos\Guayabera-QWEN\guayabera-erp-v2\backend
.\venv\Scripts\python.exe -m compileall app
```

Frontend:

```powershell
cd C:\Users\Choripapa\Documents\Proyectos\Guayabera-QWEN\guayabera-erp-v2\frontend
npx tsc --noEmit --pretty false
npm run build
```

API smoke test:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/v1/auth/login `
  -ContentType 'application/json' `
  -Body '{"email":"admin@guayabera-erp.com","password":"admin123"}'
```

Checklist minimo antes de migrar otro modulo:

- `docker compose ps` muestra servicios activos.
- `http://localhost:8000/health` responde correctamente.
- Login del superadministrador responde `access_token`, `token_type` y `user`.
- Frontend compila con `npm run build`.
- TypeScript pasa con `npx tsc --noEmit --pretty false`.
- El login desde `http://localhost:3000` entra al panel correspondiente.
