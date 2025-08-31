#!/usr/bin/env python3
"""
Script para executar a aplicação web Sócrates
"""

import subprocess
import sys
import os
import webbrowser
import time
from threading import Timer

def install_requirements():
    """Instala as dependências necessárias"""
    print("🔧 Instalando dependências...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependências instaladas com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        return False

def open_browser():
    """Abre o navegador após alguns segundos"""
    time.sleep(2)
    try:
        webbrowser.open('http://localhost:5000')
        print("🌐 Navegador aberto automaticamente!")
    except:
        print("⚠️ Não foi possível abrir o navegador automaticamente")

def run_flask():
    """Executa a aplicação Flask"""
    print("🚀 Iniciando aplicação web...")
    try:
        # Abrir navegador em background
        Timer(3.0, open_browser).start()
        
        # Executar Flask
        subprocess.run([sys.executable, "app.py"])
    except KeyboardInterrupt:
        print("\n👋 Aplicação encerrada pelo usuário.")
    except Exception as e:
        print(f"❌ Erro ao executar aplicação: {e}")

def main():
    print("🎪 Sistema Sócrates - Versão Web Flask")
    print("=" * 50)
    
    # Verificar se o arquivo de requisitos existe
    if not os.path.exists("requirements.txt"):
        print("❌ Arquivo requirements.txt não encontrado!")
        sys.exit(1)
    
    # Verificar se app.py existe
    if not os.path.exists("app.py"):
        print("❌ Arquivo app.py não encontrado!")
        sys.exit(1)
    
    # Perguntar se deve instalar dependências
    install = input("📦 Instalar/atualizar dependências? (s/n): ").lower().strip()
    
    if install in ['s', 'sim', 'y', 'yes', '']:
        if not install_requirements():
            print("❌ Falha na instalação das dependências. Abortando.")
            sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🌐 A aplicação será aberta no seu navegador!")
    print("📍 URL: http://localhost:5000")
    print("🛑 Para parar: Ctrl+C")
    print("=" * 50)
    
    run_flask()

if __name__ == "__main__":
    main()
