"""
Hospital Management System - Main Application

This is the entry point for the Streamlit application implementing:
- CONFIDENTIALITY: Role-based data access with encryption
- INTEGRITY: Comprehensive audit logging
- AVAILABILITY: Error handling and graceful degradation
- GDPR: Data minimization and anonymization

Pages:
1. Login - User authentication
2. Dashboard - System overview
3. Patient Management - Core feature with role-based access
4. Audit Logs - Admin-only audit trail viewing
"""

import streamlit as st
from sqlalchemy.orm import Session
from database import SessionLocal, init_db, get_db
from models import User, Patient, AuditLog
from auth import login, require_login, require_role, get_current_user, logout, log_audit_action
from utils import CryptoManager, mask_contact, anonymize_name, export_audit_logs_to_csv, export_patients_to_csv
from datetime import datetime
import sys

# Page configuration
st.set_page_config(
    page_title="Hospital Management System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'user' not in st.session_state:
    st.session_state['user'] = None
if 'db_initialized' not in st.session_state:
    st.session_state['db_initialized'] = False


def initialize_database():
    """Initialize database on first run."""
    if not st.session_state['db_initialized']:
        try:
            init_db()
            st.session_state['db_initialized'] = True
        except Exception as e:
            st.error(f"Database initialization error: {str(e)}")
            st.stop()


def show_login_page():
    """
    Login page for user authentication.
    
    CONFIDENTIALITY: Only authenticated users can proceed.
    INTEGRITY: Logs all login attempts.
    """
    st.title("🏥 Hospital Management System")
    st.subheader("Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            db = SessionLocal()
            try:
                success, user, message = login(db, username, password)
                
                if success:
                    st.session_state['user'] = user
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            except Exception as e:
                st.error(f"Login error: {str(e)}")
            finally:
                db.close()


def show_dashboard():
    """
    Dashboard page showing system overview.
    
    AVAILABILITY: Displays system status and user information.
    """
    st.title("🏥 Hospital Management System")
    st.header("Dashboard")
    
    user = get_current_user()
    if user:
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Current User", user['username'])
            st.metric("Role", user['role'].upper())
        
        with col2:
            # AVAILABILITY: Show system uptime/last sync
            st.metric("Last Data Sync", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            st.metric("System Status", "🟢 Online")
        
        st.divider()
        
        # Quick stats
        db = SessionLocal()
        try:
            patient_count = db.query(Patient).count()
            audit_count = db.query(AuditLog).count()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Patients", patient_count)
            with col2:
                st.metric("Total Audit Logs", audit_count)
        except Exception as e:
            st.error(f"Error loading statistics: {str(e)}")
        finally:
            db.close()
    
    # Logout button
    if st.button("Logout", type="primary"):
        logout()


def show_patient_management():
    """
    Patient Management page with role-based access.
    
    CONFIDENTIALITY: 
    - Admins see decrypted data
    - Doctors see anonymized data
    - Receptionists see masked data
    
    INTEGRITY: All patient operations are logged.
    """
    st.title("Patient Management")
    
    if not require_login():
        st.warning("Please login to access this page.")
        return
    
    user = get_current_user()
    user_role = user['role']
    
    db = SessionLocal()
    crypto = CryptoManager()
    
    try:
        # INTEGRITY: Log patient list view
        log_audit_action(
            db,
            user['id'],
            user_role,
            "VIEW_PATIENTS",
            f"User {user['username']} viewed patient list"
        )
        
        # Display patients table
        st.subheader("Patient List")
        
        patients = db.query(Patient).order_by(Patient.created_at.desc()).all()
        
        if not patients:
            st.info("No patients found.")
        else:
            # Prepare data for display based on role
            # CONFIDENTIALITY: Role-based data display
            display_data = []
            for patient in patients:
                if user_role == "admin":
                    # Admin sees decrypted data
                    name = crypto.decrypt(patient.name_encrypted)
                    contact = crypto.decrypt(patient.contact_encrypted)
                else:
                    # GDPR: Non-admins see anonymized/masked data
                    name = anonymize_name(patient.id)
                    contact = mask_contact(
                        crypto.decrypt(patient.contact_encrypted)  # Need to decrypt to mask
                    )
                
                display_data.append({
                    "ID": patient.id,
                    "Name": name,
                    "Contact": contact,
                    "Diagnosis": patient.diagnosis or "N/A",
                    "Created": patient.created_at.strftime("%Y-%m-%d") if patient.created_at else "",
                    "Updated": patient.updated_at.strftime("%Y-%m-%d") if patient.updated_at else ""
                })
            
            st.dataframe(display_data, use_container_width=True)
            
            # Export button
            if st.button("Export Patients to CSV"):
                csv_content = export_patients_to_csv(patients, crypto, user_role)
                st.download_button(
                    label="Download CSV",
                    data=csv_content,
                    file_name=f"patients_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        st.divider()
        
        # Patient actions based on role
        if user_role == "receptionist":
            st.subheader("Add New Patient")
            with st.form("add_patient_form"):
                name = st.text_input("Patient Name *")
                contact = st.text_input("Contact *")
                diagnosis = st.text_area("Diagnosis")
                submit = st.form_submit_button("Add Patient")
                
                if submit:
                    if name and contact:
                        try:
                            # CONFIDENTIALITY: Encrypt PII before storing
                            new_patient = Patient(
                                name_encrypted=crypto.encrypt(name),
                                contact_encrypted=crypto.encrypt(contact),
                                diagnosis=diagnosis if diagnosis else None,
                                created_at=datetime.now(),
                                updated_at=datetime.now()
                            )
                            db.add(new_patient)
                            db.commit()
                            
                            # INTEGRITY: Log patient creation
                            log_audit_action(
                                db,
                                user['id'],
                                user_role,
                                "ADD_PATIENT",
                                f"Added patient with ID {new_patient.id}"
                            )
                            
                            st.success("Patient added successfully!")
                            st.rerun()
                        except Exception as e:
                            db.rollback()
                            st.error(f"Error adding patient: {str(e)}")
                    else:
                        st.error("Name and Contact are required fields.")
            
            st.divider()
            st.subheader("Edit Patient Diagnosis")
            with st.form("edit_diagnosis_form"):
                patient_id = st.number_input("Patient ID", min_value=1, step=1)
                new_diagnosis = st.text_area("New Diagnosis")
                submit = st.form_submit_button("Update Diagnosis")
                
                if submit:
                    try:
                        patient = db.query(Patient).filter(Patient.id == patient_id).first()
                        if patient:
                            patient.diagnosis = new_diagnosis if new_diagnosis else None
                            patient.updated_at = datetime.now()
                            db.commit()
                            
                            # INTEGRITY: Log diagnosis update
                            log_audit_action(
                                db,
                                user['id'],
                                user_role,
                                "UPDATE_DIAGNOSIS",
                                f"Updated diagnosis for patient ID {patient_id}"
                            )
                            
                            st.success("Diagnosis updated successfully!")
                            st.rerun()
                        else:
                            st.error("Patient not found.")
                    except Exception as e:
                        db.rollback()
                        st.error(f"Error updating diagnosis: {str(e)}")
        
        elif user_role == "admin":
            st.subheader("Add New Patient")
            with st.form("add_patient_form_admin"):
                name = st.text_input("Patient Name *")
                contact = st.text_input("Contact *")
                diagnosis = st.text_area("Diagnosis")
                submit = st.form_submit_button("Add Patient")
                
                if submit:
                    if name and contact:
                        try:
                            # CONFIDENTIALITY: Encrypt PII before storing
                            new_patient = Patient(
                                name_encrypted=crypto.encrypt(name),
                                contact_encrypted=crypto.encrypt(contact),
                                diagnosis=diagnosis if diagnosis else None,
                                created_at=datetime.now(),
                                updated_at=datetime.now()
                            )
                            db.add(new_patient)
                            db.commit()
                            
                            # INTEGRITY: Log patient creation
                            log_audit_action(
                                db,
                                user['id'],
                                user_role,
                                "ADD_PATIENT",
                                f"Added patient with ID {new_patient.id}"
                            )
                            
                            st.success("Patient added successfully!")
                            st.rerun()
                        except Exception as e:
                            db.rollback()
                            st.error(f"Error adding patient: {str(e)}")
                    else:
                        st.error("Name and Contact are required fields.")
            
            st.divider()
            st.subheader("Edit Patient (Admin)")
            with st.form("edit_patient_form_admin"):
                patient_id = st.number_input("Patient ID", min_value=1, step=1)
                new_name = st.text_input("New Name")
                new_contact = st.text_input("New Contact")
                new_diagnosis = st.text_area("New Diagnosis")
                submit = st.form_submit_button("Update Patient")
                
                if submit:
                    try:
                        patient = db.query(Patient).filter(Patient.id == patient_id).first()
                        if patient:
                            if new_name:
                                patient.name_encrypted = crypto.encrypt(new_name)
                            if new_contact:
                                patient.contact_encrypted = crypto.encrypt(new_contact)
                            if new_diagnosis:
                                patient.diagnosis = new_diagnosis
                            patient.updated_at = datetime.now()
                            db.commit()
                            
                            # INTEGRITY: Log patient update
                            log_audit_action(
                                db,
                                user['id'],
                                user_role,
                                "UPDATE_PATIENT",
                                f"Updated patient ID {patient_id}"
                            )
                            
                            st.success("Patient updated successfully!")
                            st.rerun()
                        else:
                            st.error("Patient not found.")
                    except Exception as e:
                        db.rollback()
                        st.error(f"Error updating patient: {str(e)}")
        
        elif user_role == "doctor":
            st.info("👨‍⚕️ Doctors can view patient information but cannot add or edit patients.")
    
    except Exception as e:
        st.error(f"Error loading patient data: {str(e)}")
    finally:
        db.close()


def show_audit_logs():
    """
    Audit Logs page (Admin only).
    
    INTEGRITY: Displays complete audit trail of all system actions.
    CONFIDENTIALITY: Only admins can view audit logs.
    """
    st.title("Audit Logs")
    
    if not require_login():
        st.warning("Please login to access this page.")
        return
    
    # CONFIDENTIALITY: Only admins can view audit logs
    if not require_role(["admin"]):
        st.error("❌ Access Denied: This page is only accessible to administrators.")
        return
    
    db = SessionLocal()
    
    try:
        # Get all audit logs, newest first
        audit_logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()
        
        if not audit_logs:
            st.info("No audit logs found.")
        else:
            st.subheader(f"Total Logs: {len(audit_logs)}")
            
            # Display logs in a table
            log_data = []
            for log in audit_logs:
                log_data.append({
                    "ID": log.id,
                    "User": log.user.username if log.user else "N/A",
                    "Role": log.role_snapshot,
                    "Action": log.action,
                    "Timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "",
                    "Details": log.details or ""
                })
            
            st.dataframe(log_data, use_container_width=True)
            
            # Export button
            st.divider()
            if st.button("Export Logs to CSV"):
                csv_content = export_audit_logs_to_csv(audit_logs)
                st.download_button(
                    label="Download Audit Logs CSV",
                    data=csv_content,
                    file_name=f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    except Exception as e:
        st.error(f"Error loading audit logs: {str(e)}")
    finally:
        db.close()


# Main application logic
def main():
    """Main application entry point."""
    # Initialize database on first run
    try:
        initialize_database()
    except Exception as e:
        st.error(f"Critical error: Database initialization failed. {str(e)}")
        st.stop()
    
    # Check if user is logged in
    if not require_login():
        show_login_page()
    else:
        # Navigation sidebar
        with st.sidebar:
            st.title("Navigation")
            page = st.radio(
                "Select Page",
                ["Dashboard", "Patient Management", "Audit Logs"],
                index=0
            )
            
            st.divider()
            user = get_current_user()
            if user:
                st.write(f"Logged in as: **{user['username']}**")
                st.write(f"Role: **{user['role'].upper()}**")
                if st.button("Logout"):
                    logout()
        
        # Route to appropriate page
        if page == "Dashboard":
            show_dashboard()
        elif page == "Patient Management":
            show_patient_management()
        elif page == "Audit Logs":
            show_audit_logs()


if __name__ == "__main__":
    main()

