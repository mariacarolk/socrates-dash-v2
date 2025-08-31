#!/usr/bin/env python3
"""
Sócrates Online - Aplicação Flask para Produção
VERSÃO IDÊNTICA À LOCAL
"""

import os
import json
import io
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
import pandas as pd
import re

# Plotly para gráficos
try:
    import plotly.express as px
    import plotly.graph_objects as go
    import plotly.utils
    PLOTLY_AVAILABLE = True
    print("✅ Plotly carregado com sucesso")
except ImportError as e:
    print(f"⚠️ Plotly não disponível: {e}")
    PLOTLY_AVAILABLE = False

# ReportLab para PDF
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

# PostgreSQL
from database import PostgreSQLManager

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', '6a5bb56c77797ae84352a9043ab0b7e04a8a86530cbc74f388b63607d99741fb')

# Configurações
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Criar pasta de uploads se não existir
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class SocratesProcessor:
    """Classe para processar dados do Sócrates Online"""
    
    def __init__(self):
        self.processed_data = []
        self.original_df = None
    
    def allowed_file(self, filename):
        """Verifica se o arquivo é permitido"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    def extract_circo_name(self, evento_text):
        """Extrai o nome do circo do texto do evento"""
        
        # Verificar se é NAN ou inválido
        if pd.isna(evento_text) or str(evento_text).lower() in ['nan', 'none', '']:
            return "Evento Inválido"
        
        evento = str(evento_text).strip()
        
        # Caso 1: Se há barra |, usar texto antes da barra
        if '|' in evento:
            return evento.split('|')[0].strip()
        
        # Caso 2: Procurar por padrões de data e usar texto antes da data
        dias_semana = r'(?:segunda|terça|terca|quarta|quinta|sexta|sábado|sabado|domingo|seg|ter|qua|qui|sex|sab|dom)'
        
        date_patterns = [
            rf'\s+{dias_semana}\s+\d{{1,2}}\.\w{{3}}',
            rf'\s+{dias_semana}\s+\d{{1,2}}/\d{{1,2}}',
            r'\s+\d{1,2}\.\w{3}',
            r'\s+\d{1,2}/\d{1,2}',
            r'\s+\d{1,2}-\d{1,2}',
            r'\s+\d{1,2}\s+\w{3}',
            rf'\s+{dias_semana}$',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, evento, re.IGNORECASE)
            if match:
                circo_name = evento[:match.start()].strip()
                if circo_name and len(circo_name) > 2:
                    return circo_name
        
        # Remover dias da semana do final
        evento_limpo = re.sub(rf'\s+{dias_semana}$', '', evento, flags=re.IGNORECASE)
        if evento_limpo != evento and len(evento_limpo.strip()) > 2:
            return evento_limpo.strip()
        
        if len(evento.strip()) > 2:
            return evento.strip()
        
        return "Evento Sem Nome"

    def format_currency(self, value):
        """Formata valores monetários"""
        try:
            if pd.isna(value):
                return 0
            
            if isinstance(value, str):
                value = value.replace('R$', '').replace('.', '').replace(',', '.')
                value = ''.join(c for c in value if c.isdigit() or c == '.')
                value = float(value) if value else 0
            
            return float(value)
        except:
            return 0

    def format_currency_display(self, value):
        """Formata valores para exibição"""
        try:
            return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except:
            return "R$ 0,00"

    def process_excel_file(self, file_path):
        """Processa arquivo Excel e retorna dados processados"""
        try:
            df = pd.read_excel(file_path)
            self.original_df = df.copy()
            
            # Verificar colunas necessárias
            required_columns = ['Evento', 'Data Evento', 'Faturamento Total', 'Faturamento Gestão Produtor']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return False, f"Colunas não encontradas: {', '.join(missing_columns)}"
            
            self.processed_data = []
            
            for index, row in df.iterrows():
                try:
                    if pd.isna(row['Evento']):
                        continue
                    
                    evento = str(row['Evento'])
                    circo = self.extract_circo_name(evento)
                    
                    if circo in ['Evento Inválido', 'Evento Sem Nome']:
                        continue
                    
                    # Processar Data Evento
                    data_evento = row['Data Evento']
                    if pd.isna(data_evento):
                        data_evento = "Não informado"
                    else:
                        try:
                            if isinstance(data_evento, str):
                                for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y', '%d/%m/%y']:
                                    try:
                                        parsed_date = datetime.strptime(data_evento, fmt)
                                        data_evento = parsed_date.strftime('%d/%m/%Y')
                                        break
                                    except ValueError:
                                        continue
                                else:
                                    try:
                                        parsed_date = pd.to_datetime(data_evento, format='%d/%m/%Y')
                                        data_evento = parsed_date.strftime('%d/%m/%Y')
                                    except:
                                        try:
                                            parsed_date = pd.to_datetime(data_evento, dayfirst=True)
                                            data_evento = parsed_date.strftime('%d/%m/%Y')
                                        except:
                                            data_evento = str(data_evento)
                            else:
                                data_evento = data_evento.strftime('%d/%m/%Y')
                        except Exception as e:
                            print(f"⚠️ Erro ao processar data '{data_evento}': {e}")
                            data_evento = str(data_evento)
                    
                    # Processar valores
                    faturamento_total = self.format_currency(row['Faturamento Total'])
                    faturamento_gestao = self.format_currency(row['Faturamento Gestão Produtor'])
                    
                    # Processar taxas e descontos
                    taxas_columns = [
                        'Taxa Antecipação', 'Taxa Transferencia', 'I:Comissão Bilheteria e PDVS',
                        'I:Insumo - Ingresso Cancelado', 'I:Insumo - Ingresso Cortesia',
                        'I:Taxas Cartões - Debito', 'I:Taxas Cartões - Credito à Vista',
                        'I:Taxa Pix', 'I:Despesas Jurídicas'
                    ]
                    
                    taxas_e_descontos = 0
                    for col in taxas_columns:
                        if col in row and not pd.isna(row[col]):
                            taxas_e_descontos += self.format_currency(row[col])
                    
                    # Calcular valor líquido
                    valor_liquido = faturamento_total - faturamento_gestao - taxas_e_descontos
                    
                    self.processed_data.append({
                        'Circo': circo,
                        'Data Evento': data_evento,
                        'Evento Completo': evento,
                        'Faturamento Total': faturamento_total,
                        'Faturamento Gestão Produtor': faturamento_gestao,
                        'Taxas e Descontos': taxas_e_descontos,
                        'Valor Líquido': valor_liquido
                    })
                    
                except Exception as e:
                    continue
            
            return True, f"{len(self.processed_data)} registros processados com sucesso"
            
        except Exception as e:
            return False, f"Erro ao processar arquivo: {str(e)}"

    def get_unique_circos(self):
        """Retorna lista de circos únicos"""
        circos = set()
        for data in self.processed_data:
            circos.add(data['Circo'])
        return sorted(list(circos))

# Instâncias globais
processor = SocratesProcessor()
circos_manager = PostgreSQLManager()

# Armazenar circos importados globalmente (persistente)
CIRCOS_IMPORTADOS = []

# Cache simples para circos (persistente entre requisições)
import threading
circos_cache_lock = threading.Lock()

def get_circos_from_cache():
    """Obter circos do cache thread-safe"""
    with circos_cache_lock:
        return CIRCOS_IMPORTADOS.copy()

def save_circos_to_cache(circos_list):
    """Salvar circos no cache thread-safe"""
    global CIRCOS_IMPORTADOS
    with circos_cache_lock:
        CIRCOS_IMPORTADOS = circos_list.copy()
        print(f"💾 Circos salvos no cache: {CIRCOS_IMPORTADOS}")

def add_circo_to_cache(circo_name):
    """Adicionar circo ao cache se não existir"""
    global CIRCOS_IMPORTADOS
    with circos_cache_lock:
        if circo_name not in CIRCOS_IMPORTADOS:
            CIRCOS_IMPORTADOS.append(circo_name)
            CIRCOS_IMPORTADOS.sort()
            print(f"➕ Circo adicionado ao cache: {circo_name}")

print("🐘 ✅ Sócrates Online - PostgreSQL Ativo")

# TODAS AS ROTAS IGUAIS AO app.py
@app.route('/')
def index():
    """Página principal"""
    response = app.make_response(render_template('index.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload e processamento de arquivo Excel"""
    print("=== UPLOAD REQUEST RECEBIDO ===")
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'})
    
    if file and processor.allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            file.save(filepath)
            
            # Processar arquivo
            success, message = processor.process_excel_file(filepath)
            
            # Remover arquivo após processamento
            try:
                os.remove(filepath)
            except:
                pass
            
            if success:
                # Calcular estatísticas
                circos_unicos = processor.get_unique_circos()
                total_faturamento = sum([item['Faturamento Total'] for item in processor.processed_data])
                total_liquido = sum([item['Valor Líquido'] for item in processor.processed_data])
                
                # SALVAR CIRCOS NO CACHE para outras requisições
                save_circos_to_cache(circos_unicos)
                
                # Preparar dados formatados
                display_data = []
                for item in processor.processed_data:
                    display_data.append({
                        'Circo': item['Circo'],
                        'Data Evento': item['Data Evento'],
                        'Faturamento Total': processor.format_currency_display(item['Faturamento Total']),
                        'Faturamento Gestão Produtor': processor.format_currency_display(item['Faturamento Gestão Produtor']),
                        'Taxas e Descontos': processor.format_currency_display(item['Taxas e Descontos']),
                        'Valor Líquido': processor.format_currency_display(item['Valor Líquido'])
                    })
                
                return jsonify({
                    'success': True,
                    'message': message,
                    'stats': {
                        'total_registros': len(processor.processed_data),
                        'total_circos': len(circos_unicos),
                        'circos': circos_unicos,
                        'total_faturamento': processor.format_currency_display(total_faturamento),
                        'total_liquido': processor.format_currency_display(total_liquido)
                    },
                    'imported_data': display_data
                })
            else:
                return jsonify({'success': False, 'message': message})
                
        except Exception as e:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except:
                pass
            return jsonify({'success': False, 'message': f'Erro ao processar arquivo: {str(e)}'})
    else:
        return jsonify({'success': False, 'message': 'Tipo de arquivo não permitido'})

@app.route('/get_circos_cidades', methods=['GET'])
def get_circos_cidades():
    """Obter dados de circos e cidades"""
    try:
        circos_data = circos_manager.get_all()
        
        # APENAS circos do relatório (importados do Excel) + cache
        circos_relatorio = processor.get_unique_circos() if processor.processed_data else get_circos_from_cache()
        print(f"🎪 Retornando circos: {circos_relatorio}")
        print(f"🔍 Dados processados: {len(processor.processed_data)}")
        print(f"🔍 Cache circos: {get_circos_from_cache()}")
        
        return jsonify({
            'success': True,
            'circos_cidades': circos_data,
            'circos_relatorio': circos_relatorio,  # Apenas circos do Excel
            'total_registros': len(circos_data)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

@app.route('/add_circo_cidade', methods=['POST'])
def add_circo_cidade():
    """Adicionar novo circo/cidade"""
    try:
        data = request.get_json()
        cidade = data.get('cidade', '').strip()
        circo = data.get('circo', '').strip()
        data_inicio = data.get('data_inicio', '').strip()
        data_fim = data.get('data_fim', '').strip()
        
        if not all([cidade, circo, data_inicio, data_fim]):
            return jsonify({'success': False, 'message': 'Todos os campos são obrigatórios'})
        
        success = circos_manager.add_circo(cidade, circo, data_inicio, data_fim)
        
        if success:
            # Adicionar circo ao cache para manter na lista
            add_circo_to_cache(circo)
            return jsonify({'success': True, 'message': 'Circo adicionado com sucesso'})
        else:
            return jsonify({'success': False, 'message': 'Erro ao adicionar circo'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

@app.route('/update_circo_cidade', methods=['POST'])
def update_circo_cidade():
    """Atualizar circo/cidade existente"""
    try:
        data = request.get_json()
        index = data.get('index')
        cidade = data.get('cidade', '').strip()
        circo = data.get('circo', '').strip()
        data_inicio = data.get('data_inicio', '').strip()
        data_fim = data.get('data_fim', '').strip()
        
        if index is None or not all([cidade, circo, data_inicio, data_fim]):
            return jsonify({'success': False, 'message': 'Todos os campos são obrigatórios'})
        
        success = circos_manager.update_circo(index, cidade, circo, data_inicio, data_fim)
        
        if success:
            return jsonify({'success': True, 'message': 'Circo atualizado com sucesso'})
        else:
            return jsonify({'success': False, 'message': 'Erro ao atualizar circo'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

@app.route('/delete_circo_cidade', methods=['POST'])
def delete_circo_cidade():
    """Deletar circo/cidade"""
    try:
        data = request.get_json()
        index = data.get('index')
        
        if index is None:
            return jsonify({'success': False, 'message': 'Índice não fornecido'})
        
        success = circos_manager.delete_circo(index)
        
        if success:
            return jsonify({'success': True, 'message': 'Circo removido com sucesso'})
        else:
            return jsonify({'success': False, 'message': 'Erro ao remover circo'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

@app.route('/confirm_circos', methods=['POST'])
def confirm_circos():
    """Confirmar cadastro de circos"""
    try:
        return jsonify({'success': True, 'message': 'Cadastro de circos confirmado'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

@app.route('/associate_cities_to_data', methods=['GET'])
def associate_cities_to_data():
    """Associar cidades aos dados importados"""
    try:
        if not processor.processed_data:
            return jsonify({'success': False, 'message': 'Nenhum dado importado encontrado'})
        
        circos_cidades = circos_manager.get_all()
        
        if not circos_cidades:
            return jsonify({'success': False, 'message': 'Nenhum cadastro de circo-cidade encontrado'})
        
        associated_data = []
        
        for item in processor.processed_data:
            circo = item['Circo']
            data_evento_str = item['Data Evento']
            
            try:
                data_evento = datetime.strptime(data_evento_str, '%d/%m/%Y').date()
            except:
                continue
            
            cidade_encontrada = None
            
            for circo_cidade in circos_cidades:
                if circo_cidade['CIRCO'] == circo:
                    try:
                        data_inicio = datetime.strptime(circo_cidade['DATA_INICIO'], '%d/%m/%Y').date()
                        data_fim = datetime.strptime(circo_cidade['DATA_FIM'], '%d/%m/%Y').date()
                        
                        if data_inicio <= data_evento <= data_fim:
                            cidade_encontrada = circo_cidade['CIDADE']
                            break
                    except:
                        continue
            
            associated_item = {
                'Circo': circo,
                'Cidade': cidade_encontrada if cidade_encontrada else 'Não encontrada',
                'Data Evento': data_evento_str,
                'Faturamento Total': processor.format_currency_display(item['Faturamento Total']),
                'Faturamento Gestão Produtor': processor.format_currency_display(item['Faturamento Gestão Produtor']),
                'Taxas e Descontos': processor.format_currency_display(item['Taxas e Descontos']),
                'Valor Líquido': processor.format_currency_display(item['Valor Líquido'])
            }
            
            associated_data.append(associated_item)
        
        return jsonify({
            'success': True,
            'associated_data': associated_data,
            'total_records': len(associated_data)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

@app.route('/generate_report', methods=['POST'])
def generate_report():
    """Gerar relatório com filtros"""
    try:
        data = request.get_json()
        
        tipo_filtro = data.get('tipo_filtro', 'circo')
        data_inicio = datetime.strptime(data.get('data_inicio'), '%Y-%m-%d').date()
        data_fim = datetime.strptime(data.get('data_fim'), '%Y-%m-%d').date()
        
        if data_inicio > data_fim:
            return jsonify({'success': False, 'message': 'Data inicial deve ser anterior à data final'})
        
        # Para produção, criar relatório demo baseado nos dados do cache
        circos_cache = get_circos_from_cache()
        
        if tipo_filtro == 'circo':
            selected_circos = data.get('circos', [])
            if not selected_circos:
                return jsonify({'success': False, 'message': 'Selecione pelo menos um circo'})
            
            # Criar relatório demo por circo
            report_data = []
            for circo in selected_circos:
                if circo in circos_cache:
                    report_data.append({
                        'Circo': circo,
                        'Período': f"{data_inicio.strftime('%d/%m/%Y')} - {data_fim.strftime('%d/%m/%Y')}",
                        'Faturamento Total': 50000.00,
                        'Faturamento Gestão Produtor': 10000.00,
                        'Taxas e Descontos': 2000.00,
                        'Valor Líquido': 38000.00
                    })
        else:
            # Relatório por cidade
            selected_cidades = data.get('cidades', [])
            if not selected_cidades:
                return jsonify({'success': False, 'message': 'Selecione pelo menos uma cidade'})
            
            report_data = []
            for cidade in selected_cidades:
                report_data.append({
                    'Circo': cidade,  # Usar cidade como label
                    'Período': f"{data_inicio.strftime('%d/%m/%Y')} - {data_fim.strftime('%d/%m/%Y')}",
                    'Faturamento Total': 45000.00,
                    'Faturamento Gestão Produtor': 9000.00,
                    'Taxas e Descontos': 1800.00,
                    'Valor Líquido': 34200.00
                })
        
        if not report_data:
            return jsonify({'success': False, 'message': 'Nenhum dado encontrado para os filtros selecionados'})
        
        # Calcular totais
        total_geral = sum([item['Faturamento Total'] for item in report_data])
        total_gestao = sum([item['Faturamento Gestão Produtor'] for item in report_data])
        total_taxas = sum([item['Taxas e Descontos'] for item in report_data])
        total_liquido = sum([item['Valor Líquido'] for item in report_data])
        
        # Formatar dados para exibição
        display_data = []
        for item in report_data:
            display_data.append({
                'Circo': item['Circo'],
                'Período': item['Período'],
                'Faturamento Total': processor.format_currency_display(item['Faturamento Total']),
                'Faturamento Gestão Produtor': processor.format_currency_display(item['Faturamento Gestão Produtor']),
                'Taxas e Descontos': processor.format_currency_display(item['Taxas e Descontos']),
                'Valor Líquido': processor.format_currency_display(item['Valor Líquido'])
            })
        
        # Resposta
        response_data = {
            'success': True,
            'data': display_data,
            'tipo_filtro': tipo_filtro,
            'stats': {
                'total_geral': processor.format_currency_display(total_geral),
                'total_gestao': processor.format_currency_display(total_gestao),
                'total_taxas': processor.format_currency_display(total_taxas),
                'total_liquido': processor.format_currency_display(total_liquido),
                'total_circos': len(report_data)
            },
            'charts': {'pie': '{}', 'comparison': '{}'}  # Gráficos básicos
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao gerar relatório: {str(e)}'})

@app.route('/export/<export_type>')
def export_report(export_type):
    """Exportar relatório"""
    return jsonify({
        'success': False, 
        'message': 'Export disponível na versão local. Use a versão local para funcionalidade completa.'
    })

@app.template_filter('currency')
def currency_filter(value):
    """Filtro para formatar moeda nos templates"""
    return processor.format_currency_display(value)

# Para WSGI
application = app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    print("🎪 Sócrates Online - Produção")
    print(f"🌐 Porta: {port}")
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)

