# 🔐 Sistema de Roles e Permissões

Este documento explica o sistema de roles e permissões do VMS.

## 📋 Roles Disponíveis

O sistema possui 3 roles (perfis) principais:

### 1. **Admin** (Administrador)
Acesso completo ao sistema.

**Permissões:**
- ✅ Ver câmeras
- ✅ Controlar câmeras (gravar, parar)
- ✅ Gerenciar câmeras (adicionar/remover)
- ✅ Ver gravações
- ✅ Baixar gravações
- ✅ Deletar gravações
- ✅ Gerenciar usuários
- ✅ Gerenciar configurações
- ✅ Ver dashboard
- ✅ Ver eventos/logs
- ✅ Exportar vídeos

### 2. **Operator** (Operador)
Acesso para operação diária.

**Permissões:**
- ✅ Ver câmeras
- ✅ Controlar câmeras (gravar, parar)
- ✅ Ver gravações
- ✅ Baixar gravações
- ✅ Ver dashboard
- ✅ Ver eventos/logs
- ✅ Exportar vídeos
- ❌ Gerenciar câmeras
- ❌ Deletar gravações
- ❌ Gerenciar usuários
- ❌ Gerenciar configurações

### 3. **Viewer** (Visualizador)
Acesso apenas para visualização.

**Permissões:**
- ✅ Ver câmeras
- ✅ Ver gravações
- ✅ Baixar gravações
- ✅ Ver dashboard
- ✅ Ver eventos/logs
- ❌ Controlar câmeras
- ❌ Gerenciar câmeras
- ❌ Deletar gravações
- ❌ Gerenciar usuários
- ❌ Gerenciar configurações
- ❌ Exportar vídeos

---

## 🔧 Como Definir Role de Usuário

### Durante Cadastro (Padrão)

Por padrão, **todos os novos usuários são criados como `viewer`**.

### Alterar Role de Usuário Existente

Para alterar o role de um usuário existente, você precisa editar diretamente no banco de dados:

#### SQLite:
```sql
UPDATE users SET role = 'admin' WHERE username = 'nome_do_usuario';
UPDATE users SET role = 'operator' WHERE username = 'nome_do_usuario';
UPDATE users SET role = 'viewer' WHERE username = 'nome_do_usuario';
```

#### MySQL:
```sql
UPDATE users SET role = 'admin' WHERE username = 'nome_do_usuario';
UPDATE users SET role = 'operator' WHERE username = 'nome_do_usuario';
UPDATE users SET role = 'viewer' WHERE username = 'nome_do_usuario';
```

---

## 📝 Migração de Usuários Existentes

Se você já tem usuários no sistema, eles serão criados com role `viewer` por padrão.

### Definir Primeiro Admin

**IMPORTANTE:** O primeiro usuário admin deve ser definido manualmente no banco de dados:

#### SQLite:
```sql
-- Conecte ao banco
sqlite3 vms_database.db

-- Defina o primeiro usuário como admin
UPDATE users SET role = 'admin' WHERE username = 'seu_usuario';
```

#### MySQL:
```sql
-- Conecte ao banco
mysql -u seu_usuario -p nome_do_banco

-- Defina o primeiro usuário como admin
UPDATE users SET role = 'admin' WHERE username = 'seu_usuario';
```

---

## 🔒 Proteção de Rotas

As rotas do sistema estão protegidas com permissões:

### Rotas Públicas (Login):
- `/login` - Página de login
- `/register` - Página de cadastro
- `/api/login` - API de login
- `/api/register` - API de cadastro

### Rotas Protegidas:
- `/` - Ver câmeras (todos os roles)
- `/dashboard` - Ver dashboard (todos os roles)
- `/events` - Ver eventos (todos os roles)
- `/cameras` - Gerenciar câmeras (**admin**)
- `/settings` - Gerenciar configurações (**admin**)

### APIs Protegidas:
- `/start_recording/<cam_id>` - **control_cameras**
- `/stop_recording/<cam_id>` - **control_cameras**
- `/api/cameras/add` - **manage_cameras**
- `/api/cameras/remove/<cam_id>` - **manage_cameras**
- `/api/cameras/update/<cam_id>` - **manage_cameras**
- `/api/settings/update` - **manage_settings**
- `/api/events/clear` - **admin**

---

## 🛠️ Usar no Código

### Decorator `@role_required`:
```python
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
```

### Decorator `@permission_required`:
```python
@app.route('/delete_video')
@login_required
@permission_required('delete_recordings')
def delete_video():
    return "Apenas usuários com permissão delete_recordings"
```

### Verificar Permissão em Código:
```python
from app.auth import user_has_permission, get_user_role

username = get_current_user()
if user_has_permission(username, 'manage_cameras'):
    # Usuário pode gerenciar câmeras
    pass
```

---

## 📚 Referências

- Ver `app/auth.py` para funções de permissão
- Ver `app/routes.py` para exemplos de uso
- Ver `app/database.py` para funções de banco de dados

