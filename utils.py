"""
Utility Functions for Encryption and Data Export

This module implements:
- CONFIDENTIALITY: Fernet encryption for PII (patient names, contacts)
- GDPR: Data masking for non-admin users
- AVAILABILITY: CSV export functionality for data portability
"""

import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import csv
import io
from typing import Optional

load_dotenv()


class CryptoManager:
    """
    Encryption manager using Fernet symmetric encryption.

    CONFIDENTIALITY: 
    - Encrypts PII before storing in database
    - Decrypts only when authorized (admin role)
    - Uses environment variable for key management (GDPR best practice)
    """

    def __init__(self):
        """
        Initialize encryption manager with key from environment.

        CONFIDENTIALITY: Encryption key stored in environment variable,
        not hardcoded in source code.
        """
        # Prefer Streamlit secrets (cloud) then environment variables (local)
        _key = None
        try:
            import streamlit as st
            _key = st.secrets.get("ENCRYPTION_KEY")
        except Exception:
            # Not running inside Streamlit or secrets unavailable
            pass

        if not _key:
            _key = os.getenv("ENCRYPTION_KEY")

        # Guard against placeholder values left in the template
        if _key is None or (isinstance(_key, str) and _key.strip().startswith("your_")):
            raise ValueError(
                "ENCRYPTION_KEY not set (or still a placeholder). "
                "Generate a proper key and add it to .env or Streamlit secrets."
            )

        # Initialize Fernet cipher from the provided key
        if isinstance(_key, str):
            try:
                self.cipher = Fernet(_key.encode())
            except Exception:
                raise ValueError(
                    "Invalid ENCRYPTION_KEY format. "
                    "Generate a new key using: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
                )
        else:
            # Allow bytes-style keys
            try:
                self.cipher = Fernet(_key)
            except Exception:
                raise ValueError("Invalid ENCRYPTION_KEY bytes provided.")

    def encrypt(self, plaintext: str) -> bytes:
        """
        Encrypt plaintext string to bytes.

        CONFIDENTIALITY: Converts sensitive PII to encrypted binary format.

        Args:
            plaintext: The string to encrypt
            
        Returns:
            Encrypted bytes
        """
        return self.cipher.encrypt(plaintext.encode('utf-8'))
    
    def decrypt(self, ciphertext: bytes) -> str:
        """
        Decrypt bytes to plaintext string.

        CONFIDENTIALITY: Only called for admin users to view actual PII.

        Args:
            ciphertext: The encrypted bytes
            
        Returns:
            Decrypted string
        """
        return self.cipher.decrypt(ciphertext).decode('utf-8')


def mask_contact(contact: str) -> str:
    """
    Mask contact information for non-admin users.
    
    GDPR: Data minimization - show only last 4 digits of contact.
    
    Args:
        contact: The contact string to mask
        
    Returns:
        Masked contact (e.g., "XXX-XXX-1234")
    """
    if not contact:
        return "XXX"

    if len(contact) <= 4:
        return "XXX"
    
    # Show only last 4 characters
    last_four = contact[-4:]
    masked = "X" * (len(contact) - 4) + last_four
    
    # Format phone numbers nicely
    if "-" in contact:
        parts = []
        idx = 0
        for part in contact.split("-"):
            part_len = len(part)
            masked_part = masked[idx:idx+part_len]
            parts.append(masked_part)
            idx += part_len + 1  # account for dash
        return "-".join(parts)
    
    return masked


def anonymize_name(patient_id: int) -> str:
    """
    Generate anonymized name for non-admin users.
    
    GDPR: Data anonymization - replace actual name with identifier.
    
    Args:
        patient_id: The patient's ID
        
    Returns:
        Anonymized name (e.g., "ANON_1")
    """
    return f"ANON_{patient_id}"


def export_audit_logs_to_csv(audit_logs: list) -> str:
    """
    Export audit logs to CSV format.
    
    AVAILABILITY: Provides data export functionality for compliance and backup.
    INTEGRITY: CSV export preserves audit trail for external analysis.
    
    Args:
        audit_logs: List of AuditLog objects
        
    Returns:
        CSV content as string
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "ID", "User ID", "Username", "Role", "Action", 
        "Timestamp", "Details"
    ])
    
    # Write data rows
    for log in audit_logs:
        writer.writerow([
            log.id,
            log.user_id,
            log.user.username if getattr(log, 'user', None) else "N/A",
            getattr(log, 'role_snapshot', ''),
            getattr(log, 'action', ''),
            log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if getattr(log, 'timestamp', None) else "",
            getattr(log, 'details', '') or ""
        ])
    
    return output.getvalue()


def export_patients_to_csv(patients: list, crypto: Optional[CryptoManager] = None, user_role: str = "receptionist") -> str:
    """
    Export patients to CSV format with appropriate masking.
    
    CONFIDENTIALITY: Only admins get decrypted data in export.
    GDPR: Non-admins get anonymized data.
    
    Args:
        patients: List of Patient objects
        crypto: CryptoManager instance (required for admin exports)
        user_role: Role of the user requesting export
        
    Returns:
        CSV content as string
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(["ID", "Name", "Contact", "Diagnosis", "Created At", "Updated At"])
    
    # Write data rows
    for patient in patients:
        if user_role == "admin" and crypto:
            # CONFIDENTIALITY: Admin can see decrypted data
            name = crypto.decrypt(patient.name_encrypted)
            contact = crypto.decrypt(patient.contact_encrypted)
        else:
            # GDPR: Non-admins get anonymized data
            name = anonymize_name(getattr(patient, 'id', ''))
            contact = mask_contact(
                crypto.decrypt(patient.contact_encrypted) if crypto else "XXX-XXX-XXXX"
            )
        
        writer.writerow([
            getattr(patient, 'id', ''),
            name,
            contact,
            getattr(patient, 'diagnosis', '') or "",
            patient.created_at.strftime("%Y-%m-%d %H:%M:%S") if getattr(patient, 'created_at', None) else "",
            patient.updated_at.strftime("%Y-%m-%d %H:%M:%S") if getattr(patient, 'updated_at', None) else ""
        ])
    
    return output.getvalue()
