#!/usr/bin/env python3
"""
Script de Deploy Automatizado - Sócrates Online
Prepara o projeto para deploy em plataformas gratuitas
"""

import os
import subprocess
import sys

def run_command(command, description):
    """Executa comando e mostra resultado"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Sucesso!")
            return True
        else:
            print(f"❌ {description} - Erro:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ {description} - Exceção: {e}")
        return False

def check_git():
    """Verificar se Git está configurado"""
    if not os.path.exists('.git'):
        print("📁 Inicializando repositório Git...")
        run_command("git init", "Inicializar Git")
        run_command("git branch -M main", "Configurar branch main")
    
    # Verificar se há mudanças para commit
    result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    if result.stdout.strip():
        print("📝 Adicionando arquivos ao Git...")
        run_command("git add .", "Adicionar arquivos")
        run_command('git commit -m "Deploy: Sócrates Online com todas funcionalidades"', "Commit inicial")
    else:
        print("✅ Git já está atualizado")

def show_deployment_options():
    """Mostrar opções de deploy"""
    print("\n" + "="*60)
    print("🚀 OPÇÕES DE DEPLOY GRATUITO")
    print("="*60)
    
    print("\n🥇 RENDER.COM (Recomendado)")
    print("   • 500 horas/mês grátis")
    print("   • SSL automático")
    print("   • Domínio personalizado")
    print("   • URL: https://render.com")
    
    print("\n🥈 RAILWAY.APP")
    print("   • $5 crédito mensal")
    print("   • Deploy super rápido")
    print("   • URL: https://railway.app")
    
    print("\n🥉 FLY.IO")
    print("   • Allowance generoso")
    print("   • Performance excelente")
    print("   • URL: https://fly.io")
    
    print("\n" + "="*60)

def main():
    print("🎪 Sócrates Online - Deploy Automatizado")
    print("="*50)
    
    # Verificar arquivos necessários
    required_files = [
        'app.py', 'app_production.py', 'requirements.txt', 
        'Procfile', 'templates/index.html', 'static/img/logo.png'
    ]
    
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        print(f"❌ Arquivos necessários não encontrados: {missing_files}")
        sys.exit(1)
    
    print("✅ Todos os arquivos necessários encontrados")
    
    # Preparar Git
    check_git()
    
    # Mostrar opções
    show_deployment_options()
    
    print("\n📋 PRÓXIMOS PASSOS:")
    print("1. Escolha uma plataforma (Render recomendado)")
    print("2. Crie conta na plataforma escolhida")
    print("3. Conecte seu repositório GitHub/GitLab")
    print("4. Configure as variáveis de ambiente:")
    print("   - FLASK_ENV=production")
    print("   - SECRET_KEY=sua_chave_secreta")
    print("5. Deploy automático!")
    
    print("\n🌐 Sua aplicação estará disponível em uma URL como:")
    print("   https://socrates-online.onrender.com")
    print("   https://socrates-online.up.railway.app")
    print("   https://socrates-online.fly.dev")
    
    print("\n📖 Consulte DEPLOY_GUIDE.md para detalhes completos!")

if __name__ == "__main__":
    main()
