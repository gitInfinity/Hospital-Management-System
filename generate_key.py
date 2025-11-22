"""
Simple script to generate a Fernet encryption key for the Hospital Management System.
Run this script to generate a key, then copy it to your .env file.
"""

from cryptography.fernet import Fernet

if __name__ == "__main__":
    key = Fernet.generate_key()
    print("\n" + "="*60)
    print("ENCRYPTION KEY GENERATED")
    print("="*60)
    print(f"\n{key.decode()}\n")
    print("="*60)
    print("\nCopy the key above and paste it into your .env file as ENCRYPTION_KEY")
    print("="*60 + "\n")

