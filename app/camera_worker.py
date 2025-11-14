"""
================================================================================
CAMERA WORKER - Classe que gerencia cada câmera
================================================================================

Este arquivo contém a classe CameraWorker, que é responsável por:
- Ler frames da câmera continuamente
- Processar detecção de movimento (se estiver ativada)
- Gravar vídeo quando necessário
- Armazenar o último frame para transmissão ao vivo
"""

import cv2  # OpenCV - para trabalhar com vídeo e câmeras
import time  # Para medir tempo (cooldown da detecção de movimento)
import threading  # Para rodar cada câmera em paralelo (threads)
import numpy as np  # Para criar arrays de imagens

# Importa VLC Python para streams RTSP (opcional)
try:
    import vlc
    VLC_AVAILABLE = True
except ImportError:
    VLC_AVAILABLE = False
    print("AVISO: VLC Python não disponível. Instale: pip install python-vlc")
    print("       Para câmeras IP (RTSP), o VLC é recomendado para melhor performance.")

# Importa as configurações
from app.config import (
    PASTA_GRAVACOES, MOTION_COOLDOWN, MIN_CONTOUR_AREA,
    OBJECT_DETECTION_ENABLED, YOLO_MODEL, OBJECT_CONFIDENCE_THRESHOLD,
    OBJECT_CLASSES_FILTER, AUTO_RECORD_ON_OBJECTS
)

# Importa o detector de objetos (opcional - só carrega se necessário)
try:
    from app.object_detector import ObjectDetector
    OBJECT_DETECTION_AVAILABLE = True
except ImportError:
    OBJECT_DETECTION_AVAILABLE = False
    print("AVISO: Detecção de objetos não disponível. Instale ultralytics: pip install ultralytics")

# Importa o logger de eventos
try:
    from app.event_logger import log_event, EventType, EventSeverity
    EVENT_LOGGING_AVAILABLE = True
except ImportError:
    EVENT_LOGGING_AVAILABLE = False
    print("AVISO: Logger de eventos não disponível.")


def create_no_camera_frame(cam_id, width=640, height=480):
    """
    Cria um frame informativo quando a câmera não está disponível.
    
    cam_id: ID da câmera
    width: Largura do frame
    height: Altura do frame
    
    Retorna: Frame (imagem numpy) com mensagem de erro
    """
    # Cria uma imagem preta
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Define cores
    cor_fundo = (40, 40, 40)  # Cinza escuro
    cor_texto = (255, 255, 255)  # Branco
    cor_aviso = (0, 165, 255)  # Laranja
    
    # Preenche com cor de fundo
    frame[:] = cor_fundo
    
    # Adiciona textos
    fonte = cv2.FONT_HERSHEY_SIMPLEX
    
    # Título
    texto1 = "Camera Nao Disponivel"
    tamanho1 = cv2.getTextSize(texto1, fonte, 0.8, 2)[0]
    x1 = (width - tamanho1[0]) // 2
    cv2.putText(frame, texto1, (x1, height // 2 - 60), fonte, 0.8, cor_aviso, 2)
    
    # ID da câmera
    texto2 = f"ID: {cam_id}"
    tamanho2 = cv2.getTextSize(texto2, fonte, 0.6, 2)[0]
    x2 = (width - tamanho2[0]) // 2
    cv2.putText(frame, texto2, (x2, height // 2 - 10), fonte, 0.6, cor_texto, 2)
    
    # Instruções
    texto3 = "Verifique:"
    tamanho3 = cv2.getTextSize(texto3, fonte, 0.5, 1)[0]
    x3 = (width - tamanho3[0]) // 2
    cv2.putText(frame, texto3, (x3, height // 2 + 30), fonte, 0.5, cor_texto, 1)
    
    texto4 = "- Webcam conectada?"
    tamanho4 = cv2.getTextSize(texto4, fonte, 0.4, 1)[0]
    x4 = (width - tamanho4[0]) // 2
    cv2.putText(frame, texto4, (x4, height // 2 + 55), fonte, 0.4, cor_texto, 1)
    
    texto5 = "- Outra aplicacao usando a camera?"
    tamanho5 = cv2.getTextSize(texto5, fonte, 0.4, 1)[0]
    x5 = (width - tamanho5[0]) // 2
    cv2.putText(frame, texto5, (x5, height // 2 + 75), fonte, 0.4, cor_texto, 1)
    
    texto6 = "- Permissoes de acesso?"
    tamanho6 = cv2.getTextSize(texto6, fonte, 0.4, 1)[0]
    x6 = (width - tamanho6[0]) // 2
    cv2.putText(frame, texto6, (x6, height // 2 + 95), fonte, 0.4, cor_texto, 1)
    
    return frame


class CameraWorker(threading.Thread):
    """
    Esta classe representa UMA câmera trabalhando.
    Cada câmera tem sua própria instância desta classe rodando em paralelo.
    
    O QUE ELA FAZ:
    - Lê frames da câmera continuamente
    - Processa detecção de movimento (se estiver ativada)
    - Grava vídeo quando necessário
    - Armazena o último frame para transmissão ao vivo
    """
    
    def __init__(self, cam_id, source):
        """
        Inicializador - roda quando criamos uma nova câmera.
        
        cam_id: ID único da câmera (ex: "webcam")
        source: Fonte da câmera (ex: 0 para webcam USB, ou endereço RTSP como "rtsp://...")
        """
        # Chama o inicializador da classe Thread (permite rodar em paralelo)
        super().__init__()
        
        # Armazena o ID e a fonte da câmera
        self.cam_id = cam_id  # Exemplo: "webcam"
        self.source = source  # Exemplo: 0 (webcam USB) ou "rtsp://..." (câmera IP)
        
        # Daemon = True significa que a thread para quando o programa principal parar
        self.daemon = True
        
        print(f"Iniciando câmera: {self.cam_id}")
        
        # ================================================================
        # DETECÇÃO AUTOMÁTICA: RTSP vs USB
        # ================================================================
        # Verifica se source é uma string começando com "rtsp://" (câmera IP)
        is_rtsp = isinstance(source, str) and source.lower().startswith('rtsp://')
        
        # Se for RTSP e VLC está disponível, usa VLC (mais eficiente)
        # Caso contrário, usa OpenCV (funciona para USB e RTSP, mas menos eficiente para RTSP)
        self.use_vlc = is_rtsp and VLC_AVAILABLE
        self.cap = None  # OpenCV VideoCapture
        self.vlc_instance = None  # Instância VLC
        self.vlc_player = None  # Player VLC
        
        if self.use_vlc:
            # ============================================================
            # CONFIGURAÇÃO VLC PARA STREAMS RTSP
            # ============================================================
            print(f"  [{self.cam_id}] Detectado stream RTSP - usando VLC Python")
            try:
                # Cria instância VLC
                self.vlc_instance = vlc.Instance(['--no-audio', '--quiet', '--network-caching=300'])
                # Cria player VLC
                self.vlc_player = self.vlc_instance.media_player_new()
                # Define a URL RTSP como fonte
                media = self.vlc_instance.media_new(source)
                self.vlc_player.set_media(media)
                # Configura para não mostrar janela (headless)
                if hasattr(self.vlc_player, 'set_xwindow'):
                    self.vlc_player.set_xwindow(-1)  # Linux
                # Reproduz o stream
                self.vlc_player.play()
                # Aguarda um pouco para o stream iniciar
                time.sleep(2)
                print(f"  [{self.cam_id}] Stream RTSP iniciado via VLC")
            except Exception as e:
                print(f"  ERRO [{self.cam_id}]: Falha ao iniciar VLC: {e}")
                print(f"  [{self.cam_id}] Tentando fallback para OpenCV...")
                self.use_vlc = False
        
        if not self.use_vlc:
            # ============================================================
            # CONFIGURAÇÃO OPENCV (USB ou RTSP fallback)
            # ============================================================
            print(f"  [{self.cam_id}] Usando OpenCV ({'USB' if not is_rtsp else 'RTSP fallback'})")
            self.cap = cv2.VideoCapture(source)
            # Para RTSP, configura timeouts maiores
            if is_rtsp:
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduz buffer para menor latência
            # Verifica se a câmera foi aberta com sucesso
            if not self.cap.isOpened():
                print(f"ERRO: Não foi possível abrir a câmera {self.cam_id}")
        
        # LOCKS (Cadeados) - Previnem conflitos quando múltiplas threads acessam os mesmos dados
        # frame_lock: protege o frame que é transmitido ao vivo
        self.frame_lock = threading.Lock()
        # state_lock: protege todas as variáveis de estado (gravação, detecção, etc)
        self.state_lock = threading.Lock()
        
        # VARIÁVEIS DE ESTADO DA CÂMERA
        
        # Último frame processado (com retângulos de detecção, se houver)
        # Este frame é o que aparece no stream ao vivo
        self.output_frame = None
        
        # Indica se está gravando no momento
        self.is_recording = False
        
        # Objeto que escreve o vídeo no arquivo (None quando não está gravando)
        self.video_writer = None
        
        # Indica se a detecção de movimento está ativada
        self.motion_detection_enabled = False
        
        # Imagem do fundo estático (usada para comparar e detectar movimento)
        # None significa que ainda não foi definido
        self.static_background = None
        
        # Timestamp (momento) da última vez que movimento foi detectado
        self.last_motion_time = 0
        
        # ================================================================
        # CONFIGURAÇÃO DE DETECÇÃO DE OBJETOS (IA)
        # ================================================================
        
        # Indica se a detecção de objetos está ativada
        self.object_detection_enabled = OBJECT_DETECTION_ENABLED
        
        # Detector de objetos (será inicializado se necessário)
        self.object_detector = None
        
        # Última detecção de objetos (para evitar processar todos os frames)
        self.last_detection_time = 0
        self.detection_interval = 0.5  # Processa detecção a cada 0.5 segundos (2 FPS)
        
        # Estatísticas de detecção de objetos
        self.detection_stats_lock = threading.Lock()  # Lock para proteger estatísticas
        self.last_detections = []  # Últimas detecções (armazena as últimas 10)
        self.total_detections = 0  # Contador total de detecções
        self.detection_counts = {}  # Contador por classe de objeto (ex: {'person': 5, 'car': 2})
        self.last_detection_timestamp = 0  # Timestamp da última detecção
        
        # Inicializa o detector de objetos se estiver disponível e habilitado
        if OBJECT_DETECTION_AVAILABLE and self.object_detection_enabled:
            try:
                self.object_detector = ObjectDetector(
                    model_path=YOLO_MODEL,
                    conf_threshold=OBJECT_CONFIDENCE_THRESHOLD
                )
                if OBJECT_CLASSES_FILTER:
                    self.object_detector.set_classes_filter(OBJECT_CLASSES_FILTER)
                print(f"Detector de objetos inicializado para câmera {self.cam_id}")
            except Exception as e:
                print(f"ERRO ao inicializar detector de objetos para {self.cam_id}: {e}")
                self.object_detection_enabled = False

    def get_latest_frame(self):
        """
        Pega o último frame processado de forma segura.
        Retorna uma CÓPIA do frame para não causar conflitos.
        
        Retorna: Frame em formato numpy array, ou None se não houver frame
        """
        # Usa o lock para acessar o frame de forma segura
        with self.frame_lock:
            if self.output_frame is None:
                return None
            # Retorna uma CÓPIA para não modificar o original
            return self.output_frame.copy()
    
    def _read_frame(self):
        """
        Lê um frame da câmera usando VLC (RTSP) ou OpenCV (USB).
        Retorna: Frame numpy array ou None se falhar
        """
        if self.use_vlc and self.vlc_player:
            # ============================================================
            # LEITURA VIA VLC (RTSP)
            # ============================================================
            try:
                # Verifica se o player está reproduzindo
                state = self.vlc_player.get_state()
                if state == vlc.State.Ended or state == vlc.State.Error:
                    # Tenta reiniciar o stream
                    self.vlc_player.stop()
                    self.vlc_player.play()
                    time.sleep(1)
                
                # Obtém o frame atual do player VLC
                # VLC fornece frames como arrays de bytes
                video_track = self.vlc_player.video_get_track()
                if video_track == -1:
                    return None
                
                # Lê o frame como imagem usando callback VLC
                # Alternativa: usar OpenCV para ler do buffer VLC
                # Por enquanto, vamos usar um método mais direto
                width = self.vlc_player.video_get_width()
                height = self.vlc_player.video_get_height()
                
                if width <= 0 or height <= 0:
                    return None
                
                # VLC não fornece acesso direto aos frames via Python bindings simples
                # Vamos usar uma abordagem diferente: VLC salva frame temporariamente
                # ou podemos usar OpenCV para ler do mesmo stream RTSP em paralelo
                # Por enquanto, vamos fazer fallback para OpenCV quando VLC não conseguir
                # Na prática, VLC gerencia o stream melhor, mas precisamos acessar os frames
                # Vamos usar uma solução híbrida: VLC gerencia conexão, OpenCV lê frames
                
                # Abre um VideoCapture separado apenas para ler frames
                # (VLC gerencia a conexão, mas precisamos dos frames para processar)
                if not hasattr(self, '_opencv_fallback'):
                    self._opencv_fallback = cv2.VideoCapture(self.source)
                    self._opencv_fallback.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                ret, frame = self._opencv_fallback.read()
                if ret:
                    return frame
                return None
                
            except Exception as e:
                print(f"ERRO ao ler frame via VLC ({self.cam_id}): {e}")
                return None
        else:
            # ============================================================
            # LEITURA VIA OPENCV (USB ou RTSP fallback)
            # ============================================================
            if self.cap is None or not self.cap.isOpened():
                return None
            ret, frame = self.cap.read()
            if ret:
                return frame
            return None

    def start_recording_logic(self):
        """
        Função interna que INICIA a gravação de vídeo.
        IMPORTANTE: Esta função deve ser chamada dentro de um 'with self.state_lock:'
        """
        # Se já está gravando, não faz nada
        if self.is_recording:
            return
        
        print(f"LOG ({self.cam_id}): Iniciando gravação...")
        self.is_recording = True
        
        # Tenta pegar um frame para descobrir as dimensões do vídeo
        frame = self.get_latest_frame()
        
        # Se não houver frame ainda (câmera acabou de iniciar), tenta ler direto
        if frame is None:
            frame = self._read_frame()
            if frame is None:
                print(f"ERRO ({self.cam_id}): Não conseguiu ler frame para iniciar gravação.")
                self.is_recording = False
                # Registra erro no log
                if EVENT_LOGGING_AVAILABLE:
                    log_event(EventType.SYSTEM_ERROR, EventSeverity.ERROR, 
                             camera_id=self.cam_id,
                             message=f"Falha ao iniciar gravação: não foi possível ler frame")
                return
        
        # Pega as dimensões do frame (altura, largura)
        # frame.shape retorna (altura, largura, canais_de_cor)
        altura, largura, _ = frame.shape
        
        # FPS (frames por segundo) da gravação
        fps = 20.0
        
        # Codec de vídeo (VP80 = formato WebM)
        fourcc = cv2.VideoWriter_fourcc(*'VP80')
        
        # Cria um nome único para o arquivo usando data e hora
        timestr = time.strftime("%d-%m-%Y_%H%M%S")  # Exemplo: 25-12-2024_143022
        # Nome do arquivo inclui o ID da câmera para identificar qual câmera gravou
        nome_arquivo = f"{PASTA_GRAVACOES}/{self.cam_id}-gravacao-{timestr}.webm"
        
        # Cria o objeto que escreve o vídeo no arquivo
        self.video_writer = cv2.VideoWriter(nome_arquivo, fourcc, fps, (largura, altura))
        
        print(f"Salvando vídeo ({self.cam_id}) em: {nome_arquivo}")
        
        # Registra evento de início de gravação
        if EVENT_LOGGING_AVAILABLE:
            log_event(EventType.RECORDING_STARTED, EventSeverity.INFO,
                     camera_id=self.cam_id,
                     message=f"Gravação iniciada",
                     details={'filename': nome_arquivo, 'resolution': f"{largura}x{altura}", 'fps': fps})

    def stop_recording_logic(self):
        """
        Função interna que PARA a gravação de vídeo.
        IMPORTANTE: Esta função deve ser chamada dentro de um 'with self.state_lock:'
        """
        # Se não está gravando, não faz nada
        if not self.is_recording:
            return
        
        print(f"LOG ({self.cam_id}): Parando gravação...")
        self.is_recording = False
        
        # Se o video_writer existe, fecha e salva o arquivo
        if self.video_writer is not None:
            self.video_writer.release()  # Fecha o arquivo
            self.video_writer = None  # Limpa a variável
            print(f"Arquivo de vídeo ({self.cam_id}) salvo e fechado.")
            
            # Registra evento de parada de gravação
            if EVENT_LOGGING_AVAILABLE:
                log_event(EventType.RECORDING_STOPPED, EventSeverity.INFO,
                         camera_id=self.cam_id,
                         message=f"Gravação parada")

    def run(self):
        """
        Esta é a função principal que roda em loop infinito.
        Ela é executada automaticamente quando a thread é iniciada.
        
        O QUE ELA FAZ A CADA ITERAÇÃO:
        1. Lê um frame da câmera
        2. Se detecção de movimento estiver ativa, processa o frame
        3. Se detectar movimento, inicia gravação
        4. Se estiver gravando, salva o frame no arquivo
        5. Armazena o frame processado para transmissão ao vivo
        """
        # Loop infinito - roda para sempre até o programa fechar
        while True:
            # Verifica se a câmera ainda está disponível
            if self.use_vlc:
                # Verifica estado do player VLC
                if self.vlc_player is None:
                    error_frame = create_no_camera_frame(self.cam_id)
                    with self.frame_lock:
                        self.output_frame = error_frame
                    time.sleep(5)
                    continue
                # Verifica se está reproduzindo
                state = self.vlc_player.get_state()
                if state == vlc.State.Error or state == vlc.State.Ended:
                    print(f"({self.cam_id}): Erro no stream VLC. Tentando reconectar em 5s...")
                    error_frame = create_no_camera_frame(self.cam_id)
                    with self.frame_lock:
                        self.output_frame = error_frame
                    time.sleep(5)
                    # Tenta reiniciar
                    try:
                        self.vlc_player.stop()
                        self.vlc_player.play()
                        time.sleep(2)
                    except:
                        pass
                    continue
            else:
                # Verifica se a câmera OpenCV ainda está aberta
                if self.cap is None or not self.cap.isOpened():
                    print(f"({self.cam_id}): Câmera não está aberta. Tentando reconectar em 5s...")
                    # Cria um frame informativo para exibir ao usuário
                    error_frame = create_no_camera_frame(self.cam_id)
                    with self.frame_lock:
                        self.output_frame = error_frame
                    time.sleep(5)  # Espera 5 segundos
                    # Tenta abrir a câmera novamente
                    self.cap = cv2.VideoCapture(self.source)
                    if isinstance(self.source, str) and self.source.lower().startswith('rtsp://'):
                        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    continue  # Volta para o início do loop
            
            # Lê um frame da câmera (via VLC ou OpenCV)
            frame_original = self._read_frame()
            
            # Se não conseguiu ler o frame, mostra mensagem de erro
            if frame_original is None:
                print(f"({self.cam_id}): Falha ao ler frame. Câmera não disponível.")
                # Cria um frame informativo para exibir ao usuário
                error_frame = create_no_camera_frame(self.cam_id)
                # Salva este frame como output para o stream
                with self.frame_lock:
                    self.output_frame = error_frame
                time.sleep(1)  # Espera 1 segundo antes de tentar novamente
                continue  # Volta para o início do loop
            
            # Cria uma cópia do frame para processar (adicionar retângulos de detecção)
            # frame_processado será o que aparece no stream (com retângulos verdes)
            frame_processado = frame_original.copy()
            
            # Flag para indicar se movimento foi detectado neste frame
            motion_detected_this_frame = False
            
            # Flag para indicar se objetos foram detectados neste frame
            objects_detected_this_frame = False
            detected_objects = []
            
            # Pega o estado da detecção de movimento (protegido pelo lock)
            with self.state_lock:
                motion_is_on = self.motion_detection_enabled
            
            # ================================================================
            # PROCESSAMENTO DE DETECÇÃO DE MOVIMENTO
            # ================================================================
            if motion_is_on:
                # Converte o frame colorido para escala de cinza
                # Isso facilita a comparação e é mais rápido
                gray_frame = cv2.cvtColor(frame_original, cv2.COLOR_BGR2GRAY)
                
                # Aplica um filtro de desfoque (blur) para reduzir ruído
                # (21, 21) = tamanho do kernel de desfoque
                gray_frame = cv2.GaussianBlur(gray_frame, (21, 21), 0)
                
                # Acessa o fundo estático de forma segura
                with self.state_lock:
                    # Se ainda não temos um fundo estático, usa este frame como fundo
                    if self.static_background is None:
                        self.static_background = gray_frame
                        print(f"DETECÇÃO ({self.cam_id}): Fundo estático definido.")
                        # Pula este frame e vai para o próximo (precisa de mais frames para comparar)
                        continue
                    
                    # Copia o fundo para não ficar travado no lock
                    bg = self.static_background.copy()
                
                # Calcula a diferença entre o fundo e o frame atual
                # Quanto maior a diferença, mais movimento há
                diff_frame = cv2.absdiff(bg, gray_frame)
                
                # Converte a diferença em imagem binária (preto e branco)
                # Pixels com diferença > 30 viram branco (movimento), resto fica preto
                thresh_frame = cv2.threshold(diff_frame, 30, 255, cv2.THRESH_BINARY)[1]
                
                # Encontra os contornos (blocos) de movimento na imagem
                contours, _ = cv2.findContours(thresh_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # Para cada contorno encontrado
                for contour in contours:
                    # Calcula a área do contorno (quantos pixels tem)
                    area = cv2.contourArea(contour)
                    
                    # Se a área for muito pequena, ignora (é apenas ruído)
                    if area < MIN_CONTOUR_AREA:
                        continue
                    
                    # Se chegou aqui, é movimento real!
                    motion_detected_this_frame = True
                    
                    # Pega as coordenadas do retângulo que envolve o movimento
                    (x, y, w, h) = cv2.boundingRect(contour)
                    # x, y = canto superior esquerdo
                    # w, h = largura e altura
                    
                    # Desenha um retângulo verde no frame processado
                    # (0, 255, 0) = cor verde em BGR
                    # 2 = espessura da linha
                    cv2.rectangle(frame_processado, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # ============================================================
                # LÓGICA DE GRAVAÇÃO AUTOMÁTICA POR MOVIMENTO
                # ============================================================
                with self.state_lock:
                    if motion_detected_this_frame:
                        # Movimento detectado! Atualiza o timestamp
                        self.last_motion_time = time.time()
                        
                        # Se não está gravando, inicia a gravação
                        if not self.is_recording:
                            print(f"DETECÇÃO ({self.cam_id}): Movimento detectado! Iniciando gravação...")
                            # Registra evento de detecção de movimento
                            if EVENT_LOGGING_AVAILABLE:
                                log_event(EventType.MOTION_DETECTED, EventSeverity.INFO,
                                         camera_id=self.cam_id,
                                         message=f"Movimento detectado - iniciando gravação automática")
                            self.start_recording_logic()
                    else:
                        # Não há movimento neste frame
                        # Se está gravando E já passou o tempo de cooldown, para a gravação
                        tempo_sem_movimento = time.time() - self.last_motion_time
                        if self.is_recording and tempo_sem_movimento > MOTION_COOLDOWN:
                            print(f"DETECÇÃO ({self.cam_id}): Sem movimento por {MOTION_COOLDOWN}s. Parando gravação...")
                            self.stop_recording_logic()
            
            # ================================================================
            # DETECÇÃO DE OBJETOS (IA)
            # ================================================================
            # Processa detecção de objetos se estiver ativada
            # (processa a cada X segundos para não sobrecarregar o sistema)
            current_time = time.time()
            if (self.object_detection_enabled and 
                self.object_detector is not None and
                current_time - self.last_detection_time >= self.detection_interval):
                
                try:
                    # Faz a detecção de objetos no frame
                    frame_processado, detected_objects = self.object_detector.detect(frame_processado)
                    
                    # Atualiza o timestamp da última detecção
                    self.last_detection_time = current_time
                    
                    # Verifica se detectou objetos
                    if detected_objects:
                        objects_detected_this_frame = True
                        
                        # Atualiza as estatísticas (protegido por lock)
                        with self.detection_stats_lock:
                            # Adiciona às últimas detecções (mantém apenas as últimas 10)
                            self.last_detections.append({
                                'timestamp': current_time,
                                'objects': detected_objects.copy(),
                                'count': len(detected_objects)
                            })
                            if len(self.last_detections) > 10:
                                self.last_detections.pop(0)  # Remove a mais antiga
                            
                            # Atualiza contadores
                            self.total_detections += len(detected_objects)
                            self.last_detection_timestamp = current_time
                            
                            # Conta objetos por classe
                            for obj in detected_objects:
                                class_name = obj['class']
                                if class_name not in self.detection_counts:
                                    self.detection_counts[class_name] = 0
                                self.detection_counts[class_name] += 1
                        
                        # Se AUTO_RECORD_ON_OBJECTS está configurado, verifica se detectou objetos relevantes
                        if AUTO_RECORD_ON_OBJECTS:
                            detected_classes = [obj['class'] for obj in detected_objects]
                            # Verifica se algum objeto detectado está na lista de objetos para gravar
                            if any(cls in AUTO_RECORD_ON_OBJECTS for cls in detected_classes):
                                with self.state_lock:
                                    if not self.is_recording:
                                        print(f"DETECÇÃO DE OBJETOS ({self.cam_id}): {detected_classes} detectados! Iniciando gravação...")
                                        self.start_recording_logic()
                                        self.last_motion_time = current_time  # Atualiza para não parar imediatamente
                        
                        # Registra evento de detecção de objetos
                        if EVENT_LOGGING_AVAILABLE:
                            detected_classes = [obj['class'] for obj in detected_objects]
                            log_event(EventType.OBJECT_DETECTED, EventSeverity.INFO,
                                     camera_id=self.cam_id,
                                     message=f"{len(detected_objects)} objeto(s) detectado(s): {', '.join(detected_classes)}",
                                     details={'objects': detected_classes, 'count': len(detected_objects)})
                    
                except Exception as e:
                    # Se der erro na detecção, apenas registra e continua
                    print(f"ERRO na detecção de objetos ({self.cam_id}): {e}")
                    # Registra erro no log
                    if EVENT_LOGGING_AVAILABLE:
                        log_event(EventType.SYSTEM_ERROR, EventSeverity.ERROR,
                                 camera_id=self.cam_id,
                                 message=f"Erro na detecção de objetos: {str(e)}")
    
            # ================================================================
            # GRAVAÇÃO DE VÍDEO (Manual ou Automática)
            # ================================================================
            with self.state_lock:
                # Se está gravando, salva o frame no arquivo
                if self.is_recording and self.video_writer is not None:
                    try:
                        # Salva o frame ORIGINAL (sem retângulos) no arquivo
                        # Isso garante que o vídeo gravado seja limpo
                        self.video_writer.write(frame_original)
                    except cv2.error:
                        # Se der erro (arquivo foi fechado), ignora
                        pass
            
            # ================================================================
            # ARMAZENAMENTO DO FRAME PARA STREAM AO VIVO
            # ================================================================
            with self.frame_lock:
                # Salva o frame PROCESSADO (com retângulos, se houver) para o stream
                # Este é o frame que aparece na interface web
                self.output_frame = frame_processado
    
    def get_detection_stats(self):
        """
        Retorna as estatísticas de detecção de objetos.
        
        Retorna: Dicionário com estatísticas
        """
        with self.detection_stats_lock:
            return {
                'total_detections': self.total_detections,
                'detection_counts': self.detection_counts.copy(),
                'last_detection_timestamp': self.last_detection_timestamp,
                'last_detections': self.last_detections[-5:].copy() if self.last_detections else [],  # Últimas 5 detecções
                'is_enabled': self.object_detection_enabled,
                'has_detector': self.object_detector is not None
            }

    def release(self):
        """
        Função para limpar recursos quando o servidor for fechado.
        Fecha a câmera e para qualquer gravação em andamento.
        """
        # Para a gravação se estiver gravando
        with self.state_lock:
            if self.is_recording:
                self.stop_recording_logic()
        
        # Fecha a câmera (VLC ou OpenCV)
        if self.use_vlc and self.vlc_player:
            try:
                self.vlc_player.stop()
                self.vlc_player.release()
            except:
                pass
            if hasattr(self, '_opencv_fallback') and self._opencv_fallback is not None:
                self._opencv_fallback.release()
        elif self.cap is not None:
            self.cap.release()

