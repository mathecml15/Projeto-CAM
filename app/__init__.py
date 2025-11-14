"""
================================================================================
APP - Pacote principal da aplicação VMS
================================================================================

Este pacote contém todos os módulos da aplicação de gerenciamento de vídeo.

MÓDULOS PRINCIPAIS:
- auth: Autenticação e controle de acesso
- auth_routes: Rotas de autenticação (login, registro)
- camera_manager: Gerenciamento de configurações de câmeras
- camera_worker: Worker thread para cada câmera
- config: Configurações do sistema
- database: Operações com banco de dados MySQL
- event_logger: Sistema de logging de eventos
- object_detector: Detecção de objetos usando IA (YOLO)
- routes: Rotas principais da aplicação
- stats: Estatísticas e métricas do sistema
- video_converter: Conversão de formatos de vídeo
- video_stream: Streaming de vídeo para a interface web
"""

__version__ = '1.0.0'
__author__ = 'VMS Team'
