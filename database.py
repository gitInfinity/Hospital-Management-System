"""
Database Configuration and Initialization Module

This module handles:
- SQLAlchemy engine and session factory setup
- Database initialization with table creation
- Seeding default users and sample patients

AVAILABILITY: Implements connection pooling and error handling to ensure
the system remains accessible even during database connection issues.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import os
import warnings
from dotenv import load_dotenv
from models import Base, User, Patient, AuditLog, UserRole
from passlib.context import CryptContext
from utils import CryptoManager
from datetime import datetime

# Load environment variables
load_dotenv()

# Suppress bcrypt version warnings (compatibility issue with passlib)
warnings.filterwarnings('ignore', category=UserWarning, module='passlib')

# Password hashing context - INTEGRITY: Ensures passwords are securely hashed
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Get database URL from environment
# SQLite: file-based database, no separate server needed
# AVAILABILITY: SQLite is embedded, ensuring database is always available
DB_URL = os.getenv("DB_URL", "sqlite:///hospital.db")

# Create SQLAlchemy engine
# AVAILABILITY: SQLite provides reliable file-based storage
engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False},  # Required for Streamlit multi-threading
    echo=False  # Set to True for SQL query debugging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Dependency function to get database session.
    
    AVAILABILITY: Provides a clean way to manage database sessions
    and ensures proper cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database: create tables and seed initial data.
    
    This function implements:
    - AVAILABILITY: Creates database structure if it doesn't exist
    - INTEGRITY: Seeds default users with proper password hashing
    - CONFIDENTIALITY: Seeds sample patients with encrypted PII
    """
    try:
        # Create all tables
        # AVAILABILITY: Creates schema if it doesn't exist, preventing errors
        Base.metadata.create_all(bind=engine)
        
        db = SessionLocal()
        
        try:
            # Check if users already exist to avoid duplicate seeding
            existing_users = db.query(User).count()
            
            if existing_users == 0:
                # INTEGRITY: Hash passwords before storing (prevents plaintext storage)
                # Seed default users
                default_users = [
                    User(
                        username="admin",
                        password_hash=pwd_context.hash("admin123"),
                        role=UserRole.ADMIN,
                        created_at=datetime.now()
                    ),
                    User(
                        username="dr_bob",
                        password_hash=pwd_context.hash("doc123"),
                        role=UserRole.DOCTOR,
                        created_at=datetime.now()
                    ),
                    User(
                        username="alice_recep",
                        password_hash=pwd_context.hash("rec123"),
                        role=UserRole.RECEPTIONIST,
                        created_at=datetime.now()
                    )
                ]
                
                db.add_all(default_users)
                db.commit()
                
                # Initialize encryption manager
                crypto = CryptoManager()
                
                # CONFIDENTIALITY: Encrypt PII before storing in database
                # Seed sample patients with encrypted data
                sample_patients = [
                    Patient(
                        name_encrypted=crypto.encrypt("John Doe"),
                        contact_encrypted=crypto.encrypt("555-0101"),
                        diagnosis="Hypertension - Regular monitoring required",
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    ),
                    Patient(
                        name_encrypted=crypto.encrypt("Jane Smith"),
                        contact_encrypted=crypto.encrypt("555-0102"),
                        diagnosis="Diabetes Type 2 - Medication management",
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    ),
                    Patient(
                        name_encrypted=crypto.encrypt("Robert Johnson"),
                        contact_encrypted=crypto.encrypt("555-0103"),
                        diagnosis="Asthma - Inhaler prescribed",
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                ]
                
                db.add_all(sample_patients)
                db.commit()
                
                print("Database initialized successfully with default users and sample patients.")
            else:
                print("Database already contains users. Skipping seed data.")
                
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Error seeding database: {e}")
            raise
        finally:
            db.close()
            
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

