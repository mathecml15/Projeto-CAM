"""
Script de diagnóstico para problemas com HTTPS.
"""

import os
import sys

def diagnostico():
    """Executa diagnóstico de problemas com HTTPS."""
    print("=" * 60)
    print("DIAGNÓSTICO DE HTTPS")
    print("=" * 60)
    
    # Verifica arquivo .env
    print("\n1. Verificando arquivo .env...")
    if os.path.exists('.env'):
        print("   ✅ Arquivo .env existe")
        with open('.env', 'r', encoding='utf-8') as f:
            env_content = f.read()
            if 'USE_HTTPS=True' in env_content:
                print("   ⚠️  HTTPS está ativado")
            else:
                print("   ℹ️  HTTPS não está ativado (usando HTTP)")
            if 'ALLOW_INSECURE_COOKIES=True' in env_content:
                print("   ⚠️  ALLOW_INSECURE_COOKIES está ativado (apenas para desenvolvimento)")
    else:
        print("   ❌ Arquivo .env não encontrado")
        print("   💡 Crie um arquivo .env com suas configurações")
    
    # Verifica certificados
    print("\n2. Verificando certificados SSL...")
    cert_path = os.getenv('SSL_CERT_PATH', 'cert.pem')
    key_path = os.getenv('SSL_KEY_PATH', 'key.pem')
    
    if os.path.exists(cert_path):
        print(f"   ✅ Certificado encontrado: {cert_path}")
        size = os.path.getsize(cert_path)
        print(f"   📊 Tamanho: {size} bytes")
    else:
        print(f"   ❌ Certificado não encontrado: {cert_path}")
        print("   💡 Gere certificados: python gerar_certificado_ssl.py")
    
    if os.path.exists(key_path):
        print(f"   ✅ Chave encontrada: {key_path}")
        size = os.path.getsize(key_path)
        print(f"   📊 Tamanho: {size} bytes")
    else:
        print(f"   ❌ Chave não encontrada: {key_path}")
        print("   💡 Gere certificados: python gerar_certificado_ssl.py")
    
    # Verifica porta
    print("\n3. Verificando porta...")
    port = os.getenv('PORT', '5000')
    print(f"   ℹ️  Porta configurada: {port}")
    
    # Recomendações
    print("\n" + "=" * 60)
    print("RECOMENDAÇÕES")
    print("=" * 60)
    
    print("\n💡 Para DESENVOLVIMENTO (recomendado):")
    print("   Use HTTP (mais simples, sem problemas):")
    print("   USE_HTTPS=False no .env")
    print("   Acesse: http://localhost:5000")
    
    print("\n💡 Para DESENVOLVIMENTO com HTTPS:")
    print("   Se a página não carregar após aceitar certificado:")
    print("   1. Adicione ao .env: ALLOW_INSECURE_COOKIES=True")
    print("   2. Limpe cache e cookies do navegador")
    print("   3. Reinicie o servidor")
    print("   4. Acesse: https://localhost:5000")
    
    print("\n💡 Para PRODUÇÃO:")
    print("   Use HTTPS com certificado válido (Let's Encrypt)")
    print("   NÃO use ALLOW_INSECURE_COOKIES=True em produção!")
    
    print("\n" + "=" * 60)
    print("SOLUÇÃO RÁPIDA")
    print("=" * 60)
    print("\n1. Edite o arquivo .env:")
    print("   USE_HTTPS=False  # Para desenvolvimento")
    print("   PORT=5000")
    print("\n2. Reinicie o servidor:")
    print("   python servidor.py")
    print("\n3. Acesse:")
    print("   http://localhost:5000")
    print("\n" + "=" * 60)

if __name__ == '__main__':
    try:
        diagnostico()
    except Exception as e:
        print(f"\n❌ Erro ao executar diagnóstico: {e}")
        sys.exit(1)

