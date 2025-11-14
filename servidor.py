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
# Configuração HTTPS: True se usar SSL, False para desenvolvimento
USE_HTTPS = os.getenv('USE_HTTPS', 'False').lower() == 'true'
SSL_CERT_PATH = os.getenv('SSL_CERT_PATH', 'config/cert.pem')
SSL_KEY_PATH = os.getenv('SSL_KEY_PATH', 'config/key.pem')
# Configuração de cookies de sessão
# Para desenvolvimento com certificado auto-assinado, é CRÍTICO
# permitir cookies mesmo com certificado não confiável
# Por padrão, se HTTPS está ativo, permite cookies inseguros (desenvolvimento)
ALLOW_INSECURE_COOKIES = os.getenv('ALLOW_INSECURE_COOKIES', 'True' if USE_HTTPS else 'False').lower() == 'true'

# CRÍTICO: Com certificado auto-assinado, SESSION_COOKIE_SECURE DEVE ser False
# Caso contrário, os cookies não serão enviados pelo navegador e a sessão não funcionará
# Por padrão, se HTTPS está ativo, permite cookies inseguros (ALLOW_INSECURE_COOKIES=True)
if USE_HTTPS:
    if ALLOW_INSECURE_COOKIES:
        # Desenvolvimento: certificado auto-assinado - cookies não seguros
        # Isso permite que cookies funcionem mesmo com certificado não confiável
        app.config['SESSION_COOKIE_SECURE'] = False
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Lax funciona melhor que None sem Secure
    else:
        # Produção: certificado válido - cookies seguros
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
else:
    # Sem HTTPS, não usa cookies seguros
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

app.config['SESSION_COOKIE_HTTPONLY'] = True  # Protege contra XSS
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 horas

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
    
    # Configuração de porta
    port = int(os.getenv('PORT', '5000'))
    
    # Carrega configuração HTTPS (usa variável local para não modificar global)
    use_https = USE_HTTPS
    
    # Verifica se deve usar HTTPS
    if use_https:
        # Verifica se os certificados existem
        if not os.path.exists(SSL_CERT_PATH) or not os.path.exists(SSL_KEY_PATH):
            print(f"\n⚠️  AVISO: Certificados SSL não encontrados!")
            print(f"   Certificado: {SSL_CERT_PATH}")
            print(f"   Chave: {SSL_KEY_PATH}")
            print(f"\n   🔄 Tentando gerar certificados automaticamente...")
            
            # Tenta gerar certificados automaticamente
            try:
                import subprocess
                import sys
                
                # Comando para gerar certificado auto-assinado
                cmd = [
                    'openssl', 'req', '-x509', '-newkey', 'rsa:4096',
                    '-nodes',  # Não criptografa a chave privada
                    '-out', SSL_CERT_PATH,
                    '-keyout', SSL_KEY_PATH,
                    '-days', '365',
                    '-subj', '/C=BR/ST=SP/L=SaoPaulo/O=VMS/CN=localhost'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0 and os.path.exists(SSL_CERT_PATH) and os.path.exists(SSL_KEY_PATH):
                    print(f"   ✅ Certificados gerados com sucesso!")
                    print(f"   📋 Certificado: {os.path.abspath(SSL_CERT_PATH)}")
                    print(f"   📋 Chave: {os.path.abspath(SSL_KEY_PATH)}")
                else:
                    raise Exception("Falha ao gerar certificados")
                    
            except FileNotFoundError:
                print(f"   ❌ OpenSSL não encontrado!")
                print(f"\n   💡 Soluções:")
                print(f"   1. Instale OpenSSL:")
                print(f"      Windows: Baixe de https://slproweb.com/products/Win32OpenSSL.html")
                print(f"      Ou use: python scripts/gerar_certificado_ssl.py")
                print(f"   2. Gere manualmente:")
                print(f"      openssl req -x509 -newkey rsa:4096 -nodes -out {SSL_CERT_PATH} -keyout {SSL_KEY_PATH} -days 365")
                print(f"   3. Desative HTTPS: USE_HTTPS=False no .env")
                print(f"\n   Iniciando sem HTTPS...")
                use_https = False
            except Exception as e:
                print(f"   ❌ Erro ao gerar certificados: {e}")
                print(f"\n   💡 Gere manualmente: python scripts/gerar_certificado_ssl.py")
                print(f"   Ou desative HTTPS: USE_HTTPS=False no .env")
                print(f"\n   Iniciando sem HTTPS...")
                use_https = False
        else:
            # Certificados existem, verifica se são válidos
            print(f"   ✅ Certificados encontrados:")
            print(f"      Certificado: {os.path.abspath(SSL_CERT_PATH)}")
            print(f"      Chave: {os.path.abspath(SSL_KEY_PATH)}")
            
            # Verifica tamanho dos arquivos
            cert_size = os.path.getsize(SSL_CERT_PATH)
            key_size = os.path.getsize(SSL_KEY_PATH)
            print(f"      Tamanho certificado: {cert_size} bytes")
            print(f"      Tamanho chave: {key_size} bytes")
            
            if cert_size == 0 or key_size == 0:
                print(f"   ⚠️  AVISO: Certificados estão vazios! Gerando novos...")
                try:
                    import subprocess
                    cmd = [
                        'openssl', 'req', '-x509', '-newkey', 'rsa:4096',
                        '-nodes', '-out', SSL_CERT_PATH, '-keyout', SSL_KEY_PATH,
                        '-days', '365', '-subj', '/C=BR/ST=SP/L=SaoPaulo/O=VMS/CN=localhost'
                    ]
                    subprocess.run(cmd, capture_output=True, timeout=30, check=True)
                    print(f"   ✅ Novos certificados gerados!")
                except Exception as e:
                    print(f"   ❌ Erro: {e}")
                    print(f"   Iniciando sem HTTPS...")
                    use_https = False
    
    if use_https:
        protocol = 'https'
        print(f"\n{'='*60}")
        print(f"🔒 HTTPS ATIVADO")
        print(f"{'='*60}")
        print(f"\n✅ Servidor HTTPS iniciado com sucesso!")
        print(f"\n📍 URLs de acesso:")
        print(f"   https://127.0.0.1:{port}")
        print(f"   https://localhost:{port}")
        print(f"\n⚠️  IMPORTANTE - Certificado Auto-Assinado:")
        print(f"   1. O navegador mostrará aviso de segurança (NORMAL para desenvolvimento)")
        print(f"   2. Clique em 'Avançado' ou 'Advanced'")
        print(f"   3. Clique em 'Continuar para localhost' ou 'Proceed to localhost'")
        print(f"   4. A página carregará normalmente após isso")
        print(f"\n💡 Dica: Se a página não carregar após aceitar o certificado:")
        print(f"   - Limpe cache e cookies do navegador (Ctrl+Shift+Delete)")
        print(f"   - Tente usar outro navegador (Firefox funciona melhor)")
        print(f"   - Verifique o console do navegador (F12) para erros")
        print(f"\n🔐 Configuração de Cookies:")
        if ALLOW_INSECURE_COOKIES:
            print(f"   ✅ Cookies permitidos com certificado auto-assinado (desenvolvimento)")
        else:
            print(f"   ⚠️  Cookies seguros ativados (pode causar problemas com certificado auto-assinado)")
            print(f"   💡 Se houver problemas, adicione ao .env: ALLOW_INSECURE_COOKIES=True")
    else:
        protocol = 'http'
        print(f"\n{'='*60}")
        print(f"🌐 HTTP ATIVADO")
        print(f"{'='*60}")
        print(f"\n📍 URLs de acesso:")
        print(f"   http://127.0.0.1:{port}")
        print(f"   http://localhost:{port}")
    
    print(f"\nPressione Ctrl+C para parar o servidor.\n")
    
    # Inicia o servidor Flask
    # host='0.0.0.0' = aceita conexões de qualquer IP
    # port = porta do servidor (padrão 5000)
    # debug=True com HTTPS para ver erros (ajuda a diagnosticar problemas)
    # threaded=True = permite múltiplas requisições simultâneas
    try:
        if use_https:
            print(f"\n🔒 Iniciando servidor HTTPS na porta {port}...")
            print(f"📋 Certificado: {os.path.abspath(SSL_CERT_PATH)}")
            print(f"📋 Chave: {os.path.abspath(SSL_KEY_PATH)}")
            
            # Verifica se os certificados são válidos
            try:
                import ssl
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                context.load_cert_chain(SSL_CERT_PATH, SSL_KEY_PATH)
                print(f"   ✅ Certificados validados com sucesso!")
            except Exception as e:
                print(f"   ⚠️  AVISO: Problema ao validar certificados: {e}")
                print(f"   Continuando mesmo assim...")
                context = (SSL_CERT_PATH, SSL_KEY_PATH)
            
            print(f"\n🚀 Servidor iniciando...")
            app.run(
                host='0.0.0.0', 
                port=port, 
                debug=True,  # Ativa debug para ver erros
                threaded=True,
                ssl_context=(SSL_CERT_PATH, SSL_KEY_PATH),
                use_reloader=False,  # Desativa reloader para evitar problemas
                use_debugger=True  # Ativa debugger
            )
        else:
            print(f"\n🌐 Iniciando servidor HTTP na porta {port}...")
            app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    except OSError as e:
        if "Address already in use" in str(e) or "already in use" in str(e).lower():
            print(f"\n❌ ERRO: Porta {port} já está em uso!")
            print(f"\n💡 Soluções:")
            print(f"   1. Feche outras instâncias do servidor")
            print(f"   2. Use outra porta: PORT=5001 no .env")
            print(f"   3. No Windows: netstat -ano | findstr :{port}")
        else:
            print(f"\n❌ ERRO ao iniciar servidor: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERRO ao iniciar servidor: {e}")
        print(f"\n💡 Dicas:")
        print(f"   - Verifique se a porta {port} não está em uso")
        print(f"   - Verifique se os certificados SSL estão corretos")
        print(f"   - Tente desativar HTTPS: USE_HTTPS=False no .env")
        print(f"   - Verifique o console do navegador (F12) para erros")
        raise

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
