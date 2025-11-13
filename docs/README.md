# 📹 Sistema VMS - Gerenciador de Câmeras

Sistema completo de gerenciamento de câmeras (Video Management System) com autenticação de usuários, gravação automática, detecção de movimento e inteligência artificial para detecção de objetos.

## ✨ Funcionalidades

- 🔐 **Autenticação Segura**: Sistema de login e cadastro com senhas criptografadas
- 📹 **Gerenciamento de Múltiplas Câmeras**: Suporte para webcams e câmeras IP (RTSP)
- 💾 **Gravação Automática**: Grave vídeos manualmente ou automaticamente ao detectar movimento
- 🎯 **Detecção de Movimento**: Algoritmo inteligente para detectar movimentos em tempo real
- 🤖 **Detecção de Objetos com IA**: YOLOv8 para identificar pessoas, carros, animais e mais
- 📊 **Estatísticas em Tempo Real**: Visualize estatísticas de detecções de objetos
- 🌐 **Interface Web Moderna**: Design responsivo e intuitivo
- 🗄️ **Banco de Dados MySQL**: Armazenamento robusto de usuários e logs

## 🚀 Tecnologias Utilizadas

- **Backend**: Python 3.11+, Flask
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Visão Computacional**: OpenCV
- **Inteligência Artificial**: Ultralytics YOLOv8
- **Banco de Dados**: MySQL 8.0+
- **Segurança**: SHA-256 + Salt, Sessões seguras

## 📋 Pré-requisitos

- Python 3.11 ou superior
- MySQL 8.0 ou superior
- Webcam ou câmera IP (opcional)
- 4GB RAM mínimo (8GB recomendado para IA)

## 🔧 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/vms-camera-manager.git
cd vms-camera-manager
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure o MySQL

Execute o script SQL no MySQL Workbench ou linha de comando:

```bash
mysql -u root -p < "banco de dados MYSQL.sql"
```

Ou manualmente:

```sql
CREATE DATABASE servico_auth CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE servico_auth;

CREATE TABLE users(
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

### 4. Configure as variáveis de ambiente

Copie o arquivo de exemplo e edite com suas credenciais:

```bash
cp .env.example .env
```

Edite o arquivo `.env` e configure:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=servico_auth
DB_USER=root
DB_PASSWORD=sua_senha_mysql

SECRET_KEY=sua_chave_secreta_aqui
SALT_SECRET=sua_chave_secreta_aqui
```

**⚠️ IMPORTANTE:** O arquivo `.env` contém informações sensíveis. **NUNCA** suba este arquivo para o GitHub!

### 5. Execute o servidor

```bash
python servidor.py
```

### 6. Acesse o sistema

Abra seu navegador e acesse:

```
http://127.0.0.1:5000
```

## 📖 Como Usar

### Primeiro Acesso

1. Acesse `http://127.0.0.1:5000`
2. Clique em **"Cadastre-se aqui"**
3. Preencha seus dados:
   - Nome de usuário
   - Email
   - CPF
   - Data de nascimento
   - Senha
4. Faça login com suas credenciais

### Gerenciando Câmeras

1. Na página principal, você verá todas as câmeras configuradas
2. **Gravar**: Inicia gravação manual
3. **Parar**: Para a gravação
4. **Detecção de Movimento**: Ativa/desativa gravação automática ao detectar movimento
5. **IA Detecção**: Ativa/desativa detecção de objetos com inteligência artificial

### Visualizando Gravações

- As gravações ficam na pasta `gravacoes/`
- Lista de vídeos gravados aparece abaixo de cada câmera
- Clique em um vídeo para reproduzir

### Configurando Câmeras

Edite o arquivo `config.py`:

```python
CAMERA_SOURCES = {
    "webcam": 0,  # Webcam padrão
    "camera_ip": "rtsp://usuario:senha@192.168.1.100:554/stream1"  # Câmera IP
}
```

## 📊 Detecção de Objetos (IA)

O sistema usa YOLOv8 para detectar:

- 👥 Pessoas
- 🚗 Veículos (carros, motos, caminhões, ônibus)
- 🐕 Animais (cães, gatos, pássaros, cavalos)
- 📦 Objetos diversos (80+ classes)

### Configurações de IA

No arquivo `config.py`:

```python
# Modelo YOLO (nano, small, medium, large, x-large)
YOLO_MODEL = 'yolov8n.pt'  # 'n' = nano (mais rápido)

# Confiança mínima (0.0 a 1.0)
OBJECT_CONFIDENCE_THRESHOLD = 0.5

# Filtrar classes específicas
OBJECT_CLASSES_FILTER = ['person', 'car', 'dog']  # None = todas

# Gravar automaticamente ao detectar
AUTO_RECORD_ON_OBJECTS = ['person']  # None = desativado
```

## 📁 Estrutura do Projeto

```
vms-camera-manager/
├── servidor.py              # Servidor principal
├── config.py                # Configurações do sistema
├── database.py              # Gerenciamento do banco de dados
├── auth.py                  # Sistema de autenticação
├── auth_routes.py           # Rotas de login/cadastro
├── routes.py                # Rotas da aplicação
├── camera_worker.py         # Thread de câmera
├── video_stream.py          # Streaming de vídeo
├── object_detector.py       # Detecção de objetos IA
├── templates/
│   ├── index.html          # Interface principal
│   ├── login.html          # Página de login
│   └── register.html       # Página de cadastro
├── gravacoes/              # Vídeos gravados (ignorado pelo Git)
├── requirements.txt        # Dependências Python
├── .env                    # Variáveis de ambiente (NÃO versionar!)
├── .env.example           # Exemplo de configuração
└── README.md              # Este arquivo
```

## 🔒 Segurança

- ✅ Senhas criptografadas com SHA-256 + Salt
- ✅ Variáveis de ambiente para informações sensíveis
- ✅ Proteção contra SQL Injection
- ✅ Sessões seguras com cookies HttpOnly
- ✅ Validação de dados no backend

### Boas Práticas

1. **Nunca** commite o arquivo `.env`
2. Use senhas fortes para o MySQL
3. Gere chaves secretas aleatórias:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
4. Em produção, use HTTPS (configure `SESSION_COOKIE_SECURE = True`)

## 🐛 Troubleshooting

### Erro: "No module named 'cv2'"

```bash
pip install opencv-python
```

### Erro: "No module named 'pymysql'"

```bash
pip install pymysql
```

### Erro: "Access denied for user"

Verifique as credenciais no arquivo `.env`:
- `DB_USER` e `DB_PASSWORD` devem estar corretos
- O usuário deve ter permissões no banco `servico_auth`

### Erro: "Can't connect to MySQL server"

- Verifique se o MySQL está rodando
- Confirme a porta (padrão: 3306)
- Teste a conexão: `mysql -u root -p`

### Câmera não funciona

- Verifique se a webcam está conectada
- Teste com ID diferente: `0`, `1`, `2`
- Para câmeras IP, verifique a URL RTSP

## 📈 Roadmap

- [ ] Suporte a múltiplos usuários com permissões
- [ ] Notificações por email/WhatsApp
- [ ] Dashboard com gráficos de estatísticas
- [ ] API REST completa
- [ ] App mobile (React Native)
- [ ] Reconhecimento facial
- [ ] Suporte a áudio
- [ ] Gravação em nuvem (AWS S3, Google Cloud)
- [ ] Docker e Kubernetes

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👨‍💻 Autor

Desenvolvido com ❤️ por [Seu Nome]

## 📞 Suporte

Se tiver dúvidas ou problemas:

1. Verifique a seção [Troubleshooting](#-troubleshooting)
2. Abra uma [Issue](https://github.com/seu-usuario/vms-camera-manager/issues)
3. Entre em contato: seu-email@exemplo.com

---

⭐ Se este projeto foi útil para você, considere dar uma estrela no GitHub!
