"""
================================================================================
ROUTES - Rotas da API do servidor web
================================================================================

Este arquivo contém todas as rotas (endpoints) da API Flask.
Cada rota é uma função que responde a requisições HTTP específicas.
"""

from flask import render_template, jsonify, send_from_directory, Response, request

# Importa as configurações e módulos necessários
from app.config import PASTA_GRAVACOES, g_cameras
from app.video_stream import gerar_frames
from app.auth import login_required, get_current_user
from app.camera_manager import (
    load_cameras_config, add_camera, remove_camera, update_camera,
    list_cameras, load_system_config, save_system_config
)
from app.stats import get_all_stats, get_video_stats, get_camera_stats, get_detection_stats
from app.event_logger import (
    log_event, get_events, get_event_stats, clear_events,
    EventType, EventSeverity
)
from app.video_converter import (
    convert_video, extract_frames, get_video_info,
    SUPPORTED_FORMATS, check_ffmpeg
)
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
    @login_required  # Protege a rota - requer login
    def index():
        """
        Rota principal do servidor.
        Retorna a página HTML (index.html) que está na pasta templates/
        """
        # Pega o usuário atual para passar para o template
        user = get_current_user()
        return render_template('index.html', user=user)
    
    # ============================================================================
    # ROTAS DE INFORMAÇÃO
    # ============================================================================
    
    @app.route('/get_cameras')
    @login_required  # Protege a rota - requer login
    def get_cameras():
        """
        Retorna a lista de IDs de câmeras disponíveis.
        A interface HTML usa isso para saber quais câmeras mostrar.
        
        Retorna: JSON com lista de IDs das câmeras
        Exemplo: {"cameras": ["webcam", "corredor"]}
        """
        # Pega todas as chaves do dicionário g_cameras (os IDs das câmeras ativas)
        lista_cameras = list(g_cameras.keys())
        return jsonify(cameras=lista_cameras)
    
    @app.route('/get_status/<cam_id>')
    @login_required  # Protege a rota - requer login
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
    @login_required  # Protege a rota - requer login
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
    @login_required  # Protege a rota - requer login
    def start_recording(cam_id):
        """
        Inicia gravação manual de uma câmera específica.
        Chamada quando o usuário clica no botão "Gravar Manual".
        
        cam_id: ID da câmera
        
        Retorna: JSON com status da operação
        """
        user = get_current_user()
        
        # Verifica se a câmera existe
        if cam_id not in g_cameras:
            return jsonify(status="Erro: Câmera não encontrada"), 404
        
        # Pega o worker da câmera
        worker = g_cameras[cam_id]
        
        # Inicia a gravação (protegido pelo lock)
        with worker.state_lock:
            worker.start_recording_logic()
        
        # Registra ação do usuário
        log_event(EventType.USER_ACTION, EventSeverity.INFO,
                 camera_id=cam_id,
                 message=f"Usuário iniciou gravação manual",
                 user=user)
        
        return jsonify(status=f"Gravando ({cam_id})...")
    
    @app.route('/stop_recording/<cam_id>', methods=['POST'])
    @login_required  # Protege a rota - requer login
    def stop_recording(cam_id):
        """
        Para a gravação manual de uma câmera específica.
        Chamada quando o usuário clica no botão "Parar Manual".
        
        cam_id: ID da câmera
        
        Retorna: JSON com status da operação
        """
        user = get_current_user()
        
        # Verifica se a câmera existe
        if cam_id not in g_cameras:
            return jsonify(status="Erro: Câmera não encontrada"), 404
        
        # Pega o worker da câmera
        worker = g_cameras[cam_id]
        
        # Para a gravação (protegido pelo lock)
        with worker.state_lock:
            worker.stop_recording_logic()
        
        # Registra ação do usuário
        log_event(EventType.USER_ACTION, EventSeverity.INFO,
                 camera_id=cam_id,
                 message=f"Usuário parou gravação manual",
                 user=user)
        
        return jsonify(status=f"Ocioso ({cam_id})")
    
    # ============================================================================
    # ROTAS DE DETECÇÃO DE MOVIMENTO
    # ============================================================================
    
    @app.route('/toggle_motion_detection/<cam_id>', methods=['POST'])
    @login_required  # Protege a rota - requer login
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
    @login_required  # Protege a rota - requer login
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
                    from app.object_detector import ObjectDetector
                    from app.config import YOLO_MODEL, OBJECT_CONFIDENCE_THRESHOLD, OBJECT_CLASSES_FILTER
                    
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
    @login_required  # Protege a rota - requer login
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
    @login_required  # Protege a rota - requer login
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
    @login_required  # Protege a rota - requer login
    def playback(filename):
        """
        Envia um arquivo de vídeo para o navegador reproduzir.
        Chamada quando o usuário clica em um vídeo na lista.
        
        filename: Nome do arquivo de vídeo (ex: "webcam-gravacao-25-12-2024_143022.webm")
        
        Retorna: Arquivo de vídeo para o navegador
        """
        # Envia o arquivo da pasta de gravações
        return send_from_directory(PASTA_GRAVACOES, filename)
    
    # ============================================================================
    # ROTAS DE PÁGINAS DE GERENCIAMENTO
    # ============================================================================
    
    @app.route('/dashboard')
    @login_required
    def dashboard_page():
        """
        Página principal do dashboard com estatísticas.
        """
        user = get_current_user()
        return render_template('dashboard.html', user=user)
    
    @app.route('/cameras')
    @login_required
    def cameras_page():
        """
        Página para gerenciar câmeras (adicionar, remover, editar).
        """
        user = get_current_user()
        return render_template('cameras.html', user=user)
    
    @app.route('/settings')
    @login_required
    def settings_page():
        """
        Página de configurações do sistema.
        """
        user = get_current_user()
        return render_template('settings.html', user=user)
    
    # ============================================================================
    # API DE GERENCIAMENTO DE CÂMERAS
    # ============================================================================
    
    @app.route('/api/cameras/list')
    @login_required
    def api_list_cameras():
        """
        Lista todas as câmeras configuradas.
        """
        cameras = list_cameras()
        return jsonify(cameras)
    
    @app.route('/api/cameras/add', methods=['POST'])
    @login_required
    def api_add_camera():
        """
        Adiciona uma nova câmera.
        """
        data = request.get_json()
        
        cam_id = data.get('cam_id', '').strip()
        name = data.get('name', '').strip()
        source = data.get('source', '')
        enabled = data.get('enabled', True)
        
        if not cam_id or not name or source == '':
            return jsonify(success=False, message="Dados inválidos"), 400
        
        success, message = add_camera(cam_id, source, name, enabled)
        return jsonify(success=success, message=message)
    
    @app.route('/api/cameras/remove/<cam_id>', methods=['DELETE'])
    @login_required
    def api_remove_camera(cam_id):
        """
        Remove uma câmera.
        """
        success, message = remove_camera(cam_id)
        return jsonify(success=success, message=message)
    
    @app.route('/api/cameras/update/<cam_id>', methods=['PUT'])
    @login_required
    def api_update_camera(cam_id):
        """
        Atualiza informações de uma câmera.
        """
        data = request.get_json()
        
        source = data.get('source')
        name = data.get('name')
        enabled = data.get('enabled')
        
        success, message = update_camera(cam_id, source, name, enabled)
        return jsonify(success=success, message=message)
    
    # ============================================================================
    # API DE CONFIGURAÇÕES DO SISTEMA
    # ============================================================================
    
    @app.route('/api/settings/get')
    @login_required
    def api_get_settings():
        """
        Retorna todas as configurações do sistema.
        """
        config = load_system_config()
        return jsonify(config)
    
    @app.route('/api/settings/update', methods=['POST'])
    @login_required
    def api_update_settings():
        """
        Atualiza configurações do sistema.
        """
        data = request.get_json()
        
        section = data.get('section')
        new_config = data.get('config')
        
        if not section or not new_config:
            return jsonify(success=False, message="Dados inválidos"), 400
        
        # Carrega config atual
        config = load_system_config()
        
        # Atualiza a seção específica
        if section not in config:
            config[section] = {}
        
        config[section].update(new_config)
        
        # Salva
        if save_system_config(config):
            return jsonify(success=True, message="Configurações atualizadas com sucesso!")
        else:
            return jsonify(success=False, message="Erro ao salvar configurações"), 500
    
    # ============================================================================
    # API DE ESTATÍSTICAS
    # ============================================================================
    
    @app.route('/api/stats/all')
    @login_required
    def api_get_all_stats():
        """
        Retorna todas as estatísticas do sistema.
        """
        try:
            stats = get_all_stats()
            return jsonify(stats)
        except Exception as e:
            return jsonify(error=str(e)), 500
    
    @app.route('/api/stats/videos')
    @login_required
    def api_get_video_stats():
        """
        Retorna estatísticas de vídeos.
        """
        try:
            system_config = load_system_config()
            recording_folder = system_config.get('recording', {}).get('folder', 'gravacoes')
            stats = get_video_stats(recording_folder)
            return jsonify(stats)
        except Exception as e:
            return jsonify(error=str(e)), 500
    
    @app.route('/api/stats/cameras')
    @login_required
    def api_get_camera_stats():
        """
        Retorna estatísticas das câmeras.
        """
        try:
            stats = get_camera_stats()
            return jsonify(stats)
        except Exception as e:
            return jsonify(error=str(e)), 500
    
    @app.route('/api/stats/detections')
    @login_required
    def api_get_detection_stats():
        """
        Retorna estatísticas de detecções de objetos.
        """
        try:
            stats = get_detection_stats()
            return jsonify(stats)
        except Exception as e:
            return jsonify(error=str(e)), 500
    
    # ============================================================================
    # ROTAS DE EVENTOS/LOGS
    # ============================================================================
    
    @app.route('/events')
    @login_required
    def events_page():
        """
        Página para visualizar histórico de eventos/logs.
        """
        user = get_current_user()
        return render_template('events.html', user=user)
    
    @app.route('/api/events')
    @login_required
    def api_get_events():
        """
        Retorna eventos do log com filtros opcionais.
        
        Query parameters:
        - limit: Número máximo de eventos (padrão: 100)
        - type: Filtrar por tipo de evento
        - severity: Filtrar por severidade
        - camera_id: Filtrar por ID da câmera
        - start_date: Data inicial (ISO format)
        - end_date: Data final (ISO format)
        - search: Buscar texto na mensagem
        """
        try:
            limit = request.args.get('limit', 100, type=int)
            event_type = request.args.get('type')
            severity = request.args.get('severity')
            camera_id = request.args.get('camera_id')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            search = request.args.get('search')
            
            events = get_events(
                limit=limit,
                event_type=event_type,
                severity=severity,
                camera_id=camera_id,
                start_date=start_date,
                end_date=end_date,
                search=search
            )
            
            return jsonify(events=events, count=len(events))
        except Exception as e:
            return jsonify(error=str(e)), 500
    
    @app.route('/api/events/stats')
    @login_required
    def api_get_event_stats():
        """
        Retorna estatísticas dos eventos.
        """
        try:
            stats = get_event_stats()
            return jsonify(stats)
        except Exception as e:
            return jsonify(error=str(e)), 500
    
    @app.route('/api/events/clear', methods=['POST'])
    @login_required
    def api_clear_events():
        """
        Limpa eventos do log.
        
        Body JSON opcional:
        - older_than_days: Remove apenas eventos mais antigos que X dias
        """
        try:
            data = request.get_json() or {}
            older_than_days = data.get('older_than_days')
            
            removed = clear_events(older_than_days=older_than_days)
            
            return jsonify(success=True, removed=removed, message=f"{removed} evento(s) removido(s)")
        except Exception as e:
            return jsonify(error=str(e)), 500
    
    # ============================================================================
    # ROTAS DE EXPORTAÇÃO DE VÍDEOS
    # ============================================================================
    
    @app.route('/export')
    @login_required
    def export_page():
        """
        Página para gerenciar exportações de vídeos.
        """
        user = get_current_user()
        return render_template('export.html', user=user)
    
    @app.route('/api/export/convert', methods=['POST'])
    @login_required
    def api_convert_video():
        """
        Converte um vídeo para outro formato.
        
        Body JSON:
        - filename: Nome do arquivo de vídeo
        - format: Formato de saída ('mp4', 'avi', 'mov', 'webm')
        - quality: Qualidade ('low', 'medium', 'high')
        - fps: FPS de saída (opcional)
        """
        try:
            data = request.get_json()
            filename = data.get('filename')
            format_type = data.get('format', 'mp4')
            quality = data.get('quality', 'medium')
            fps = data.get('fps')
            
            if not filename:
                return jsonify(success=False, message="Nome do arquivo não fornecido"), 400
            
            # Caminhos
            input_path = os.path.join(PASTA_GRAVACOES, filename)
            
            if not os.path.exists(input_path):
                return jsonify(success=False, message="Arquivo não encontrado"), 404
            
            # Nome do arquivo de saída
            base_name = os.path.splitext(filename)[0]
            output_filename = f"{base_name}.{format_type}"
            output_path = os.path.join(PASTA_GRAVACOES, output_filename)
            
            # Converte
            success, message = convert_video(
                input_path, output_path,
                format_type=format_type,
                quality=quality,
                fps=fps
            )
            
            if success:
                # Registra evento
                log_event(EventType.USER_ACTION, EventSeverity.INFO,
                         message=f"Vídeo convertido: {filename} -> {output_filename}",
                         details={'format': format_type, 'quality': quality},
                         user=get_current_user())
                
                return jsonify(
                    success=True,
                    message=message,
                    output_filename=output_filename
                )
            else:
                return jsonify(success=False, message=message), 500
        
        except Exception as e:
            return jsonify(success=False, message=f"Erro: {str(e)}"), 500
    
    @app.route('/api/export/extract-frames', methods=['POST'])
    @login_required
    def api_extract_frames():
        """
        Extrai frames de um vídeo.
        
        Body JSON:
        - filename: Nome do arquivo de vídeo
        - interval: Intervalo entre frames em segundos (padrão: 1.0)
        - format: Formato dos frames ('jpg', 'png') (padrão: 'jpg')
        - max_frames: Número máximo de frames (opcional)
        """
        try:
            data = request.get_json()
            filename = data.get('filename')
            interval = float(data.get('interval', 1.0))
            frame_format = data.get('format', 'jpg')
            max_frames = data.get('max_frames')
            
            if not filename:
                return jsonify(success=False, message="Nome do arquivo não fornecido"), 400
            
            # Caminhos
            video_path = os.path.join(PASTA_GRAVACOES, filename)
            
            if not os.path.exists(video_path):
                return jsonify(success=False, message="Arquivo não encontrado"), 404
            
            # Pasta de saída
            base_name = os.path.splitext(filename)[0]
            output_folder = os.path.join(PASTA_GRAVACOES, f"{base_name}_frames")
            
            # Extrai frames
            success, message, count = extract_frames(
                video_path, output_folder,
                interval=interval,
                format=frame_format,
                max_frames=max_frames
            )
            
            if success:
                # Registra evento
                log_event(EventType.USER_ACTION, EventSeverity.INFO,
                         message=f"Frames extraídos: {filename} ({count} frames)",
                         details={'interval': interval, 'format': frame_format},
                         user=get_current_user())
                
                return jsonify(
                    success=True,
                    message=message,
                    frames_count=count,
                    output_folder=output_folder
                )
            else:
                return jsonify(success=False, message=message), 500
        
        except Exception as e:
            return jsonify(success=False, message=f"Erro: {str(e)}"), 500
    
    @app.route('/api/export/video-info/<filename>')
    @login_required
    def api_get_video_info(filename):
        """
        Obtém informações sobre um vídeo.
        """
        try:
            video_path = os.path.join(PASTA_GRAVACOES, filename)
            info = get_video_info(video_path)
            
            if 'error' in info:
                return jsonify(error=info['error']), 404
            
            return jsonify(info)
        except Exception as e:
            return jsonify(error=str(e)), 500
    
    @app.route('/api/export/formats')
    @login_required
    def api_get_formats():
        """
        Retorna os formatos suportados.
        """
        return jsonify({
            'formats': SUPPORTED_FORMATS,
            'ffmpeg_available': check_ffmpeg()
        })
    
    @app.route('/download/<filename>')
    @login_required
    def download_file(filename):
        """
        Faz download de um arquivo da pasta de gravações.
        """
        try:
            return send_from_directory(PASTA_GRAVACOES, filename, as_attachment=True)
        except Exception as e:
            return jsonify(error=str(e)), 404

