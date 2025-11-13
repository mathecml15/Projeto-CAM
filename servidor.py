"""
================================================================================
SERVIDOR PRINCIPAL - Ponto de entrada do programa
================================================================================

Este é o arquivo principal que inicia o servidor.
Ele coordena todos os outros módulos e inicia o servidor Flask.

O QUE ESTE CÓDIGO FAZ:
- Gerencia múltiplas câmeras ao mesmo tempo
- Transmite vídeo ao vivo de cada câmera na interface web
- Permite gravar vídeo manualmente (botão "Gravar Manual")
- Detecta movimento e grava automaticamente quando detecta
- Salva os vídeos na pasta "gravacoes" no formato .webm
- Permite assistir as gravações através do player na interface

COMO FUNCIONA:
1. Cada câmera roda em uma "thread" separada (processo paralelo)
2. A thread lê frames da câmera continuamente
3. Se a detecção de movimento estiver ligada, ela analisa cada frame
4. Se detectar movimento, inicia gravação automaticamente
5. O Flask (servidor web) serve a interface e recebe comandos
6. A interface HTML mostra os vídeos ao vivo e os controles
"""

# ============================================================================
# IMPORTAÇÕES
# ============================================================================

from flask import Flask  # Flask - cria o servidor web
import os  # Para criar pastas

# Importa as configurações
from app.config import PASTA_GRAVACOES, g_cameras

# Importa a classe CameraWorker
from app.camera_worker import CameraWorker

# Importa a função para registrar as rotas
from app.routes import registrar_rotas
from app.auth_routes import registrar_rotas_auth

# Importa o gerenciador de câmeras
from app.camera_manager import load_cameras_config, load_system_config

# Carrega variáveis de ambiente do arquivo .env
from dotenv import load_dotenv
load_dotenv()

# ============================================================================
# CRIAÇÃO DO APP FLASK
# ============================================================================

# Cria a aplicação Flask (servidor web)
app = Flask(__name__)

# Configuração de segurança para sessões
# SECRET_KEY é usada para criptografar as sessões (cookies)
# A chave é carregada do arquivo .env por segurança (nunca coloque no código!)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SESSION_COOKIE_SECURE'] = False  # True em produção com HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Protege contra XSS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Protege contra CSRF

# Registra todas as rotas no app
registrar_rotas_auth(app)  # Registra rotas de autenticação primeiro
registrar_rotas(app)  # Registra rotas principais (protegidas)

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """
    Função principal que inicia o servidor.
    Ela é executada quando o programa é rodado.
    """
    # Inicializa o banco de dados (se estiver usando)
    try:
        from app.database import init_database
        init_database()
        print("Banco de dados inicializado.")
    except ImportError:
        print("AVISO: Módulo database.py não encontrado. Usando armazenamento JSON (legado).")
    except Exception as e:
        print(f"AVISO: Erro ao inicializar banco de dados: {e}")
        print("Continuando com armazenamento JSON (legado)...")
    
    # Carrega configuração de câmeras do arquivo JSON
    print("Carregando configuração de câmeras...")
    cameras_config = load_cameras_config()
    print(f"Configuração de câmeras carregada: {len(cameras_config)} câmera(s) encontrada(s).")
    
    # Carrega configurações do sistema
    print("Carregando configurações do sistema...")
    system_config = load_system_config()
    print("Configurações do sistema carregadas.")
    
    # Carrega a pasta de gravações das configurações
    pasta_gravacoes = system_config.get('recording', {}).get('folder', PASTA_GRAVACOES)
    print(f"Pasta de gravações: {pasta_gravacoes}")
    
    # Cria a pasta de gravações se ela não existir
    if not os.path.exists(pasta_gravacoes):
        os.makedirs(pasta_gravacoes)  # Cria a pasta
        print(f"Pasta '{pasta_gravacoes}' criada.")
    
    # Inicializa todas as câmeras habilitadas do arquivo de configuração
    print("\n=== INICIANDO WORKERS DAS CAMERAS ===")
    
    # Para cada câmera na configuração
    for cam_id, cam_data in cameras_config.items():
        # Só inicia câmeras que estão habilitadas
        if not cam_data.get('enabled', True):
            print(f"[SKIP] Camera '{cam_id}' esta desabilitada.")
            continue
        
        source = cam_data.get('source')
        name = cam_data.get('name', cam_id)
        
        print(f"\n[INIT] Iniciando camera '{name}'")
        print(f"       ID: {cam_id}")
        print(f"       Fonte: {source}")
        
        try:
            # Cria um novo CameraWorker para esta câmera
            print(f"       Criando CameraWorker...")
            worker = CameraWorker(cam_id, source)
            
            # Inicia a thread (faz o loop run() começar a rodar)
            print(f"       Iniciando thread...")
            worker.start()
            
            # Armazena o worker no dicionário global
            g_cameras[cam_id] = worker
            print(f"       [OK] Camera '{name}' iniciada com sucesso!")
            
        except Exception as e:
            print(f"       [ERRO] Falha ao iniciar camera '{name}': {e}")
    
    print(f"\n=== WORKERS INICIADOS: {len(g_cameras)} camera(s) ativa(s) ===")
    print(f"\n=== INICIANDO SERVIDOR FLASK ===")
    print(f"Acesse: http://127.0.0.1:5000")
    print(f"ou:     http://localhost:5000")
    print(f"\nPressione Ctrl+C para parar o servidor.\n")
    
    # Inicia o servidor Flask
    # host='0.0.0.0' = aceita conexões de qualquer IP
    # port=5000 = porta do servidor
    # debug=False = modo produção (sem debug)
    # threaded=True = permite múltiplas requisições simultâneas
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

# ============================================================================
# EXECUÇÃO DO PROGRAMA
# ============================================================================

if __name__ == '__main__':
    """
    Este bloco só executa se o arquivo for rodado diretamente
    (não se for importado como módulo).
    """
    try:
        # Chama a função principal
        main()
    except KeyboardInterrupt:
        # Se o usuário pressionar Ctrl+C, interrompe o servidor
        print("\nServidor interrompido pelo usuário (Ctrl+C).")
    finally:
        # Este bloco SEMPRE executa, mesmo se der erro
        # Limpa os recursos: fecha todas as câmeras
        print("Encerrando... liberando câmeras.")
        for cam_id in g_cameras:
            g_cameras[cam_id].release()
