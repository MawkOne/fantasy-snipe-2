import os
import sys
import certifi

# Set SSL_CERT_FILE to the certifi bundle
os.environ['SSL_CERT_FILE'] = certifi.where()

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.cloud.sql.connector import Connector
import sqlalchemy
from src.config import INSTANCE_CONNECTION_NAME, DB_USER, DB_PASS, DB_NAME

def connect_with_connector() -> sqlalchemy.engine.base.Engine:
    """
    Initializes a connection pool for a Cloud SQL instance of PostgreSQL.
    Uses the Cloud SQL Python Connector package.
    """
    # Prefer explicit DATABASE_URLs if provided (bypass connector)
    db_url = os.getenv("NHL_DATABASE_URL") or os.getenv("DATABASE_URL")
    if db_url:
        try:
            return sqlalchemy.create_engine(db_url, pool_pre_ping=True)
        except Exception:
            pass
    connector = Connector()

    def getconn():
        conn = connector.connect(
            INSTANCE_CONNECTION_NAME,
            "pg8000",
            user=DB_USER,
            password=DB_PASS,
            db=DB_NAME,
            # Instance has only a private IP; requires Serverless VPC Connector from Cloud Run
            ip_type="private"
        )
        return conn

    pool = sqlalchemy.create_engine(
        "postgresql+pg8000://",
        creator=getconn,
    )
    return pool

if __name__ == "__main__":
    engine = connect_with_connector()
    with engine.connect() as connection:
        print("Successfully connected to the database!")
