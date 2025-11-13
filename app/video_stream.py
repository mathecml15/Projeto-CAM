"""
================================================================================
VIDEO STREAM - Geração de stream de vídeo ao vivo
================================================================================

Este arquivo contém a função que gera o stream de vídeo em tempo real
para exibição no navegador web.
"""

import cv2  # OpenCV - para codificar frames em JPEG
import time  # Para fazer pequenas pausas

# Importa o dicionário global de câmeras
from app.config import g_cameras


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

