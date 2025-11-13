"""
================================================================================
MÓDULO DE ESTATÍSTICAS
================================================================================

Este módulo calcula e fornece estatísticas do sistema VMS.
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from app.camera_manager import load_cameras_config, load_system_config
from app.config import g_cameras


def get_disk_usage(folder_path):
    """
    Calcula o espaço usado em disco por uma pasta.
    
    Args:
        folder_path: Caminho da pasta
        
    Returns:
        (total_size_bytes, total_size_mb, total_size_gb)
    """
    total_size = 0
    try:
        if os.path.exists(folder_path):
            for dirpath, dirnames, filenames in os.walk(folder_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except (OSError, FileNotFoundError):
                        pass
    except Exception as e:
        print(f"Erro ao calcular uso de disco: {e}")
    
    total_mb = total_size / (1024 * 1024)
    total_gb = total_size / (1024 * 1024 * 1024)
    
    return total_size, total_mb, total_gb


def get_video_stats(folder_path):
    """
    Analisa os vídeos na pasta de gravações e retorna estatísticas.
    
    Args:
        folder_path: Pasta onde estão os vídeos
        
    Returns:
        Dicionário com estatísticas de vídeos
    """
    stats = {
        'total_videos': 0,
        'videos_today': 0,
        'videos_this_week': 0,
        'videos_this_month': 0,
        'total_duration_seconds': 0,
        'total_size_bytes': 0,
        'videos_by_camera': {},
        'videos_by_date': {}
    }
    
    if not os.path.exists(folder_path):
        return stats
    
    try:
        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day)
        week_start = today_start - timedelta(days=now.weekday())
        month_start = datetime(now.year, now.month, 1)
        
        for filename in os.listdir(folder_path):
            if not filename.endswith('.webm'):
                continue
            
            filepath = os.path.join(folder_path, filename)
            
            try:
                # Tamanho do arquivo
                file_size = os.path.getsize(filepath)
                stats['total_size_bytes'] += file_size
                
                # Data de modificação (aproximação da data de gravação)
                mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                # Contagem por período
                stats['total_videos'] += 1
                
                if mod_time >= today_start:
                    stats['videos_today'] += 1
                
                if mod_time >= week_start:
                    stats['videos_this_week'] += 1
                
                if mod_time >= month_start:
                    stats['videos_this_month'] += 1
                
                # Extrai nome da câmera do filename (formato: cam_id-timestamp.webm)
                cam_id = filename.split('-')[0] if '-' in filename else 'unknown'
                if cam_id not in stats['videos_by_camera']:
                    stats['videos_by_camera'][cam_id] = 0
                stats['videos_by_camera'][cam_id] += 1
                
                # Agrupa por data
                date_key = mod_time.strftime('%Y-%m-%d')
                if date_key not in stats['videos_by_date']:
                    stats['videos_by_date'][date_key] = 0
                stats['videos_by_date'][date_key] += 1
                
            except Exception as e:
                print(f"Erro ao processar arquivo {filename}: {e}")
                continue
    
    except Exception as e:
        print(f"Erro ao analisar vídeos: {e}")
    
    return stats


def get_camera_stats():
    """
    Retorna estatísticas das câmeras ativas.
    
    Returns:
        Dicionário com estatísticas das câmeras
    """
    stats = {
        'total_cameras': 0,
        'active_cameras': 0,
        'cameras_detail': []
    }
    
    cameras_config = load_cameras_config()
    stats['total_cameras'] = len(cameras_config)
    stats['active_cameras'] = len(g_cameras)
    
    for cam_id, cam_data in cameras_config.items():
        is_active = cam_id in g_cameras
        is_enabled = cam_data.get('enabled', True)
        
        camera_info = {
            'id': cam_id,
            'name': cam_data.get('name', cam_id),
            'enabled': is_enabled,
            'active': is_active,
            'source': cam_data.get('source', 'N/A')
        }
        
        # Se a câmera está ativa, pega estatísticas do worker
        if is_active:
            worker = g_cameras[cam_id]
            with worker.state_lock:
                camera_info['is_recording'] = worker.is_recording
                camera_info['motion_detection_enabled'] = worker.motion_detection_enabled
                camera_info['object_detection_enabled'] = getattr(worker, 'object_detection_enabled', False)
                
                # Estatísticas de detecção de objetos se disponível
                if hasattr(worker, 'get_detection_stats'):
                    detection_stats = worker.get_detection_stats()
                    camera_info['detection_stats'] = {
                        'total_detections': detection_stats.get('total_detections', 0),
                        'last_detection': detection_stats.get('last_detection_timestamp', 0),
                        'detection_counts': detection_stats.get('detection_counts', {})
                    }
        
        stats['cameras_detail'].append(camera_info)
    
    return stats


def get_detection_stats():
    """
    Retorna estatísticas consolidadas de detecções de objetos.
    
    Returns:
        Dicionário com estatísticas de detecções
    """
    stats = {
        'total_detections': 0,
        'detections_by_class': {},
        'detections_by_camera': {},
        'last_detection_timestamp': 0
    }
    
    for cam_id, worker in g_cameras.items():
        if hasattr(worker, 'get_detection_stats'):
            detection_stats = worker.get_detection_stats()
            
            cam_total = detection_stats.get('total_detections', 0)
            stats['total_detections'] += cam_total
            stats['detections_by_camera'][cam_id] = cam_total
            
            # Agrega contadores por classe
            detection_counts = detection_stats.get('detection_counts', {})
            for class_name, count in detection_counts.items():
                if class_name not in stats['detections_by_class']:
                    stats['detections_by_class'][class_name] = 0
                stats['detections_by_class'][class_name] += count
            
            # Última detecção
            last_detection = detection_stats.get('last_detection_timestamp', 0)
            if last_detection > stats['last_detection_timestamp']:
                stats['last_detection_timestamp'] = last_detection
    
    return stats


def get_all_stats():
    """
    Retorna todas as estatísticas consolidadas do sistema.
    
    Returns:
        Dicionário completo com todas as estatísticas
    """
    system_config = load_system_config()
    recording_folder = system_config.get('recording', {}).get('folder', 'gravacoes')
    
    # Estatísticas de vídeos
    video_stats = get_video_stats(recording_folder)
    
    # Uso de disco
    disk_size, disk_mb, disk_gb = get_disk_usage(recording_folder)
    
    # Estatísticas de câmeras
    camera_stats = get_camera_stats()
    
    # Estatísticas de detecções
    detection_stats = get_detection_stats()
    
    # Consolida tudo
    all_stats = {
        'timestamp': datetime.now().isoformat(),
        'videos': {
            'total': video_stats['total_videos'],
            'today': video_stats['videos_today'],
            'this_week': video_stats['videos_this_week'],
            'this_month': video_stats['videos_this_month'],
            'total_size_bytes': video_stats['total_size_bytes'],
            'total_size_mb': round(disk_mb, 2),
            'total_size_gb': round(disk_gb, 2),
            'by_camera': video_stats['videos_by_camera'],
            'by_date': video_stats['videos_by_date']
        },
        'disk': {
            'used_bytes': disk_size,
            'used_mb': round(disk_mb, 2),
            'used_gb': round(disk_gb, 2),
            'folder': recording_folder
        },
        'cameras': camera_stats,
        'detections': detection_stats
    }
    
    return all_stats

