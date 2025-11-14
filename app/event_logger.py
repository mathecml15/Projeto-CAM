"""
================================================================================
LOGGER DE EVENTOS
================================================================================

Este módulo registra todos os eventos importantes do sistema VMS.
"""

import json
import os
from datetime import datetime
from threading import Lock
from enum import Enum

# Arquivo onde os eventos serão salvos
EVENTS_LOG_FILE = 'logs/events_log.json'
MAX_EVENTS = 10000  # Limite máximo de eventos no arquivo

# Lock para operações de arquivo
events_lock = Lock()


class EventType(Enum):
    """Tipos de eventos que podem ser registrados"""
    RECORDING_STARTED = "recording_started"
    RECORDING_STOPPED = "recording_stopped"
    MOTION_DETECTED = "motion_detected"
    OBJECT_DETECTED = "object_detected"
    CAMERA_CONNECTED = "camera_connected"
    CAMERA_DISCONNECTED = "camera_disconnected"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_ACTION = "user_action"
    SYSTEM_ERROR = "system_error"
    SYSTEM_INFO = "system_info"
    CONFIG_CHANGED = "config_changed"


class EventSeverity(Enum):
    """Níveis de severidade dos eventos"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


def _load_events():
    """
    Carrega eventos do arquivo JSON.
    """
    with events_lock:
        if not os.path.exists(EVENTS_LOG_FILE):
            return []
        
        try:
            with open(EVENTS_LOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar eventos: {e}")
            return []


def _save_events(events):
    """
    Salva eventos no arquivo JSON.
    Mantém apenas os últimos MAX_EVENTS eventos.
    """
    with events_lock:
        try:
            # Mantém apenas os últimos MAX_EVENTS eventos
            if len(events) > MAX_EVENTS:
                events = events[-MAX_EVENTS:]
            
            with open(EVENTS_LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(events, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar eventos: {e}")
            return False


def log_event(event_type, severity=EventSeverity.INFO, camera_id=None, 
              message="", details=None, user=None):
    """
    Registra um novo evento no log.
    
    Args:
        event_type: Tipo do evento (EventType)
        severity: Severidade do evento (EventType.INFO, WARNING, ERROR, CRITICAL)
        camera_id: ID da câmera relacionada (opcional)
        message: Mensagem descritiva do evento
        details: Dicionário com detalhes adicionais (opcional)
        user: Usuário que causou o evento (opcional)
    
    Returns:
        True se o evento foi registrado com sucesso
    """
    event = {
        'id': datetime.now().timestamp(),
        'timestamp': datetime.now().isoformat(),
        'type': event_type.value if isinstance(event_type, EventType) else str(event_type),
        'severity': severity.value if isinstance(severity, EventSeverity) else str(severity),
        'camera_id': camera_id,
        'message': message,
        'details': details or {},
        'user': user
    }
    
    events = _load_events()
    events.append(event)
    
    return _save_events(events)


def get_events(limit=100, event_type=None, severity=None, camera_id=None, 
               start_date=None, end_date=None, search=None):
    """
    Busca eventos do log com filtros opcionais.
    
    Args:
        limit: Número máximo de eventos a retornar (padrão: 100)
        event_type: Filtrar por tipo de evento
        severity: Filtrar por severidade
        camera_id: Filtrar por ID da câmera
        start_date: Data inicial (ISO format)
        end_date: Data final (ISO format)
        search: Buscar texto na mensagem
    
    Returns:
        Lista de eventos filtrados, ordenados do mais recente para o mais antigo
    """
    events = _load_events()
    
    # Filtra eventos
    filtered = events
    
    if event_type:
        filtered = [e for e in filtered if e.get('type') == event_type]
    
    if severity:
        filtered = [e for e in filtered if e.get('severity') == severity]
    
    if camera_id:
        filtered = [e for e in filtered if e.get('camera_id') == camera_id]
    
    if start_date:
        filtered = [e for e in filtered if e.get('timestamp', '') >= start_date]
    
    if end_date:
        filtered = [e for e in filtered if e.get('timestamp', '') <= end_date]
    
    if search:
        search_lower = search.lower()
        filtered = [e for e in filtered if search_lower in e.get('message', '').lower()]
    
    # Ordena por timestamp (mais recente primeiro)
    filtered.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # Limita resultados
    return filtered[:limit]


def get_event_stats():
    """
    Retorna estatísticas dos eventos.
    
    Returns:
        Dicionário com estatísticas
    """
    events = _load_events()
    
    stats = {
        'total_events': len(events),
        'by_type': {},
        'by_severity': {},
        'by_camera': {},
        'recent_24h': 0,
        'recent_7d': 0
    }
    
    now = datetime.now()
    day_ago = (now.timestamp() - 86400)  # 24 horas
    week_ago = (now.timestamp() - 604800)  # 7 dias
    
    for event in events:
        # Por tipo
        event_type = event.get('type', 'unknown')
        stats['by_type'][event_type] = stats['by_type'].get(event_type, 0) + 1
        
        # Por severidade
        severity = event.get('severity', 'info')
        stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1
        
        # Por câmera
        cam_id = event.get('camera_id')
        if cam_id:
            stats['by_camera'][cam_id] = stats['by_camera'].get(cam_id, 0) + 1
        
        # Eventos recentes
        event_timestamp = event.get('id', 0)
        if event_timestamp >= day_ago:
            stats['recent_24h'] += 1
        if event_timestamp >= week_ago:
            stats['recent_7d'] += 1
    
    return stats


def clear_events(older_than_days=None):
    """
    Limpa eventos do log.
    
    Args:
        older_than_days: Se especificado, remove apenas eventos mais antigos que X dias
    
    Returns:
        Número de eventos removidos
    """
    events = _load_events()
    
    if older_than_days:
        cutoff_timestamp = datetime.now().timestamp() - (older_than_days * 86400)
        original_count = len(events)
        events = [e for e in events if e.get('id', 0) >= cutoff_timestamp]
        removed = original_count - len(events)
    else:
        removed = len(events)
        events = []
    
    _save_events(events)
    return removed

