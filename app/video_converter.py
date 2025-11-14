"""
================================================================================
CONVERSOR DE VÍDEOS
================================================================================

Este módulo converte vídeos entre diferentes formatos e extrai frames.
"""

import os
import cv2
from pathlib import Path
from typing import Optional, Tuple, List


# Formatos suportados
SUPPORTED_FORMATS = {
    'mp4': {'ext': '.mp4', 'codec': 'mp4v', 'mime': 'video/mp4'},
    'avi': {'ext': '.avi', 'codec': 'XVID', 'mime': 'video/x-msvideo'},
    'mov': {'ext': '.mov', 'codec': 'mp4v', 'mime': 'video/quicktime'},
    'webm': {'ext': '.webm', 'codec': 'VP80', 'mime': 'video/webm'}
}

# Nota: FFmpeg foi removido. O sistema agora usa apenas OpenCV para conversão de vídeos.


def convert_video_opencv(input_path: str, output_path: str, 
                         format_type: str = 'mp4', 
                         quality: str = 'medium',
                         fps: Optional[float] = None) -> Tuple[bool, str]:
    """
    Converte vídeo usando OpenCV.
    
    Args:
        input_path: Caminho do vídeo de entrada
        output_path: Caminho do vídeo de saída
        format_type: Formato de saída ('mp4', 'avi', 'mov')
        quality: Qualidade ('low', 'medium', 'high')
        fps: FPS de saída (None = manter original)
    
    Returns:
        (sucesso, mensagem)
    """
    if not os.path.exists(input_path):
        return False, f"Arquivo não encontrado: {input_path}"
    
    if format_type not in SUPPORTED_FORMATS:
        return False, f"Formato não suportado: {format_type}"
    
    try:
        # Abre o vídeo de entrada
        cap = cv2.VideoCapture(input_path)
        
        if not cap.isOpened():
            return False, "Não foi possível abrir o vídeo de entrada"
        
        # Obtém propriedades do vídeo original
        original_fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Define FPS de saída
        output_fps = fps if fps else original_fps
        
        # Define codec e qualidade baseado no formato
        format_info = SUPPORTED_FORMATS[format_type]
        fourcc = cv2.VideoWriter_fourcc(*format_info['codec'])
        
        # Ajusta qualidade (bitrate aproximado)
        if quality == 'low':
            # Reduz resolução para baixa qualidade
            width = int(width * 0.75)
            height = int(height * 0.75)
        elif quality == 'high':
            # Mantém resolução original
            pass
        
        # Cria o writer de vídeo
        out = cv2.VideoWriter(output_path, fourcc, output_fps, (width, height))
        
        if not out.isOpened():
            cap.release()
            return False, "Não foi possível criar o arquivo de saída"
        
        # Processa frame por frame
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Redimensiona se necessário
            if quality == 'low':
                frame = cv2.resize(frame, (width, height))
            
            out.write(frame)
            frame_count += 1
        
        # Libera recursos
        cap.release()
        out.release()
        
        return True, f"Vídeo convertido com sucesso! {frame_count} frames processados."
    
    except Exception as e:
        return False, f"Erro ao converter vídeo: {str(e)}"




def convert_video(input_path: str, output_path: str,
                  format_type: str = 'mp4',
                  quality: str = 'medium',
                  fps: Optional[float] = None) -> Tuple[bool, str]:
    """
    Converte vídeo usando OpenCV.
    
    Args:
        input_path: Caminho do vídeo de entrada
        output_path: Caminho do vídeo de saída
        format_type: Formato de saída ('mp4', 'avi', 'mov', 'webm')
        quality: Qualidade ('low', 'medium', 'high')
        fps: FPS de saída (None = manter original)
    
    Returns:
        (sucesso, mensagem)
    """
    # Usa OpenCV para conversão
    return convert_video_opencv(input_path, output_path, format_type, quality, fps)


def extract_frames(video_path: str, output_folder: str,
                   interval: float = 1.0,
                   format: str = 'jpg',
                   max_frames: Optional[int] = None) -> Tuple[bool, str, int]:
    """
    Extrai frames de um vídeo.
    
    Args:
        video_path: Caminho do vídeo
        output_folder: Pasta onde salvar os frames
        interval: Intervalo entre frames em segundos (1.0 = 1 frame por segundo)
        format: Formato dos frames ('jpg', 'png')
        max_frames: Número máximo de frames a extrair (None = todos)
    
    Returns:
        (sucesso, mensagem, número_de_frames_extraídos)
    """
    if not os.path.exists(video_path):
        return False, f"Arquivo não encontrado: {video_path}", 0
    
    try:
        # Cria pasta de saída se não existir
        os.makedirs(output_folder, exist_ok=True)
        
        # Abre o vídeo
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return False, "Não foi possível abrir o vídeo", 0
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps * interval)  # Frames a pular
        
        frame_count = 0
        saved_count = 0
        video_name = Path(video_path).stem
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Salva frame no intervalo especificado
            if frame_count % frame_interval == 0:
                frame_filename = f"{video_name}_frame_{saved_count:06d}.{format}"
                frame_path = os.path.join(output_folder, frame_filename)
                
                if format == 'png':
                    cv2.imwrite(frame_path, frame)
                else:  # jpg
                    cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                
                saved_count += 1
                
                # Verifica limite de frames
                if max_frames and saved_count >= max_frames:
                    break
            
            frame_count += 1
        
        cap.release()
        
        return True, f"{saved_count} frame(s) extraído(s) com sucesso!", saved_count
    
    except Exception as e:
        return False, f"Erro ao extrair frames: {str(e)}", 0


def get_video_info(video_path: str) -> dict:
    """
    Obtém informações sobre um vídeo.
    
    Args:
        video_path: Caminho do vídeo
    
    Returns:
        Dicionário com informações do vídeo
    """
    if not os.path.exists(video_path):
        return {'error': 'Arquivo não encontrado'}
    
    try:
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return {'error': 'Não foi possível abrir o vídeo'}
        
        info = {
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'duration': 0,
            'size': os.path.getsize(video_path),
            'format': Path(video_path).suffix[1:].lower()
        }
        
        # Calcula duração
        if info['fps'] > 0:
            info['duration'] = info['frame_count'] / info['fps']
        
        cap.release()
        
        return info
    
    except Exception as e:
        return {'error': str(e)}

