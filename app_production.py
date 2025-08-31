#!/usr/bin/env python3
"""
Sócrates Online - Aplicação Flask para Produção
Versão otimizada para deploy em servidores
"""

import os
import logging

# Tentar importar app com fallback
try:
    from app import app
    print("✅ App completo carregado")
except ImportError as e:
    print(f"⚠️ Erro ao carregar app completo: {e}")
    print("🔄 Carregando versão simplificada...")
    
    # Versão simplificada para Railway
    from flask import Flask, render_template
    
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', '6a5bb56c77797ae84352a9043ab0b7e04a8a86530cbc74f388b63607d99741fb')
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/upload', methods=['POST'])
    def upload():
        return {'success': False, 'message': 'Versão simplificada - funcionalidade limitada'}
    
    print("✅ App simplificado carregado")

# Configurar logging para produção
if os.environ.get('FLASK_ENV') == 'production':
    logging.basicConfig(level=logging.INFO)

# Configurações de produção
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.config['UPLOAD_FOLDER'] = 'uploads'

# Criar pastas necessárias
os.makedirs('uploads', exist_ok=True)
os.makedirs('backups_csv', exist_ok=True)

if __name__ == '__main__':
    # Configurações para produção
    port = int(os.environ.get('PORT', 8080))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    # Usar chave secreta do ambiente se disponível
    if os.environ.get('SECRET_KEY'):
        app.secret_key = os.environ.get('SECRET_KEY')
    
    print("🎪 Sócrates Online - Produção")
    print(f"🌐 Porta: {port}")
    print(f"🔧 Debug: {debug_mode}")
    print("🚀 Iniciando servidor...")
    
    app.run(
        debug=debug_mode,
        host='0.0.0.0',
        port=port,
        threaded=True
    )
else:
    # Para WSGI servers (Gunicorn, etc.)
    application = app

