#!/usr/bin/env python3
"""
Test PostgreSQL database connection
"""
import os
import sys
from dotenv import load_dotenv
import psycopg2

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://app_user:password@localhost:5432/app_db")

def test_connection():
    """Test database connection with different SSL modes"""
    
    print("=" * 60)
    print("Testing PostgreSQL Connection")
    print("=" * 60)
    print(f"Connection String: {DATABASE_URL.split('@')[0]}@***")
    print()
    
    # Try different SSL modes
    ssl_modes = ["prefer", "require", "allow", "disable"]
    
    for ssl_mode in ssl_modes:
        print(f"Trying with sslmode={ssl_mode}...", end=" ")
        try:
            # Parse connection string
            if "?" in DATABASE_URL:
                conn_str = f"{DATABASE_URL}&sslmode={ssl_mode}"
            else:
                conn_str = f"{DATABASE_URL}?sslmode={ssl_mode}"
            
            conn = psycopg2.connect(conn_str, connect_timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            print("✅ SUCCESS!")
            print(f"   PostgreSQL version: {version.split(',')[0]}")
            print(f"   ✅ Use this in your .env file:")
            print(f"   DATABASE_URL={conn_str}")
            return True
            
        except psycopg2.OperationalError as e:
            print(f"❌ FAILED")
            print(f"   Error: {str(e)[:100]}")
        except Exception as e:
            print(f"❌ FAILED")
            print(f"   Error: {str(e)[:100]}")
        print()
    
    print("=" * 60)
    print("❌ All connection attempts failed!")
    print()
    print("Possible issues:")
    print("1. PostgreSQL server not allowing connections from your IP")
    print("2. Firewall blocking port 5432")
    print("3. Wrong credentials or database name")
    print("4. Server not running or unreachable")
    print()
    print("See POSTGRESQL_CONNECTION_FIX.md for detailed solutions")
    print("=" * 60)
    return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

