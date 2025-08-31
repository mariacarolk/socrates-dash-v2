#!/usr/bin/env python3
"""
Sócrates Online - Aplicação Web Flask com PostgreSQL
Importação de Relatório de Faturamento de Eventos
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
from config import SECRET_KEY, MAX_CONTENT_LENGTH, UPLOAD_FOLDER

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Configurações
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
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

    def filter_and_generate_report(self, selected_circos, data_inicio, data_fim):
        """Filtra dados e gera relatório por circos"""
        df = pd.DataFrame(self.processed_data)
        
        if df.empty:
            return []
        
        # Filtrar por circos selecionados
        df = df[df['Circo'].isin(selected_circos)]
        
        # Filtrar por período
        try:
            df['Data Evento'] = pd.to_datetime(df['Data Evento'], format='%d/%m/%Y', errors='coerce')
            df = df.dropna(subset=['Data Evento'])
            df = df[
                (df['Data Evento'].dt.date >= data_inicio) & 
                (df['Data Evento'].dt.date <= data_fim)
            ]
        except Exception as e:
            print(f"⚠️ Erro no filtro de datas: {e}")
            pass
        
        if df.empty:
            return []
        
        # Agrupar por circo
        grouped = df.groupby('Circo').agg({
            'Faturamento Total': 'sum',
            'Faturamento Gestão Produtor': 'sum',
            'Taxas e Descontos': 'sum',
            'Valor Líquido': 'sum'
        }).reset_index()
        
        # Criar dados do relatório
        report_data = []
        periodo_str = f"{data_inicio.strftime('%d/%m/%Y')} - {data_fim.strftime('%d/%m/%Y')}"
        
        for _, row in grouped.iterrows():
            report_data.append({
                'Circo': row['Circo'],
                'Período': periodo_str,
                'Faturamento Total': row['Faturamento Total'],
                'Faturamento Gestão Produtor': row['Faturamento Gestão Produtor'],
                'Taxas e Descontos': row['Taxas e Descontos'],
                'Valor Líquido': row['Valor Líquido'],
                'Total Geral': row['Faturamento Total']
            })
        
        self.last_report_data = report_data
        return report_data
    
    def filter_and_generate_report_by_cities(self, selected_cidades, data_inicio, data_fim):
        """Filtrar dados e gerar relatório agrupado por cidades"""
        if not self.processed_data:
            return []
        
        df = pd.DataFrame(self.processed_data)
        
        # Filtrar por período
        try:
            df['Data Evento Parsed'] = pd.to_datetime(df['Data Evento'], format='%d/%m/%Y')
            df = df[
                (df['Data Evento Parsed'].dt.date >= data_inicio) &
                (df['Data Evento Parsed'].dt.date <= data_fim)
            ]
        except:
            pass
        
        if df.empty:
            return []
        
        # Fazer associação com cidades
        circos_cidades = circos_manager.get_all()
        df['Cidade'] = 'Não encontrada'
        
        for index, row in df.iterrows():
            circo = row['Circo']
            data_evento_str = row['Data Evento']
            
            try:
                data_evento = datetime.strptime(data_evento_str, '%d/%m/%Y').date()
            except:
                continue
            
            for circo_cidade in circos_cidades:
                if circo_cidade['CIRCO'] == circo:
                    try:
                        data_inicio_cc = datetime.strptime(circo_cidade['DATA_INICIO'], '%d/%m/%Y').date()
                        data_fim_cc = datetime.strptime(circo_cidade['DATA_FIM'], '%d/%m/%Y').date()
                        
                        if data_inicio_cc <= data_evento <= data_fim_cc:
                            df.at[index, 'Cidade'] = circo_cidade['CIDADE']
                            break
                    except:
                        continue
        
        # Filtrar por cidades selecionadas
        df = df[df['Cidade'].isin(selected_cidades)]
        
        if df.empty:
            return []
        
        # Agrupar por cidade
        grouped = df.groupby('Cidade').agg({
            'Faturamento Total': 'sum',
            'Faturamento Gestão Produtor': 'sum',
            'Taxas e Descontos': 'sum',
            'Valor Líquido': 'sum'
        }).reset_index()
        
        # Criar dados do relatório
        report_data = []
        periodo_str = f"{data_inicio.strftime('%d/%m/%Y')} - {data_fim.strftime('%d/%m/%Y')}"
        
        for _, row in grouped.iterrows():
            report_data.append({
                'Circo': row['Cidade'],  # Usar cidade como label
                'Período': periodo_str,
                'Faturamento Total': row['Faturamento Total'],
                'Faturamento Gestão Produtor': row['Faturamento Gestão Produtor'],
                'Taxas e Descontos': row['Taxas e Descontos'],
                'Valor Líquido': row['Valor Líquido'],
                'Total Geral': row['Faturamento Total']
            })
        
        self.last_report_data = report_data
        return report_data

    def get_unique_circos(self):
        """Retorna lista de circos únicos"""
        circos = set()
        for data in self.processed_data:
            circos.add(data['Circo'])
        return sorted(list(circos))

    def create_excel_export(self, report_data):
        """Cria arquivo Excel para download"""
        output = io.BytesIO()
        
        df_export = pd.DataFrame(report_data)
        
        # Formatar valores monetários
        for col in ['Faturamento Total', 'Faturamento Gestão Produtor', 'Taxas e Descontos', 'Valor Líquido', 'Total Geral']:
            if col in df_export.columns:
                df_export[col] = df_export[col].apply(self.format_currency_display)
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_export.to_excel(writer, sheet_name='Relatório Sócrates Online', index=False)
            
            worksheet = writer.sheets['Relatório Sócrates Online']
            
            # Larguras das colunas
            column_widths = {
                'A': 25, 'B': 25, 'C': 20, 'D': 30, 'E': 20, 'F': 20,
            }
            
            for col_letter, width in column_widths.items():
                worksheet.column_dimensions[col_letter].width = width
            
            # Formatação
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="667EEA", end_color="667EEA", fill_type="solid")
            header_alignment = Alignment(horizontal="center", vertical="center")
            
            # Aplicar formatação ao cabeçalho
            for col in range(1, len(df_export.columns) + 1):
                cell = worksheet.cell(row=1, column=col)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
            
            # Formatação das células de dados
            data_alignment = Alignment(horizontal="center", vertical="center")
            border = Border(
                left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'), bottom=Side(style='thin')
            )
            
            for row in range(2, len(df_export) + 2):
                for col in range(1, len(df_export.columns) + 1):
                    cell = worksheet.cell(row=row, column=col)
                    cell.alignment = data_alignment
                    cell.border = border
            
            for row in range(1, len(df_export) + 2):
                worksheet.row_dimensions[row].height = 20
        
        output.seek(0)
        return output

    def create_pdf_export(self, report_data):
        """Cria arquivo PDF para download"""
        output = io.BytesIO()
        
        doc = SimpleDocTemplate(output, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Cabeçalho
        brand_style = ParagraphStyle(
            'BrandStyle', parent=styles['Heading1'], fontSize=24,
            textColor=colors.HexColor('#667eea'), alignment=1, spaceAfter=8
        )
        brand_title = Paragraph("SÓCRATES ONLINE", brand_style)
        story.append(brand_title)
        
        title_style = ParagraphStyle(
            'CustomTitle', parent=styles['Heading2'], fontSize=16,
            textColor=colors.HexColor('#764ba2'), alignment=1, spaceAfter=12
        )
        title = Paragraph("Relatório de Faturamento por Evento", title_style)
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Data de geração
        date_style = ParagraphStyle('DateStyle', parent=styles['Normal'], fontSize=10, alignment=1)
        date_text = Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", date_style)
        story.append(date_text)
        story.append(Spacer(1, 30))
        
        if report_data:
            # Tabela
            data = [['Circo', 'Período', 'Fatur. Total', 'Gestão Prod.', 'Taxas/Desc.', 'Valor Líquido']]
            
            for item in report_data:
                circo_name = item['Circo']
                if len(circo_name) > 15:
                    circo_name = circo_name[:15] + "..."
                
                data.append([
                    circo_name, item['Período'],
                    self.format_currency_display(item['Faturamento Total']),
                    self.format_currency_display(item['Faturamento Gestão Produtor']),
                    self.format_currency_display(item['Taxas e Descontos']),
                    self.format_currency_display(item['Valor Líquido'])
                ])
            
            # Totais
            total_geral = sum(item['Faturamento Total'] for item in report_data)
            total_gestao = sum(item['Faturamento Gestão Produtor'] for item in report_data)
            total_taxas = sum(item['Taxas e Descontos'] for item in report_data)
            total_liquido = sum(item['Valor Líquido'] for item in report_data)
            
            data.append([
                'TOTAL', '',
                self.format_currency_display(total_geral),
                self.format_currency_display(total_gestao),
                self.format_currency_display(total_taxas),
                self.format_currency_display(total_liquido)
            ])
            
            table = Table(data, colWidths=[1.5*inch, 1.2*inch, 1.0*inch, 1.0*inch, 1.0*inch, 1.0*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
                ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -2), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.beige, colors.lightgrey]),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#764ba2')),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ]))
            
            story.append(table)
            story.append(Spacer(1, 20))
            
            # Resumo
            summary_style = ParagraphStyle(
                'SummaryStyle', parent=styles['Normal'], fontSize=10,
                alignment=1, textColor=colors.HexColor('#333333')
            )
            
            summary_text = f"""
            <b>Resumo Executivo:</b><br/>
            • Total de Circos: {len(report_data)}<br/>
            • Faturamento Total: {self.format_currency_display(total_geral)}<br/>
            • Valor Gestão Produtor: {self.format_currency_display(total_gestao)}<br/>
            • Taxas e Descontos: {self.format_currency_display(total_taxas)}<br/>
            • Valor Líquido: {self.format_currency_display(total_liquido)}
            """
            
            summary = Paragraph(summary_text, summary_style)
            story.append(summary)
        else:
            no_data = Paragraph("Nenhum dado encontrado para os filtros selecionados.", styles['Normal'])
            story.append(no_data)
        
        doc.build(story)
        output.seek(0)
        return output

# Instâncias globais
processor = SocratesProcessor()
circos_manager = PostgreSQLManager()

print("🐘 ✅ Sócrates Online - PostgreSQL Ativo")

# Rotas da aplicação
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
        
        # APENAS circos do relatório (importados do Excel)
        circos_relatorio = processor.get_unique_circos() if processor.processed_data else []
        
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
        
        if tipo_filtro == 'circo':
            selected_circos = data.get('circos', [])
            if not selected_circos:
                return jsonify({'success': False, 'message': 'Selecione pelo menos um circo'})
            
            report_data = processor.filter_and_generate_report(selected_circos, data_inicio, data_fim)
        else:
            selected_cidades = data.get('cidades', [])
            if not selected_cidades:
                return jsonify({'success': False, 'message': 'Selecione pelo menos uma cidade'})
            
            report_data = processor.filter_and_generate_report_by_cities(selected_cidades, data_inicio, data_fim)
        
        if not report_data:
            return jsonify({'success': False, 'message': 'Nenhum dado encontrado para os filtros selecionados'})
        
        processor.last_report_data = report_data
        
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
        
        # Gráficos
        fig_pie = fig_comp = None
        
        if PLOTLY_AVAILABLE:
            try:
                # Gráfico de pizza
                gestao_liquido_data = {
                    'Tipo': ['Valor líquido em dinheiro', 'Valor Líquido'],
                    'Valor': [total_gestao, total_liquido]
                }
                
                fig_pie = px.pie(
                    gestao_liquido_data, values='Valor', names='Tipo',
                    title='Distribuição: Valor líquido em dinheiro vs Valor Líquido',
                    color_discrete_sequence=['#ff7f0e', '#28a745']
                )
                
                # Gráfico comparativo
                comparison_data = []
                label_type = 'Cidade' if tipo_filtro == 'cidade' else 'Circo'
                
                for item in report_data:
                    comparison_data.extend([
                        {label_type: item['Circo'], 'Tipo': 'Valor líquido em dinheiro', 'Valor': item['Faturamento Gestão Produtor']},
                        {label_type: item['Circo'], 'Tipo': 'Valor Líquido', 'Valor': item['Valor Líquido']}
                    ])
                
                chart_title = f'Comparativo Valor líquido em dinheiro vs Valor Líquido por {label_type}'
                
                fig_comp = px.bar(
                    comparison_data, x=label_type, y='Valor', color='Tipo',
                    title=chart_title, barmode='group'
                )
                
            except Exception as e:
                print(f"⚠️ Erro ao gerar gráficos: {e}")
                fig_pie = fig_comp = None
        
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
            }
        }
        
        # Adicionar gráficos
        if PLOTLY_AVAILABLE and fig_pie and fig_comp:
            try:
                response_data['charts'] = {
                    'pie': json.dumps(fig_pie, cls=plotly.utils.PlotlyJSONEncoder),
                    'comparison': json.dumps(fig_comp, cls=plotly.utils.PlotlyJSONEncoder)
                }
            except Exception as e:
                response_data['charts'] = {'pie': '{}', 'comparison': '{}'}
        else:
            response_data['charts'] = {'pie': '{}', 'comparison': '{}'}
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao gerar relatório: {str(e)}'})

@app.route('/export/<export_type>')
def export_report(export_type):
    """Exportar relatório"""
    try:
        if not hasattr(processor, 'last_report_data') or not processor.last_report_data:
            flash('Gere um relatório primeiro antes de exportar', 'warning')
            return redirect(url_for('index'))
        
        if export_type == 'excel':
            excel_data = processor.create_excel_export(processor.last_report_data)
            filename = f"relatorio_socrates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            return send_file(
                excel_data, as_attachment=True, download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        
        elif export_type == 'pdf':
            pdf_data = processor.create_pdf_export(processor.last_report_data)
            filename = f"relatorio_socrates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            return send_file(
                pdf_data, as_attachment=True, download_name=filename,
                mimetype='application/pdf'
            )
        
        else:
            flash('Tipo de exportação inválido', 'error')
            return redirect(url_for('index'))
            
    except Exception as e:
        flash(f'Erro ao exportar: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.template_filter('currency')
def currency_filter(value):
    """Filtro para formatar moeda nos templates"""
    return processor.format_currency_display(value)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
        print("🎪 Sócrates Online iniciando...")
        print("🌐 Acesse: http://localhost:5000")
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
