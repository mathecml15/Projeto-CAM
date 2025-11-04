"""
================================================================================
PROJETO VMS (Video Management Software) - TRABALHO DE FACULDADE
================================================================================

Este é o arquivo principal do servidor (Backend) do projeto.

Funcionalidades implementadas (Opção 1 + Opção 2):
1.  Streaming de vídeo ao vivo.
2.  Gravação manual (Iniciar/Parar) em .webm.
3.  Player para listar e assistir às gravações.
4.  Uso de Threading (Locks) para evitar conflitos.
5.  NOVO: Detecção de movimento com gravação automática e
    feedback visual (retângulo verde).
"""

# --- 1. IMPORTAÇÕES DE BIBLIOTECAS ---
# ------------------------------------------------------------------------------
import cv2
from flask import Flask, Response, render_template, jsonify, send_from_directory
import time
import os
import threading

# --- 2. CONFIGURAÇÕES E VARIÁVEIS GLOBAIS ---
# ------------------------------------------------------------------------------

# --- Constantes de Configuração ---
FONTE_DE_VIDEO = 0 
PASTA_GRAVACOES = "gravacoes"

# --- NOVO: Constantes de Detecção de Movimento ---
MOTION_COOLDOWN = 5.0  
# Tempo em segundos (5.0) sem movimento para parar a gravação automática.

MIN_CONTOUR_AREA = 500 
# A área mínima (em pixels) para que um contorno seja
# considerado "movimento" real (ignora ruídos pequenos).

# --- Inicialização dos Objetos Principais ---
app = Flask(__name__)
cap = cv2.VideoCapture(FONTE_DE_VIDEO)
lock = threading.Lock()

# --- Variáveis Globais de Estado ---
is_recording = False
video_writer = None

# --- NOVO: Variáveis de Estado para Detecção ---
motion_detection_enabled = False 
# O "interruptor" mestre (controlado pelo botão no HTML). Começa desligado.

static_background = None 
# Armazena o "frame de fundo" (sem movimento) para comparação.

last_motion_time = 0
# Registra a hora (timestamp) do último movimento detectado.


# --- 3. LÓGICA DE GRAVAÇÃO (REATORADA) ---
# ------------------------------------------------------------------------------
# Separamos a lógica de "iniciar" e "parar" em funções próprias.
# Isso nos permite chamá-las tanto pelas rotas do Flask (manual)
# quanto pela detecção de movimento (automático).
#
# IMPORTANTE: Estas funções SÓ DEVEM SER CHAMADAS de dentro
# de um bloco 'with lock:' para garantir a segurança das threads.
# ------------------------------------------------------------------------------

def start_recording_logic():
    """
    Função interna que INICIA a gravação.
    (Assume que já está dentro de um 'with lock:')
    """
    global is_recording, video_writer
    
    if is_recording:
        print("LOG: (Lógica) Já estava gravando, não iniciar novamente.")
        return # Já está gravando, não faz nada

    print("LOG: (Lógica) Iniciando gravação...")
    is_recording = True

    # Pega as dimensões do vídeo
    largura = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    altura = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = 20.0

    # Define o CODEC para .webm
    fourcc = cv2.VideoWriter_fourcc(*'VP80')
    
    # Cria nome de arquivo único
    timestr = time.strftime("%Y%m%d-%H%M%S")
    nome_arquivo = f"{PASTA_GRAVACOES}/gravacao-{timestr}.webm"
    
    # Cria o objeto 'VideoWriter'
    video_writer = cv2.VideoWriter(nome_arquivo, fourcc, fps, (largura, altura))
    print(f"Salvando vídeo em: {nome_arquivo}")

def stop_recording_logic():
    """
    Função interna que PARA a gravação.
    (Assume que já está dentro de um 'with lock:')
    """
    global is_recording, video_writer
    
    if not is_recording:
        print("LOG: (Lógica) Não estava gravando, não parar novamente.")
        return # Não estava gravando, não faz nada

    print("LOG: (Lógica) Parando gravação...")
    is_recording = False
    
    if video_writer is not None:
        video_writer.release() # Finaliza e salva o arquivo
        video_writer = None
        print("Arquivo de vídeo .webm salvo e fechado.")


# --- 4. FUNÇÃO PRINCIPAL DE STREAMING (COM DETECÇÃO) ---
# ------------------------------------------------------------------------------

def gerar_frames():
    """
    Esta é a função "geradora" principal.
    - Captura frames
    - (NOVO) Realiza a detecção de movimento
    - (NOVO) Desenha retângulos no frame
    - Controla a gravação automática
    - Envia o frame (como JPEG) para o navegador
    """
    
    # Declaramos as variáveis globais que vamos MODIFICAR
    global static_background, is_recording, last_motion_time, motion_detection_enabled
    
    print("Iniciando stream de vídeo...")
    
    while True:
        sucesso, frame = cap.read()
        if not sucesso:
            print("Erro ao ler frame.")
            break
        
        # Esta flag controla se achamos movimento NESTA iteração específica
        motion_detected_this_frame = False
        
        # --- INÍCIO DA LÓGICA DE DETECÇÃO DE MOVIMENTO ---
        
        # Só executa a lógica se o "interruptor" (botão) estiver ligado
        if motion_detection_enabled:
            
            # 1. Preparar o frame para análise
            # Converte para escala de cinza (mais simples de processar)
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Aplica um "borrão" (blur) para remover ruído (ex: grãos da imagem)
            gray_frame = cv2.GaussianBlur(gray_frame, (21, 21), 0)

            # 2. Definir o frame de fundo (o "cenário vazio")
            # Se ainda não temos um fundo, usamos este primeiro frame
            if static_background is None:
                static_background = gray_frame
                print("DETECÇÃO: Fundo estático definido.")
                continue # Pula o resto do loop e pega o próximo frame

            # 3. Calcular a Diferença Absoluta
            # Compara o 'fundo' com o 'frame atual em cinza'
            diff_frame = cv2.absdiff(static_background, gray_frame)

            # 4. Limiar (Threshold)
            # Converte a imagem de diferença em uma imagem binária (preto/branco)
            # Pixels com diferença MAIOR que 30 viram brancos (255), o resto vira preto (0)
            thresh_frame = cv2.threshold(diff_frame, 30, 255, cv2.THRESH_BINARY)[1]
            
            # 5. Encontrar Contornos (as "manchas brancas")
            # Procura por todas as áreas brancas contínuas na imagem de limiar
            contours, _ = cv2.findContours(thresh_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                # Se o contorno (área branca) for muito pequeno, é só ruído. Ignorar.
                if cv2.contourArea(contour) < MIN_CONTOUR_AREA:
                    continue
                
                # Se achamos um contorno grande o suficiente, HÁ MOVIMENTO!
                motion_detected_this_frame = True
                
                # BÔNUS: Desenhar um retângulo no frame ORIGINAL (colorido)
                (x, y, w, h) = cv2.boundingRect(contour) # Pega as coordenadas do contorno
                # Desenha um retângulo verde (0, 255, 0) com 2 pixels de espessura
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2) 

            # 6. Lógica de Cooldown e Gravação (Protegida pelo lock)
            with lock:
                if motion_detected_this_frame:
                    # Se há movimento, atualiza a "última vez que vimos movimento"
                    last_motion_time = time.time()
                    
                    # Se não estávamos gravando, iniciamos a gravação
                    if not is_recording:
                        print(f"DETECÇÃO: Movimento detectado! ({time.strftime('%H:%M:%S')})")
                        start_recording_logic() # Chama a lógica interna
                else:
                    # Se NÃO há movimento neste frame...
                    if is_recording:
                        # ...e já se passaram 5s (COOLDOWN) desde o último movimento
                        if (time.time() - last_motion_time > MOTION_COOLDOWN):
                            print(f"DETECÇÃO: Sem movimento por {MOTION_COOLDOWN}s. Parando gravação.")
                            stop_recording_logic() # Chama a lógica interna
        
        # --- FIM DA LÓGICA DE DETECÇÃO DE MOVIMENTO ---
            
        # 7. Lógica de Gravação Manual (protegida pelo lock)
        # Esta parte é para a gravação manual, que escreve o frame
        # independentemente da detecção de movimento.
        with lock:
             if is_recording and video_writer is not None:
                try:
                    video_writer.write(frame)
                except cv2.error as e:
                    print(f"Erro ao escrever frame (provavelmente foi fechado): {e}")

        # 8. Preparar o frame para o Navegador
        # Codifica o frame (agora COM os retângulos verdes, se houver) para JPEG
        (flag, buffer_codificado) = cv2.imencode(".jpg", frame)
        if not flag:
            continue
        frame_em_bytes = buffer_codificado.tobytes()

        # 9. Enviar o frame para o Navegador
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_em_bytes + b'\r\n')


# --- 5. ROTAS DA API (OS "ENDEREÇOS" DO NOSSO SERVIDOR) ---
# ------------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html') 

@app.route('/video_feed')
def video_feed():
    return Response(gerar_frames(), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# --- Rotas de Controle Manual (Agora usam a lógica refatorada) ---

@app.route('/start_recording', methods=['POST'])
def start_recording():
    """ Rota para o botão 'Iniciar Gravação Manual'. """
    with lock:
        start_recording_logic() # Chama a função interna
    return jsonify(status="Gravando (Manual)...")

@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    """ Rota para o botão 'Parar Gravação Manual'. """
    with lock:
        stop_recording_logic() # Chama a função interna
    return jsonify(status="Ocioso (Manual)")

# --- NOVO: Rotas de Controle de Detecção ---

@app.route('/toggle_motion_detection', methods=['POST'])
def toggle_motion_detection():
    """
    Rota para o botão 'Ligar/Desligar Detecção'.
    Ativa ou desativa o "interruptor" mestre.
    """
    global motion_detection_enabled, static_background
    
    with lock:
        # Inverte o valor da variável (True vira False, False vira True)
        motion_detection_enabled = not motion_detection_enabled
        
        if motion_detection_enabled:
            # Se LIGOU, reseta o fundo. O próximo frame será o novo fundo.
            static_background = None 
            print("DETECÇÃO: Ativada. Aguardando fundo estático...")
            status = "Detecção Ativada"
        else:
            # Se DESLIGOU, paramos qualquer gravação que estava em curso
            print("DETECÇÃO: Desativada.")
            status = "Detecção Desativada"
            if is_recording:
                stop_recording_logic() # Para a gravação
                
    return jsonify(status=status, enabled=motion_detection_enabled)

@app.route('/get_status')
def get_status():
    """
    Rota para o JavaScript saber o estado do servidor quando a página carrega.
    """
    with lock:
        status_text = "Ocioso"
        if is_recording:
            status_text = "Gravando..."
        elif motion_detection_enabled:
            status_text = "Detecção Ativada"
            
        return jsonify(
            motion_enabled=motion_detection_enabled, # O botão sabe se está "ligado"
            status=status_text # A mensagem de status
        )

# --- Rotas do Player de Gravações (Não mudam) ---

@app.route('/list_videos')
def list_videos():
    videos = []
    with lock:
        if os.path.exists(PASTA_GRAVACOES):
            videos = sorted(
                [f for f in os.listdir(PASTA_GRAVACOES) if f.endswith(".webm")],
                reverse=True
            )
    return jsonify(videos=videos)

@app.route('/playback/<filename>')
def playback(filename):
    with lock:
        return send_from_directory(PASTA_GRAVACOES, filename)


# --- 6. PONTO DE ENTRADA (EXECUÇÃO DO SERVIDOR) ---
# ------------------------------------------------------------------------------

def main():
    if not os.path.exists(PASTA_GRAVACOES):
        os.makedirs(PASTA_GRAVACOES)
        print(f"Pasta '{PASTA_GRAVACOES}' criada.")
        
    print(f"Iniciando servidor Flask em http://127.0.0.1:5000")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False, # Muito importante ser False
        threaded=True  # Essencial para rodar tudo em paralelo
    )

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nServidor interrompido pelo usuário (Ctrl+C).")
    finally:
        # Limpeza final
        if cap.isOpened():
            cap.release()
            print("Câmera liberada.")
        with lock:
            if video_writer is not None:
                video_writer.release()
                print("Gravação finalizada (limpeza).")