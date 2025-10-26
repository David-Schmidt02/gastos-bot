# Bot de Telegram para Actual Budget

Bot de Telegram que te permite registrar gastos desde tu celular y sincronizarlos con Actual Budget sin costos de servidor.

## Características

- **Sin servidor**: funciona con polling local, solo se ejecuta cuando prendés la PC
- **Interfaz guiada**: el bot te guía paso a paso o podés usar comandos rápidos
- **Categorías personalizables**: definidas en `config.yaml`
- **Exportación a CSV**: formato compatible con Actual Budget
- **Múltiples monedas**: soporte para ARS, USD, EUR y más
- **Timezone configurable**: timestamps en tu zona horaria

## Estructura del proyecto

```
gastos-bot/
├── config.yaml              # Configuración (token, categorías, etc.)
├── state.json               # Estado del bot (se crea automáticamente)
├── requirements.txt         # Dependencias de Python
├── main.py                  # Script principal de sincronización
├── parser.py                # Parser de comandos y validaciones
├── export_actual.py         # Generador de CSV para Actual Budget
├── data/
│   ├── ledger.json         # Base de datos local (histórico)
│   └── import_actual.csv   # CSV para importar en Actual
└── README.md
```

## Instalación

### 1. Crear el bot en Telegram

1. Hablá con [@BotFather](https://t.me/BotFather) en Telegram
2. Enviá `/newbot` y seguí las instrucciones
3. Copiá el **token** que te da BotFather

### 2. Configurar el proyecto

1. Editá `config.yaml` y pegá tu token:
```yaml
bot_token: "TU_TOKEN_AQUI"
```

2. (Opcional) Personalizá las categorías en `config.yaml`

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

Esto procesará todos los mensajes pendientes y actualizará `data/ledger.json`.

### Exportar a Actual Budget

#### Opción 1: Desde Telegram
Enviá `/export` al bot y el CSV se generará automáticamente.

#### Opción 2: Desde la PC
```bash
python export_actual.py
```

Esto genera `data/import_actual.csv` con el formato:
```csv
Date,Payee,Category,Notes,Amount
2025-01-15,,"Comida","Empanadas",-2500
```

### Importar en Actual Budget

1. Abrí Actual Budget
2. Andá a la cuenta donde querés importar
3. Click en **Import** → **CSV**
4. Seleccioná `data/import_actual.csv`
5. Mapeá las columnas (Actual lo recuerda para la próxima)
6. Listo!

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
  # ... agregá las que quieras
payee_default: ""  # Dejalo vacío o escribí un nombre
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

### ledger.json
Base de datos local con todos los movimientos:

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
Formato para importar en Actual Budget:

```csv
Date,Payee,Category,Notes,Amount
2025-01-15,,Comida,Empanadas,-2500
```

**Nota:** Los gastos son negativos, los ingresos positivos.

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
