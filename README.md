# Projeto VMS - Gerenciador de Câmeras

Sistema de gerenciamento de múltiplas câmeras com gravação e detecção de movimento.

## 📁 Estrutura do Projeto

O projeto está dividido em vários arquivos para facilitar a organização e manutenção:

### 📄 `servidor.py` (Arquivo Principal)
- **O que faz**: Inicia o servidor Flask e coordena todos os módulos
- **Quando usar**: Este é o arquivo que você roda para iniciar o servidor
- **Comando**: `python servidor.py`

### ⚙️ `config.py` (Configurações)
- **O que faz**: Contém todas as configurações do projeto
- **O que tem aqui**:
  - Definição das câmeras (`CAMERA_SOURCES`)
  - Nome da pasta de gravações (`PASTA_GRAVACOES`)
  - Configurações de detecção de movimento (`MOTION_COOLDOWN`, `MIN_CONTOUR_AREA`)
  - Dicionário global de câmeras (`g_cameras`)
- **Quando modificar**: Quando quiser adicionar câmeras ou mudar configurações

### 🎥 `camera_worker.py` (Gerenciador de Câmera)
- **O que faz**: Contém a classe `CameraWorker` que gerencia cada câmera individualmente
- **Responsabilidades**:
  - Ler frames da câmera continuamente
  - Processar detecção de movimento
  - Gravar vídeo quando necessário
  - Armazenar frames para transmissão ao vivo
- **Quando modificar**: Quando quiser alterar a lógica de detecção de movimento ou gravação

### 📺 `video_stream.py` (Streaming de Vídeo)
- **O que faz**: Gera o stream de vídeo ao vivo para exibição no navegador
- **Função principal**: `gerar_frames(cam_id)` - codifica frames em JPEG e envia para o navegador
- **Quando modificar**: Quando quiser alterar a qualidade ou formato do stream

### 🛣️ `routes.py` (Rotas da API)
- **O que faz**: Contém todas as rotas (endpoints) da API Flask
- **Rotas disponíveis**:
  - `GET /` - Página principal (interface HTML)
  - `GET /get_cameras` - Lista todas as câmeras disponíveis
  - `GET /get_status/<cam_id>` - Obtém status de uma câmera
  - `GET /video_feed/<cam_id>` - Stream de vídeo ao vivo
  - `POST /start_recording/<cam_id>` - Inicia gravação manual
  - `POST /stop_recording/<cam_id>` - Para gravação manual
  - `POST /toggle_motion_detection/<cam_id>` - Liga/desliga detecção de movimento
  - `GET /list_videos` - Lista vídeos gravados
  - `GET /playback/<filename>` - Reproduz um vídeo gravado
- **Quando modificar**: Quando quiser adicionar novas funcionalidades ou endpoints

### 📄 `templates/index.html` (Interface Web)
- **O que faz**: Interface HTML que o usuário vê no navegador
- **Funcionalidades**:
  - Mostra vídeo ao vivo de cada câmera
  - Botões para controlar gravação
  - Botão para ligar/desligar detecção de movimento
  - Player para assistir gravações

## 🚀 Como Usar

1. **Configure suas câmeras** no arquivo `config.py`:
   ```python
   CAMERA_SOURCES = {
       "webcam": 0,  # Webcam USB
       # "corredor": "rtsp://usuario:senha@192.168.1.100:554/stream1"  # Câmera IP
   }
   ```

2. **Instale as dependências**:
   ```bash
   pip install flask opencv-python
   ```

3. **Execute o servidor**:
   ```bash
   python servidor.py
   ```

4. **Acesse a interface**:
   Abra o navegador em `http://127.0.0.1:5000`

## 📝 Como Adicionar uma Nova Câmera

1. Abra o arquivo `config.py`
2. Adicione uma nova entrada no dicionário `CAMERA_SOURCES`:
   ```python
   CAMERA_SOURCES = {
       "webcam": 0,
       "nova_camera": 1,  # Para uma segunda webcam USB
       # ou
       # "camera_ip": "rtsp://usuario:senha@192.168.1.100:554/stream1"
   }
   ```
3. Reinicie o servidor

## 🔧 Ajustando a Sensibilidade da Detecção de Movimento

No arquivo `config.py`, você pode ajustar:

- **`MIN_CONTOUR_AREA`**: Área mínima de movimento (em pixels)
  - Valores menores = mais sensível (detecta movimentos pequenos)
  - Valores maiores = menos sensível (só detecta movimentos grandes)

- **`MOTION_COOLDOWN`**: Tempo de espera após movimento antes de parar a gravação (em segundos)
  - Valores menores = para de gravar mais rápido
  - Valores maiores = continua gravando por mais tempo após o movimento

## 📚 Entendendo o Código

### Fluxo de Funcionamento

1. **Inicialização** (`servidor.py`):
   - Cria a pasta de gravações
   - Cria um `CameraWorker` para cada câmera
   - Inicia cada worker em uma thread separada
   - Inicia o servidor Flask

2. **Processamento de Frames** (`camera_worker.py`):
   - Cada câmera lê frames continuamente em um loop
   - Se detecção de movimento estiver ativa, processa cada frame
   - Se detectar movimento, inicia gravação automaticamente
   - Salva frames no arquivo de vídeo se estiver gravando
   - Armazena o último frame para transmissão ao vivo

3. **Streaming** (`video_stream.py`):
   - Pega o último frame da câmera
   - Codifica em JPEG
   - Envia para o navegador em formato MJPEG

4. **API** (`routes.py`):
   - Recebe comandos do navegador (gravar, parar, etc.)
   - Atualiza o estado das câmeras
   - Retorna informações em formato JSON

## 🐛 Resolução de Problemas

### Câmera não abre
- Verifique se a câmera está conectada
- Verifique se o número da câmera está correto (0, 1, 2, etc.)
- Para câmeras IP, verifique o endereço RTSP

### Vídeo não aparece na interface
- Verifique se a câmera está funcionando corretamente
- Verifique os logs no console para erros
- Tente recarregar a página

### Detecção de movimento não funciona
- Certifique-se de que a detecção está ativada (botão "Ligar Detecção")
- Aguarde alguns segundos para o fundo estático ser definido
- Ajuste `MIN_CONTOUR_AREA` se necessário

## 📦 Dependências

- **Flask**: Servidor web
- **opencv-python**: Processamento de vídeo e câmeras
- **threading**: Execução paralela (já vem com Python)

## 📄 Licença

Este projeto é para fins educacionais.

