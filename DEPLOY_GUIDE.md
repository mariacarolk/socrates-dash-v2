# 🚀 Guia de Deploy - Sócrates Online

## 📋 Opções de Deploy Gratuito

### 🥇 **RENDER.COM (Recomendado)**

#### ✅ **Vantagens:**
- 500 horas/mês grátis
- SSL automático (HTTPS)
- Domínio personalizado gratuito
- PostgreSQL grátis incluído
- Deploy automático via Git
- Logs completos
- Zero configuração

#### 📋 **Passo a Passo:**

1. **Preparar Repositório Git:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Sócrates Online"
   git branch -M main
   ```

2. **Criar Conta no Render:**
   - Acesse: https://render.com
   - Faça login com GitHub/GitLab

3. **Conectar Repositório:**
   - Clique em "New +"
   - Selecione "Web Service"
   - Conecte seu repositório GitHub/GitLab

4. **Configurar Deploy:**
   - **Name:** `socrates-online`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app_production:application --bind 0.0.0.0:$PORT`
   - **Instance Type:** `Free`

5. **Variáveis de Ambiente:**
   ```
   FLASK_ENV=production
   SECRET_KEY=sua_chave_secreta_aqui
   ```

6. **Deploy:**
   - Clique em "Create Web Service"
   - Aguarde o build (5-10 minutos)
   - Sua URL será: `https://socrates-online.onrender.com`

---

### 🥈 **RAILWAY.APP**

#### ✅ **Vantagens:**
- $5 crédito mensal grátis
- Deploy via Git muito rápido
- Interface moderna
- Banco de dados incluído

#### 📋 **Passo a Passo:**

1. **Criar Conta:**
   - Acesse: https://railway.app
   - Login com GitHub

2. **Novo Projeto:**
   - "New Project" → "Deploy from GitHub repo"
   - Selecione seu repositório

3. **Configuração Automática:**
   - Railway detecta automaticamente Flask
   - Usa `railway.json` que já criamos

4. **Variáveis de Ambiente:**
   ```
   FLASK_ENV=production
   SECRET_KEY=sua_chave_secreta_aqui
   PORT=8080
   ```

5. **Deploy:**
   - Deploy automático após commit
   - URL gerada automaticamente

---

### 🥉 **FLY.IO**

#### ✅ **Vantagens:**
- Allowance generoso
- Performance excelente
- Regiões globais

#### 📋 **Passo a Passo:**

1. **Instalar Flyctl:**
   ```bash
   # Windows (PowerShell)
   iwr https://fly.io/install.ps1 -useb | iex
   ```

2. **Login:**
   ```bash
   fly auth login
   ```

3. **Deploy:**
   ```bash
   fly launch
   fly deploy
   ```

---

## 🛠️ **Preparação do Projeto**

### **Arquivos Criados:**
- ✅ `render.yaml` - Configuração Render
- ✅ `railway.json` - Configuração Railway  
- ✅ `fly.toml` - Configuração Fly.io
- ✅ `.gitignore` - Ignorar arquivos desnecessários
- ✅ `uploads/.gitkeep` - Manter pasta no Git

### **Arquivos Otimizados:**
- ✅ `app_production.py` - Versão para produção
- ✅ `Procfile` - Configuração Gunicorn
- ✅ `requirements.txt` - Dependências + Gunicorn

---

## 🎯 **Recomendação Final**

**Use RENDER.COM** porque:
- ✅ Mais fácil para iniciantes
- ✅ 500 horas/mês são suficientes
- ✅ SSL automático
- ✅ Domínio gratuito
- ✅ Zero configuração
- ✅ Logs excelentes para debug

### **Próximos Passos:**

1. **Criar repositório Git** (GitHub/GitLab)
2. **Fazer push do código**
3. **Conectar no Render.com**
4. **Configurar variáveis de ambiente**
5. **Deploy automático!**

**Sua URL final será algo como:**
`https://socrates-online.onrender.com`

---

## 🔧 **Troubleshooting**

### **Problemas Comuns:**
- **Build falha:** Verificar `requirements.txt`
- **App não inicia:** Verificar `PORT` e `HOST`
- **Uploads não funcionam:** Verificar permissões de pasta
- **CSV não persiste:** Usar banco de dados em produção

### **Melhorias Futuras:**
- Migrar CSV para PostgreSQL (Render oferece grátis)
- Implementar cache Redis
- Otimizar para múltiplos workers
