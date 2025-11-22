# Hospital Management System

A production-ready Hospital Management System built with **Streamlit** and **MySQL** that strictly adheres to the **CIA Triad** (Confidentiality, Integrity, Availability) and **GDPR** principles.

## 🔒 Security Features

### Confidentiality
- **PII Encryption**: Patient names and contacts are encrypted at rest using Fernet symmetric encryption
- **Role-Based Access Control (RBAC)**: Different data visibility based on user roles
  - **Admin**: Full access to decrypted patient data
  - **Doctor**: Anonymized patient data (ANON_ID format)
  - **Receptionist**: Masked contact information (XXX-XXX-1234 format)
- **Session Management**: Secure authentication and session state management

### Integrity
- **Password Hashing**: All passwords are hashed using bcrypt (never stored in plaintext)
- **Comprehensive Audit Logging**: Every sensitive action is logged with:
  - User ID and role snapshot
  - Action type (LOGIN, VIEW_PATIENTS, ADD_PATIENT, etc.)
  - Timestamp
  - Additional details
- **Data Validation**: Input validation and error handling

### Availability
- **Connection Pooling**: Efficient database connection management
- **Error Handling**: Graceful error messages instead of stack traces
- **Database Resilience**: Connection verification and automatic reconnection
- **Data Export**: CSV export functionality for backup and compliance

### GDPR Compliance
- **Data Minimization**: Only necessary data is displayed based on role
- **Data Anonymization**: Non-admin users see anonymized patient identifiers
- **Audit Trails**: Complete logging for compliance and accountability
- **Data Portability**: CSV export functionality

## 📋 Prerequisites

- **Python 3.10+** (SQLite is built-in, no separate database server needed!)
- **pip** (Python package manager)

## 🚀 Installation & Setup

### Step 1: Clone/Download Project

Navigate to your project directory:
```bash
cd "C:\Users\Rouhan\OneDrive\Documents\Information Security Assignment 4"
```

### Step 2: Install Python Dependencies

1. Create a virtual environment (recommended):
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

### Step 3: Generate Encryption Key

Generate a Fernet encryption key for PII encryption:

**Option 1: Run the provided script (Recommended)**
```bash
# Double-click generate_key.py or run:
python generate_key.py
```

**Option 2: If python command doesn't work, use the full path:**
```bash
# Find your Python path (usually shown when you run 'pip show cryptography')
# Then run:
C:\Users\YourUsername\AppData\Local\Programs\Python\Python313\python.exe generate_key.py
```

Copy the generated key (it will look like: `MtbeOonYrrLNffzxBA3TPBaDy_maHRBzAG9zy3YRHXA=`)

### Step 4: Configure Environment Variables

1. Copy the example environment file:
```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

2. Edit `.env` file and update the values:

```env
# SQLite database (default: creates hospital.db in project directory)
# You can use a custom path: sqlite:///path/to/your/database.db
DB_URL=sqlite:///hospital.db

# Paste the encryption key you generated
ENCRYPTION_KEY=your_generated_fernet_key_here
```

**Important Notes:**
- SQLite is file-based - the database file (`hospital.db`) will be created automatically
- Replace `your_generated_fernet_key_here` with the key from Step 3
- The database file will be created in the project directory by default

### Step 5: Run the Application

```bash
streamlit run main.py
```

The application will:
1. Automatically create all database tables
2. Seed default users (if database is empty)
3. Seed sample patients (if database is empty)
4. Open in your default web browser at `http://localhost:8501`

## 👥 Default Users

The system comes with three pre-configured users:

| Username | Password | Role | Access Level |
|----------|----------|------|--------------|
| `admin` | `admin123` | Admin | Full access, can decrypt all patient data |
| `dr_bob` | `doc123` | Doctor | View anonymized patient data |
| `alice_recep` | `rec123` | Receptionist | Add patients, edit diagnosis, view masked data |

**⚠️ Security Note**: Change these default passwords in production!

## 📁 Project Structure

```
.
├── main.py              # Main Streamlit application (entry point)
├── models.py            # SQLAlchemy database models
├── database.py          # Database configuration and initialization
├── auth.py              # Authentication and authorization
├── utils.py             # Encryption utilities and CSV export
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── .env                 # Your environment variables (create this)
└── README.md            # This file
```

## 🎯 Features

### 1. Login Screen
- Secure username/password authentication
- Password verification using bcrypt
- Session state management

### 2. Dashboard
- System status and uptime information
- Current user and role display
- Quick statistics (patient count, audit log count)

### 3. Patient Management
- **View Patients**: Role-based data display
  - Admin: Decrypted names and contacts
  - Doctor: Anonymized names (ANON_ID), masked contacts
  - Receptionist: Anonymized names, masked contacts
- **Add Patient**: 
  - Receptionist and Admin can add new patients
  - PII is automatically encrypted before storage
- **Edit Patient**:
  - Receptionist: Can only edit diagnosis
  - Admin: Can edit all fields (name, contact, diagnosis)
- **Export**: CSV export with appropriate data masking

### 4. Audit Logs (Admin Only)
- View all system actions chronologically
- Filter by user, role, or action type
- Export audit logs to CSV for compliance

## 🔍 Security Implementation Details

### Encryption Flow
1. **Storage**: Patient PII (name, contact) is encrypted using Fernet before database insertion
2. **Retrieval**: 
   - Admin: Data is decrypted in memory for display
   - Non-admin: Data is decrypted only to apply masking, then displayed as anonymized

### Audit Logging
Every sensitive action triggers an audit log entry:
- User login
- Viewing patient list
- Adding new patients
- Updating patient information
- Viewing audit logs

### Error Handling
- Database connection errors show user-friendly messages
- All database operations are wrapped in try/except blocks
- Failed operations are rolled back to maintain data integrity

## 🛠️ Troubleshooting

### Database Connection Error
```
Error: Unable to open database file
```
**Solution**: 
- Ensure the directory for the database file exists and is writable
- Verify DB_URL in `.env` is correct (format: `sqlite:///hospital.db`)
- Check file permissions if using a custom path

### Encryption Key Error
```
ValueError: ENCRYPTION_KEY not found
```
**Solution**: 
- Ensure `.env` file exists in the project root
- Verify `ENCRYPTION_KEY` is set in `.env`
- Generate a new key if needed (see Step 5)

### Import Errors
```
ModuleNotFoundError: No module named 'streamlit'
```
**Solution**: 
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`

### Table Already Exists Error
This is normal if you've run the app before. The system will skip table creation if they already exist.

## 📝 Development Notes

### Adding New Users
Users can be added directly to the database:
```python
from database import SessionLocal
from models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
db = SessionLocal()

new_user = User(
    username="new_user",
    password_hash=pwd_context.hash("password"),
    role="doctor"  # or "admin", "receptionist"
)
db.add(new_user)
db.commit()
```

### Changing Encryption Key
**⚠️ Warning**: Changing the encryption key will make existing encrypted data unreadable!

If you need to change the key:
1. Export all patient data (as admin)
2. Update `ENCRYPTION_KEY` in `.env`
3. Re-import patient data (it will be encrypted with the new key)

## 📄 License

This project is created for educational purposes as part of an Information Security assignment.

## 🤝 Contributing

This is an assignment project. For production use, consider:
- Implementing password complexity requirements
- Adding two-factor authentication
- Implementing rate limiting
- Adding input sanitization
- Implementing backup and recovery procedures
- Adding automated security testing

---

**Built with security in mind** 🔒 | **CIA Triad Compliant** ✅ | **GDPR Ready** 📋

