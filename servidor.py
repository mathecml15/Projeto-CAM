"""
================================================================================
PROJETO VMS (Video Management Software) - Gerenciador de Câmeras
================================================================================

O QUE ESTE CÓDIGO FAZ:
- Gerencia múltiplas câmeras ao mesmo tempo
- Transmite vídeo ao vivo de cada câmera na interface web
- Permite gravar vídeo manualmente (botão "Gravar Manual")
- Detecta movimento e grava automaticamente quando detecta
- Salva os vídeos na pasta "gravacoes" no formato .webm
- Permite assistir as gravações através do player na interface

COMO FUNCIONA:
1. Cada câmera roda em uma "thread" separada (processo paralelo)
2. A thread lê frames da câmera continuamente
3. Se a detecção de movimento estiver ligada, ela analisa cada frame
4. Se detectar movimento, inicia gravação automaticamente
5. O Flask (servidor web) serve a interface e recebe comandos
6. A interface HTML mostra os vídeos ao vivo e os controles
"""

# ============================================================================
# PARTE 1: IMPORTAÇÕES (Bibliotecas que vamos usar)
# ============================================================================

import cv2  # OpenCV - para trabalhar com vídeo e câmeras
from flask import Flask, Response, render_template, jsonify, send_from_directory
# Flask - cria o servidor web
# Response - para enviar vídeo em tempo real
# render_template - para mostrar a página HTML
# jsonify - para enviar dados em formato JSON
# send_from_directory - para enviar arquivos de vídeo

import time  # Para medir tempo (cooldown da detecção de movimento)
import os  # Para criar pastas e listar arquivos
import threading  # Para rodar cada câmera em paralelo (threads)

# ============================================================================
# PARTE 2: CONFIGURAÇÕES (Aqui você define suas câmeras e ajustes)
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

# Nome da pasta onde os vídeos serão salvos
PASTA_GRAVACOES = "gravacoes"

# Tempo de espera após detectar movimento antes de parar a gravação (em segundos)
# Se não detectar movimento por 5 segundos, para de gravar
MOTION_COOLDOWN = 5.0

# Área mínima de movimento para considerar detecção (em pixels)
# Valores menores = mais sensível, valores maiores = menos sensível
MIN_CONTOUR_AREA = 500

# Dicionário global para armazenar todas as câmeras ativas
# A chave é o ID da câmera (ex: "webcam") e o valor é o objeto CameraWorker
g_cameras = {}

# ============================================================================
# PARTE 3: CLASSE CameraWorker (O "trabalhador" de cada câmera)
# ============================================================================

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
        source: Fonte da câmera (ex: 0 para webcam USB, ou endereço RTSP)
        """
        # Chama o inicializador da classe Thread (permite rodar em paralelo)
        super().__init__()
        
        # Armazena o ID e a fonte da câmera
        self.cam_id = cam_id  # Exemplo: "webcam"
        self.source = source  # Exemplo: 0 (webcam USB)
        
        # Daemon = True significa que a thread para quando o programa principal parar
        self.daemon = True
        
        print(f"Iniciando câmera: {self.cam_id}")
        
        # Abre a câmera usando OpenCV
        self.cap = cv2.VideoCapture(source)
        
        # Verifica se a câmera foi aberta com sucesso
        if not self.cap.isOpened():
            print(f"ERRO: Não foi possível abrir a câmera {self.cam_id}")
        
        # LOCKS (Cadeados) - Previnem conflitos quando múltiplas threads acessam os mesmos dados
        # frame_lock: protege o frame que é transmitido ao vivo
        self.frame_lock = threading.Lock()
        # state_lock: protege todas as variáveis de estado (gravação, detecção, etc)
        self.state_lock = threading.Lock()
        
        # VARIÁVEIS DE ESTADO DA CÂMERAL
        
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
            ret, frame = self.cap.read()
            if not ret:
                print(f"ERRO ({self.cam_id}): Não conseguiu ler frame para iniciar gravação.")
                self.is_recording = False
                return
        
        # Pega as dimensões do frame (altura, largura)
        # frame.shape retorna (altura, largura, canais_de_cor)
        altura, largura, _ = frame.shape
        
        # FPS (frames por segundo) da gravação
        fps = 20.0
        
        # Codec de vídeo (VP80 = formato WebM)
        fourcc = cv2.VideoWriter_fourcc(*'VP80')
        
        # Cria um nome único para o arquivo usando data e hora
        timestr = time.strftime("%Y%m%d-%H%M%S")  # Exemplo: 20241225-143022
        # Nome do arquivo inclui o ID da câmera para identificar qual câmera gravou
        nome_arquivo = f"{PASTA_GRAVACOES}/{self.cam_id}-gravacao-{timestr}.webm"
        
        # Cria o objeto que escreve o vídeo no arquivo
        self.video_writer = cv2.VideoWriter(nome_arquivo, fourcc, fps, (largura, altura))
        
        print(f"Salvando vídeo ({self.cam_id}) em: {nome_arquivo}")

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
            # Verifica se a câmera ainda está aberta
            if not self.cap.isOpened():
                print(f"({self.cam_id}): Câmera não está aberta. Tentando reconectar em 5s...")
                time.sleep(5)  # Espera 5 segundos
                # Tenta abrir a câmera novamente
                self.cap = cv2.VideoCapture(self.source)
                continue  # Volta para o início do loop
            
            # Lê um frame da câmera
            # ret = True se conseguiu ler, False se falhou
            # frame_original = a imagem capturada
            ret, frame_original = self.cap.read()
            
            # Se não conseguiu ler o frame, espera e tenta novamente
            if not ret:
                print(f"({self.cam_id}): Falha ao ler frame. Fim do stream?")
                time.sleep(1)  # Espera 1 segundo
                continue  # Volta para o início do loop
            
            # Cria uma cópia do frame para processar (adicionar retângulos de detecção)
            # frame_processado será o que aparece no stream (com retângulos verdes)
            frame_processado = frame_original.copy()
            
            # Flag para indicar se movimento foi detectado neste frame
            motion_detected_this_frame = False
            
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
                            self.start_recording_logic()
                    else:
                        # Não há movimento neste frame
                        # Se está gravando E já passou o tempo de cooldown, para a gravação
                        tempo_sem_movimento = time.time() - self.last_motion_time
                        if self.is_recording and tempo_sem_movimento > MOTION_COOLDOWN:
                            print(f"DETECÇÃO ({self.cam_id}): Sem movimento por {MOTION_COOLDOWN}s. Parando gravação...")
                            self.stop_recording_logic()
            
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

    def release(self):
        """
        Função para limpar recursos quando o servidor for fechado.
        Fecha a câmera e para qualquer gravação em andamento.
        """
        # Fecha a câmera
        self.cap.release()
        
        # Para a gravação se estiver gravando
        with self.state_lock:
            if self.is_recording:
                self.stop_recording_logic()

# ============================================================================
# PARTE 4: FUNÇÃO PARA GERAR STREAM DE VÍDEO (Para o Flask)
# ============================================================================

def gerar_frames(cam_id):
    """
    Esta função gera o stream de vídeo em tempo real para uma câmera específica.
    Ela é chamada pelo Flask e retorna frames continuamente.
    
    cam_id: ID da câmera (ex: "webcam")
    
    Retorna: Generator que produz frames codificados em JPEG
    """
    # Verifica se a câmera existe
    if cam_id not in g_cameras:
        print(f"ERRO: Tentativa de acessar stream de câmera inexistente: {cam_id}")
        return
    
    # Pega o worker (objeto CameraWorker) da câmera solicitada
    worker = g_cameras[cam_id]
    
    # Loop infinito - gera frames continuamente
    while True:
        # Pega o último frame processado da câmera
        frame = worker.get_latest_frame()
        
        # Se não houver frame ainda (câmera acabou de iniciar), espera um pouco
        if frame is None:
            time.sleep(0.1)  # Espera 100 milissegundos
            continue
        
        # Codifica o frame em formato JPEG
        # Isso comprime a imagem para enviar pela internet
        (flag, buffer_codificado) = cv2.imencode(".jpg", frame)
        
        # Se falhou a codificação, pula este frame
        if not flag:
            continue
        
        # Converte o buffer codificado em bytes
        frame_em_bytes = buffer_codificado.tobytes()
        
        # Retorna o frame no formato MJPEG (Motion JPEG)
        # Este é o formato usado para streaming de vídeo no navegador
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_em_bytes + b'\r\n')

# ============================================================================
# PARTE 5: ROTAS DO FLASK (API do servidor web)
# ============================================================================

# Cria a aplicação Flask (servidor web)
app = Flask(__name__)

# Rota principal - mostra a página HTML
@app.route('/')
def index():
    """
    Rota principal do servidor.
    Retorna a página HTML (index.html) que está na pasta templates/
    """
    return render_template('index.html')

# Rota para listar todas as câmeras disponíveis
@app.route('/get_cameras')
def get_cameras():
    """
    Retorna a lista de IDs de câmeras disponíveis.
    A interface HTML usa isso para saber quais câmeras mostrar.
    
    Retorna: JSON com lista de IDs das câmeras
    Exemplo: {"cameras": ["webcam", "corredor"]}
    """
    # Pega todas as chaves do dicionário CAMERA_SOURCES (os IDs das câmeras)
    lista_cameras = list(CAMERA_SOURCES.keys())
    return jsonify(cameras=lista_cameras)

# Rota para o stream de vídeo de uma câmera específica
@app.route('/video_feed/<cam_id>')
def video_feed(cam_id):
    """
    Rota que fornece o stream de vídeo ao vivo de uma câmera.
    
    cam_id: ID da câmera (ex: "webcam")
    
    Retorna: Stream de vídeo MJPEG
    """
    # Cria uma resposta de streaming usando a função gerar_frames
    return Response(gerar_frames(cam_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Rota para iniciar gravação manual de uma câmera
@app.route('/start_recording/<cam_id>', methods=['POST'])
def start_recording(cam_id):
    """
    Inicia gravação manual de uma câmera específica.
    Chamada quando o usuário clica no botão "Gravar Manual".
    
    cam_id: ID da câmera
    
    Retorna: JSON com status da operação
    """
    # Verifica se a câmera existe
    if cam_id not in g_cameras:
        return jsonify(status="Erro: Câmera não encontrada"), 404
    
    # Pega o worker da câmera
    worker = g_cameras[cam_id]
    
    # Inicia a gravação (protegido pelo lock)
    with worker.state_lock:
        worker.start_recording_logic()
    
    return jsonify(status=f"Gravando ({cam_id})...")

# Rota para parar gravação manual de uma câmera
@app.route('/stop_recording/<cam_id>', methods=['POST'])
def stop_recording(cam_id):
    """
    Para a gravação manual de uma câmera específica.
    Chamada quando o usuário clica no botão "Parar Manual".
    
    cam_id: ID da câmera
    
    Retorna: JSON com status da operação
    """
    # Verifica se a câmera existe
    if cam_id not in g_cameras:
        return jsonify(status="Erro: Câmera não encontrada"), 404
    
    # Pega o worker da câmera
    worker = g_cameras[cam_id]
    
    # Para a gravação (protegido pelo lock)
    with worker.state_lock:
        worker.stop_recording_logic()
    
    return jsonify(status=f"Ocioso ({cam_id})")

# Rota para ligar/desligar detecção de movimento
@app.route('/toggle_motion_detection/<cam_id>', methods=['POST'])
def toggle_motion_detection(cam_id):
    """
    Liga ou desliga a detecção de movimento de uma câmera.
    Se estiver ligada, desliga. Se estiver desligada, liga.
    Chamada quando o usuário clica no botão "Ligar/Desligar Detecção".
    
    cam_id: ID da câmera
    
    Retorna: JSON com status e se está ativada ou não
    """
    # Verifica se a câmera existe
    if cam_id not in g_cameras:
        return jsonify(status="Erro: Câmera não encontrada"), 404
    
    # Pega o worker da câmera
    worker = g_cameras[cam_id]
    
    # Variáveis para resposta
    status_msg = ""
    is_enabled = False
    
    # Alterna o estado da detecção (protegido pelo lock)
    with worker.state_lock:
        # Inverte o estado (True vira False, False vira True)
        worker.motion_detection_enabled = not worker.motion_detection_enabled
        is_enabled = worker.motion_detection_enabled
        
        if is_enabled:
            # Se ativou, reseta o fundo estático (vai recalcular no próximo frame)
            worker.static_background = None
            status_msg = f"Detecção Ativada ({cam_id})"
        else:
            # Se desativou, para qualquer gravação automática em andamento
            status_msg = f"Detecção Desativada ({cam_id})"
            if worker.is_recording:
                worker.stop_recording_logic()
    
    return jsonify(status=status_msg, enabled=is_enabled)

# Rota para obter o status atual de uma câmera
@app.route('/get_status/<cam_id>')
def get_status(cam_id):
    """
    Retorna o status atual de uma câmera.
    A interface HTML usa isso para atualizar os status na tela.
    
    cam_id: ID da câmera
    
    Retorna: JSON com status, se está gravando, se detecção está ativa, etc.
    """
    # Verifica se a câmera existe
    if cam_id not in g_cameras:
        return jsonify(status="Erro: Câmera não encontrada"), 404
    
    # Pega o worker da câmera
    worker = g_cameras[cam_id]
    
    # Pega o status atual (protegido pelo lock)
    with worker.state_lock:
        # Define a mensagem de status baseada no estado atual
        status_text = "Ocioso"  # Padrão: não está fazendo nada
        if worker.is_recording:
            status_text = "Gravando..."  # Está gravando
        elif worker.motion_detection_enabled:
            status_text = "Detecção Ativada"  # Detecção ligada mas não gravando
        
        # Retorna todas as informações em formato JSON
        return jsonify(
            cam_id=cam_id,
            motion_enabled=worker.motion_detection_enabled,  # Se detecção está ativa
            is_recording=worker.is_recording,  # Se está gravando
            status=status_text  # Mensagem de status legível
        )

# ============================================================================
# PARTE 6: ROTAS DO PLAYER DE VÍDEO (Para assistir gravações)
# ============================================================================

# Rota para listar todos os vídeos gravados
@app.route('/list_videos')
def list_videos():
    """
    Retorna a lista de todos os vídeos gravados na pasta de gravações.
    A interface HTML usa isso para mostrar a lista de vídeos disponíveis.
    
    Retorna: JSON com lista de nomes de arquivos de vídeo
    """
    videos = []
    
    # Verifica se a pasta de gravações existe
    if os.path.exists(PASTA_GRAVACOES):
        # Lista todos os arquivos na pasta
        arquivos = os.listdir(PASTA_GRAVACOES)
        
        # Filtra apenas arquivos .webm (nossos vídeos)
        videos = [f for f in arquivos if f.endswith(".webm")]
        
        # Ordena por nome (mais recentes primeiro, se o nome tiver timestamp)
        videos = sorted(videos, reverse=True)
    
    return jsonify(videos=videos)

# Rota para reproduzir um vídeo específico
@app.route('/playback/<filename>')
def playback(filename):
    """
    Envia um arquivo de vídeo para o navegador reproduzir.
    Chamada quando o usuário clica em um vídeo na lista.
    
    filename: Nome do arquivo de vídeo (ex: "webcam-gravacao-20241225-143022.webm")
    
    Retorna: Arquivo de vídeo para o navegador
    """
    # Envia o arquivo da pasta de gravações
    return send_from_directory(PASTA_GRAVACOES, filename)

# ============================================================================
# PARTE 7: FUNÇÃO PRINCIPAL (Ponto de entrada do programa)
# ============================================================================

def main():
    """
    Função principal que inicia o servidor.
    Ela é executada quando o programa é rodado.
    """
    # Cria a pasta de gravações se ela não existir
    if not os.path.exists(PASTA_GRAVACOES):
        os.makedirs(PASTA_GRAVACOES)  # Cria a pasta
        print(f"Pasta '{PASTA_GRAVACOES}' criada.")
    
    # Inicializa todas as câmeras definidas em CAMERA_SOURCES
    print("Iniciando workers das câmeras...")
    
    # Para cada câmera no dicionário
    for cam_id, source in CAMERA_SOURCES.items():
        # Cria um novo CameraWorker para esta câmera
        worker = CameraWorker(cam_id, source)
        
        # Inicia a thread (faz o loop run() começar a rodar)
        worker.start()
        
        # Armazena o worker no dicionário global
        g_cameras[cam_id] = worker
    
    print("Todos os workers iniciados.")
    print(f"Iniciando servidor Flask em http://127.0.0.1:5000")
    
    # Inicia o servidor Flask
    # host='0.0.0.0' = aceita conexões de qualquer IP
    # port=5000 = porta do servidor
    # debug=False = modo produção (sem debug)
    # threaded=True = permite múltiplas requisições simultâneas
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

# ============================================================================
# PARTE 8: EXECUÇÃO DO PROGRAMA
# ============================================================================

if __name__ == '__main__':
    """
    Este bloco só executa se o arquivo for rodado diretamente
    (não se for importado como módulo).
    """
    try:
        # Chama a função principal
        main()
    except KeyboardInterrupt:
        # Se o usuário pressionar Ctrl+C, interrompe o servidor
        print("\nServidor interrompido pelo usuário (Ctrl+C).")
    finally:
        # Este bloco SEMPRE executa, mesmo se der erro
        # Limpa os recursos: fecha todas as câmeras
        print("Encerrando... liberando câmeras.")
        for cam_id in g_cameras:
            g_cameras[cam_id].release()
