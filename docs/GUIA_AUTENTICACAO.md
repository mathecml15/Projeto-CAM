# 🔐 Guia de Autenticação - Sistema de Login e Cadastro

## 📋 O que foi implementado?

Foi criado um sistema completo de autenticação com:

### ✅ Funcionalidades:
1. **Login** - Página de login com validação
2. **Cadastro** - Página de cadastro de novos usuários
3. **Logout** - Botão para sair do sistema
4. **Proteção de Rotas** - Todas as rotas principais estão protegidas
5. **Sessões Seguras** - Usa cookies criptografados
6. **Hash de Senhas** - Senhas são armazenadas com hash (SHA-256)

## 🚀 Como Funciona?

### 1. Armazenamento de Usuários
- Usuários são armazenados em `users.json`
- Senhas são hasheadas (nunca armazenadas em texto puro)
- Cada usuário tem: username, password_hash, created_at

### 2. Fluxo de Autenticação
1. Usuário acessa o sistema
2. Se não estiver logado, é redirecionado para `/login`
3. Após login, é redirecionado para a página principal
4. Sessão é mantida através de cookies
5. Ao fazer logout, a sessão é encerrada

### 3. Proteção de Rotas
- Todas as rotas principais estão protegidas com `@login_required`
- Rotas públicas: `/login`, `/register`
- Rotas protegidas: `/`, `/get_cameras`, `/video_feed/*`, etc.

## 📁 Arquivos Criados

### 1. `auth.py`
- Gerenciamento de usuários
- Hash de senhas
- Verificação de autenticação
- Decorator `@login_required`

### 2. `auth_routes.py`
- Rotas de login (`/login`)
- Rotas de cadastro (`/register`)
- Rotas de logout (`/logout`)
- APIs JSON para login e cadastro

### 3. `templates/login.html`
- Página de login
- Formulário de autenticação
- Link para cadastro

### 4. `templates/register.html`
- Página de cadastro
- Formulário de registro
- Validação de senhas
- Link para login

## 🎯 Como Usar

### 1. Primeiro Acesso
1. Acesse `http://127.0.0.1:5000`
2. Você será redirecionado para `/login`
3. Clique em "Cadastre-se aqui"
4. Preencha o formulário de cadastro
5. Após cadastro, você será redirecionado para login
6. Faça login com suas credenciais

### 2. Acessos Posteriores
1. Acesse `http://127.0.0.1:5000`
2. Se não estiver logado, será redirecionado para login
3. Faça login com suas credenciais
4. Acesse o sistema normalmente

### 3. Logout
1. Clique no botão "Sair" no canto superior direito
2. Você será deslogado e redirecionado para login

## 🔒 Segurança

### O que está implementado:
- ✅ Hash de senhas (SHA-256)
- ✅ Sessões seguras (cookies criptografados)
- ✅ Proteção contra XSS (HTTPOnly cookies)
- ✅ Proteção contra CSRF (SameSite cookies)
- ✅ Validação de entrada (nome de usuário e senha)

### Recomendações para Produção:
1. **Altere a SECRET_KEY** no `servidor.py`:
   ```python
   app.config['SECRET_KEY'] = 'sua-chave-secreta-aleatoria-aqui'
   ```
   Use: `python -c "import secrets; print(secrets.token_hex(32))"`

2. **Use HTTPS**:
   ```python
   app.config['SESSION_COOKIE_SECURE'] = True  # Apenas com HTTPS
   ```

3. **Altere o SALT_SECRET** no `auth.py`:
   ```python
   SALT_SECRET = "sua-chave-secreta-unica-aqui"
   ```

4. **Migre para Banco de Dados**:
   - SQLite (simples)
   - PostgreSQL (produção)
   - MySQL (produção)

## 📊 Estrutura de Dados

### Arquivo `users.json`:
```json
{
    "usuario1": {
        "password_hash": "hash_da_senha_aqui",
        "created_at": "2024-12-25T10:30:00"
    },
    "usuario2": {
        "password_hash": "hash_da_senha_aqui",
        "created_at": "2024-12-25T11:00:00"
    }
}
```

## 🛠️ Personalização

### Alterar Validações:
Edite `auth.py`:
```python
# Nome de usuário mínimo
if len(username.strip()) < 3:  # Altere para o valor desejado

# Senha mínima
if len(password) < 4:  # Altere para o valor desejado
```

### Alterar Mensagens:
Edite `auth.py` e `auth_routes.py` para personalizar as mensagens de erro e sucesso.

### Alterar Design:
Edite `templates/login.html` e `templates/register.html` para personalizar o design.

## 🐛 Troubleshooting

### Problema: "Erro ao salvar usuário"
**Solução**: Verifique permissões de escrita na pasta do projeto.

### Problema: "Usuário ou senha incorretos"
**Solução**: Verifique se o usuário existe e se a senha está correta.

### Problema: "Nome de usuário já existe"
**Solução**: Escolha outro nome de usuário ou exclua o usuário existente em `users.json`.

### Problema: Sessão não persiste
**Solução**: Verifique se os cookies estão habilitados no navegador.

## 📝 Próximos Passos (Opcional)

### Melhorias Possíveis:
1. **Recuperação de Senha** - Envio de email para redefinir senha
2. **Roles/Permissões** - Diferentes níveis de acesso (admin, usuário, etc.)
3. **Rate Limiting** - Limitar tentativas de login
4. **2FA** - Autenticação de dois fatores
5. **Banco de Dados** - Migrar de JSON para banco de dados
6. **Logs de Acesso** - Registrar quem acessou o sistema
7. **Expiração de Sessão** - Sessões que expiram após X minutos

## 📚 Conceitos Importantes

### Hash de Senhas
- Senhas nunca são armazenadas em texto puro
- Hash é uma função matemática que transforma dados em uma string única
- Mesma senha sempre produz o mesmo hash
- É praticamente impossível reverter um hash para obter a senha original

### Sessões
- Sessão é um mecanismo para manter o estado do usuário entre requisições
- Usa cookies para armazenar um identificador de sessão
- O servidor armazena os dados da sessão
- Cookies são criptografados para segurança

### Decorators
- `@login_required` é um decorator que protege rotas
- Verifica se o usuário está logado antes de executar a função
- Se não estiver logado, redireciona para login

## 💡 Dicas

1. **Backup**: Faça backup do arquivo `users.json` regularmente
2. **Senhas Fortes**: Encoraje usuários a usarem senhas fortes
3. **Logs**: Considere adicionar logs de acesso e tentativas de login
4. **Testes**: Teste o sistema com diferentes usuários e cenários

## 📞 Suporte

Se tiver problemas ou dúvidas:
1. Verifique os logs do servidor
2. Verifique o arquivo `users.json`
3. Verifique as permissões de arquivo
4. Consulte a documentação do Flask sobre sessões

