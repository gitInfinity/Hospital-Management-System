@echo off
echo Generating encryption key...
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
pause

