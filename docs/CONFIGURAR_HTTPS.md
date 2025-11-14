# 🔒 Como Configurar HTTPS

Este guia explica como configurar HTTPS no seu VMS.

## 📋 Requisitos

Para usar HTTPS, você precisa de certificados SSL/TLS. Você tem duas opções:

### Opção 1: Certificado Auto-Assinado (Desenvolvimento)
✅ **Vantagens:** Rápido, fácil, gratuito  
❌ **Desvantagens:** Navegador mostrará aviso de segurança (normal para desenvolvimento)

### Opção 2: Certificado Válido (Produção)
✅ **Vantagens:** Sem avisos, válido para produção  
❌ **Desvantagens:** Requer domínio e configuração adicional

---

## 🚀 Opção 1: Certificado Auto-Assinado (Recomendado para Desenvolvimento)

### Windows:

1. **Instale OpenSSL** (se não tiver):
   - Baixe de: https://slproweb.com/products/Win32OpenSSL.html
   - Ou use Git Bash (já vem com OpenSSL)

2. **Gere os certificados:**
   ```bash
   openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
   ```

3. **Responda as perguntas:**
   - Country Name: BR
   - State: Seu Estado
   - City: Sua Cidade
   - Organization: Seu Nome/Organização
   - Common Name: **localhost** (ou seu IP)

4. **Coloque os arquivos no projeto:**
   - `cert.pem` → raiz do projeto
   - `key.pem` → raiz do projeto

5. **Configure o `.env`:**
   ```env
   USE_HTTPS=True
   SSL_CERT_PATH=cert.pem
   SSL_KEY_PATH=key.pem
   ```

### Linux/Mac:

```bash
# Gere os certificados
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Coloque no projeto
mv cert.pem /caminho/do/projeto/
mv key.pem /caminho/do/projeto/

# Configure o .env
echo "USE_HTTPS=True" >> .env
echo "SSL_CERT_PATH=cert.pem" >> .env
echo "SSL_KEY_PATH=key.pem" >> .env
```

---

## 🌐 Opção 2: Certificado Válido (Let's Encrypt - Produção)

### Usando Let's Encrypt (Gratuito):

1. **Instale Certbot:**
   ```bash
   # Ubuntu/Debian
   sudo apt install certbot
   
   # CentOS/RHEL
   sudo yum install certbot
   ```

2. **Gere certificados:**
   ```bash
   sudo certbot certonly --standalone -d seu-dominio.com
   ```

3. **Configure o `.env`:**
   ```env
   USE_HTTPS=True
   SSL_CERT_PATH=/etc/letsencrypt/live/seu-dominio.com/fullchain.pem
   SSL_KEY_PATH=/etc/letsencrypt/live/seu-dominio.com/privkey.pem
   ```

4. **Renovação automática (recomendado):**
   ```bash
   # Adicione ao crontab
   sudo crontab -e
   # Adicione esta linha (renova a cada 3 meses)
   0 0 1 * * certbot renew --quiet
   ```

---

## ⚙️ Configuração no `.env`

Adicione estas variáveis ao arquivo `.env`:

```env
# HTTPS
USE_HTTPS=True
SSL_CERT_PATH=cert.pem
SSL_KEY_PATH=key.pem
PORT=5000
```

**Variáveis:**
- `USE_HTTPS`: `True` para ativar, `False` para desativar
- `SSL_CERT_PATH`: Caminho para o certificado (relativo ou absoluto)
- `SSL_KEY_PATH`: Caminho para a chave privada (relativo ou absoluto)
- `PORT`: Porta do servidor (padrão: 5000)

---

## 🔍 Verificação

Após configurar, inicie o servidor:

```bash
python servidor.py
```

Você verá:
```
🔒 HTTPS ativado
Acesse: https://127.0.0.1:5000
```

**No navegador:**
- **Auto-assinado:** Clique em "Avançado" → "Continuar para localhost" (é seguro para desenvolvimento)
- **Let's Encrypt:** Funciona normalmente sem avisos

---

## ⚠️ Importante

1. **Desenvolvimento:** Use certificados auto-assinados (sem problemas)
2. **Produção:** Use Let's Encrypt ou certificados comerciais
3. **Porta 443:** Para produção, use porta 443 (padrão HTTPS)
4. **Firewall:** Certifique-se de abrir a porta HTTPS no firewall

---

## 🐛 Troubleshooting

### Erro: "Certificados não encontrados"
- Verifique se os arquivos `cert.pem` e `key.pem` estão na raiz do projeto
- Ou configure caminhos absolutos no `.env`

### Erro: "Permission denied"
- No Linux, certifique-se de que o usuário tem permissão de leitura dos certificados
- Use `chmod 644 cert.pem key.pem`

### Aviso de segurança no navegador
- **Normal para certificados auto-assinados!**
- Clique em "Avançado" → "Continuar"
- Ou use certificados válidos (Let's Encrypt)

---

## 📚 Referências

- [Let's Encrypt](https://letsencrypt.org/)
- [OpenSSL](https://www.openssl.org/)
- [Flask SSL Context](https://flask.palletsprojects.com/en/latest/deploying/configuration/#ssl-context)

