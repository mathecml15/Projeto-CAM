"""
================================================================================
DATABASE - Módulo de banco de dados MySQL
================================================================================

Este arquivo contém todas as funções relacionadas ao banco de dados MySQL:
- Conexão com o banco de dados
- Criação de tabelas
- Operações CRUD (Create, Read, Update, Delete)
"""

import os
from datetime import datetime
from contextlib import contextmanager
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# ============================================================================
# CONFIGURAÇÃO DO BANCO DE DADOS
# ============================================================================

# Configurações de conexão MySQL
# IMPORTANTE: Configure o arquivo .env com suas credenciais
# As senhas NUNCA ficam no código por segurança!
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')


def get_db_connection():
    """
    Cria uma conexão com o banco de dados MySQL.
    
    Retorna: Objeto de conexão com o banco de dados
    """
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


def init_database():
    """
    Inicializa o banco de dados criando as tabelas necessárias.
    Se as tabelas já existirem, não faz nada.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Cria a tabela de usuários
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
                role VARCHAR(20) DEFAULT 'viewer',
                INDEX idx_username (username),
                INDEX idx_email (email)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        # Adiciona coluna role se não existir (para migração)
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT "viewer"')
        except:
            pass  # Coluna já existe
        
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
        cursor.execute('SELECT id FROM users WHERE username = %s', (username.lower(),))
        result = cursor.fetchone()
        return result is not None
    finally:
        conn.close()


def create_user_db(username, password_hash, email, cpf, data_nascimento, created_at=None, role='viewer'):
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
    username_lower = username.lower()
    email_lower = email.lower()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Insere o novo usuário
            cursor.execute('''
                INSERT INTO users (username, password_hash, email, cpf, data_nascimento, is_active, role)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (username_lower, password_hash, email_lower, cpf, data_nascimento, True, role))
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
        # MySQL - pymysql já retorna dicionário
        cursor.execute('SELECT * FROM users WHERE username = %s', (username.lower(),))
        row = cursor.fetchone()
        return row if row else None
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


def get_database_stats():
    """
    Retorna estatísticas do banco de dados.
    
    Retorna: Dicionário com estatísticas
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
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
            'db_type': 'mysql',
            'db_file': f"mysql://{DB_HOST}:{DB_PORT}/{DB_NAME}"
        }
    finally:
        conn.close()


def get_user_role(username):
    """
    Obtém o role (perfil) de um usuário.
    
    username: Nome de usuário
    
    Retorna: Role do usuário ('admin', 'operator', 'viewer') ou None
    """
    user = get_user_by_username(username)
    if user:
        return user.get('role', 'viewer')
    return None


def update_user_role(username, role):
    """
    Atualiza o role de um usuário.
    
    username: Nome de usuário
    role: Novo role ('admin', 'operator', 'viewer')
    
    Retorna: True se atualizado com sucesso, False caso contrário
    """
    valid_roles = ['admin', 'operator', 'viewer']
    if role not in valid_roles:
        return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE users 
            SET role = %s 
            WHERE username = %s
        ''', (role, username.lower()))
        
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Erro ao atualizar role do usuário: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
