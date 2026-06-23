import mysql.connector
import os
import certifi
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Only load .env for the backend — never .env.tidb (that is ingestion-only).
# .env.tidb is intentionally excluded so the backend always uses local/configured DB.
load_dotenv(PROJECT_ROOT / ".env")


def _database_config():
    """Build a local MySQL or certificate-verified TiDB configuration."""
    target = os.getenv("DB_TARGET", "local").strip().lower()
    prefix = "TIDB_" if target == "tidb" else "DB_"

    required = {
        "host": os.getenv(f"{prefix}HOST"),
        "user": os.getenv(f"{prefix}USER"),
        "password": os.getenv(f"{prefix}PASSWORD"),
        "database": os.getenv(f"{prefix}NAME", "stock_db"),
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(
            f"Missing {target} database configuration: {', '.join(missing)}"
        )

    config = {
        **required,
        "port": int(os.getenv(f"{prefix}PORT", "4000" if target == "tidb" else "3306")),
        "autocommit": False,
        "charset": "utf8mb4",
        "use_unicode": True,
        "connect_timeout": 10,
        "raise_on_warnings": False,
    }

    if target == "tidb":
        ca_value = os.getenv("TIDB_CA")
        ca_path = Path(ca_value) if ca_value else Path(certifi.where())
        if ca_value and not ca_path.is_absolute():
            ca_path = PROJECT_ROOT / ca_path
        if not ca_path.is_file():
            raise RuntimeError("TiDB CA certificate file was not found")

        config.update(
            ssl_ca=str(ca_path),
            ssl_verify_cert=True,
            ssl_verify_identity=True,
        )

    return config

def get_db():
    """Get database connection with better error handling."""
    try:
        connection = mysql.connector.connect(**_database_config())
        if connection.is_connected():
            return connection
        else:
            raise mysql.connector.Error("Connection not established")
            
    except mysql.connector.Error as e:
        error_msg = f"Database connection error: {e}"
        
        if hasattr(e, 'errno'):
            if e.errno == 1045:
                error_msg = "Database authentication failed - check the configured username/password"
            elif e.errno == 2003:
                error_msg = "Cannot connect to the database server - check host, network, and IP access"
            elif e.errno == 1049:
                error_msg = "The configured database does not exist"
            elif e.errno == 1146:
                error_msg = "Required database tables are missing"
        
        print(f"[database error] {error_msg}")
        raise Exception("Database connection issue. Please try again.")
        
    except Exception as e:
        print(f"[database error] Unexpected database error: {e}")
        raise Exception("Database connection issue. Please try again.")
