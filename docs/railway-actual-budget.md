# Guía de despliegue gestionado (Railway) para Actual Budget + Bot

Esta guía describe la arquitectura recomendada para ejecutar Actual Budget (server + web) y el bot de Telegram utilizando servicios administrados en Railway. Incluye la creación de una base de datos PostgreSQL compartida entre ambos componentes y el registro de las variables sensibles necesarias.

> **Importante:** Desde este repositorio no se pueden ejecutar comandos contra Railway. Los pasos siguientes deben realizarse desde tu cuenta de Railway utilizando su interfaz web o la CLI oficial.

## 1. Crear el proyecto en Railway

1. Iniciá sesión en [Railway](https://railway.app) con tu cuenta de GitHub.
2. Creá un nuevo proyecto vacío.

Dentro del proyecto vamos a desplegar tres servicios:

| Servicio | Descripción | Plantilla |
|----------|-------------|-----------|
| `actual-server` | API Node.js de Actual Budget (`server` en la documentación oficial). | Deploy desde repositorio oficial o imagen Docker `actualbudget/actual-server`. |
| `actual-web` | Frontend estático (React) de Actual Budget (`web`). | Deploy estático desde el build del repo oficial o usando la imagen `actualbudget/actual-web`. |
| `gastos-bot` | Este bot de Telegram ejecutándose como worker Python. | Conectar con este repositorio. |

## 2. Aprovisionar PostgreSQL

1. Dentro del proyecto, seleccioná **New → Database → PostgreSQL**.
2. Railway creará la instancia y expondrá la variable `DATABASE_URL`. Renombrala a `ACTUAL_BUDGET_DATABASE_URL` para distinguirla del bot.
3. Creá un duplicado de la URL para el bot:
   - Variable: `DATABASE_URL`
   - Valor: mismo que `ACTUAL_BUDGET_DATABASE_URL`

De esta forma tanto Actual Budget como el bot comparten la misma base de datos.

### 2.1. Inicializar el esquema del bot

Ejecutá el siguiente script desde la consola SQL de Railway (o usando `psql`):

```sql
\i docs/database-schema.sql
```

Esto creará las tablas `ledger_entries` y `bot_state` que utiliza el bot.

## 3. Configurar Actual Budget

### 3.1 Variables sensibles

Antes de desplegar, prepará las siguientes variables para el servicio `actual-server`:

| Variable | Descripción |
|----------|-------------|
| `ACTUAL_SERVER_PORT` | Puerto de escucha (por ejemplo `5006`). Railway inyecta también `PORT`; podés reutilizarlo para mantener los contenedores sincronizados. |
| `DATABASE_URL` | Usa el valor de `ACTUAL_BUDGET_DATABASE_URL`. |
| `ENCRYPTION_KEY` | Clave de cifrado para los archivos sincronizados (genera una cadena de 64 caracteres aleatorios). |
| `SECRET_KEY` | Secreto para sesiones JWT del servidor. |
| `SYNC_URL` | URL pública del frontend (`https://<tu-subdominio>.up.railway.app`). |

> Consultá la documentación oficial de Actual Budget para valores adicionales opcionales (`ADMIN_PASSWORD`, `ACTUAL_HOST`, etc.).

### 3.2 Desplegar `actual-server`

1. En el proyecto de Railway hacé clic en **New → Deploy Image**.
2. Ingresá `actualbudget/actual-server` como nombre de la imagen y confirmá con **Deploy**.
3. Una vez creado el servicio, abrí la pestaña **Variables** y cargá todas las claves listadas en el punto anterior. Si Railway ya creó `PORT`, copiá su valor en `ACTUAL_SERVER_PORT` para evitar conflictos.
4. En **Settings → Networking** verificá que esté habilitado **Generate Domain** para exponer la API públicamente.
5. Guardá la URL pública del dominio generado; la vas a usar tanto en el frontend como en el bot (`ACTUAL_BUDGET_API_URL`).

> Si preferís desplegar desde el repositorio oficial, podés usar la opción **Deploy from GitHub Repo** apuntando a `actualbudget/actual-server`. Railway detecta el `Dockerfile` y crea la imagen automáticamente.

### 3.3 Desplegar `actual-web`

1. Repetí **New → Deploy Image** pero esta vez usando `actualbudget/actual-web`.
2. En **Variables** añadí `VITE_SERVER_URL` apuntando a la URL pública del servicio `actual-server` (por ejemplo `https://actual-server-production.up.railway.app`).
3. Railway expone el servicio como sitio estático; verificá en **Settings → Networking** que tenga un dominio público habilitado.
4. Abrí esa URL en el navegador y completá el onboarding inicial de Actual Budget para generar el presupuesto y las cuentas.

> Alternativa: si necesitás personalizar el frontend, generá un build propio con `yarn build` desde el repo oficial y desplegalo como servicio **Static** en Railway. Recordá definir igualmente `VITE_SERVER_URL`.

## 4. Configurar el bot de gastos

En el servicio `gastos-bot`, además de `TELEGRAM_BOT_TOKEN`, añadí:

| Variable | Valor |
|----------|-------|
| `DATABASE_URL` | URL de PostgreSQL (misma que Actual Budget). |
| `ACTUAL_BUDGET_API_URL` | URL pública del servicio `actual-server` (por ejemplo `https://actual-server-production.up.railway.app`). |
| `ACTUAL_BUDGET_API_TOKEN` | Token Bearer configurado en Actual Budget (si habilitaste autenticación). |
| `ACTUAL_BUDGET_BUDGET_ID` | ID del presupuesto destino (obtenelo desde la UI o API de Actual). |
| `ACTUAL_BUDGET_ACCOUNT_ID` | ID de la cuenta donde registrar los movimientos (UUID). |
| `ACTUAL_BUDGET_ENCRYPTION_KEY` | Misma clave configurada en el servidor (necesaria para cifrado de payloads en algunas instalaciones). |

> Si el servidor de Actual Budget no requiere token, podés dejar `ACTUAL_BUDGET_API_TOKEN` vacío.

## 5. Validar la instalación

1. Accedé a la URL del servicio `actual-web` y completá la configuración inicial (crear usuario, presupuesto y cuenta).
2. Obtené los UUID desde la consola de Actual (`Cuenta → ... → Copy ID`).
3. Registrá un gasto desde el bot de Telegram.
4. Verificá en la interfaz web que la transacción aparece asociada al presupuesto y cuenta configurados.
5. Revisá los logs del bot en Railway para confirmar que la sincronización reporta `Transacción sincronizada con Actual Budget`.

> ✅ El bot intenta primero el endpoint `/import-transactions` y, si la versión del server no lo ofrece, hace fallback automático a `/transactions`.

## 6. Buenas prácticas

- **Backups:** Configurá backups automáticos de la base PostgreSQL desde Railway o exportando dumps periódicos.
- **Rotación de claves:** Regenerá `SECRET_KEY` y `ENCRYPTION_KEY` ante cualquier sospecha de filtración.
- **Variables de entorno:** Nunca publiques estos valores en repositorios públicos. Railway permite marcarlos como `private`.
- **Monitorización:** Usa la pestaña *Metrics* para asegurarte de que los contenedores no exceden los límites del plan gratuito.

Con esta configuración, el bot y Actual Budget comparten una única base de datos gestionada, permitiendo que las transacciones registradas desde Telegram se reflejen inmediatamente en la interfaz web.
