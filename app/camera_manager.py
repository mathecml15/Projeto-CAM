"""
================================================================================
GERENCIADOR DE CÂMERAS
================================================================================

Este módulo gerencia câmeras dinamicamente, permitindo adicionar, remover e 
editar câmeras sem precisar modificar o código.
"""

import json
import os
from threading import Lock

# Arquivo onde as câmeras serão salvas
CAMERAS_CONFIG_FILE = 'cameras_config.json'
SYSTEM_CONFIG_FILE = 'system_config.json'

# Lock para operações de arquivo
config_lock = Lock()

# ============================================================================
# FUNÇÕES DE GERENCIAMENTO DE CÂMERAS
# ============================================================================

def load_cameras_config():
    """
    Carrega a configuração de câmeras do arquivo JSON.
    Se o arquivo não existir, retorna a configuração padrão.
    """
    with config_lock:
        if not os.path.exists(CAMERAS_CONFIG_FILE):
            # Configuração padrão
            default_config = {
                "webcam": {
                    "source": 0,
                    "name": "Webcam",
                    "enabled": True
                }
            }
            # Salva diretamente sem usar save_cameras_config para evitar deadlock
            try:
                with open(CAMERAS_CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"Erro ao criar arquivo de configuração padrão: {e}")
            return default_config
        
        try:
            with open(CAMERAS_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar configuração de câmeras: {e}")
            return {}

def save_cameras_config(cameras_config):
    """
    Salva a configuração de câmeras no arquivo JSON.
    """
    with config_lock:
        try:
            with open(CAMERAS_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(cameras_config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar configuração de câmeras: {e}")
            return False

def add_camera(cam_id, source, name="Nova Câmera", enabled=True):
    """
    Adiciona uma nova câmera à configuração.
    
    Args:
        cam_id: ID único da câmera (ex: "camera1")
        source: Fonte da câmera (ex: 0 para webcam, ou URL RTSP)
        name: Nome amigável da câmera
        enabled: Se a câmera está habilitada
    
    Returns:
        (sucesso, mensagem)
    """
    cameras = load_cameras_config()
    
    if cam_id in cameras:
        return False, f"Já existe uma câmera com o ID '{cam_id}'"
    
    # Tenta converter para int se for número
    try:
        source = int(source)
    except ValueError:
        pass  # Mantém como string (provavelmente URL)
    
    cameras[cam_id] = {
        "source": source,
        "name": name,
        "enabled": enabled
    }
    
    if save_cameras_config(cameras):
        return True, f"Câmera '{name}' adicionada com sucesso!"
    else:
        return False, "Erro ao salvar configuração"

def remove_camera(cam_id):
    """
    Remove uma câmera da configuração.
    """
    cameras = load_cameras_config()
    
    if cam_id not in cameras:
        return False, f"Câmera '{cam_id}' não encontrada"
    
    del cameras[cam_id]
    
    if save_cameras_config(cameras):
        return True, f"Câmera removida com sucesso!"
    else:
        return False, "Erro ao salvar configuração"

def update_camera(cam_id, source=None, name=None, enabled=None):
    """
    Atualiza as informações de uma câmera.
    """
    cameras = load_cameras_config()
    
    if cam_id not in cameras:
        return False, f"Câmera '{cam_id}' não encontrada"
    
    if source is not None:
        try:
            cameras[cam_id]["source"] = int(source)
        except ValueError:
            cameras[cam_id]["source"] = source
    
    if name is not None:
        cameras[cam_id]["name"] = name
    
    if enabled is not None:
        cameras[cam_id]["enabled"] = enabled
    
    if save_cameras_config(cameras):
        return True, f"Câmera atualizada com sucesso!"
    else:
        return False, "Erro ao salvar configuração"

def get_camera_info(cam_id):
    """
    Retorna informações de uma câmera específica.
    """
    cameras = load_cameras_config()
    return cameras.get(cam_id, None)

def list_cameras():
    """
    Lista todas as câmeras configuradas.
    """
    return load_cameras_config()

# ============================================================================
# FUNÇÕES DE GERENCIAMENTO DE CONFIGURAÇÕES DO SISTEMA
# ============================================================================

def load_system_config():
    """
    Carrega as configurações do sistema.
    """
    with config_lock:
        if not os.path.exists(SYSTEM_CONFIG_FILE):
            # Configurações padrão
            default_config = {
                "motion_detection": {
                    "cooldown": 5.0,
                    "min_contour_area": 500
                },
                "object_detection": {
                    "enabled": False,
                    "model": "models/yolov8n.pt",
                    "confidence_threshold": 0.5,
                    "classes_filter": None,
                    "auto_record_on_objects": None
                },
                "recording": {
                    "folder": "gravacoes"
                }
            }
            # Salva diretamente sem usar save_system_config para evitar deadlock
            try:
                with open(SYSTEM_CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"Erro ao criar arquivo de configuração do sistema: {e}")
            return default_config
        
        try:
            with open(SYSTEM_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar configurações do sistema: {e}")
            return {}

def save_system_config(config):
    """
    Salva as configurações do sistema.
    """
    with config_lock:
        try:
            with open(SYSTEM_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar configurações do sistema: {e}")
            return False

def update_system_config(section, key, value):
    """
    Atualiza uma configuração específica do sistema.
    
    Args:
        section: Seção da configuração (ex: "motion_detection")
        key: Chave da configuração (ex: "cooldown")
        value: Novo valor
    """
    config = load_system_config()
    
    if section not in config:
        config[section] = {}
    
    config[section][key] = value
    
    if save_system_config(config):
        return True, "Configuração atualizada com sucesso!"
    else:
        return False, "Erro ao salvar configuração"

