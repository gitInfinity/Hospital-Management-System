"""
SQLAlchemy Database Models

This module defines the database schema with proper relationships and constraints.

CONFIDENTIALITY: Patient model stores encrypted PII (name, contact) as LargeBinary.
INTEGRITY: AuditLog model tracks all system actions for accountability.
AVAILABILITY: Proper indexing and relationships ensure efficient queries.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

Base = declarative_base()


class UserRole(enum.Enum):
    """User role enumeration for role-based access control."""
    ADMIN = "admin"
    DOCTOR = "doctor"
    RECEPTIONIST = "receptionist"


class User(Base):
    """
    User model for authentication and authorization.
    
    INTEGRITY: Stores password hashes (not plaintext) to prevent unauthorized access.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # INTEGRITY: Hashed password
    role = Column(Enum(UserRole), nullable=False)  # Role-based access control
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationship to audit logs
    audit_logs = relationship("AuditLog", back_populates="user")


class Patient(Base):
    """
    Patient model storing encrypted PII.
    
    CONFIDENTIALITY: 
    - name_encrypted and contact_encrypted are stored as LargeBinary (encrypted)
    - Only admins can decrypt these fields
    - GDPR: Personal data is encrypted at rest
    
    INTEGRITY:
    - created_at and updated_at track data lifecycle
    - Diagnosis field can be updated by authorized users
    """
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    name_encrypted = Column(LargeBinary, nullable=False)  # CONFIDENTIALITY: Encrypted PII
    contact_encrypted = Column(LargeBinary, nullable=False)  # CONFIDENTIALITY: Encrypted PII
    diagnosis = Column(Text, nullable=True)  # Medical information (not PII, can be viewed)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class AuditLog(Base):
    """
    Audit log model for tracking all system actions.
    
    INTEGRITY: 
    - Records every sensitive action (login, view, edit, anonymize)
    - Stores role snapshot to track privilege changes
    - Timestamp provides chronological audit trail
    
    CONFIDENTIALITY:
    - Logs who accessed what data and when
    - Enables GDPR compliance through audit trails
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role_snapshot = Column(String(20), nullable=False)  # INTEGRITY: Captures role at time of action
    action = Column(String(50), nullable=False, index=True)  # e.g., 'LOGIN', 'VIEW_PATIENTS', 'ADD_PATIENT'
    timestamp = Column(DateTime, default=datetime.now, index=True)
    details = Column(Text, nullable=True)  # Additional context about the action
    
    # Relationship to user
    user = relationship("User", back_populates="audit_logs")

