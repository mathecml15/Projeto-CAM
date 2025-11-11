"""
================================================================================
ROUTES - Rotas da API do servidor web
================================================================================

Este arquivo contém todas as rotas (endpoints) da API Flask.
Cada rota é uma função que responde a requisições HTTP específicas.
"""

from flask import render_template, jsonify, send_from_directory, Response

# Importa as configurações e módulos necessários
from config import CAMERA_SOURCES, PASTA_GRAVACOES, g_cameras
from video_stream import gerar_frames
import os


def registrar_rotas(app):
    """
    Esta função registra todas as rotas no app Flask.
    É chamada pelo servidor.py após criar o app.
    
    app: Objeto Flask que receberá as rotas
    """
    
    # ============================================================================
    # ROTA PRINCIPAL - Página HTML
    # ============================================================================
    
    @app.route('/')
    def index():
        """
        Rota principal do servidor.
        Retorna a página HTML (index.html) que está na pasta templates/
        """
        return render_template('index.html')
    
    # ============================================================================
    # ROTAS DE INFORMAÇÃO
    # ============================================================================
    
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
                motion_enabled=worker.motion_detection_enabled,  # Se detecção de movimento está ativa
                object_detection_enabled=getattr(worker, 'object_detection_enabled', False),  # Se detecção de objetos está ativa
                is_recording=worker.is_recording,  # Se está gravando
                status=status_text  # Mensagem de status legível
            )
    
    # ============================================================================
    # ROTAS DE STREAMING
    # ============================================================================
    
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
    
    # ============================================================================
    # ROTAS DE CONTROLE DE GRAVAÇÃO
    # ============================================================================
    
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
    
    # ============================================================================
    # ROTAS DE DETECÇÃO DE MOVIMENTO
    # ============================================================================
    
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
    
    # ============================================================================
    # ROTAS DE DETECÇÃO DE OBJETOS (IA)
    # ============================================================================
    
    @app.route('/toggle_object_detection/<cam_id>', methods=['POST'])
    def toggle_object_detection(cam_id):
        """
        Liga ou desliga a detecção de objetos de uma câmera.
        Se estiver ligada, desliga. Se estiver desligada, liga.
        Chamada quando o usuário clica no botão "Ligar/Desligar Detecção de Objetos".
        
        cam_id: ID da câmera
        
        Retorna: JSON com status e se está ativada ou não
        """
        # Verifica se a câmera existe
        if cam_id not in g_cameras:
            return jsonify(status="Erro: Câmera não encontrada"), 404
        
        # Pega o worker da câmera
        worker = g_cameras[cam_id]
        
        # Verifica se a detecção de objetos está disponível
        if not hasattr(worker, 'object_detection_enabled'):
            return jsonify(status="Erro: Detecção de objetos não disponível. Instale ultralytics."), 400
        
        # Variáveis para resposta
        status_msg = ""
        is_enabled = False
        
        # Alterna o estado da detecção de objetos (protegido pelo lock)
        with worker.state_lock:
            # Inverte o estado (True vira False, False vira True)
            worker.object_detection_enabled = not worker.object_detection_enabled
            is_enabled = worker.object_detection_enabled
            
            # Se está ativando e o detector ainda não foi inicializado
            if is_enabled and worker.object_detector is None:
                try:
                    from object_detector import ObjectDetector
                    from config import YOLO_MODEL, OBJECT_CONFIDENCE_THRESHOLD, OBJECT_CLASSES_FILTER
                    
                    worker.object_detector = ObjectDetector(
                        model_path=YOLO_MODEL,
                        conf_threshold=OBJECT_CONFIDENCE_THRESHOLD
                    )
                    if OBJECT_CLASSES_FILTER:
                        worker.object_detector.set_classes_filter(OBJECT_CLASSES_FILTER)
                    print(f"Detector de objetos inicializado para câmera {cam_id}")
                except Exception as e:
                    print(f"ERRO ao inicializar detector de objetos para {cam_id}: {e}")
                    worker.object_detection_enabled = False
                    return jsonify(status=f"Erro ao inicializar detector: {str(e)}"), 500
            
            if is_enabled:
                status_msg = f"Detecção de Objetos Ativada ({cam_id})"
            else:
                status_msg = f"Detecção de Objetos Desativada ({cam_id})"
        
        return jsonify(status=status_msg, enabled=is_enabled)
    
    @app.route('/get_object_detection_stats/<cam_id>')
    def get_object_detection_stats(cam_id):
        """
        Retorna as estatísticas de detecção de objetos de uma câmera.
        
        cam_id: ID da câmera
        
        Retorna: JSON com estatísticas de detecção
        """
        # Verifica se a câmera existe
        if cam_id not in g_cameras:
            return jsonify(error="Câmera não encontrada"), 404
        
        # Pega o worker da câmera
        worker = g_cameras[cam_id]
        
        # Verifica se a detecção de objetos está disponível
        if not hasattr(worker, 'get_detection_stats'):
            return jsonify(error="Estatísticas de detecção não disponíveis"), 400
        
        # Pega as estatísticas
        stats = worker.get_detection_stats()
        
        return jsonify(stats)
    
    # ============================================================================
    # ROTAS DO PLAYER DE VÍDEO (Para assistir gravações)
    # ============================================================================
    
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
    
    @app.route('/playback/<filename>')
    def playback(filename):
        """
        Envia um arquivo de vídeo para o navegador reproduzir.
        Chamada quando o usuário clica em um vídeo na lista.
        
        filename: Nome do arquivo de vídeo (ex: "webcam-gravacao-25-12-2024_143022.webm")
        
        Retorna: Arquivo de vídeo para o navegador
        """
        # Envia o arquivo da pasta de gravações
        return send_from_directory(PASTA_GRAVACOES, filename)

