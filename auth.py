"""
================================================================================
AUTENTICAÇÃO - Sistema de login e cadastro de usuários
================================================================================

Este arquivo contém todas as funções relacionadas à autenticação:
- Hash de senhas (para segurança)
- Armazenamento de usuários
- Verificação de login
- Gerenciamento de sessões

ARMAZENAMENTO:
- Usuários são armazenados em banco de dados SQL (SQLite, PostgreSQL, MySQL)
- Senhas são hasheadas (não são armazenadas em texto puro)
- Cada usuário tem: id, username, password_hash, created_at, last_login, is_active
"""

import os
import hashlib
import secrets
from datetime import datetime
from functools import wraps

# Importa o módulo de banco de dados
try:
    from database import (
        init_database, user_exists as db_user_exists,
        create_user_db, get_user_by_username, get_user_password_hash,
        update_user_last_login, get_all_users_db, get_database_stats
    )
    USE_DATABASE = True
except ImportError:
    USE_DATABASE = False
    print("AVISO: Módulo database.py não encontrado. Usando armazenamento JSON (legado).")

# Se não estiver usando banco de dados, usa JSON (modo legado)
if not USE_DATABASE:
    import json
    USERS_FILE = "users.json"

# Chave secreta para hash (carregada do arquivo .env por segurança)
# Esta chave é usada para "salgar" as senhas (torna mais seguro)
# NUNCA coloque a chave diretamente no código!
SALT_SECRET = os.getenv('SALT_SECRET', 'd90f3d102ecbd11ca0e499890bc16b6379159bc075a65b490fee510adf7f1865')


def hash_password(password):
    """
    Cria um hash seguro da senha.
    
    password: Senha em texto puro
    
    Retorna: Hash da senha (string hexadecimal)
    """
    # Combina a senha com uma chave secreta (salt)
    # Isso torna o hash único e mais seguro
    salted_password = password + SALT_SECRET
    
    # Cria o hash usando SHA-256
    # SHA-256 é um algoritmo seguro de hash
    hash_object = hashlib.sha256(salted_password.encode('utf-8'))
    password_hash = hash_object.hexdigest()
    
    return password_hash


def verify_password(password, password_hash):
    """
    Verifica se uma senha corresponde ao hash armazenado.
    
    password: Senha em texto puro (do usuário)
    password_hash: Hash armazenado no banco de dados
    
    Retorna: True se a senha estiver correta, False caso contrário
    """
    # Cria o hash da senha fornecida
    provided_hash = hash_password(password)
    
    # Compara os hashes
    return provided_hash == password_hash


# Funções legadas para JSON (usadas apenas se USE_DATABASE = False)
def load_users():
    """
    [LEGADO] Carrega a lista de usuários do arquivo JSON.
    Usado apenas se o banco de dados não estiver disponível.
    """
    if USE_DATABASE:
        return {}  # Não usado quando há banco de dados
    
    if not os.path.exists(USERS_FILE):
        return {}
    
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)
        return users
    except (json.JSONDecodeError, IOError) as e:
        print(f"Erro ao carregar usuários: {e}")
        return {}


def save_users(users):
    """
    [LEGADO] Salva a lista de usuários no arquivo JSON.
    Usado apenas se o banco de dados não estiver disponível.
    """
    if USE_DATABASE:
        return False  # Não usado quando há banco de dados
    
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=4, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"Erro ao salvar usuários: {e}")
        return False


def user_exists(username):
    """
    Verifica se um usuário já existe.
    
    username: Nome de usuário para verificar
    
    Retorna: True se o usuário existe, False caso contrário
    """
    if USE_DATABASE:
        # Usa banco de dados
        return db_user_exists(username)
    else:
        # Modo legado: usa JSON
        users = load_users()
        return username.lower() in users


def create_user(username, password, email, cpf, data_nascimento):
    """
    Cria um novo usuário.
    
    username: Nome de usuário
    password: Senha em texto puro
    email: Email do usuário
    cpf: CPF do usuário
    data_nascimento: Data de nascimento (formato YYYY-MM-DD)
    
    Retorna: (success, message)
             - success: True se o usuário foi criado, False caso contrário
             - message: Mensagem de erro ou sucesso
    """
    # Validação do nome de usuário
    if not username or len(username.strip()) < 3:
        return False, "Nome de usuário deve ter pelo menos 3 caracteres"
    
    # Validação da senha
    if not password or len(password) < 4:
        return False, "Senha deve ter pelo menos 4 caracteres"
    
    # Validação do email
    if not email or '@' not in email:
        return False, "Email inválido"
    
    # Validação do CPF (básica)
    if not cpf or len(cpf.replace('.', '').replace('-', '')) != 11:
        return False, "CPF inválido (deve ter 11 dígitos)"
    
    # Validação da data de nascimento
    if not data_nascimento:
        return False, "Data de nascimento é obrigatória"
    
    # Remove espaços do nome de usuário e converte para minúsculas
    username = username.strip().lower()
    email = email.strip().lower()
    cpf = cpf.replace('.', '').replace('-', '').strip()  # Remove formatação do CPF
    
    # Verifica se o usuário já existe
    if user_exists(username):
        return False, "Nome de usuário já existe"
    
    # Cria o hash da senha
    password_hash = hash_password(password)
    created_at = datetime.now().isoformat()
    
    if USE_DATABASE:
        # Usa banco de dados
        success, message, user_id = create_user_db(username, password_hash, email, cpf, data_nascimento, created_at)
        return success, message
    else:
        # Modo legado: usa JSON
        users = load_users()
        users[username] = {
            'password_hash': password_hash,
            'email': email,
            'cpf': cpf,
            'data_nascimento': data_nascimento,
            'created_at': created_at
        }
        if save_users(users):
            return True, "Usuário criado com sucesso!"
        else:
            return False, "Erro ao salvar usuário"


def authenticate_user(username, password):
    """
    Autentica um usuário (verifica login e senha).
    
    username: Nome de usuário
    password: Senha em texto puro
    
    Retorna: (success, message)
             - success: True se a autenticação foi bem-sucedida, False caso contrário
             - message: Mensagem de erro ou sucesso
    """
    # Remove espaços do nome de usuário e converte para minúsculas
    username = username.strip().lower()
    
    if USE_DATABASE:
        # Usa banco de dados
        # Busca o hash da senha no banco
        stored_hash = get_user_password_hash(username)
        
        if stored_hash is None:
            return False, "Usuário ou senha incorretos"
        
        # Verifica se a senha está correta
        if verify_password(password, stored_hash):
            # Atualiza o último login
            update_user_last_login(username)
            return True, "Login realizado com sucesso!"
        else:
            return False, "Usuário ou senha incorretos"
    else:
        # Modo legado: usa JSON
        users = load_users()
        
        # Verifica se o usuário existe
        if username not in users:
            return False, "Usuário ou senha incorretos"
        
        # Pega o hash da senha armazenado
        stored_hash = users[username]['password_hash']
        
        # Verifica se a senha está correta
        if verify_password(password, stored_hash):
            return True, "Login realizado com sucesso!"
        else:
            return False, "Usuário ou senha incorretos"


def login_required(f):
    """
    Decorator para proteger rotas que requerem autenticação.
    
    Uso:
        @app.route('/protegida')
        @login_required
        def rota_protegida():
            return "Esta rota está protegida"
    
    Se o usuário não estiver logado, será redirecionado para a página de login.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Importa aqui para evitar importação circular
        from flask import session, request, redirect, jsonify
        
        # Verifica se o usuário está logado (se 'user' está na sessão)
        if 'user' not in session:
            # Se não estiver logado, redireciona para login
            # Se for uma requisição AJAX (JSON), retorna erro JSON
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Autenticação necessária'}), 401
            # Redireciona para login com next parameter para voltar após login
            return redirect(f'/login?next={request.url}')
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """
    Retorna o usuário atual logado.
    
    Retorna: Nome de usuário (string) ou None se não estiver logado
    """
    from flask import session
    return session.get('user')


def logout_user():
    """
    Faz logout do usuário atual (remove da sessão).
    """
    from flask import session
    session.pop('user', None)


def get_all_users():
    """
    Retorna a lista de todos os usuários (apenas nomes, sem senhas).
    
    Retorna: Lista de nomes de usuários
    """
    if USE_DATABASE:
        # Usa banco de dados
        return get_all_users_db()
    else:
        # Modo legado: usa JSON
        users = load_users()
        return list(users.keys())

