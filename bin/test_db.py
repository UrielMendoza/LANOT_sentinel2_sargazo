#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prueba la conexion a la base de datos usando las credenciales de base.py
Uso: python3 test_db.py
"""
import psycopg2
import base

print(f"Conectando a {base.DB_host}:{base.DB_port} / db={base.DB_name} / user={base.DB_user} ...")

try:
    conect = psycopg2.connect(
        host     = base.DB_host,
        database = base.DB_name,
        user     = base.DB_user,
        password = base.DB_password,
        port     = base.DB_port,
        connect_timeout = 10
    )
    cur = conect.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()
    print(f"Conexion exitosa.")
    print(f"PostgreSQL: {version[0]}")
    cur.close()
    conect.close()
except psycopg2.OperationalError as e:
    print(f"Error de conexion: {e}")
except Exception as e:
    print(f"Error inesperado: {e}")
