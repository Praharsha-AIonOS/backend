#!/usr/bin/env python3
"""
Generate a secure JWT secret key for use in .env file
"""
import secrets

def generate_secret_key(length=32):
    """Generate a cryptographically secure random hex string"""
    return secrets.token_hex(length)

if __name__ == "__main__":
    key = generate_secret_key(32)
    print("=" * 60)
    print("JWT_SECRET_KEY generated successfully!")
    print("=" * 60)
    print(f"\nJWT_SECRET_KEY={key}\n")
    print("=" * 60)
    print("\nCopy this key to your .env file:")
    print(f"JWT_SECRET_KEY={key}")
    print("\n" + "=" * 60)

