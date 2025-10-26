# Instrucciones para inicializar la base de datos

## Opción 1: Ejecutar desde tu máquina (RECOMENDADO)

### Paso 1: Obtener la URL pública de PostgreSQL

La URL que tenés en el `.env` usa `postgres.railway.internal`, que **solo funciona dentro de Railway**.

Para conectarte desde tu PC:

1. Andá a Railway → Tu proyecto → Servicio PostgreSQL
2. Click en **Connect** o **Variables**
3. Copiá la URL que dice **Public URL** o **Connection String**
   - Debe verse algo como: `postgresql://postgres:password@viaduct.proxy.rlwy.net:12345/railway`

### Paso 2: Actualizar el .env temporalmente

Editá el archivo `.env` y reemplazá la línea de `DATABASE_URL` con la URL pública:

```bash
DATABASE_URL=postgresql://postgres:JcxSNYeeWVIUjNJTRUkHxYdVbDYvOofY@viaduct.proxy.rlwy.net:XXXXX/railway
```

> **Nota:** El puerto y el host cambiarán según tu instancia de Railway.

### Paso 3: Ejecutar el script

```bash
python init_database.py
```

El script va a:
- Leer el `.env`
- Conectarse a PostgreSQL
- Ejecutar el schema de `docs/database-schema.sql`
- Crear las tablas `ledger_entries` y `bot_state`

---

## Opción 2: Ejecutar directamente con psql

Si tenés `psql` instalado (PostgreSQL client):

```bash
# Conectarte a la base
psql "postgresql://postgres:JcxSNYeeWVIUjNJTRUkHxYdVbDYvOofY@viaduct.proxy.rlwy.net:XXXXX/railway"

# Una vez conectado, ejecutar:
\i docs/database-schema.sql
```

---

## Opción 3: Copiar y pegar en Railway Query Editor

Si ninguna de las anteriores funciona, andá a Railway → PostgreSQL → **Data** → **Query** y pegá esto:

```sql
CREATE TABLE IF NOT EXISTS ledger_entries (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    ts BIGINT NOT NULL,
    date_iso VARCHAR(32) NOT NULL,
    amount BIGINT NOT NULL,
    currency VARCHAR(12) NOT NULL,
    category VARCHAR(128) NOT NULL,
    description TEXT DEFAULT '',
    payee VARCHAR(255) DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_ledger_chat_message UNIQUE (chat_id, message_id)
);

CREATE TABLE IF NOT EXISTS bot_state (
    key VARCHAR(64) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Luego click en **Run**.

---

## Verificar que las tablas se crearon

Ejecutá esta query en Railway o con psql:

```sql
\dt
```

Deberías ver:

```
Schema | Name            | Type  | Owner
-------+-----------------+-------+--------
public | ledger_entries  | table | postgres
public | bot_state       | table | postgres
```

---

## ⚠️ IMPORTANTE: Restaurar el .env para Railway

Después de ejecutar el script, **recordá volver a cambiar el `.env`** a la URL interna:

```bash
DATABASE_URL=postgresql://postgres:JcxSNYeeWVIUjNJTRUkHxYdVbDYvOofY@postgres.railway.internal:5432/railway
```

O mejor aún, **no uses el `.env` en Railway** y configurá las variables directamente en la UI de Railway (pestaña **Variables**).
