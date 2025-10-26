# 🚀 Deploy del Bot en Railway (Servidor 24/7 Gratuito)

Esta guía te explica cómo deployar el bot en Railway para que funcione 24/7 de forma gratuita.

> 💡 Para desplegar **Actual Budget (server + web)** junto al bot compartiendo la misma base PostgreSQL, seguí primero la guía [docs/railway-actual-budget.md](docs/railway-actual-budget.md) y luego continuá con los pasos de este documento.

## ✨ Ventajas de usar Railway

- ✅ **100% Gratuito** (500 horas/mes, suficiente para 24/7)
- ✅ **Bot siempre activo** - responde al instante
- ✅ **Menú interactivo funciona** perfectamente
- ✅ **Deploy en 5 minutos**
- ✅ **Logs en tiempo real**

---

## 📋 Pre-requisitos

1. **Cuenta de GitHub** (gratis)
2. **Cuenta de Railway** (gratis) → https://railway.app
3. **Bot de Telegram** ya creado (token de @BotFather)

---

## 🛠️ Paso 1: Preparar el repositorio en GitHub

### 1.1 Crear repositorio en GitHub

1. Ve a https://github.com/new
2. Nombre: `gastos-bot-telegram`
3. Privado o público (tu elección)
4. **NO agregues** README, .gitignore ni licencia (ya los tenés)
5. Click en **Create repository**

### 1.2 Subir el código a GitHub

Abrí la terminal en la carpeta `gastos-bot`:

```bash
# Inicializar git (si no lo hiciste ya)
git init

# Agregar todos los archivos
git add .

# Primer commit
git commit -m "Initial commit: Bot de gastos para Actual Budget"

# Conectar con GitHub (reemplazá TU_USUARIO)
git remote add origin https://github.com/TU_USUARIO/gastos-bot-telegram.git

# Subir el código
git branch -M main
git push -u origin main
```

---

## 🚂 Paso 2: Deploy en Railway

### 2.1 Crear cuenta en Railway

1. Andá a https://railway.app
2. Click en **Login with GitHub**
3. Autorizá Railway a acceder a tus repos

### 2.2 Crear nuevo proyecto

1. Click en **New Project**
2. Seleccioná **Deploy from GitHub repo**
3. Elegí `gastos-bot-telegram` (el repo que creaste)
4. Railway empieza a detectar el proyecto automáticamente

### 2.3 Configurar variables de entorno

Railway va a intentar deployar, pero **va a fallar** porque falta el token y las credenciales de base de datos. ¡Está bien!

1. En Railway, andá a la pestaña **Variables**
2. Cargá las siguientes variables mínimas:
   - `TELEGRAM_BOT_TOKEN`: Token que te dio BotFather.
   - `DATABASE_URL`: URL de PostgreSQL (idealmente la misma que usa Actual Budget).
   - `ACTUAL_BUDGET_API_URL`: URL pública del servicio `actual-server`.
   - `ACTUAL_BUDGET_BUDGET_ID` y `ACTUAL_BUDGET_ACCOUNT_ID`: IDs del presupuesto y la cuenta donde se guardarán los movimientos.
   - (Opcional) `ACTUAL_BUDGET_API_TOKEN` y `ACTUAL_BUDGET_ENCRYPTION_KEY` si tu servidor lo requiere.

**IMPORTANTE**: No es necesario subir `config.yaml` si preferís manejar todo por variables de entorno. El bot las interpreta automáticamente.

Recordá que también podés definir `DEFAULT_CURRENCY`, `TIMEZONE`, `CATEGORIES` y cualquier otro valor del `config.yaml` mediante variables.

### 2.4 Verificar que es Worker, no Web

Railway a veces detecta mal el tipo de servicio.

1. Andá a **Settings** → **Deploy**
2. Verificá que **Start Command** sea: `python main.py --server`
3. Si no está, agregalo manualmente

### 2.5 Re-deployar

1. Click en **Deploy** (arriba a la derecha)
2. Esperá 1-2 minutos
3. Andá a la pestaña **Logs**

Deberías ver:

```
============================================================
🤖 Bot de Gastos - Modo Servidor 24/7
============================================================
✅ Bot iniciado correctamente
⏰ 2025-01-15 14:30:00
📡 Esperando mensajes...
```

---

## ✅ Paso 3: Probar el bot

1. Abrí Telegram
2. Escribí `/start` a tu bot
3. Deberías ver el **menú con botones** al instante:

```
┌────────────────────────────┐
│ 💸 Nuevo Gasto │ 💰 Nuevo Ingreso │
│ 📊 Ver Categorías │ 📤 Exportar CSV │
│          ❓ Ayuda            │
└────────────────────────────┘
```

4. Click en "💸 Nuevo Gasto"
5. Seguí el wizard guiado

**¡Listo!** El bot está funcionando 24/7 🎉

---

## 📊 Ver logs en tiempo real

En Railway:
1. Click en tu proyecto
2. Pestaña **Logs**
3. Vas a ver cada mensaje que procesa en tiempo real

---

## 🔧 Actualizar el bot

Cuando hagas cambios en el código:

```bash
git add .
git commit -m "Descripción del cambio"
git push
```

Railway **re-deploya automáticamente** en ~1 minuto.

---

## 💰 Costos

Railway Free Tier:
- ✅ **500 horas/mes gratis** (suficiente para 24/7 = ~720 horas)
- ⚠️ Si superás las 500 horas, se pausa hasta el mes siguiente
- 💡 Podés upgradearlo a $5/mes para más horas (opcional)

---

## ❓ Troubleshooting

### El bot no responde

1. Verificá logs en Railway
2. Buscá errores rojos
3. Verificá que el token en `config.yaml` o variable de entorno sea correcto

### "Application failed to respond"

Esto es **normal** para un Worker (bot). Railway espera una app web, pero tu bot es un worker que hace polling. Ignorá este warning.

### "Out of memory"

El bot usa ~50MB de RAM. Si pasa esto:
1. Andá a Settings → Resources
2. Aumentá la memoria a 512MB (gratis)

### Quiero ver cuántos gastos tengo registrados

En Railway logs, vas a ver cada mensaje procesado.

También podés:
1. Ejecutar `/export` desde Telegram
2. Railway genera el CSV
3. Podés agregarlo a un volumen persistente si querés

---

## 🔄 Migrar de modo local a Railway

Si ya venías usando el modo local (`python main.py`), **no perdés datos**:

1. El `ledger.json` está en `data/` (gitignored)
2. Antes de pushear a GitHub, copiá `data/ledger.json`
3. Después del deploy, podés:
   - Usar Railway CLI para subir el archivo
   - O empezar de cero (los gastos viejos los tenés en tu PC)

---

## 📝 Notas importantes

- ✅ El bot funciona con **config.yaml** del repo o variables de entorno
- ✅ Los datos se guardan en Railway (pero se pierden si se re-deploya)
- ✅ Para persistencia, considerá usar Railway Volumes (gratis también)
- ✅ El modo local (`python main.py` sin `--server`) sigue funcionando

---

## 🎯 Próximos pasos

Una vez que el bot esté corriendo en Railway:

1. **Integración con Actual Budget**
   - Exportar CSV automáticamente
   - O conectar con la API de Actual

2. **Mejoras al bot**
   - Estadísticas mensuales
   - Gráficos de gastos
   - Recordatorios

3. **Backups automáticos**
   - Exportar `ledger.json` periódicamente
   - Enviar por Telegram o Google Drive

---

¿Algún problema? Revisá los logs en Railway o preguntame!
