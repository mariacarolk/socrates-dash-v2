#!/usr/bin/env python3
"""
Módulo de Banco de Dados PostgreSQL - Sócrates Online
Gerenciamento de dados de circos e cidades com persistência
"""

import os
import psycopg2
import psycopg2.extras
from datetime import datetime
import csv
import os

# Usar DATABASE_URL do ambiente (Railway/Render) ou config local
DATABASE_URL = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')

# Se não tiver DATABASE_URL do ambiente, usar config local
if not DATABASE_URL:
    try:
        from config import DATABASE_URL as LOCAL_DATABASE_URL
        DATABASE_URL = LOCAL_DATABASE_URL
        print("📄 Usando DATABASE_URL local")
    except ImportError:
        DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/socrates_online'
        print("⚠️ Usando DATABASE_URL padrão")
else:
    print("☁️ Usando DATABASE_URL da produção")

class PostgreSQLManager:
    """Classe para gerenciar dados no PostgreSQL"""
    
    def __init__(self):
        self.connection = None
        self.connect()
        self.create_tables()
        self.migrate_csv_data()
    
    def connect(self):
        """Conectar ao PostgreSQL"""
        try:
            print("🔗 Conectando ao PostgreSQL...")
            print(f"🔗 URL: {DATABASE_URL[:50]}...")
            print(f"🌐 Ambiente: {os.environ.get('RAILWAY_ENVIRONMENT', 'local')}")
            
            self.connection = psycopg2.connect(DATABASE_URL)
            print("✅ Conectado ao PostgreSQL!")
            
            # Testar conexão
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            print("✅ Conexão PostgreSQL testada e funcionando")
                
        except Exception as e:
            print(f"❌ Erro ao conectar PostgreSQL: {e}")
            print(f"🔍 DATABASE_URL presente: {'DATABASE_URL' in os.environ}")
            print(f"🔍 Variáveis disponíveis: {[k for k in os.environ.keys() if 'DATA' in k.upper()]}")
            
            # Verificar se está em produção
            if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RENDER'):
                print("🚨 ATENÇÃO: PostgreSQL não configurado em produção!")
                print("📋 Para corrigir no Railway:")
                print("   1. Dashboard → Add Service → Database → PostgreSQL")
                print("   2. Railway criará DATABASE_URL automaticamente")
                print("   3. Re-deploy acontecerá automaticamente")
                print("⚠️ Enquanto isso, operações de CRUD não funcionarão")
            
            self.connection = None
    
    def create_tables(self):
        """Criar tabelas necessárias"""
        if not self.connection:
            return
            
        try:
            cursor = self.connection.cursor()
            
            # Tabela de circos e cidades
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS circos_cidades (
                    id SERIAL PRIMARY KEY,
                    cidade VARCHAR(100) NOT NULL,
                    circo VARCHAR(100) NOT NULL,
                    data_inicio DATE NOT NULL,
                    data_fim DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Índices para performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_circos_cidades_circo 
                ON circos_cidades(circo)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_circos_cidades_cidade 
                ON circos_cidades(cidade)
            """)
            
            self.connection.commit()
            cursor.close()
            print("✅ Tabelas PostgreSQL criadas/verificadas")
            
        except Exception as e:
            print(f"❌ Erro ao criar tabelas: {e}")
            if self.connection:
                self.connection.rollback()
    
    def migrate_csv_data(self):
        """Migrar dados do CSV para PostgreSQL"""
        if not self.connection or not os.path.exists('circos_cidades.csv'):
            return
            
        try:
            cursor = self.connection.cursor()
            
            # Verificar se já há dados
            cursor.execute("SELECT COUNT(*) FROM circos_cidades")
            count = cursor.fetchone()[0]
            
            if count > 0:
                print(f"📊 PostgreSQL já tem {count} registros")
                cursor.close()
                return
            
            # Migrar dados do CSV
            print("📦 Migrando dados do CSV para PostgreSQL...")
            
            with open('circos_cidades.csv', 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                migrated = 0
                
                for row in reader:
                    try:
                        cursor.execute("""
                            INSERT INTO circos_cidades (cidade, circo, data_inicio, data_fim)
                            VALUES (%s, %s, %s, %s)
                        """, (
                            row['CIDADE'],
                            row['CIRCO'],
                            datetime.strptime(row['DATA_INICIO'], '%d/%m/%Y').date(),
                            datetime.strptime(row['DATA_FIM'], '%d/%m/%Y').date()
                        ))
                        migrated += 1
                    except Exception as e:
                        print(f"⚠️ Erro ao migrar registro {row}: {e}")
                        continue
            
            self.connection.commit()
            cursor.close()
            print(f"✅ {migrated} registros migrados para PostgreSQL")
            
        except Exception as e:
            print(f"❌ Erro na migração: {e}")
            if self.connection:
                self.connection.rollback()
    
    def get_all(self):
        """Obter todos os registros"""
        if not self.connection:
            # Fallback para CSV se PostgreSQL não disponível
            return self._get_csv_fallback()
        
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("""
                SELECT cidade, circo, 
                       TO_CHAR(data_inicio, 'DD/MM/YYYY') as data_inicio,
                       TO_CHAR(data_fim, 'DD/MM/YYYY') as data_fim
                FROM circos_cidades 
                ORDER BY cidade, circo
            """)
            
            results = cursor.fetchall()
            cursor.close()
            
            # Converter para formato compatível
            data = []
            for row in results:
                data.append({
                    'CIDADE': row['cidade'],
                    'CIRCO': row['circo'],
                    'DATA_INICIO': row['data_inicio'],
                    'DATA_FIM': row['data_fim']
                })
            
            return data
            
        except Exception as e:
            print(f"❌ Erro ao buscar dados PostgreSQL: {e}")
            return self._get_csv_fallback()
    
    def add_circo(self, cidade, circo, data_inicio, data_fim):
        """Adicionar novo registro"""
        print(f"🔄 Tentando adicionar: {circo} em {cidade} ({data_inicio} - {data_fim})")
        print(f"🔍 Conexão disponível: {self.connection is not None}")
        
        if not self.connection:
            print("❌ Sem conexão PostgreSQL - operação cancelada")
            return False
        
        try:
            cursor = self.connection.cursor()
            print("📝 Executando INSERT no PostgreSQL...")
            
            cursor.execute("""
                INSERT INTO circos_cidades (cidade, circo, data_inicio, data_fim)
                VALUES (%s, %s, %s, %s)
            """, (
                cidade,
                circo,
                datetime.strptime(data_inicio, '%d/%m/%Y').date(),
                datetime.strptime(data_fim, '%d/%m/%Y').date()
            ))
            
            self.connection.commit()
            cursor.close()
            print(f"✅ Circo adicionado ao PostgreSQL: {circo} em {cidade}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao adicionar circo: {e}")
            import traceback
            traceback.print_exc()
            if self.connection:
                self.connection.rollback()
            return False
    
    def update_circo(self, index, cidade, circo, data_inicio, data_fim):
        """Atualizar registro existente"""
        if not self.connection:
            return False
        
        try:
            # Buscar registro pelo índice (simulado)
            all_data = self.get_all()
            if 0 <= index < len(all_data):
                old_record = all_data[index]
                
                cursor = self.connection.cursor()
                cursor.execute("""
                    UPDATE circos_cidades 
                    SET cidade = %s, circo = %s, data_inicio = %s, data_fim = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE cidade = %s AND circo = %s 
                    AND data_inicio = %s AND data_fim = %s
                """, (
                    cidade, circo,
                    datetime.strptime(data_inicio, '%d/%m/%Y').date(),
                    datetime.strptime(data_fim, '%d/%m/%Y').date(),
                    old_record['CIDADE'], old_record['CIRCO'],
                    datetime.strptime(old_record['DATA_INICIO'], '%d/%m/%Y').date(),
                    datetime.strptime(old_record['DATA_FIM'], '%d/%m/%Y').date()
                ))
                
                self.connection.commit()
                cursor.close()
                print(f"✅ Circo atualizado no PostgreSQL: {circo} em {cidade}")
                return True
            
        except Exception as e:
            print(f"❌ Erro ao atualizar circo: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def delete_circo(self, index):
        """Deletar registro"""
        if not self.connection:
            return False
        
        try:
            all_data = self.get_all()
            if 0 <= index < len(all_data):
                record = all_data[index]
                
                cursor = self.connection.cursor()
                cursor.execute("""
                    DELETE FROM circos_cidades 
                    WHERE cidade = %s AND circo = %s 
                    AND data_inicio = %s AND data_fim = %s
                """, (
                    record['CIDADE'], record['CIRCO'],
                    datetime.strptime(record['DATA_INICIO'], '%d/%m/%Y').date(),
                    datetime.strptime(record['DATA_FIM'], '%d/%m/%Y').date()
                ))
                
                self.connection.commit()
                cursor.close()
                print(f"✅ Circo removido do PostgreSQL: {record['CIRCO']} em {record['CIDADE']}")
                return True
                
        except Exception as e:
            print(f"❌ Erro ao deletar circo: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def _get_csv_fallback(self):
        """Fallback para CSV se PostgreSQL não disponível"""
        try:
            if os.path.exists('circos_cidades.csv'):
                with open('circos_cidades.csv', 'r', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    return list(reader)
            return []
        except:
            return []
    
    def get_circos_unicos(self):
        """Obter lista de circos únicos"""
        data = self.get_all()
        circos = set(item['CIRCO'] for item in data)
        return sorted(list(circos))
    
    def verify_and_recover(self):
        """Verificar conexão e dados"""
        if self.connection:
            try:
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                print("✅ PostgreSQL: Conexão ativa")
                return True
            except:
                print("⚠️ PostgreSQL: Reconectando...")
                self.connect()
                return self.connection is not None
        return False
