# Sistema Sócrates - Versão Flask

Sistema web para análise e geração de relatórios de faturamento de circos, convertido de Streamlit para Flask para facilitar a publicação.

## 🚀 Características

- **Interface Web Moderna**: Bootstrap 5 com design responsivo
- **Upload de Arquivos**: Drag & drop para arquivos Excel
- **Relatórios Dinâmicos**: Filtros por circo e período
- **Visualizações**: Gráficos interativos com Plotly
- **Exportação**: Download em Excel e PDF
- **Fácil Publicação**: Compatível com diversos serviços de hosting

## 📋 Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

## 🛠️ Instalação e Execução

### Método 1: Execução Automática (Recomendado)

```bash
python run_web.py
```

O script irá:
1. Verificar e instalar dependências
2. Iniciar a aplicação Flask
3. Abrir automaticamente no navegador
4. Aplicação ficará disponível em: http://localhost:5000

### Método 2: Execução Manual

1. **Instalar dependências:**
```bash
pip install -r requirements.txt
```

2. **Executar aplicação:**
```bash
python app.py
```

3. **Acessar no navegador:**
```
http://localhost:5000
```

## 📂 Estrutura do Projeto

```
socrates-dash-v2/
├── app.py                 # Aplicação Flask principal
├── run_web.py            # Script de execução
├── requirements.txt      # Dependências Python
├── templates/
│   └── index.html       # Template HTML principal
├── static/
│   ├── css/            # Arquivos CSS customizados
│   └── js/             # Scripts JavaScript
├── uploads/            # Pasta temporária para uploads
└── README_FLASK.md     # Este arquivo
```

## 💻 Como Usar

### 1. Upload do Arquivo Excel

- Clique na área de upload ou arraste o arquivo Excel
- Formatos suportados: `.xlsx`, `.xls`
- Tamanho máximo: 16MB

**Colunas necessárias no Excel:**
- `Evento`: Nome do evento/circo
- `Data Evento`: Data do evento
- `Faturamento Total`: Valor total
- `Faturamento Gestão Produtor`: Valor Gestão Produtor
- `Faturamento Web`: Valor Web

### 2. Configurar Filtros

- **Circos**: Selecione um ou mais circos
- **Período**: Defina data inicial e final
- Clique em "Gerar Relatório"

### 3. Visualizar Resultados

- **Métricas**: Resumo dos valores
- **Tabela**: Detalhamento por circo
- **Gráficos**: Visualizações interativas

### 4. Exportar Relatórios

- **Excel**: Download em formato `.xlsx`
- **PDF**: Download em formato `.pdf`

## 🌐 Publicação (Deploy)

### Heroku

1. **Criar Procfile:**
```
web: python app.py
```

2. **Configurar porta dinâmica no app.py:**
```python
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
```

### Vercel

1. **Criar vercel.json:**
```json
{
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ]
}
```

### PythonAnywhere

1. Fazer upload dos arquivos
2. Configurar Web App como Flask
3. Apontar para `app.py`

### Railway / Render

1. Conectar repositório Git
2. Configurar como Python/Flask app
3. Deploy automático

## 🔧 Configurações

### Variáveis de Ambiente

```bash
# Opcional - para produção
export FLASK_ENV=production
export SECRET_KEY=sua_chave_secreta_aqui
```

### Configurações de Produção

Para produção, edite `app.py`:

```python
# Desabilitar debug
app.run(debug=False, host='0.0.0.0', port=5000)

# Usar chave secreta do ambiente
app.secret_key = os.environ.get('SECRET_KEY', 'fallback_key')
```

## 📊 Funcionalidades

### Processamento de Dados
- Extração automática do nome do circo
- Formatação de valores monetários
- Filtros por data e circo
- Agrupamento e totalização

### Visualizações
- Gráfico de barras por circo
- Gráfico de pizza Gestão Produtor vs Web
- Comparativo Gestão Produtor vs Web por circo

### Exportação
- Excel com formatação
- PDF com layout profissional
- Nomes de arquivo com timestamp

## 🐛 Solução de Problemas

### Erro de Dependências
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Porta já em uso
```bash
# Usar porta diferente
python app.py
# E no código alterar para: app.run(port=8080)
```

### Problemas com Upload
- Verificar tamanho do arquivo (máx 16MB)
- Verificar formato (.xlsx ou .xls)
- Verificar colunas obrigatórias

## 📞 Suporte

Para problemas ou sugestões:
1. Verificar logs no terminal
2. Verificar formato do arquivo Excel
3. Testar com arquivo de exemplo

## 🔄 Diferenças da Versão Streamlit

| Característica | Streamlit | Flask |
|---|---|---|
| Interface | Automática | Customizada |
| Controle | Limitado | Total |
| Deploy | Streamlit Cloud | Qualquer servidor |
| Customização | Restrita | Ilimitada |
| Performance | Boa | Melhor |

## 📝 Licença

Este projeto é de uso interno e educacional.

---

**Sistema Sócrates - Versão Flask © 2025**
