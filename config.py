#!/usr/bin/env python3
"""
Configurações - Sócrates Online
"""

import os

# Configuração do banco de dados
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/socrates_online')

# Configurações Flask
SECRET_KEY = os.environ.get('SECRET_KEY', '6a5bb56c77797ae84352a9043ab0b7e04a8a86530cbc74f388b63607d99741fb')
FLASK_ENV = os.environ.get('FLASK_ENV', 'development')

# Upload
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
UPLOAD_FOLDER = 'uploads'

print(f"🔧 Configuração carregada:")
print(f"   DATABASE_URL: {DATABASE_URL[:50]}...")
print(f"   FLASK_ENV: {FLASK_ENV}")
print(f"   SECRET_KEY: {'*' * 20}... (oculta)")
