# 🗄️ Como Configurar o MySQL - Guia Completo

## 📋 O que mudou?

Atualizei o sistema para usar o banco de dados MySQL com os seguintes campos:
- **Nome de usuário** (username)
- **Email** (email)
- **CPF** (cpf)
- **Data de Nascimento** (data_nascimento)
- **Senha** (password_hash - criptografada)

## 🎯 Configuração do Banco de Dados

### Passo 1: Configure a Conexão com o MySQL

Abra o arquivo `database.py` e edite as seguintes linhas (por volta da linha 32-40):

```python
DB_TYPE = 'mysql'  # Já está configurado
DB_HOST = 'localhost'  # Se o MySQL está na sua máquina
DB_PORT = '3306'  # Porta padrão do MySQL
DB_NAME = 'vms_db'  # ALTERE para o nome do seu banco no Workbench
DB_USER = 'root'  # ALTERE para seu usuário do MySQL
DB_PASSWORD = ''  # ALTERE para sua senha do MySQL
```

### Passo 2: Crie o Banco de Dados (se ainda não criou)

Abra o MySQL Workbench e execute:

```sql
-- Cria o banco de dados
CREATE DATABASE IF NOT EXISTS vms_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- Seleciona o banco
USE vms_db;

-- Cria a tabela de usuários
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Passo 3: Instale o Driver Python para MySQL

Abra o terminal/PowerShell e execute:

```bash
pip install pymysql
```

### Passo 4: Teste a Conexão

Execute o servidor:

```bash
python servidor.py
```

Se aparecer a mensagem "Banco de dados inicializado.", está funcionando!

## 🎨 Formulário de Cadastro Atualizado

O formulário de cadastro agora possui os seguintes campos:

1. **Nome de Usuário** - mínimo 3 caracteres
2. **Email** - validação automática de formato
3. **CPF** - máscara automática (formato: 000.000.000-00)
4. **Data de Nascimento** - seletor de data
5. **Senha** - mínimo 4 caracteres
6. **Confirmar Senha** - deve ser igual à senha

## 🧪 Como Testar

### 1. Acesse o sistema:

```
http://127.0.0.1:5000
```

### 2. Clique em "Cadastre-se aqui"

### 3. Preencha todos os campos:

- **Nome de Usuário**: teste
- **Email**: teste@email.com
- **CPF**: 12345678900 (pode digitar com ou sem formatação)
- **Data de Nascimento**: Escolha uma data
- **Senha**: 1234
- **Confirmar Senha**: 1234

### 4. Clique em "Cadastrar"

### 5. Verifique no MySQL Workbench:

```sql
USE vms_db;
SELECT * FROM users;
```

Você deverá ver o usuário cadastrado com todos os dados!

## 📊 Estrutura da Tabela

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INT | ID único (chave primária, auto incremento) |
| username | VARCHAR(100) | Nome de usuário (único) |
| password_hash | VARCHAR(255) | Senha criptografada (SHA-256) |
| email | VARCHAR(255) | Email (único) |
| cpf | VARCHAR(14) | CPF sem formatação (único) |
| data_nascimento | DATE | Data de nascimento (formato YYYY-MM-DD) |
| created_at | TIMESTAMP | Data de criação (automático) |
| last_login | TIMESTAMP | Data do último login |
| is_active | BOOLEAN | Se o usuário está ativo (1/TRUE) |

## 🔒 Segurança

### Senhas:
- São criptografadas com SHA-256 + salt
- Nunca são armazenadas em texto puro
- Não podem ser recuperadas (apenas redefinidas)

### CPF e Email:
- São únicos no banco (não permite duplicatas)
- Email é validado no formato
- CPF aceita formatação (000.000.000-00) ou sem (00000000000)

## ⚙️ Configuração Avançada

### Variáveis de Ambiente (Opcional)

Para não deixar a senha no código, você pode usar variáveis de ambiente:

**Windows (PowerShell):**
```powershell
$env:DB_TYPE = "mysql"
$env:DB_HOST = "localhost"
$env:DB_PORT = "3306"
$env:DB_NAME = "vms_db"
$env:DB_USER = "root"
$env:DB_PASSWORD = "sua_senha_aqui"
```

**Linux/macOS:**
```bash
export DB_TYPE=mysql
export DB_HOST=localhost
export DB_PORT=3306
export DB_NAME=vms_db
export DB_USER=root
export DB_PASSWORD=sua_senha_aqui
```

Depois, só executar:
```bash
python servidor.py
```

## 🐛 Troubleshooting

### Erro: "No module named 'pymysql'"

**Solução:**
```bash
pip install pymysql
```

### Erro: "Access denied for user"

**Solução:**
- Verifique o usuário e senha no `database.py`
- Certifique-se que o usuário tem permissão no banco

### Erro: "Unknown database 'vms_db'"

**Solução:**
- Crie o banco de dados no MySQL Workbench
- Execute o script SQL do Passo 2

### Erro: "Can't connect to MySQL server"

**Solução:**
- Verifique se o MySQL está rodando
- Verifique se a porta está correta (3306)
- Verifique o host (localhost ou 127.0.0.1)

### Erro: "Duplicate entry ... for key 'username'"

**Solução:**
- Esse usuário já existe no banco
- Use outro nome de usuário

### Erro: "Duplicate entry ... for key 'email'"

**Solução:**
- Esse email já está cadastrado
- Use outro email

### Erro: "Duplicate entry ... for key 'cpf'"

**Solução:**
- Esse CPF já está cadastrado
- Use outro CPF

## 📝 Consultas Úteis no MySQL

### Ver todos os usuários:
```sql
SELECT id, username, email, cpf, data_nascimento, created_at 
FROM users;
```

### Buscar usuário específico:
```sql
SELECT * FROM users WHERE username = 'teste';
```

### Contar usuários:
```sql
SELECT COUNT(*) as total FROM users;
```

### Ver usuários ativos:
```sql
SELECT * FROM users WHERE is_active = TRUE;
```

### Deletar usuário (cuidado!):
```sql
DELETE FROM users WHERE username = 'teste';
```

### Desativar usuário (mais seguro):
```sql
UPDATE users SET is_active = FALSE WHERE username = 'teste';
```

## ✅ Checklist de Configuração

- [ ] MySQL instalado e rodando
- [ ] Banco de dados criado no Workbench
- [ ] Tabela `users` criada
- [ ] Driver `pymysql` instalado (`pip install pymysql`)
- [ ] Arquivo `database.py` configurado com:
  - [ ] DB_TYPE = 'mysql'
  - [ ] DB_HOST correto
  - [ ] DB_PORT = '3306'
  - [ ] DB_NAME = nome do seu banco
  - [ ] DB_USER = seu usuário
  - [ ] DB_PASSWORD = sua senha
- [ ] Servidor testado (`python servidor.py`)
- [ ] Cadastro testado (criar um usuário)
- [ ] Dados verificados no MySQL Workbench

## 🎉 Pronto!

Agora seu sistema está usando MySQL com todos os campos:
- Nome de usuário
- Email
- CPF
- Data de nascimento
- Senha (criptografada)

Todos os cadastros feitos no site serão salvos automaticamente no banco MySQL!

## 💡 Dicas

1. **Backup**: Faça backup do banco regularmente
   ```bash
   mysqldump -u root -p vms_db > backup.sql
   ```

2. **Restaurar Backup**:
   ```bash
   mysql -u root -p vms_db < backup.sql
   ```

3. **Ver estrutura da tabela**:
   ```sql
   DESCRIBE users;
   ```

4. **Ver índices**:
   ```sql
   SHOW INDEX FROM users;
   ```

Se tiver problemas, verifique:
- Logs do servidor Python
- Logs do MySQL
- Configurações de conexão no `database.py`

