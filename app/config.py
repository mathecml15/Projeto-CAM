"""
================================================================================
ARQUIVO DE CONFIGURAÇÕES
================================================================================

Este arquivo contém todas as configurações do projeto.
Aqui você define suas câmeras e ajusta os parâmetros do sistema.
"""

# ============================================================================
# CONFIGURAÇÃO DE CÂMERAS
# ============================================================================

# DICIONÁRIO DE CÂMERAS
# Aqui você define quantas câmeras quer usar e qual a fonte de cada uma
# - "webcam": 0  significa usar a webcam padrão do computador
# - Você pode adicionar mais câmeras com outros IDs e fontes
CAMERA_SOURCES = {
    "webcam": 0,  # ID da câmera: fonte (0 = primeira webcam USB)
    # Exemplo para adicionar uma câmera IP (descomente e configure):
    # "corredor": "rtsp://usuario:senha@192.168.1.100:554/stream1"
}

# ============================================================================
# CONFIGURAÇÕES DE GRAVAÇÃO
# ============================================================================

# Nome da pasta onde os vídeos serão salvos
PASTA_GRAVACOES = "gravacoes"

# ============================================================================
# CONFIGURAÇÕES DE DETECÇÃO DE MOVIMENTO
# ============================================================================

# Tempo de espera após detectar movimento antes de parar a gravação (em segundos)
# Se não detectar movimento por 5 segundos, para de gravar
MOTION_COOLDOWN = 5.0

# Área mínima de movimento para considerar detecção (em pixels)
# Valores menores = mais sensível, valores maiores = menos sensível
MIN_CONTOUR_AREA = 500

# ============================================================================
# CONFIGURAÇÕES DE DETECÇÃO DE OBJETOS (IA)
# ============================================================================

# Ativa ou desativa a detecção de objetos por padrão
OBJECT_DETECTION_ENABLED = False

# Modelo YOLO a ser usado (agora na pasta models/)
# Opções: 'yolov8n.pt' (nano - mais rápido), 'yolov8s.pt' (small),
#         'yolov8m.pt' (medium), 'yolov8l.pt' (large), 'yolov8x.pt' (extra large)
YOLO_MODEL = 'models/yolov8n.pt'  # Recomendado: nano para CPU, small/medium para GPU

# Limiar de confiança para detecções (0.0 a 1.0)
# Valores maiores = só detecta objetos com alta certeza (menos falsos positivos)
# Valores menores = detecta mais objetos (pode ter mais falsos positivos)
OBJECT_CONFIDENCE_THRESHOLD = 0.5

# Classes de objetos para detectar (None = detecta todas as classes)
# Exemplo: ['person', 'car', 'dog'] = só detecta pessoas, carros e cachorros
OBJECT_CLASSES_FILTER = None  # None = detecta todas as 80 classes

# Gravar automaticamente quando detectar objetos específicos
# Se None, não grava automaticamente por detecção de objetos
# Exemplo: ['person'] = grava quando detectar pessoas
AUTO_RECORD_ON_OBJECTS = None  # None ou lista de classes (ex: ['person'])

# ============================================================================
# CONFIGURAÇÕES DE BANCO DE DADOS
# ============================================================================

# Tipo de banco de dados a usar
# Opções: 'sqlite' (padrão, mais simples), 'postgresql', 'mysql'
# SQLite não requer servidor separado e é ideal para desenvolvimento
# PostgreSQL/MySQL são recomendados para produção
DB_TYPE = 'sqlite'  # Padrão: SQLite

# ============================================================================
# VARIÁVEL GLOBAL PARA ARMAZENAR CÂMERAS
# ============================================================================

# Dicionário global para armazenar todas as câmeras ativas
# A chave é o ID da câmera (ex: "webcam") e o valor é o objeto CameraWorker
# Esta variável é inicializada no servidor.py
g_cameras = {}

