# 📁 Estrutura Organizada do Projeto

Este documento descreve a estrutura organizada do projeto VMS após a reorganização.

## 📂 Estrutura de Pastas

```
Projeto/
├── app/                          # Módulos principais da aplicação
│   ├── __init__.py              # Inicialização do pacote
│   ├── auth.py                   # Autenticação e permissões
│   ├── auth_routes.py            # Rotas de autenticação
│   ├── camera_manager.py         # Gerenciamento de câmeras
│   ├── camera_worker.py         # Worker thread para cada câmera
│   ├── config.py                # Configurações do sistema
│   ├── database.py              # Operações MySQL
│   ├── event_logger.py          # Sistema de logs
│   ├── object_detector.py       # Detecção de objetos (IA)
│   ├── routes.py                # Rotas principais
│   ├── stats.py                 # Estatísticas
│   ├── video_converter.py       # Conversão de vídeos
│   └── video_stream.py          # Streaming de vídeo
│
├── config/                       # Arquivos de configuração
│   ├── cameras_config.json       # Configuração de câmeras
│   ├── system_config.json        # Configuração do sistema
│   ├── cert.pem                 # Certificado SSL (se usar HTTPS)
│   └── key.pem                   # Chave SSL (se usar HTTPS)
│
├── database/                      # Scripts e esquemas do banco
│   ├── banco de dados MYSQL.sql  # Script SQL
│   └── banco.mwb                 # Modelo MySQL Workbench
│
├── docs/                          # Documentação
│   ├── README.md
│   ├── CONFIGURAR_HTTPS.md
│   ├── CONFIGURAR_MYSQL.md
│   ├── ESTRUTURA_PROJETO.md
│   ├── GUIA_AUTENTICACAO.md
│   ├── GUIA_DETECCAO_OBJETOS.md
│   ├── ROLES_E_PERMISSOES.md
│   └── SOLUCAO_PROBLEMAS_HTTPS.md
│
├── gravacoes/                     # Vídeos gravados
│   └── *.webm, *.mp4, etc.
│
├── logs/                          # Logs do sistema
│   └── events_log.json            # Histórico de eventos
│
├── models/                         # Modelos de IA
│   └── yolov8n.pt                 # Modelo YOLO
│
├── scripts/                        # Scripts utilitários
│   └── gerar_certificado_ssl.py   # Gerador de certificados SSL
│
├── static/                        # Arquivos estáticos (CSS, JS, imagens)
│
├── templates/                      # Templates HTML
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── cameras.html
│   ├── dashboard.html
│   ├── events.html
│   ├── export.html
│   └── settings.html
│
├── tools/                          # Ferramentas externas
│   └── ffmpeg/
│       └── bin/
│           ├── ffmpeg.exe
│           ├── ffplay.exe
│           └── ffprobe.exe
│
├── .env                            # Variáveis de ambiente (NÃO commitar!)
├── .gitignore                     # Arquivos ignorados pelo Git
├── README.md                       # Documentação principal
├── requirements.txt                # Dependências Python
└── servidor.py                     # Ponto de entrada principal
```

## 📝 Descrição das Pastas

### `app/`
Contém todos os módulos Python da aplicação. Cada arquivo tem uma responsabilidade específica:
- **auth.py**: Sistema de autenticação, roles e permissões
- **auth_routes.py**: Rotas de login, registro e logout
- **camera_manager.py**: Gerencia configurações de câmeras (JSON)
- **camera_worker.py**: Thread worker para processar cada câmera
- **config.py**: Configurações gerais do sistema
- **database.py**: Todas as operações com MySQL
- **event_logger.py**: Sistema de logging de eventos
- **object_detector.py**: Detecção de objetos usando YOLO
- **routes.py**: Rotas principais da aplicação
- **stats.py**: Cálculo de estatísticas
- **video_converter.py**: Conversão de formatos de vídeo
- **video_stream.py**: Streaming MJPEG para interface web

### `config/`
Armazena todos os arquivos de configuração:
- **cameras_config.json**: Lista de câmeras configuradas
- **system_config.json**: Configurações do sistema (detecção, gravação, etc.)
- **cert.pem / key.pem**: Certificados SSL (se usar HTTPS)

### `database/`
Scripts e esquemas do banco de dados MySQL.

### `docs/`
Documentação completa do projeto em Markdown.

### `gravacoes/`
Vídeos gravados pelo sistema. Formatos: WebM, MP4, AVI, MOV.

### `logs/`
Logs do sistema:
- **events_log.json**: Histórico completo de eventos

### `models/`
Modelos de IA (YOLO) para detecção de objetos.

### `scripts/`
Scripts utilitários:
- **gerar_certificado_ssl.py**: Gera certificados SSL auto-assinados

### `static/`
Arquivos estáticos (CSS, JavaScript, imagens) servidos pelo Flask.

### `templates/`
Templates HTML usando Jinja2.

### `tools/`
Ferramentas externas (FFmpeg, etc.).

## 🔄 Mudanças Realizadas

### Organização de Arquivos
1. ✅ Criadas pastas `config/`, `logs/`, `scripts/`
2. ✅ Movidos arquivos JSON para `config/`
3. ✅ Movido `events_log.json` para `logs/`
4. ✅ Movido `gerar_certificado_ssl.py` para `scripts/`
5. ✅ Atualizados caminhos nos arquivos Python

### Limpeza de Código
1. ✅ Removido código SQLite (não usado)
2. ✅ Removido código PostgreSQL (não usado)
3. ✅ Removido código JSON legado de autenticação
4. ✅ Mantido apenas MySQL
5. ✅ Removidos scripts temporários

### Documentação
1. ✅ Criado `README.md` principal
2. ✅ Atualizado `app/__init__.py` com documentação
3. ✅ Criado `.gitignore` completo

## 📌 Convenções

- **Configurações**: Sempre em `config/`
- **Logs**: Sempre em `logs/`
- **Scripts**: Sempre em `scripts/`
- **Documentação**: Sempre em `docs/`
- **Código Python**: Sempre em `app/`
- **Templates**: Sempre em `templates/`
- **Arquivos estáticos**: Sempre em `static/`

## 🚀 Próximos Passos

Para manter a organização:
1. Sempre coloque novos arquivos de configuração em `config/`
2. Novos scripts vão em `scripts/`
3. Novos logs vão em `logs/`
4. Mantenha a estrutura de pastas consistente

