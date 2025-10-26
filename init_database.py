#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para inicializar el esquema de la base de datos.
Ejecutar: python init_database.py
"""
import os
import sys
from pathlib import Path

# Fix para Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

try:
    import psycopg2
except ImportError:
    print("[ERROR] psycopg2 no esta instalado")
    print("Instala las dependencias: pip install psycopg2-binary")
    sys.exit(1)

# Cargar variables de entorno desde .env si existe
env_file = Path(".env")
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

# Obtener DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("[ERROR] DATABASE_URL no esta definida")
    print("Asegurate de tener un archivo .env con la variable DATABASE_URL")
    sys.exit(1)

# Reemplazar postgres.railway.internal por el host público si es necesario
if "railway.internal" in DATABASE_URL:
    print("[AVISO] Detecte 'railway.internal' en la URL.")
    print("   Para conectarte desde tu maquina local, necesitas la URL publica de Railway.")
    print("   Anda a Railway -> PostgreSQL -> Connect -> Public URL")
    print()
    public_url = input("Pega la URL publica aqui (o Enter para usar la interna): ").strip()
    if public_url:
        DATABASE_URL = public_url

# Leer el schema SQL
schema_file = Path("docs/database-schema.sql")
if not schema_file.exists():
    print(f"[ERROR] No se encontro {schema_file}")
    sys.exit(1)

with open(schema_file, "r", encoding="utf-8") as f:
    schema_sql = f.read()

# Ejecutar el schema
print("[INFO] Conectando a la base de datos...")
try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    print("[INFO] Ejecutando schema SQL...")
    cursor.execute(schema_sql)
    conn.commit()

    print("[EXITO] Schema creado exitosamente!")
    print()
    print("Tablas creadas:")
    print("  - ledger_entries (gastos registrados)")
    print("  - bot_state (estado del bot)")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"[ERROR] Error al ejecutar el schema: {e}")
    sys.exit(1)
