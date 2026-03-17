import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def get_db():
    """Get database connection with better error handling."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            autocommit=False,
            charset='utf8mb4',
            use_unicode=True,
            connect_timeout=10,
            raise_on_warnings=False
        )        
        if connection.is_connected():
            return connection
        else:
            raise mysql.connector.Error("Connection not established")
            
    except mysql.connector.Error as e:
        error_msg = f"Database connection error: {e}"
        
        if hasattr(e, 'errno'):
            if e.errno == 1045:
                error_msg = "Database authentication failed - check username/password in .env file"
            elif e.errno == 2003:
                error_msg = "Cannot connect to MySQL server - check if MySQL is running"
            elif e.errno == 1049:
                error_msg = f"Database '{os.getenv('DB_NAME')}' does not exist"
            elif e.errno == 1146:
                error_msg = "Required database tables are missing"
        
        print(f"❌ {error_msg}")
        raise Exception("Database connection issue. Please try again.")
        
    except Exception as e:
        print(f"❌ Unexpected database error: {e}")
        raise Exception("Database connection issue. Please try again.")
