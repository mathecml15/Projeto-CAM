"""
================================================================================
DATABASE - Módulo de banco de dados
================================================================================

Este arquivo contém todas as funções relacionadas ao banco de dados:
- Conexão com o banco de dados
- Criação de tabelas
- Operações CRUD (Create, Read, Update, Delete)
- Migração de dados do JSON para SQL

BANCOS SUPORTADOS:
- SQLite (padrão, mais simples, não requer servidor)
- PostgreSQL (produção, mais robusto)
- MySQL (produção, mais comum)
"""

import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Nome do arquivo do banco de dados SQLite
DB_FILE = "vms_database.db"

# ============================================================================
# CONFIGURAÇÃO DO BANCO DE DADOS
# ============================================================================

# Tipo de banco de dados a usar
# Opções: 'sqlite', 'postgresql', 'mysql'
# Alterado para MySQL conforme solicitado
DB_TYPE = os.getenv('DB_TYPE', 'mysql')  # Padrão: MySQL

# Configurações de conexão (para PostgreSQL/MySQL)
# IMPORTANTE: Configure o arquivo .env com suas credenciais
# As senhas NÃO ficam mais no código por segurança!
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '3306')  # MySQL padrão: 3306
DB_NAME = os.getenv('DB_NAME')  # Carrega do .env
DB_USER = os.getenv('DB_USER')  # Carrega do .env
DB_PASSWORD = os.getenv('DB_PASSWORD')  # Carrega do .env (NUNCA coloque a senha aqui!)


def get_db_connection():
    """
    Cria uma conexão com o banco de dados.
    
    Retorna: Objeto de conexão com o banco de dados
    """
    if DB_TYPE == 'sqlite':
        # SQLite - banco de dados em arquivo
        # Cria o arquivo se não existir
        conn = sqlite3.connect(DB_FILE)
        # Configura para retornar dicionários ao invés de tuplas
        conn.row_factory = sqlite3.Row
        return conn
    elif DB_TYPE == 'postgresql':
        # PostgreSQL - requer psycopg2
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            return conn
        except ImportError:
            raise ImportError("Para usar PostgreSQL, instale: pip install psycopg2-binary")
    elif DB_TYPE == 'mysql':
        # MySQL - requer pymysql ou mysql-connector-python
        try:
            import pymysql
            conn = pymysql.connect(
                host=DB_HOST,
                port=int(DB_PORT),
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                cursorclass=pymysql.cursors.DictCursor
            )
            return conn
        except ImportError:
            raise ImportError("Para usar MySQL, instale: pip install pymysql")
    else:
        raise ValueError(f"Tipo de banco de dados não suportado: {DB_TYPE}")


def init_database():
    """
    Inicializa o banco de dados criando as tabelas necessárias.
    Se as tabelas já existirem, não faz nada.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Cria a tabela de usuários
        # SQLite usa tipos diferentes, mas funciona com TEXT, INTEGER, etc.
        if DB_TYPE == 'sqlite':
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    cpf TEXT UNIQUE NOT NULL,
                    data_nascimento TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_login TEXT,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            # Cria índices para melhorar performance (SQLite)
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_username ON users(username)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_email ON users(email)
            ''')
        elif DB_TYPE == 'postgresql':
            # PostgreSQL
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    cpf VARCHAR(14) UNIQUE NOT NULL,
                    data_nascimento DATE NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            # Cria índices para melhorar performance (PostgreSQL)
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_username ON users(username)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_email ON users(email)
            ''')
        else:
            # MySQL
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    cpf VARCHAR(14) UNIQUE NOT NULL,
                    data_nascimento DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    INDEX idx_username (username),
                    INDEX idx_email (email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
        
        # Salva as mudanças
        conn.commit()
        print("Banco de dados inicializado com sucesso!")
        
    except Exception as e:
        print(f"Erro ao inicializar banco de dados: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def get_db():
    """
    Context manager para gerenciar conexões com o banco de dados.
    Garante que a conexão seja fechada corretamente.
    
    Uso:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
    """
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def user_exists(username):
    """
    Verifica se um usuário já existe no banco de dados.
    
    username: Nome de usuário para verificar
    
    Retorna: True se o usuário existe, False caso contrário
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Usa placeholder correto baseado no tipo de banco
        if DB_TYPE == 'sqlite':
            cursor.execute('SELECT id FROM users WHERE username = ?', (username.lower(),))
        else:
            # PostgreSQL/MySQL usam %s
            cursor.execute('SELECT id FROM users WHERE username = %s', (username.lower(),))
        result = cursor.fetchone()
        return result is not None
    finally:
        conn.close()


def create_user_db(username, password_hash, email, cpf, data_nascimento, created_at=None):
    """
    Cria um novo usuário no banco de dados.
    
    username: Nome de usuário
    password_hash: Hash da senha
    email: Email do usuário
    cpf: CPF do usuário
    data_nascimento: Data de nascimento (formato YYYY-MM-DD)
    created_at: Data de criação (opcional, usa data atual se None)
    
    Retorna: (success, message, user_id)
             - success: True se o usuário foi criado, False caso contrário
             - message: Mensagem de erro ou sucesso
             - user_id: ID do usuário criado (ou None se falhou)
    """
    if created_at is None:
        created_at = datetime.now().isoformat()
    
    username_lower = username.lower()
    email_lower = email.lower()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Insere o novo usuário
            if DB_TYPE == 'sqlite':
                cursor.execute('''
                    INSERT INTO users (username, password_hash, email, cpf, data_nascimento, created_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (username_lower, password_hash, email_lower, cpf, data_nascimento, created_at, 1))
                user_id = cursor.lastrowid
            elif DB_TYPE == 'postgresql':
                cursor.execute('''
                    INSERT INTO users (username, password_hash, email, cpf, data_nascimento, created_at, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
                ''', (username_lower, password_hash, email_lower, cpf, data_nascimento, created_at, True))
                user_id = cursor.fetchone()[0]
            else:
                # MySQL
                cursor.execute('''
                    INSERT INTO users (username, password_hash, email, cpf, data_nascimento, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (username_lower, password_hash, email_lower, cpf, data_nascimento, True))
                user_id = cursor.lastrowid
            
            conn.commit()
            return True, "Usuário criado com sucesso!", user_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
            
    except Exception as e:
        error_msg = str(e)
        if 'username' in error_msg.lower() and ('UNIQUE' in error_msg or 'duplicate' in error_msg.lower() or '1062' in error_msg):
            return False, "Nome de usuário já existe", None
        elif 'email' in error_msg.lower() and ('UNIQUE' in error_msg or 'duplicate' in error_msg.lower() or '1062' in error_msg):
            return False, "Email já cadastrado", None
        elif 'cpf' in error_msg.lower() and ('UNIQUE' in error_msg or 'duplicate' in error_msg.lower() or '1062' in error_msg):
            return False, "CPF já cadastrado", None
        else:
            return False, f"Erro ao criar usuário: {error_msg}", None


def get_user_by_username(username):
    """
    Busca um usuário pelo nome de usuário.
    
    username: Nome de usuário
    
    Retorna: Dicionário com dados do usuário ou None se não encontrado
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Usa placeholder correto baseado no tipo de banco
        if DB_TYPE == 'sqlite':
            cursor.execute('SELECT * FROM users WHERE username = ?', (username.lower(),))
            row = cursor.fetchone()
            if row:
                return dict(row)
        elif DB_TYPE == 'postgresql':
            # PostgreSQL - precisa usar RealDictCursor para retornar dicionário
            import psycopg2.extras
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute('SELECT * FROM users WHERE username = %s', (username.lower(),))
            row = cursor.fetchone()
            if row:
                return dict(row)
        else:
            # MySQL - pymysql já retorna dicionário
            cursor.execute('SELECT * FROM users WHERE username = %s', (username.lower(),))
            row = cursor.fetchone()
            if row:
                return row
        
        return None
    finally:
        conn.close()


def get_user_password_hash(username):
    """
    Busca o hash da senha de um usuário.
    
    username: Nome de usuário
    
    Retorna: Hash da senha ou None se o usuário não existir
    """
    user = get_user_by_username(username)
    if user:
        return user['password_hash']
    return None


def update_user_last_login(username):
    """
    Atualiza a data do último login de um usuário.
    
    username: Nome de usuário
    """
    last_login = datetime.now().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Usa placeholder correto baseado no tipo de banco
        if DB_TYPE == 'sqlite':
            cursor.execute('''
                UPDATE users 
                SET last_login = ? 
                WHERE username = ?
            ''', (last_login, username.lower()))
        else:
            # PostgreSQL/MySQL
            cursor.execute('''
                UPDATE users 
                SET last_login = %s 
                WHERE username = %s
            ''', (last_login, username.lower()))
        
        conn.commit()
    finally:
        conn.close()


def get_all_users_db():
    """
    Retorna a lista de todos os usuários (apenas nomes, sem senhas).
    
    Retorna: Lista de nomes de usuários
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Usa placeholder correto baseado no tipo de banco
        if DB_TYPE == 'sqlite':
            cursor.execute('SELECT username FROM users WHERE is_active = ?', (1,))
            rows = cursor.fetchall()
            return [row['username'] for row in rows]
        elif DB_TYPE == 'postgresql':
            # PostgreSQL - precisa usar RealDictCursor
            import psycopg2.extras
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute('SELECT username FROM users WHERE is_active = %s', (True,))
            rows = cursor.fetchall()
            return [row['username'] for row in rows]
        else:
            # MySQL - pymysql já retorna dicionário
            cursor.execute('SELECT username FROM users WHERE is_active = %s', (True,))
            rows = cursor.fetchall()
            return [row['username'] for row in rows]
    finally:
        conn.close()


def delete_user(username):
    """
    Deleta um usuário do banco de dados (ou desativa).
    
    username: Nome de usuário
    
    Retorna: True se o usuário foi deletado, False caso contrário
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Marca como inativo ao invés de deletar (mais seguro)
            if DB_TYPE == 'sqlite':
                cursor.execute('''
                    UPDATE users 
                    SET is_active = ? 
                    WHERE username = ?
                ''', (0, username.lower()))
            else:
                # PostgreSQL/MySQL
                cursor.execute('''
                    UPDATE users 
                    SET is_active = %s 
                    WHERE username = %s
                ''', (False, username.lower()))
            
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    except Exception as e:
        print(f"Erro ao deletar usuário: {e}")
        return False


def migrate_from_json(json_file='users.json'):
    """
    Migra usuários do arquivo JSON para o banco de dados SQL.
    
    json_file: Caminho do arquivo JSON com os usuários
    
    Retorna: (success_count, error_count, errors)
    """
    import json
    from auth import hash_password  # Importa a função de hash
    
    if not os.path.exists(json_file):
        print(f"Arquivo {json_file} não encontrado. Nada para migrar.")
        return 0, 0, []
    
    try:
        # Carrega usuários do JSON
        with open(json_file, 'r', encoding='utf-8') as f:
            users = json.load(f)
        
        success_count = 0
        error_count = 0
        errors = []
        
        # Migra cada usuário
        for username, user_data in users.items():
            try:
                # Verifica se o usuário já existe no banco
                if user_exists(username):
                    print(f"Usuário {username} já existe no banco. Pulando...")
                    continue
                
                # Pega os dados do usuário
                password_hash = user_data.get('password_hash')
                created_at = user_data.get('created_at', datetime.now().isoformat())
                
                # Cria o usuário no banco
                success, message, user_id = create_user_db(username, password_hash, created_at)
                
                if success:
                    success_count += 1
                    print(f"✓ Usuário {username} migrado com sucesso!")
                else:
                    error_count += 1
                    errors.append(f"{username}: {message}")
                    print(f"✗ Erro ao migrar usuário {username}: {message}")
                    
            except Exception as e:
                error_count += 1
                error_msg = f"{username}: {str(e)}"
                errors.append(error_msg)
                print(f"✗ Erro ao migrar usuário {username}: {e}")
        
        print(f"\nMigração concluída!")
        print(f"Sucessos: {success_count}")
        print(f"Erros: {error_count}")
        
        if errors:
            print("\nErros encontrados:")
            for error in errors:
                print(f"  - {error}")
        
        return success_count, error_count, errors
        
    except Exception as e:
        print(f"Erro ao migrar dados: {e}")
        return 0, 0, [str(e)]


def get_database_stats():
    """
    Retorna estatísticas do banco de dados.
    
    Retorna: Dicionário com estatísticas
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if DB_TYPE == 'sqlite':
            # Conta total de usuários
            cursor.execute('SELECT COUNT(*) as total FROM users')
            row = cursor.fetchone()
            total = row['total'] if row else 0
            
            # Conta usuários ativos
            cursor.execute('SELECT COUNT(*) as total FROM users WHERE is_active = ?', (1,))
            row = cursor.fetchone()
            active = row['total'] if row else 0
            
            # Conta usuários inativos
            cursor.execute('SELECT COUNT(*) as total FROM users WHERE is_active = ?', (0,))
            row = cursor.fetchone()
            inactive = row['total'] if row else 0
        elif DB_TYPE == 'postgresql':
            # PostgreSQL - precisa usar RealDictCursor
            import psycopg2.extras
            cursor.close()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            cursor.execute('SELECT COUNT(*) as total FROM users')
            row = cursor.fetchone()
            total = row['total'] if row else 0
            
            cursor.execute('SELECT COUNT(*) as total FROM users WHERE is_active = %s', (True,))
            row = cursor.fetchone()
            active = row['total'] if row else 0
            
            cursor.execute('SELECT COUNT(*) as total FROM users WHERE is_active = %s', (False,))
            row = cursor.fetchone()
            inactive = row['total'] if row else 0
        else:
            # MySQL - pymysql já retorna dicionário
            cursor.execute('SELECT COUNT(*) as total FROM users')
            row = cursor.fetchone()
            total = row['total'] if row else 0
            
            cursor.execute('SELECT COUNT(*) as total FROM users WHERE is_active = %s', (True,))
            row = cursor.fetchone()
            active = row['total'] if row else 0
            
            cursor.execute('SELECT COUNT(*) as total FROM users WHERE is_active = %s', (False,))
            row = cursor.fetchone()
            inactive = row['total'] if row else 0
        
        return {
            'total_users': total,
            'active_users': active,
            'inactive_users': inactive,
            'db_type': DB_TYPE,
            'db_file': DB_FILE if DB_TYPE == 'sqlite' else f"{DB_TYPE}://{DB_HOST}:{DB_PORT}/{DB_NAME}"
        }
    finally:
        conn.close()

