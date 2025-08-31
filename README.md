# Sistema Sócrates - Relatórios de Faturamento

Sistema completo para importar arquivos Excel e gerar relatórios de faturamento de eventos de circo.

## 🎯 Versão Disponível

- **🌐 Web (Streamlit)**: Interface moderna no navegador com gráficos e exportação

## Funcionalidades

- **Importação de Excel**: Carrega arquivos `.xlsx` e `.xls`
- **Processamento de dados**: 
  - Extrai nome do circo da coluna 'Evento' (texto antes da barra `|`)
  - Processa datas de eventos
  - Formata valores de faturamento
- **Interface gráfica**: Exibe dados em tabela organizada
- **Validação**: Verifica se as colunas necessárias existem no arquivo
- **Geração de Relatórios**: 
  - Filtros por circo (seleção múltipla)
  - Filtros por período (data inicial e final)
  - Soma de faturamentos por circo
  - Exibição de resultados em tabela dedicada
- **📊 Versão Web Adicional**:
  - Interface moderna e responsiva
  - Gráficos interativos (barras, pizza, comparativos)
  - Métricas em tempo real
  - Exportação para Excel e PDF
  - Visualizações com Plotly

## Colunas Processadas

- **Circo**: Extraído da coluna 'Evento' (nome antes da barra)
- **Data Evento**: Data do evento formatada
- **Faturamento Total**: Valor total formatado em R$
- **Faturamento Produtor**: Valor de gestão do produtor formatado em R$
- **Valor Líquido**: Faturamento Total - Faturamento Produtor (valor líquido)

## Como usar

### 🌐 **Versão Web**

1. **Execução rápida**:
   ```bash
   python run_web.py
   ```
   
2. **Ou execução manual**:
   ```bash
   pip install -r requirements.txt
   streamlit run app_web.py
   ```

3. **Usar no navegador**:
   - Acesse: `http://localhost:8501`
   - Faça upload do arquivo Excel na barra lateral
   - Visualize todos os dados importados na tabela
   - Configure os filtros (circos e período)  
   - Gere relatórios com gráficos interativos
   - Exporte para Excel ou PDF

## Requisitos

- Python 3.7+
- pandas
- openpyxl
- xlrd
- streamlit
- plotly
- reportlab

## Estrutura do Arquivo Excel

O arquivo Excel deve conter as seguintes colunas:
- `Evento`
- `Data Evento`
- `Faturamento Total`
- `Faturamento Gestão Produtor`


