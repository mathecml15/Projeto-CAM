"""
Script de teste para verificar se o servidor HTTPS está funcionando.
"""

import requests
import ssl
import urllib3

# Desabilita avisos de certificado auto-assinado
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_https():
    """Testa se o servidor HTTPS está respondendo."""
    url = "https://localhost:5000"
    
    print("=" * 60)
    print("TESTE DE CONEXÃO HTTPS")
    print("=" * 60)
    print(f"\nTestando: {url}")
    print("(Ignorando certificado auto-assinado)\n")
    
    try:
        # Tenta fazer uma requisição (ignora certificado inválido)
        response = requests.get(url, verify=False, timeout=5)
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"✅ Servidor respondendo!")
        
        if response.status_code == 200:
            print(f"✅ Página carregada com sucesso!")
        elif response.status_code == 302:
            print(f"⚠️  Redirecionamento detectado (provavelmente para /login)")
            print(f"   Isso é normal se você não estiver logado.")
        else:
            print(f"⚠️  Status inesperado: {response.status_code}")
            
    except requests.exceptions.SSLError as e:
        print(f"❌ Erro SSL: {e}")
        print(f"\n💡 Isso pode ser normal com certificado auto-assinado.")
        print(f"   O navegador pode mostrar aviso, mas deve funcionar.")
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Erro de conexão: {e}")
        print(f"\n💡 Verifique se o servidor está rodando:")
        print(f"   python servidor.py")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    test_https()

