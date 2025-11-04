# 1. Importar as bibliotecas necessárias
import cv2
from flask import Flask, Response, render_template, jsonify, send_from_directory # Adicione 'render_template'
import time  # Para nomes de arquivo únicos
import os    # Para criar pastas
import threading  # NOVO: Importar a biblioteca de threading

# 2. Inicializar o objeto de captura de vídeo
# (Igual ao script anterior)
FONTE_DE_VIDEO = 0 
PASTA_GRAVACOES = "gravacoes"  # Nome da pasta para salvar os vídeos

# --- Constantes de Detecção de Movimento ---
MOTION_COOLDOWN = 5.0  # Segundos sem movimento para parar de gravar
MIN_CONTOUR_AREA = 500 # Área mínima (em pixels) para ser considerado "movimento"

# Variáveis globais para controlar a gravação
is_recording = False    # Começa desligado
video_writer = None     # Objeto que vai escrever o vídeo
lock = threading.Lock() # Este cadeado vai proteger nossas variáveis 'is_recording' e 'video_writer'

# NOVO: Variáveis para Detecção de Movimento
motion_detection_enabled = False # O "interruptor" mestre
static_background = None         # O frame de fundo para comparação
last_motion_time = 0             # Hora do último movimento detectado

# Inicializar o objeto de captura de vídeo
cap = cv2.VideoCapture(FONTE_DE_VIDEO)

# 3. Inicializar o aplicativo Flask
# __name__ é uma variável especial do Python que dá um nome ao app
app = Flask(__name__)

# 4. Criar a função que vai gerar o stream de vídeo
def gerar_frames():
    # Precisamos declarar que vamos usar as variáveis globais
    global is_recording, video_writer

    print("Iniciando stream de vídeo...")
    while True:
        # 5. Ler um frame da câmera
        sucesso, frame = cap.read()
        
        if not sucesso:
            print("Erro ao ler frame ou fim do stream.")
            break # Sai do loop se a câmera falhar
        else:
            # --- LÓGICA DE GRAVAÇÃO ---
            # Se 'is_recording' for True E o video_writer estiver pronto...
            with lock:
                if is_recording and video_writer is not None:
                    try:
                        video_writer.write(frame)
                    except cv2.error as e:
                        # Escreve o frame ORIGINAL no arquivo de vídeo
                        print(f"Erro ao escrever frame (provavelmente foi fechado): {e}")
            # O cadeado é liberado automaticamente aqui

            # 6. Codificar o frame para o formato JPEG
            # O navegador não entende o frame "cru" do OpenCV,
            # mas entende perfeitamente imagens JPEG.
            (flag, buffer_codificado) = cv2.imencode(".jpg", frame)
            
            if not flag:
                print("Erro ao codificar frame para JPEG.")
                continue # Pula para a próxima iteração do loop

            # 7. Converter o buffer (dados da imagem) para bytes
            frame_em_bytes = buffer_codificado.tobytes()

            # 8. "Servir" o frame como parte de um stream MJPEG
            # Esta é a "mágica" do streaming:
            # 'yield' é como um 'return', mas não para a função.
            # Ele envia o dado (o frame) e continua executando o loop.
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_em_bytes + b'\r\n')

# 9. Definir as "Rotas" (os links) do nosso site
@app.route('/')
def index():
    # Agora, em vez de uma string simples, renderizamos o arquivo HTML.
    # O Flask procura 'index.html' automaticamente na pasta 'templates'.
    return render_template('index.html') 

@app.route('/video_feed')
def video_feed():
    return Response(gerar_frames(), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# --- NOSSAS NOVAS ROTAS DE CONTROLE ---

@app.route('/start_recording', methods=['POST'])
def start_recording():
    global is_recording, video_writer
    
    # Pede o cadeado antes de fazer qualquer coisa
    with lock:
        if is_recording:
            return jsonify(status="Já estava gravando")

    print("Comando para INICIAR gravação recebido!")
    is_recording = True

    # Pegar tamanho do frame da câmera
    largura = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    altura = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = 30.0  # Podemos chutar um valor (20-30 fps)

    # Definir o codec (formato do vídeo)
    # XVID é um codec .avi que funciona bem e é simples
    fourcc = cv2.VideoWriter_fourcc(*'VP80')
    
    # Criar nome de arquivo único com data e hora
    timestr = time.strftime("%Y%m%d-%H%M%S")
    nome_arquivo = f"{PASTA_GRAVACOES}/gravacao-{timestr}.webm"

    # Criar o objeto VideoWriter
    video_writer = cv2.VideoWriter(nome_arquivo, fourcc, fps, (largura, altura))
    
    print(f"Salvando vídeo em: {nome_arquivo}")

    # Retorna uma resposta JSON para o JavaScript
    return jsonify(status="Gravando (em .webm)...")

# NOVO: Rota modificada com o cadeado
@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    global is_recording, video_writer

    # Pede o cadeado antes de fazer qualquer coisa
    with lock:
        if not is_recording:
            return jsonify(status="Não estava gravando")

    print("Comando para PARAR gravação recebido!")
    is_recording = False
    
    if video_writer is not None:
        video_writer.release()  # IMPORTANTE: Salva e fecha o arquivo
        video_writer = None
        print("Arquivo de vídeo .webm salvo e fechado.")
        
    return jsonify(status="Ocioso (gravação salva)")

# NOVO: API para listar os vídeos
@app.route('/list_videos')
def list_videos():
    videos = []
    if os.path.exists(PASTA_GRAVACOES):
        # Filtra para pegar apenas nossos arquivos .webm
        # e ordena da mais nova para a mais antiga (reverse=True)
        videos = sorted(
            [f for f in os.listdir(PASTA_GRAVACOES) if f.endswith(".webm")],
            reverse=True
        )
    return jsonify(videos=videos) # Retorna a lista como JSON

# NOVO: API para "servir" o arquivo de vídeo
@app.route('/playback/<filename>')
def playback(filename):
    # send_from_directory é a forma segura do Flask enviar um arquivo
    # de uma pasta específica.
    print(f"Servindo vídeo: {filename}")
    return send_from_directory(PASTA_GRAVACOES, filename)

# --- Função Principal para Rodar o Servidor ---

def main():
    # Criar a pasta de gravações se ela não existir
    if not os.path.exists(PASTA_GRAVACOES):
        os.makedirs(PASTA_GRAVACOES)
        print(f"Pasta '{PASTA_GRAVACOES}' criada.")
        
    print(f"Iniciando servidor Flask em http://127.0.0.1:5000")
    # debug=False é importante para não criar dois objetos de câmera
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nServidor interrompido pelo usuário (Ctrl+C).")
    finally:
        # Limpeza final quando o servidor é derrubado
        if cap.isOpened():
            cap.release()
            print("Câmera liberada.")
        if video_writer is not None:
            video_writer.release()
            print("Gravação finalizada (limpeza).")