"""
Authentication and Authorization Module

This module handles:
- User authentication (login)
- Password verification
- Session state management
- Role-based access control

INTEGRITY: Verifies user credentials securely using bcrypt.
CONFIDENTIALITY: Manages user sessions to control data access.
"""

import streamlit as st
import warnings
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from models import User, AuditLog
from datetime import datetime

# Suppress bcrypt version warnings (compatibility issue with passlib)
warnings.filterwarnings('ignore', category=UserWarning, module='passlib')

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    INTEGRITY: Uses bcrypt to securely verify passwords without storing plaintext.
    
    Args:
        plain_password: The plaintext password to verify
        hashed_password: The stored password hash
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def log_audit_action(db: Session, user_id: int, role: str, action: str, details: str = None):
    """
    Log an action to the audit log.
    
    INTEGRITY: Records all system actions for accountability and compliance.
    
    Args:
        db: Database session
        user_id: ID of the user performing the action
        role: Role of the user at the time of action
        action: Type of action (e.g., 'LOGIN', 'VIEW_PATIENTS')
        details: Additional details about the action
    """
    try:
        audit_log = AuditLog(
            user_id=user_id,
            role_snapshot=role,  # INTEGRITY: Capture role at time of action
            action=action,
            timestamp=datetime.now(),
            details=details
        )
        db.add(audit_log)
        db.commit()
    except Exception as e:
        # AVAILABILITY: Don't fail the main operation if logging fails
        db.rollback()
        print(f"Failed to log audit action: {e}")


def login(db: Session, username: str, password: str) -> tuple[bool, dict | None, str]:
    """
    Authenticate a user.
    
    INTEGRITY: Verifies credentials securely.
    CONFIDENTIALITY: Only returns user info if credentials are valid.
    
    Args:
        db: Database session
        username: Username to authenticate
        password: Password to verify
        
    Returns:
        Tuple of (success: bool, user_info: dict | None, message: str)
        user_info contains: id, username, role
    """
    try:
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            return False, None, "Invalid username or password"
        
        if not verify_password(password, user.password_hash):
            return False, None, "Invalid username or password"
        
        # INTEGRITY: Log successful login
        log_audit_action(
            db, 
            user.id, 
            user.role.value, 
            "LOGIN", 
            f"User {username} logged in successfully"
        )
        
        # Store user info as dict to avoid session dependency issues
        user_info = {
            'id': user.id,
            'username': user.username,
            'role': user.role.value
        }
        
        return True, user_info, "Login successful"
        
    except Exception as e:
        return False, None, f"Login error: {str(e)}"


def require_login():
    """
    Check if user is logged in, redirect to login if not.
    
    CONFIDENTIALITY: Ensures only authenticated users can access the system.
    
    Returns:
        True if user is logged in, False otherwise
    """
    if 'user' not in st.session_state or st.session_state['user'] is None:
        return False
    return True


def require_role(allowed_roles: list[str]):
    """
    Decorator-like function to check user role.
    
    CONFIDENTIALITY: Implements role-based access control (RBAC).
    GDPR: Ensures users only access data appropriate to their role.
    
    Args:
        allowed_roles: List of role names that are allowed
        
    Returns:
        True if user has required role, False otherwise
    """
    if not require_login():
        return False
    
    user_info = st.session_state.get('user', None)
    if not user_info:
        return False
    
    user_role = user_info.get('role')
    return user_role in allowed_roles


def get_current_user() -> dict | None:
    """
    Get the current logged-in user info from session state.
    
    Returns:
        User info dict (id, username, role) if logged in, None otherwise
    """
    return st.session_state.get('user', None)


def logout():
    """
    Log out the current user.
    
    CONFIDENTIALITY: Clears session state to prevent unauthorized access.
    """
    if 'user' in st.session_state:
        st.session_state['user'] = None
    st.rerun()

