# Bot de Telegram para Actual Budget

Bot de Telegram que te permite registrar gastos desde tu celular y sincronizarlos con Actual Budget sin costos de servidor.

## Características

- **Persistencia en PostgreSQL** (opcional): si definís `DATABASE_URL`, el bot guarda el ledger y el estado en la base (ideal para Railway).
- **Modo legado en archivos**: sin base de datos, sigue funcionando con `data/ledger.json` para pruebas locales.
- **Sincronización inmediata con Actual Budget**: cada gasto se envía automáticamente al servidor configurado.
- **Interfaz guiada**: el bot te guía paso a paso o podés usar comandos rápidos.
- **Categorías personalizables** y múltiples monedas configurables.
- **Exportación CSV** compatible con Actual Budget.

## Estructura del proyecto

```
gastos-bot/
├── docs/                    # Guías de despliegue y esquema SQL
├── requirements.txt         # Dependencias de Python
├── main.py                  # Punto de entrada del bot
├── src/
│   ├── bot.py               # Orquestador principal
│   ├── config/settings.py   # Manejo de configuración y env vars
│   ├── repositories/        # Persistencia (archivos o PostgreSQL)
│   ├── schemas.py           # Dataclasses compartidas
│   └── services/            # Servicios (Telegram, Actual Budget, etc.)
├── data/
│   ├── ledger.json          # Ledger local (solo modo legacy)
│   └── import_actual.csv    # Exportaciones CSV
└── README.md
```

## Instalación

### 1. Crear el bot en Telegram

1. Hablá con [@BotFather](https://t.me/BotFather) en Telegram
2. Enviá `/newbot` y seguí las instrucciones
3. Copiá el **token** que te da BotFather

### 2. Configurar el proyecto

1. Editá `config.yaml` y pegá tu token (o usá variables de entorno, ver sección "Configuración avanzada").

2. (Opcional) Personalizá las categorías en `config.yaml`.

### 3. Instalar dependencias

```bash
# Crear entorno virtual (recomendado)
python -m venv .venv

# Activar entorno virtual
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## Uso

### Desde Telegram

#### Modo guiado (recomendado para empezar):

```
Vos: /gasto
Bot: "Decime el monto (número)."
Vos: 2500
Bot: "Moneda? (predeterminado: ARS)"
Vos: ARS
Bot: "Elegí categoría:" [muestra teclado]
Vos: Comida
Bot: "Descripción (opcional, o /omitir):"
Vos: Empanadas
Bot: "Cargado ✅"
```

#### Modo rápido (una sola línea):

```
/gasto 2500 ARS Comida "Empanadas"
/ingreso 50000 ARS "Sueldo mensual"
```

#### Otros comandos:

- `/start` - Mensaje de bienvenida
- `/categorias` - Ver categorías disponibles
- `/export` - Generar CSV (también se puede hacer desde la PC)

### Sincronización desde la PC

Cuando prendés la PC, ejecutá:

```bash
python main.py
```

Esto procesará todos los mensajes pendientes y actualizará tu base de datos. Si no configuraste PostgreSQL, el bot seguirá escribiendo en `data/ledger.json`.

### Sincronización automática con Actual Budget

Si configurás las variables `ACTUAL_BUDGET_API_URL`, `ACTUAL_BUDGET_BUDGET_ID` y `ACTUAL_BUDGET_ACCOUNT_ID` (y opcionalmente el
token/encryption key), cada gasto registrado se envía a Actual Budget en el acto usando la API oficial.

- El monto se envía en **milliunits** (p. ej. `$ -2500` se transforma en `-2500000`).
- Se agrega un `importedId` con el formato `telegram:<chat_id>:<message_id>` para evitar duplicados si reenviás el mismo mensaje.
- Si completás el `payee_default` o escribís un pagador durante el flujo del bot, se usa como `payeeName`.
- El nombre de la categoría (`categoryName`) debe existir en Actual Budget; si no coincide se importará como `Sin categorizar`.

> 💡 Si tu versión del servidor no soporta el endpoint `/import-transactions`, el bot hace fallback automático al endpoint
> `/transactions` clásico.

### Exportar manualmente a CSV

Si preferís el modo tradicional, `/export` sigue generando `data/import_actual.csv` con el formato:

```csv
Date,Payee,Category,Notes,Amount
2025-01-15,,"Comida","Empanadas",-2500
```

Luego importalo desde la UI de Actual Budget con **Import → CSV**.

## Configuración avanzada

### config.yaml

```yaml
bot_token: "TU_TOKEN"
default_currency: "ARS"                    # Moneda por defecto
timezone: "America/Argentina/Buenos_Aires" # Tu zona horaria
categories:
  - Comida
  - Supermercado
  - Transporte
payee_default: ""

# Opcional: configura endpoints de Actual Budget y base de datos
database_url: "postgresql://usuario:pass@host:5432/actual"
actual_budget:
  api_url: "https://actual-server.production.up.railway.app/"
  api_token: "TOKEN_OPCIONAL"
  budget_id: "<uuid-del-presupuesto>"
  account_id: "<uuid-de-la-cuenta>"
  encryption_key: "<clave-si-tu-servidor-lo-requiere>"
```

### Agregar categorías

Editá `config.yaml` y agregá líneas en la sección `categories`:

```yaml
categories:
  - Comida
  - Supermercado
  - MiNuevaCategoria  # ← agregá acá
```

### Cambiar timezone

Buscá tu timezone en [esta lista](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) y actualizá `config.yaml`:

```yaml
timezone: "America/Buenos_Aires"  # o tu zona
```

## Formato de datos

### ledger.json (modo legacy)
Si no configurás PostgreSQL, el bot crea `data/ledger.json` con todos los movimientos:

```json
[
  {
    "chat_id": 123456789,
    "message_id": 42,
    "user_id": 123456789,
    "ts": 1705334400,
    "date_iso": "2025-01-15 14:30",
    "amount": -2500,
    "currency": "ARS",
    "category": "Comida",
    "description": "Empanadas",
    "payee": ""
  }
]
```

### import_actual.csv
Formato para importar manualmente en Actual Budget:

```csv
Date,Payee,Category,Notes,Amount
2025-01-15,,Comida,Empanadas,-2500
```

**Nota:** Los gastos son negativos, los ingresos positivos.

## Despliegue gestionado

La guía [docs/railway-actual-budget.md](docs/railway-actual-budget.md) detalla cómo desplegar Actual Budget (server + web) y este bot en Railway compartiendo una misma base PostgreSQL.

## Tips y trucos

- **Ejecución automática**: podés agregar `python main.py` a un script de inicio de tu PC
- **Backup**: `data/ledger.json` es tu histórico completo, hacele backup periódicamente
- **Múltiples usuarios**: el bot soporta varios usuarios simultáneamente
- **Ediciones**: si editás un mensaje en Telegram después de enviarlo, NO se procesará de nuevo (previene duplicados)

## Solución de problemas

### El bot no responde
- Verificá que el token en `config.yaml` sea correcto
- Asegurate de que haya conexión a internet
- Revisá que el bot NO esté bloqueado en Telegram

### Error al importar CSV en Actual
- Verificá que el archivo `data/import_actual.csv` exista
- Asegurate de que las columnas estén mapeadas correctamente
- Los montos deben ser números (sin símbolos de moneda)

### Los timestamps están mal
- Revisá el `timezone` en `config.yaml`
- Actualizá la librería: `pip install --upgrade python-dateutil`

## Próximas mejoras

- [ ] Soporte para adjuntar fotos de tickets
- [ ] Estadísticas mensuales desde el bot
- [ ] Búsqueda de gastos anteriores
- [ ] Recordatorios automáticos
- [ ] Integración directa con Actual Budget API (cuando esté disponible)

## Licencia

Proyecto personal de código abierto. Usalo, modificalo y compartilo libremente.

---

**¿Preguntas o sugerencias?** Abrí un issue en el repositorio.
