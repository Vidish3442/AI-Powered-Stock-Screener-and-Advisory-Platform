"""
Database connection for ingestion scripts.
Connects to TiDB Cloud using SSL.
Reads config from .env.tidb file.
"""

import mysql.connector
import os
from pathlib import Path
from dotenv import load_dotenv

# Load TiDB-specific env file
_base = Path(__file__).resolve().parent.parent
load_dotenv(_base / ".env.tidb")

def get_db():
    """Get TiDB Cloud database connection with SSL."""
    host     = os.getenv("TIDB_HOST")
    port     = int(os.getenv("TIDB_PORT", 4000))
    user     = os.getenv("TIDB_USER")
    password = os.getenv("TIDB_PASSWORD")
    database = os.getenv("TIDB_DB", "stock_db")
    ssl_ca   = os.getenv("TIDB_CA")

    if not host or not user or not password:
        raise ValueError(
            "Missing TiDB config. Ensure TIDB_HOST, TIDB_USER, TIDB_PASSWORD are set in .env.tidb"
        )

    # Resolve CA cert path — try relative to project root, then absolute, then skip
    if ssl_ca:
        candidate = _base / ssl_ca          # e.g.  project/.certs/isrgrootx1.pem
        if candidate.exists():
            ssl_ca = str(candidate)
        elif Path(ssl_ca).exists():          # already absolute
            ssl_ca = str(Path(ssl_ca))
        else:
            # In CI the cert is written by the workflow step; if missing, connect
            # without cert verification (still TLS-encrypted, just no chain check)
            print(f"⚠️  CA cert not found at '{ssl_ca}' — connecting without cert verification")
            ssl_ca = None

    try:
        conn_kwargs = {
            "host":             host,
            "port":             port,
            "user":             user,
            "password":         password,
            "database":         database,
            "autocommit":       False,
            "charset":          "utf8mb4",
            "use_unicode":      True,
            "connect_timeout":  30,
            "raise_on_warnings": False,
        }

        if ssl_ca:
            conn_kwargs["ssl_ca"]              = ssl_ca
            conn_kwargs["ssl_verify_cert"]     = True
            conn_kwargs["ssl_verify_identity"] = True
        else:
            conn_kwargs["ssl_disabled"] = False   # still encrypted, no cert check

        connection = mysql.connector.connect(**conn_kwargs)

        if connection.is_connected():
            server_info = connection.get_server_info()
            print(f"✅ Connected to TiDB Cloud  ({host}:{port})  server={server_info}")
            return connection

        raise mysql.connector.Error("Connection established but is_connected() is False")

    except mysql.connector.Error as e:
        msg = str(e)
        if hasattr(e, "errno"):
            if e.errno == 1045:
                msg = "Auth failed — check TIDB_USER / TIDB_PASSWORD in .env.tidb"
            elif e.errno == 2003:
                msg = f"Cannot reach TiDB host '{host}' — check TIDB_HOST in .env.tidb"
            elif e.errno == 1049:
                msg = f"Database '{database}' does not exist on TiDB Cloud"
        print(f"❌ TiDB connection error: {msg}")
        raise

    except Exception as e:
        print(f"❌ Unexpected error connecting to TiDB Cloud: {e}")
        raise
