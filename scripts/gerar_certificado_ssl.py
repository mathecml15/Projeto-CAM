"""
================================================================================
GERADOR DE CERTIFICADOS SSL AUTO-ASSINADOS
================================================================================

Este script gera certificados SSL auto-assinados para uso em desenvolvimento.
Para produção, use certificados válidos (Let's Encrypt, etc.).
"""

import subprocess
import os
import sys

def gerar_certificado():
    """
    Gera certificados SSL auto-assinados.
    """
    print("=" * 60)
    print("GERADOR DE CERTIFICADOS SSL AUTO-ASSINADOS")
    print("=" * 60)
    print("\nEste script irá gerar:")
    print("  - config/cert.pem (certificado)")
    print("  - config/key.pem (chave privada)")
    print("\n⚠️  AVISO: Certificados auto-assinados são para DESENVOLVIMENTO apenas!")
    print("   O navegador mostrará aviso de segurança (é normal).\n")
    
    # Verifica se OpenSSL está instalado
    try:
        result = subprocess.run(['openssl', 'version'], 
                              capture_output=True, 
                              check=True)
        print(f"✅ OpenSSL encontrado: {result.stdout.decode().strip()}\n")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ERRO: OpenSSL não encontrado!")
        print("\nPara instalar:")
        print("  - Windows: Baixe de https://slproweb.com/products/Win32OpenSSL.html")
        print("  - Linux: sudo apt install openssl")
        print("  - Mac: brew install openssl")
        sys.exit(1)
    
    # Pergunta informações básicas
    print("Informe os dados do certificado:")
    print("(Pressione Enter para usar valores padrão)\n")
    
    country = input("País [BR]: ").strip() or "BR"
    state = input("Estado: ").strip() or "SP"
    city = input("Cidade: ").strip() or "São Paulo"
    org = input("Organização [VMS]: ").strip() or "VMS"
    common_name = input("Nome comum (hostname/IP) [localhost]: ").strip() or "localhost"
    
    # Cria pasta config se não existir
    config_dir = 'config'
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        print(f"✅ Pasta '{config_dir}' criada.\n")
    
    cert_path = os.path.join(config_dir, 'cert.pem')
    key_path = os.path.join(config_dir, 'key.pem')
    
    # Comando OpenSSL
    cmd = [
        'openssl', 'req', '-x509', '-newkey', 'rsa:4096',
        '-nodes',  # Não criptografa a chave privada
        '-out', cert_path,
        '-keyout', key_path,
        '-days', '365',  # Válido por 1 ano
        '-subj', f'/C={country}/ST={state}/L={city}/O={org}/CN={common_name}'
    ]
    
    print("\n🔄 Gerando certificados...\n")
    
    try:
        # Executa o comando
        subprocess.run(cmd, check=True)
        
        # Verifica se os arquivos foram criados
        if os.path.exists(cert_path) and os.path.exists(key_path):
            print("✅ Certificados gerados com sucesso!\n")
            print("Arquivos criados:")
            print(f"  - {os.path.abspath(cert_path)}")
            print(f"  - {os.path.abspath(key_path)}\n")
            print("📝 Próximos passos:")
            print("  1. Configure o arquivo .env:")
            print("     USE_HTTPS=True")
            print("     SSL_CERT_PATH=config/cert.pem")
            print("     SSL_KEY_PATH=config/key.pem")
            print("  2. Reinicie o servidor")
            print("  3. Acesse: https://localhost:5000")
            print("\n⚠️  Lembre-se: Certificados auto-assinados mostram aviso de segurança.")
            print("   Isso é normal para desenvolvimento. Clique em 'Avançado' → 'Continuar'.\n")
        else:
            print("❌ ERRO: Certificados não foram criados corretamente.")
            sys.exit(1)
            
    except subprocess.CalledProcessError as e:
        print(f"❌ ERRO ao gerar certificados: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERRO: {e}")
        sys.exit(1)


if __name__ == '__main__':
    try:
        gerar_certificado()
    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo usuário.")
        sys.exit(0)

