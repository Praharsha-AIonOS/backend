# backend/db.py

import psycopg2
from psycopg2 import errors
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection string from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://app_user:password@localhost:5432/app_db")

# Connection pool for better performance
connection_pool = None

def init_connection_pool():
    """Initialize PostgreSQL connection pool"""
    global connection_pool
    if connection_pool is None:
        try:
            # Add SSL mode to connection string if not present
            # This helps with GCP Cloud SQL connections
            conn_string = DATABASE_URL
            if "sslmode" not in conn_string.lower() and "?" not in conn_string:
                # Try with prefer mode first (will use SSL if available, otherwise not)
                conn_string = f"{DATABASE_URL}?sslmode=prefer"
            
            # Create connection pool
            connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, 20, conn_string
            )
            if connection_pool:
                print("✅ Database connection pool created successfully")
        except (Exception, psycopg2.Error) as error:
            print(f"❌ Error while connecting to PostgreSQL: {error}")
            print("\n💡 Troubleshooting tips:")
            print("   1. Check if PostgreSQL server allows connections from your IP")
            print("   2. Verify pg_hba.conf is configured correctly on the server")
            print("   3. Ensure firewall rules allow port 5432")
            print("   4. For GCP: Check Cloud SQL authorized networks")
            print("   5. Try adding ?sslmode=require to your DATABASE_URL if using SSL")
            print("   6. Run: python test_db_connection.py to test different connection modes")
            raise

def get_db_connection():
    """Get a database connection from the pool"""
    global connection_pool
    if connection_pool is None:
        init_connection_pool()
    
    try:
        conn = connection_pool.getconn()
        if conn:
            return conn
    except (Exception, psycopg2.Error) as error:
        print(f"❌ Error getting connection from pool: {error}")
        raise
    
    raise Exception("Failed to get database connection")

def return_db_connection(conn):
    """Return a connection to the pool"""
    global connection_pool
    if connection_pool:
        connection_pool.putconn(conn)

def init_db():
    """Initialize database tables"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create users table for authentication
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id SERIAL PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        except errors.DiskFull as e:
            print("\n" + "=" * 60)
            print("❌ DISK SPACE ERROR: PostgreSQL server is out of disk space!")
            print("=" * 60)
            print("\nTo fix this issue:")
            print("1. SSH into your GCP VM")
            print("2. Run: sudo -u postgres psql -d app_db -c 'VACUUM FULL;'")
            print("3. Or increase the disk size in GCP Console")
            print("\nSee POSTGRESQL_DISK_SPACE_FIX.md for detailed instructions")
            print("=" * 60 + "\n")
            raise

        # Create sessions table for token management (optional, for token blacklisting)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                token_jti VARCHAR(255) UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create jobs table (migrated from SQLite)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id VARCHAR(255) PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                input_video TEXT NOT NULL,
                input_audio TEXT NOT NULL,
                output_video TEXT NOT NULL,
                status VARCHAR(50) NOT NULL,
                feature VARCHAR(50),
                created_at TIMESTAMP NOT NULL,
                started_at TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)

        # Create indexes for better performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_token_jti ON sessions(token_jti)
        """)

        conn.commit()
        print("✅ Database tables initialized successfully")
    except psycopg2.errors.DiskFull as e:
        if conn:
            conn.rollback()
        print("\n" + "=" * 60)
        print("❌ DISK SPACE ERROR: PostgreSQL server is out of disk space!")
        print("=" * 60)
        print("\nTo fix this issue:")
        print("1. SSH into your GCP VM")
        print("2. Run: sudo -u postgres psql -d app_db -c 'VACUUM FULL;'")
        print("3. Or increase the disk size in GCP Console")
        print("\nSee POSTGRESQL_DISK_SPACE_FIX.md for detailed instructions")
        print("=" * 60 + "\n")
        raise
    except (Exception, psycopg2.Error) as error:
        if conn:
            conn.rollback()
        print(f"❌ Error initializing database: {error}")
        raise
    finally:
        if conn:
            return_db_connection(conn)
