#!/usr/bin/env python3
"""
Sócrates Online - Versão Simplificada para Deploy
Versão que funciona sem pandas para evitar problemas de compilação
"""

import os
import csv
import json
import io
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'socrates_sistema_2025_secret_key')

# Configurações
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('backups_csv', exist_ok=True)

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload simplificado - retorna mensagem para usar versão local"""
    return jsonify({
        'success': False, 
        'message': 'Para processamento completo de Excel, use a versão local. Esta é uma versão demo online.'
    })

@app.route('/get_circos_cidades', methods=['GET'])
def get_circos_cidades():
    """Obter dados de circos e cidades"""
    try:
        circos_data = []
        if os.path.exists('circos_cidades.csv'):
            with open('circos_cidades.csv', 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                circos_data = list(reader)
        
        return jsonify({
            'success': True,
            'circos_cidades': circos_data,
            'circos_relatorio': [],
            'total_registros': len(circos_data)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)
