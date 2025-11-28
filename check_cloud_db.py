import psycopg2
import os

# Cloud SQL Connection using the connection string format
# You can find the PUBLIC IP in your Cloud SQL dashboard
# For this environment, I'll assume we use the same credentials as the local test script
# but with environment variables for security.

DB_HOST = os.getenv("DB_HOST", "34.47.23.137")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "123-new-password")
DB_NAME = os.getenv("DB_NAME", "postgres") # or "nhl_api" if that's the target

def test_connection():
    print(f"Connecting to {DB_HOST} as {DB_USER}...")
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            dbname=DB_NAME,
            sslmode='require'
        )
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"✅ Connected! Version: {version[0]}")
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()

