#!/usr/bin/env python3
"""
Sócrates Online - Aplicação Flask para Produção
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename

# Criar app Flask
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', '6a5bb56c77797ae84352a9043ab0b7e04a8a86530cbc74f388b63607d99741fb')

# Configurações
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Criar pastas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Importar dependências opcionais
try:
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    import plotly.utils
    PANDAS_AVAILABLE = True
    PLOTLY_AVAILABLE = True
    print("✅ Pandas e Plotly carregados")
except ImportError as e:
    print(f"⚠️ Pandas/Plotly não disponível: {e}")
    PANDAS_AVAILABLE = False
    PLOTLY_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
    print("✅ ReportLab carregado")
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("⚠️ ReportLab não disponível")

# PostgreSQL
try:
    import psycopg2
    import psycopg2.extras
    
    # Configuração do banco
    DATABASE_URL = (
        os.environ.get('DATABASE_URL') or 
        os.environ.get('POSTGRES_URL') or 
        'postgresql://postgres:postgres@localhost:5432/socrates_online'
    )
    
    class SimplePostgreSQLManager:
        def __init__(self):
            self.connection = None
            self.connect()
        
        def connect(self):
            try:
                print("🔗 Conectando ao PostgreSQL...")
                self.connection = psycopg2.connect(DATABASE_URL, connect_timeout=10)
                print("✅ PostgreSQL conectado!")
            except Exception as e:
                print(f"❌ PostgreSQL erro: {e}")
                self.connection = None
        
        def get_all(self):
            if not self.connection:
                return []
            try:
                cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute("SELECT * FROM circos_cidades ORDER BY cidade")
                results = cursor.fetchall()
                cursor.close()
                return [dict(row) for row in results]
            except:
                return []
        
        def add_circo(self, cidade, circo, data_inicio, data_fim):
            if not self.connection:
                return False
            try:
                cursor = self.connection.cursor()
                cursor.execute("""
                    INSERT INTO circos_cidades (cidade, circo, data_inicio, data_fim)
                    VALUES (%s, %s, %s, %s)
                """, (cidade, circo, 
                     datetime.strptime(data_inicio, '%d/%m/%Y').date(),
                     datetime.strptime(data_fim, '%d/%m/%Y').date()))
                self.connection.commit()
                cursor.close()
                return True
            except Exception as e:
                print(f"❌ Erro add_circo: {e}")
                return False
    
    circos_manager = SimplePostgreSQLManager()
    POSTGRESQL_AVAILABLE = True
    print("✅ PostgreSQL Manager carregado")
    
except ImportError:
    # Fallback simples
    class CSVFallback:
        def get_all(self):
            return []
        def add_circo(self, *args):
            return False
    
    circos_manager = CSVFallback()
    POSTGRESQL_AVAILABLE = False
    print("⚠️ PostgreSQL não disponível")

# Classe de processamento simplificada
class SimpleProcessor:
    def __init__(self):
        self.processed_data = []
    
    def get_unique_circos(self):
        return []

processor = SimpleProcessor()

# Rotas básicas
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_circos_cidades', methods=['GET'])
def get_circos_cidades():
    try:
        circos_data = circos_manager.get_all()
        return jsonify({
            'success': True,
            'circos_cidades': circos_data,
            'circos_relatorio': [],
            'total_registros': len(circos_data)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload e processamento de arquivo Excel"""
    if not PANDAS_AVAILABLE:
        return jsonify({
            'success': False, 
            'message': 'Pandas não disponível - funcionalidade limitada'
        })
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'})
    
    if file and file.filename.lower().endswith(('.xlsx', '.xls')):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            file.save(filepath)
            
            # Processar arquivo Excel básico
            df = pd.read_excel(filepath)
            
            # Extrair circos únicos
            circos_unicos = []
            if 'Evento' in df.columns:
                eventos = df['Evento'].dropna().astype(str)
                for evento in eventos:
                    # Extrair nome do circo (versão simplificada)
                    if '|' in evento:
                        circo = evento.split('|')[0].strip()
                    else:
                        circo = evento.strip()
                    
                    if len(circo) > 2 and circo not in circos_unicos:
                        circos_unicos.append(circo)
            
            # Remover arquivo
            try:
                os.remove(filepath)
            except:
                pass
            
            return jsonify({
                'success': True,
                'message': f'{len(df)} registros processados',
                'stats': {
                    'total_registros': len(df),
                    'total_circos': len(circos_unicos),
                    'circos': circos_unicos,
                    'total_faturamento': 'R$ 0,00',
                    'total_liquido': 'R$ 0,00'
                },
                'imported_data': []
            })
            
        except Exception as e:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except:
                pass
            return jsonify({'success': False, 'message': f'Erro ao processar arquivo: {str(e)}'})
    else:
        return jsonify({'success': False, 'message': 'Tipo de arquivo não permitido'})

@app.route('/add_circo_cidade', methods=['POST'])
def add_circo_cidade():
    try:
        data = request.get_json()
        success = circos_manager.add_circo(
            data.get('cidade', '').strip(),
            data.get('circo', '').strip(),
            data.get('data_inicio', '').strip(),
            data.get('data_fim', '').strip()
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Circo adicionado com sucesso'})
        else:
            return jsonify({'success': False, 'message': 'Erro ao adicionar circo'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

# Outras rotas básicas
@app.route('/update_circo_cidade', methods=['POST'])
def update_circo_cidade():
    return jsonify({'success': False, 'message': 'Funcionalidade disponível na versão local'})

@app.route('/delete_circo_cidade', methods=['POST'])
def delete_circo_cidade():
    return jsonify({'success': False, 'message': 'Funcionalidade disponível na versão local'})

@app.route('/confirm_circos', methods=['POST'])
def confirm_circos():
    return jsonify({'success': True, 'message': 'Confirmado'})

@app.route('/associate_cities_to_data', methods=['GET'])
def associate_cities_to_data():
    return jsonify({'success': True, 'associated_data': [], 'total_records': 0})

@app.route('/generate_report', methods=['POST'])
def generate_report():
    return jsonify({'success': False, 'message': 'Relatórios disponíveis na versão local'})

@app.route('/export/<export_type>')
def export_report(export_type):
    return jsonify({'success': False, 'message': 'Export disponível na versão local'})

# Para WSGI
application = app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print("🎪 Sócrates Online - Produção Simplificada")
    print(f"🌐 Porta: {port}")
    app.run(debug=False, host='0.0.0.0', port=port)

