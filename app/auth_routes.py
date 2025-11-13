"""
================================================================================
AUTH ROUTES - Rotas de autenticação (login, cadastro, logout)
================================================================================

Este arquivo contém todas as rotas relacionadas à autenticação:
- /login - Página de login
- /register - Página de cadastro
- /logout - Fazer logout
- /api/login - API para login (POST)
- /api/register - API para cadastro (POST)
"""

from flask import render_template, request, redirect, url_for, session, jsonify, flash
from app.auth import (
    create_user, authenticate_user, logout_user, 
    get_current_user, login_required
)


def registrar_rotas_auth(app):
    """
    Registra todas as rotas de autenticação no app Flask.
    
    app: Objeto Flask que receberá as rotas
    """
    
    # ============================================================================
    # ROTAS DE AUTENTICAÇÃO
    # ============================================================================
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """
        Rota de login.
        - GET: Mostra a página de login
        - POST: Processa o login
        """
        # Se o usuário já estiver logado, redireciona para a página principal
        if 'user' in session:
            return redirect('/')
        
        # Se for uma requisição POST (formulário enviado)
        if request.method == 'POST':
            # Pega os dados do formulário
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            
            # Validação básica
            if not username or not password:
                flash('Por favor, preencha todos os campos', 'error')
                return render_template('login.html')
            
            # Tenta autenticar o usuário
            success, message = authenticate_user(username, password)
            
            if success:
                # Se a autenticação foi bem-sucedida, salva na sessão
                session['user'] = username
                flash('Login realizado com sucesso!', 'success')
                
                # Redireciona para a página principal
                # Tenta pegar a página que o usuário queria acessar (se houver)
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect('/')
            else:
                # Se a autenticação falhou, mostra mensagem de erro
                flash(message, 'error')
                return render_template('login.html')
        
        # Se for GET, mostra a página de login
        return render_template('login.html')
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """
        Rota de cadastro.
        - GET: Mostra a página de cadastro
        - POST: Processa o cadastro
        """
        # Se o usuário já estiver logado, redireciona para a página principal
        if 'user' in session:
            return redirect('/')
        
        # Se for uma requisição POST (formulário enviado)
        if request.method == 'POST':
            # Pega os dados do formulário
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            cpf = request.form.get('cpf', '').strip()
            data_nascimento = request.form.get('data_nascimento', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            # Validação básica
            if not username or not email or not cpf or not data_nascimento or not password or not confirm_password:
                flash('Por favor, preencha todos os campos', 'error')
                return render_template('register.html')
            
            # Verifica se as senhas coincidem
            if password != confirm_password:
                flash('As senhas não coincidem', 'error')
                return render_template('register.html')
            
            # Tenta criar o usuário
            success, message = create_user(username, password, email, cpf, data_nascimento)
            
            if success:
                # Se o usuário foi criado, mostra mensagem de sucesso
                flash(message, 'success')
                # Redireciona para a página de login
                return redirect(url_for('login'))
            else:
                # Se houve erro, mostra mensagem de erro
                flash(message, 'error')
                return render_template('register.html')
        
        # Se for GET, mostra a página de cadastro
        return render_template('register.html')
    
    @app.route('/logout')
    @login_required  # Só pode fazer logout se estiver logado
    def logout():
        """
        Rota de logout.
        Remove o usuário da sessão e redireciona para a página de login.
        """
        # Remove o usuário da sessão
        logout_user()
        flash('Logout realizado com sucesso!', 'success')
        return redirect(url_for('login'))
    
    # ============================================================================
    # APIs DE AUTENTICAÇÃO (para uso com JavaScript/AJAX)
    # ============================================================================
    
    @app.route('/api/login', methods=['POST'])
    def api_login():
        """
        API para login (retorna JSON).
        Útil para fazer login via JavaScript/AJAX.
        """
        # Pega os dados do JSON
        data = request.get_json()
        username = data.get('username', '').strip() if data else ''
        password = data.get('password', '') if data else ''
        
        # Validação básica
        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'Por favor, preencha todos os campos'
            }), 400
        
        # Tenta autenticar o usuário
        success, message = authenticate_user(username, password)
        
        if success:
            # Se a autenticação foi bem-sucedida, salva na sessão
            session['user'] = username
            return jsonify({
                'success': True,
                'message': message,
                'user': username
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 401
    
    @app.route('/api/register', methods=['POST'])
    def api_register():
        """
        API para cadastro (retorna JSON).
        Útil para fazer cadastro via JavaScript/AJAX.
        """
        # Pega os dados do JSON
        data = request.get_json()
        username = data.get('username', '').strip() if data else ''
        email = data.get('email', '').strip() if data else ''
        cpf = data.get('cpf', '').strip() if data else ''
        data_nascimento = data.get('data_nascimento', '').strip() if data else ''
        password = data.get('password', '') if data else ''
        confirm_password = data.get('confirm_password', '') if data else ''
        
        # Validação básica
        if not username or not email or not cpf or not data_nascimento or not password or not confirm_password:
            return jsonify({
                'success': False,
                'message': 'Por favor, preencha todos os campos'
            }), 400
        
        # Verifica se as senhas coincidem
        if password != confirm_password:
            return jsonify({
                'success': False,
                'message': 'As senhas não coincidem'
            }), 400
        
        # Tenta criar o usuário
        success, message = create_user(username, password, email, cpf, data_nascimento)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
    
    @app.route('/api/user')
    def api_user():
        """
        API para obter informações do usuário atual.
        Retorna o nome de usuário se estiver logado, ou None.
        """
        user = get_current_user()
        return jsonify({
            'user': user,
            'is_authenticated': user is not None
        })

