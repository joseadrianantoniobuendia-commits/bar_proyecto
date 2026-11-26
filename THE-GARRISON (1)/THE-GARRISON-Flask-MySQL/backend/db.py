"""Conexión MySQL del proyecto, siguiendo el patrón Flask del Taller 7."""

import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "garrison_app",
    "password": "",
    "database": "cantinadb",
    "charset": "utf8mb4",
    "autocommit": False,
}

try:
    from config_local import DB_CONFIG as LOCAL_DB_CONFIG
except ImportError:
    LOCAL_DB_CONFIG = {}

DB_CONFIG.update(LOCAL_DB_CONFIG)


def get_db_connection():
    """Abre una conexión nueva; las rutas deben cerrarla en su bloque finally."""
    if not DB_CONFIG["password"]:
        raise RuntimeError(
            "Falta configurar backend/config_local.py. Copia el archivo de ejemplo y agrega la clave MySQL."
        )
    return mysql.connector.connect(**DB_CONFIG)
