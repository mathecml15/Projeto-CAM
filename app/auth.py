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
    from app.database import (
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


def create_user(username, password, email, cpf, data_nascimento, role='viewer'):
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
    
    # Validação do role
    valid_roles = ['admin', 'operator', 'viewer']
    if role not in valid_roles:
        role = 'viewer'  # Default para viewer se inválido
    
    if USE_DATABASE:
        # Usa banco de dados
        success, message, user_id = create_user_db(username, password_hash, email, cpf, data_nascimento, created_at, role)
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
            # Usa request.path em vez de request.url para evitar problemas com HTTPS
            return redirect(f'/login?next={request.path}')
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


# ============================================================================
# SISTEMA DE PERMISSÕES E ROLES
# ============================================================================

# Definição de roles e suas permissões
ROLES = {
    'admin': {
        'name': 'Administrador',
        'permissions': [
            'view_cameras',           # Ver câmeras
            'control_cameras',        # Controlar câmeras (gravar, parar)
            'manage_cameras',         # Adicionar/remover câmeras
            'view_recordings',        # Ver gravações
            'download_recordings',    # Baixar gravações
            'delete_recordings',      # Deletar gravações
            'manage_users',           # Gerenciar usuários
            'manage_settings',        # Gerenciar configurações do sistema
            'view_dashboard',         # Ver dashboard
            'view_events',            # Ver eventos/logs
            'export_videos',          # Exportar vídeos
        ]
    },
    'operator': {
        'name': 'Operador',
        'permissions': [
            'view_cameras',           # Ver câmeras
            'control_cameras',        # Controlar câmeras (gravar, parar)
            'view_recordings',        # Ver gravações
            'download_recordings',    # Baixar gravações
            'view_dashboard',         # Ver dashboard
            'view_events',            # Ver eventos/logs
            'export_videos',          # Exportar vídeos
        ]
    },
    'viewer': {
        'name': 'Visualizador',
        'permissions': [
            'view_cameras',           # Ver câmeras
            'view_recordings',        # Ver gravações
            'download_recordings',    # Baixar gravações
            'view_dashboard',         # Ver dashboard
            'view_events',            # Ver eventos/logs
        ]
    }
}


def get_user_role(username):
    """
    Obtém o role de um usuário.
    
    username: Nome de usuário
    
    Retorna: Role do usuário ('admin', 'operator', 'viewer') ou 'viewer' por padrão
    """
    if USE_DATABASE:
        try:
            from app.database import get_user_role as db_get_user_role
            role = db_get_user_role(username)
            # Se o role não existe ou é inválido, retorna 'viewer'
            if not role or role not in ROLES:
                # Se o role for 'user' (legado), converte para 'viewer'
                if role == 'user':
                    return 'viewer'
                return 'viewer'
            return role
        except ImportError:
            return 'viewer'
    else:
        # Modo legado: usuários JSON têm role viewer por padrão
        return 'viewer'


def user_has_permission(username, permission):
    """
    Verifica se um usuário tem uma permissão específica.
    
    username: Nome de usuário
    permission: Nome da permissão (ex: 'manage_cameras')
    
    Retorna: True se o usuário tem a permissão, False caso contrário
    """
    role = get_user_role(username)
    role_config = ROLES.get(role, ROLES['viewer'])
    return permission in role_config['permissions']


def role_required(*required_roles):
    """
    Decorator para proteger rotas que requerem roles específicos.
    
    Uso:
        @app.route('/admin')
        @login_required
        @role_required('admin')
        def admin_page():
            return "Apenas admins podem ver isso"
        
        @app.route('/operator')
        @login_required
        @role_required('admin', 'operator')
        def operator_page():
            return "Admins ou operadores podem ver isso"
    
    required_roles: Lista de roles permitidos (ex: 'admin', 'operator')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Importa aqui para evitar importação circular
            from flask import session, request, redirect, jsonify
            
            # Verifica se está logado
            if 'user' not in session:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'Autenticação necessária'}), 401
                # Usa request.path em vez de request.url para evitar problemas com HTTPS
                return redirect(f'/login?next={request.path}')
            
            # Obtém o role do usuário
            username = session.get('user')
            user_role = get_user_role(username)
            
            # Verifica se o role do usuário está na lista de roles permitidos
            if user_role not in required_roles:
                # Usuário não tem permissão
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({
                        'error': 'Permissão negada',
                        'message': f'Esta ação requer um dos seguintes roles: {", ".join(required_roles)}',
                        'your_role': user_role
                    }), 403
                from flask import flash
                flash(f'Acesso negado. Requer role: {", ".join(required_roles)}', 'error')
                return redirect('/')
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def permission_required(permission):
    """
    Decorator para proteger rotas que requerem permissões específicas.
    
    Uso:
        @app.route('/delete_video')
        @login_required
        @permission_required('delete_recordings')
        def delete_video():
            return "Apenas usuários com permissão delete_recordings podem fazer isso"
    
    permission: Nome da permissão necessária (ex: 'manage_cameras')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Importa aqui para evitar importação circular
            from flask import session, request, redirect, jsonify
            
            # Verifica se está logado
            if 'user' not in session:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'Autenticação necessária'}), 401
                # Usa request.path em vez de request.url para evitar problemas com HTTPS
                return redirect(f'/login?next={request.path}')
            
            # Verifica se o usuário tem a permissão
            username = session.get('user')
            if not user_has_permission(username, permission):
                # Usuário não tem permissão
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({
                        'error': 'Permissão negada',
                        'message': f'Esta ação requer a permissão: {permission}',
                        'your_role': get_user_role(username)
                    }), 403
                from flask import flash
                user_role = get_user_role(username)
                role_name = ROLES.get(user_role, {}).get('name', user_role)
                # Mensagem mais informativa
                flash(f'❌ Acesso negado! Você precisa da permissão "{permission}" para acessar esta página. Seu role atual: {role_name}. Entre em contato com um administrador para obter acesso.', 'error')
                return redirect('/')
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

