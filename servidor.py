"""
================================================================================
PROJETO VMS (Video Management Software) - TRABALHO DE FACULDADE
================================================================================

Este é o arquivo principal do servidor (Backend) do projeto.

Funcionalidades implementadas (Opção 1 + 2 + 3):
1.  Streaming de vídeo.
2.  Gravação manual e por detecção em .webm.
3.  Player para gravações.
4.  NOVO: Suporte a múltiplas câmeras, cada uma com seu próprio
    estado (gravação, detecção) rodando em uma thread separada.
"""

# --- 1. IMPORTAÇÕES DE BIBLIOTECAS ---
import cv2
from flask import Flask, Response, render_template, jsonify, send_from_directory
import time
import os
import threading

# --- 2. CONFIGURAÇÕES PRINCIPAIS ---

# --- NOVO: DEFINA SUAS CÂMERAS AQUI ---
# Crie um dicionário com um 'id' (nome) único para cada câmera.
# O 'id' será usado na URL (ex: /video_feed/webcam).
# A 'fonte' pode ser um número (para webcams) ou um endereço RTSP.
CAMERA_SOURCES = {
    "webcam": 0,
    # Exemplo de câmera IP (descomente e mude se tiver uma):
    # "corredor": "rtsp://admin:senha123@192.168.1.100:554/stream1"
}

PASTA_GRAVACOES = "gravacoes"
MOTION_COOLDOWN = 5.0
MIN_CONTOUR_AREA = 500

# --- NOVO: Dicionário Global para armazenar os 'workers' das câmeras
g_cameras = {}

# --- 3. A CLASSE 'CameraWorker' ---
# ------------------------------------------------------------------------------
# Esta classe é o novo "cérebro". Cada câmera terá sua própria
# instância desta classe, rodando em sua própria thread.
# ------------------------------------------------------------------------------

class CameraWorker(threading.Thread):
    def __init__(self, cam_id, source):
        """ Inicializador da classe. Roda quando criamos um novo 'CameraWorker'. """
        super().__init__()
        self.cam_id = cam_id      # ID (ex: "webcam")
        self.source = source      # Fonte (ex: 0 ou "rtsp://...")
        self.daemon = True        # Faz a thread parar quando o programa principal parar
        
        print(f"Iniciando Câmera Worker para: {self.cam_id}")
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            print(f"ERRO: Não foi possível abrir a câmera {self.cam_id}")

        # --- Locks (Cadeados) ---
        # Lock para o frame de saída (para o stream)
        self.frame_lock = threading.Lock()
        # Lock para TODAS as outras variáveis de estado (gravação, detecção)
        self.state_lock = threading.Lock()

        # --- Estado da Câmera (agora é interno da classe) ---
        self.output_frame = None           # O último frame processado (com retângulos)
        self.is_recording = False
        self.video_writer = None
        self.motion_detection_enabled = False
        self.static_background = None
        self.last_motion_time = 0

    def get_latest_frame(self):
        """ Pega o último frame processado de forma segura. """
        with self.frame_lock:
            if self.output_frame is None:
                return None
            return self.output_frame.copy() # Retorna uma CÓPIA

    # --- Lógica de Gravação (agora são 'métodos' da classe) ---
    # (Estas funções DEVEM ser chamadas de dentro de um 'with self.state_lock:')
    
    def start_recording_logic(self):
        """ Função interna que INICIA a gravação. """
        if self.is_recording:
            return

        print(f"LOG ({self.cam_id}): Iniciando gravação...")
        self.is_recording = True
        
        # Pega dimensões do frame (usa get_latest_frame para segurança)
        frame = self.get_latest_frame()
        if frame is None: # Se a câmera ainda não enviou um frame
             # Tenta pegar direto da captura (pode bloquear, mas é raro)
             ret, frame = self.cap.read()
             if not ret:
                 print(f"ERRO ({self.cam_id}): Não conseguiu ler frame para iniciar gravação.")
                 self.is_recording = False
                 return
        
        altura, largura, _ = frame.shape
        fps = 20.0
        fourcc = cv2.VideoWriter_fourcc(*'VP80')
        
        timestr = time.strftime("%Y%m%d-%H%M%S")
        # NOVO: Nome do arquivo agora inclui o ID da câmera
        nome_arquivo = f"{PASTA_GRAVACOES}/{self.cam_id}-gravacao-{timestr}.webm"
        
        self.video_writer = cv2.VideoWriter(nome_arquivo, fourcc, fps, (largura, altura))
        print(f"Salvando vídeo ({self.cam_id}) em: {nome_arquivo}")

    def stop_recording_logic(self):
        """ Função interna que PARA a gravação. """
        if not self.is_recording:
            return

        print(f"LOG ({self.cam_id}): Parando gravação...")
        self.is_recording = False
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None
            print(f"Arquivo de vídeo ({self.cam_id}) salvo e fechado.")
            
    # --- O Loop Principal da Thread ---
    
    def run(self):
        """
        Esta função é o loop principal da thread.
        Ela roda para sempre, lendo, processando e gravando frames.
        """
        while True:
            if not self.cap.isOpened():
                print(f"({self.cam_id}): Câmera não está aberta. Tentando reconectar em 5s...")
                time.sleep(5)
                self.cap = cv2.VideoCapture(self.source)
                continue

            ret, frame_original = self.cap.read()
            if not ret:
                print(f"({self.cam_id}): Falha ao ler frame. Fim do stream?")
                time.sleep(1) # Espera um segundo antes de tentar de novo
                continue
            
            # Copia o frame para processamento. 'frame_processado'
            # receberá os retângulos de detecção.
            frame_processado = frame_original.copy()
            
            motion_detected_this_frame = False

            # Pega o estado atual da detecção (protegido pelo lock)
            with self.state_lock:
                motion_is_on = self.motion_detection_enabled

            # --- Lógica de Detecção de Movimento (igual a antes, mas usa 'self.') ---
            if motion_is_on:
                gray_frame = cv2.cvtColor(frame_original, cv2.COLOR_BGR2GRAY)
                gray_frame = cv2.GaussianBlur(gray_frame, (21, 21), 0)

                with self.state_lock: # Protege 'self.static_background'
                    if self.static_background is None:
                        self.static_background = gray_frame
                        print(f"DETECÇÃO ({self.cam_id}): Fundo estático definido.")
                        continue
                    
                    # Copia o fundo para não ficar travado no 'lock'
                    bg = self.static_background.copy()

                diff_frame = cv2.absdiff(bg, gray_frame)
                thresh_frame = cv2.threshold(diff_frame, 30, 255, cv2.THRESH_BINARY)[1]
                contours, _ = cv2.findContours(thresh_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                for contour in contours:
                    if cv2.contourArea(contour) < MIN_CONTOUR_AREA:
                        continue
                    
                    motion_detected_this_frame = True
                    (x, y, w, h) = cv2.boundingRect(contour)
                    # Desenha o retângulo no 'frame_processado'
                    cv2.rectangle(frame_processado, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # --- Lógica de Cooldown/Gravação (protegida pelo lock) ---
                with self.state_lock:
                    if motion_detected_this_frame:
                        self.last_motion_time = time.time()
                        if not self.is_recording:
                            print(f"DETECÇÃO ({self.cam_id}): Movimento detectado!")
                            self.start_recording_logic()
                    else:
                        if self.is_recording and (time.time() - self.last_motion_time > MOTION_COOLDOWN):
                            print(f"DETECÇÃO ({self.cam_id}): Sem movimento por {MOTION_COOLDOWN}s.")
                            self.stop_recording_logic()

            # --- Lógica de Gravação (Manual ou por Detecção) ---
            with self.state_lock:
                if self.is_recording and self.video_writer is not None:
                    try:
                        # Salva o frame ORIGINAL (sem retângulos)
                        self.video_writer.write(frame_original) 
                    except cv2.error:
                        pass # Ignora erros se o writer foi fechado
            
            # --- Armazena o Frame Processado (para o Stream) ---
            with self.frame_lock:
                # Salva o frame COM retângulos para ser visto no stream
                self.output_frame = frame_processado

    def release(self):
        """ Função para limpar tudo quando o servidor fechar. """
        self.cap.release()
        with self.state_lock:
            if self.is_recording:
                self.stop_recording_logic()

# --- 4. FUNÇÃO GERADORA (PARA O STREAM FLASK) ---
# ------------------------------------------------------------------------------

def gerar_frames(cam_id):
    """
    Esta função agora é um gerador simples. Ela não faz processamento.
    Ela apenas pega o frame mais recente do 'CameraWorker' correto.
    """
    
    # Verifica se a câmera pedida existe
    if cam_id not in g_cameras:
        print(f"ERRO: Tentativa de acessar stream de câmera inexistente: {cam_id}")
        return

    worker = g_cameras[cam_id]
    
    while True:
        frame = worker.get_latest_frame()
        
        if frame is None:
            # Espera a câmera inicializar
            time.sleep(0.1)
            continue
            
        # Codifica o frame (que já tem os retângulos, se houver) para JPEG
        (flag, buffer_codificado) = cv2.imencode(".jpg", frame)
        if not flag:
            continue

        frame_em_bytes = buffer_codificado.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_em_bytes + b'\r\n')


# --- 5. ROTAS DA API (AGORA PARAMETRIZADAS) ---
# ------------------------------------------------------------------------------

app = Flask(__name__) # O Flask app (precisa estar antes das rotas)

@app.route('/')
def index():
    return render_template('index.html') 

# NOVO: Rota para o frontend saber quais câmeras existem
@app.route('/get_cameras')
def get_cameras():
    # Retorna a lista de IDs (ex: ["webcam", "corredor"])
    return jsonify(cameras=list(CAMERA_SOURCES.keys()))

# NOVO: Rota de stream agora aceita um 'cam_id'
@app.route('/video_feed/<cam_id>')
def video_feed(cam_id):
    return Response(gerar_frames(cam_id), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# --- Rotas de Controle (agora com <cam_id>) ---

@app.route('/start_recording/<cam_id>', methods=['POST'])
def start_recording(cam_id):
    if cam_id not in g_cameras:
        return jsonify(status="Erro: Câmera não encontrada"), 404
        
    worker = g_cameras[cam_id]
    with worker.state_lock: # Usa o lock daquele worker específico
        worker.start_recording_logic()
    return jsonify(status=f"Gravando ({cam_id})...")

@app.route('/stop_recording/<cam_id>', methods=['POST'])
def stop_recording(cam_id):
    if cam_id not in g_cameras:
        return jsonify(status="Erro: Câmera não encontrada"), 404
        
    worker = g_cameras[cam_id]
    with worker.state_lock:
        worker.stop_recording_logic()
    return jsonify(status=f"Ocioso ({cam_id})")

@app.route('/toggle_motion_detection/<cam_id>', methods=['POST'])
def toggle_motion_detection(cam_id):
    if cam_id not in g_cameras:
        return jsonify(status="Erro: Câmera não encontrada"), 404
    
    worker = g_cameras[cam_id]
    status_msg = ""
    is_enabled = False
    
    with worker.state_lock:
        worker.motion_detection_enabled = not worker.motion_detection_enabled
        is_enabled = worker.motion_detection_enabled
        
        if is_enabled:
            worker.static_background = None # Reseta o fundo
            status_msg = f"Detecção Ativada ({cam_id})"
        else:
            status_msg = f"Detecção Desativada ({cam_id})"
            # Se desligar, paramos qualquer gravação automática
            if worker.is_recording:
                worker.stop_recording_logic()
                
    return jsonify(status=status_msg, enabled=is_enabled)

@app.route('/get_status/<cam_id>')
def get_status(cam_id):
    if cam_id not in g_cameras:
        return jsonify(status="Erro: Câmera não encontrada"), 404
        
    worker = g_cameras[cam_id]
    
    with worker.state_lock: # Acessa o estado de forma segura
        status_text = "Ocioso"
        if worker.is_recording:
            status_text = "Gravando..."
        elif worker.motion_detection_enabled:
            status_text = "Detecção Ativada"
            
        return jsonify(
            cam_id=cam_id,
            motion_enabled=worker.motion_detection_enabled,
            is_recording=worker.is_recording, # NOVO: Informa se está gravando
            status=status_text
        )

# --- Rotas do Player (Globais - Não mudam) ---

@app.route('/list_videos')
def list_videos():
    videos = []
    # O lock global aqui não é mais necessário,
    # pois a pasta é lida de forma segura pelo 'os'.
    if os.path.exists(PASTA_GRAVACOES):
        videos = sorted(
            [f for f in os.listdir(PASTA_GRAVACOES) if f.endswith(".webm")],
            reverse=True
        )
    return jsonify(videos=videos)

@app.route('/playback/<filename>')
def playback(filename):
    return send_from_directory(PASTA_GRAVACOES, filename)


# --- 6. PONTO DE ENTRADA (EXECUÇÃO DO SERVIDOR) ---
# ------------------------------------------------------------------------------

def main():
    if not os.path.exists(PASTA_GRAVACOES):
        os.makedirs(PASTA_GRAVACOES)
        print(f"Pasta '{PASTA_GRAVACOES}' criada.")
    
    # --- NOVO: Inicialização dos Workers das Câmeras ---
    print("Iniciando workers das câmeras...")
    for cam_id, source in CAMERA_SOURCES.items():
        worker = CameraWorker(cam_id, source)
        worker.start() # Inicia a thread (o loop 'run()' da classe)
        g_cameras[cam_id] = worker # Armazena o worker no dicionário global
    
    print("Todos os workers iniciados.")
    print(f"Iniciando servidor Flask em http://127.0.0.1:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nServidor interrompido pelo usuário (Ctrl+C).")
    finally:
        # Limpeza final: libera todas as câmeras
        print("Encerrando... liberando câmeras.")
        for cam_id in g_cameras:
            g_cameras[cam_id].release()