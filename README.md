# 🎥 Sistema VMS (Video Management System)

Sistema completo de gerenciamento de câmeras com detecção de movimento, detecção de objetos por IA, gravação de vídeo e interface web moderna.

## 📋 Índice

- [Características](#características)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso](#uso)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Documentação](#documentação)

## ✨ Características

- 🎥 **Gerenciamento de Múltiplas Câmeras**: Suporte para câmeras USB e IP (RTSP/HTTP)
- 📹 **Gravação de Vídeo**: Gravação manual e automática por detecção de movimento
- 🤖 **Detecção de Objetos (IA)**: Detecção em tempo real usando YOLOv8
- 🔐 **Sistema de Autenticação**: Login, registro e controle de acesso baseado em roles
- 📊 **Dashboard**: Estatísticas e métricas do sistema
- 📝 **Histórico de Eventos**: Log completo de todas as ações do sistema
- 🔒 **HTTPS**: Suporte a conexões seguras (SSL/TLS)
- 🎨 **Interface Moderna**: Interface web responsiva com tema claro/escuro
- 📦 **Exportação de Vídeos**: Conversão para múltiplos formatos (MP4, AVI, MOV, WebM)

## 🔧 Requisitos

- Python 3.8 ou superior
- MySQL 5.7 ou superior
- OpenSSL (para HTTPS - opcional)

## 📦 Instalação

1. **Clone o repositório**:
```bash
git clone <seu-repositorio>
cd Projeto
```

2. **Instale as dependências**:
```bash
pip install -r requirements.txt
```

3. **Configure o banco de dados MySQL**:
   - Crie um banco de dados MySQL
   - Configure as credenciais no arquivo `.env` (veja `.env.example`)

4. **Configure o arquivo `.env`**:
```env
# Banco de Dados
DB_HOST=localhost
DB_PORT=3306
DB_NAME=seu_banco
DB_USER=seu_usuario
DB_PASSWORD=sua_senha

# Segurança
SECRET_KEY=sua_chave_secreta_aqui
SALT_SECRET=sua_chave_salt_aqui

# HTTPS (opcional)
USE_HTTPS=False
SSL_CERT_PATH=config/cert.pem
SSL_KEY_PATH=config/key.pem
ALLOW_INSECURE_COOKIES=True

# Servidor
PORT=5000
```

## 🚀 Uso

1. **Inicie o servidor**:
```bash
python servidor.py
```

2. **Acesse a interface web**:
   - HTTP: `http://localhost:5000`
   - HTTPS: `https://localhost:5000` (se configurado)

3. **Faça login**:
   - Primeiro acesso: crie uma conta na página de registro
   - O primeiro usuário criado terá role `viewer` por padrão
   - Para tornar-se admin, atualize o role no banco de dados

## 📁 Estrutura do Projeto

```
Projeto/
├── app/                    # Módulos principais da aplicação
│   ├── __init__.py
│   ├── auth.py            # Autenticação e permissões
│   ├── auth_routes.py     # Rotas de autenticação
│   ├── camera_manager.py  # Gerenciamento de câmeras
│   ├── camera_worker.py  # Worker de cada câmera
│   ├── config.py         # Configurações do sistema
│   ├── database.py       # Conexão e operações MySQL
│   ├── event_logger.py   # Sistema de logs
│   ├── object_detector.py # Detecção de objetos (IA)
│   ├── routes.py         # Rotas principais
│   ├── stats.py          # Estatísticas do sistema
│   ├── video_converter.py # Conversão de vídeos
│   └── video_stream.py   # Streaming de vídeo
├── config/                # Arquivos de configuração
│   ├── cameras_config.json
│   └── system_config.json
├── database/              # Scripts e esquemas do banco
│   ├── banco de dados MYSQL.sql
│   └── banco.mwb
├── docs/                  # Documentação
│   ├── CONFIGURAR_HTTPS.md
│   ├── CONFIGURAR_MYSQL.md
│   ├── ESTRUTURA_PROJETO.md
│   ├── ESTRUTURA_ORGANIZADA.md
│   ├── GUIA_AUTENTICACAO.md
│   ├── GUIA_DETECCAO_OBJETOS.md
│   ├── ROLES_E_PERMISSOES.md
│   └── ...
├── gravacoes/             # Vídeos gravados
├── logs/                  # Logs do sistema
│   └── events_log.json
├── models/                # Modelos de IA
│   └── yolov8n.pt
├── scripts/               # Scripts utilitários
│   └── gerar_certificado_ssl.py
├── static/                # Arquivos estáticos (CSS, JS, imagens)
├── templates/             # Templates HTML
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   └── ...
├── tools/                 # Ferramentas externas
│   └── ffmpeg/
├── .env                   # Variáveis de ambiente (criar)
├── requirements.txt       # Dependências Python
└── servidor.py           # Ponto de entrada principal
```

## 📚 Documentação

Documentação completa disponível na pasta `docs/`:

- [Estrutura do Projeto](docs/ESTRUTURA_PROJETO.md)
- [Estrutura Organizada](docs/ESTRUTURA_ORGANIZADA.md)
- [Changelog - Organização](docs/CHANGELOG_ORGANIZACAO.md)
- [Configurar HTTPS](docs/CONFIGURAR_HTTPS.md)
- [Configurar MySQL](docs/CONFIGURAR_MYSQL.md)
- [Guia de Autenticação](docs/GUIA_AUTENTICACAO.md)
- [Detecção de Objetos](docs/GUIA_DETECCAO_OBJETOS.md)
- [Roles e Permissões](docs/ROLES_E_PERMISSOES.md)

## 🔐 Roles e Permissões

O sistema possui três roles:

- **Admin**: Acesso total ao sistema
- **Operator**: Pode controlar câmeras e visualizar gravações
- **Viewer**: Apenas visualização (padrão para novos usuários)

## 🛠️ Desenvolvimento

Para contribuir ou modificar o projeto:

1. Mantenha a estrutura de pastas organizada
2. Siga os padrões de código existentes
3. Adicione comentários em português
4. Teste as mudanças antes de commitar

## 📝 Licença

Este projeto é de uso pessoal/educacional.

## 🤝 Suporte

Para problemas ou dúvidas, consulte a documentação em `docs/` ou verifique os logs em `logs/events_log.json`.

