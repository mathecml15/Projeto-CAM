# ⚡ Solução Rápida: Página não carrega após aceitar certificado HTTPS

## 🔴 Problema

Após aceitar o certificado auto-assinado no navegador, a página não carrega ou fica em branco.

## ✅ Solução Rápida

### Opção 1: Permitir cookies inseguros (Desenvolvimento)

Adicione ao arquivo `.env`:

```env
USE_HTTPS=True
ALLOW_INSECURE_COOKIES=True
```

**⚠️ IMPORTANTE:** Use `ALLOW_INSECURE_COOKIES=True` APENAS para desenvolvimento!

### Opção 2: Usar HTTP para desenvolvimento (Recomendado)

Para desenvolvimento local, é mais simples usar HTTP:

```env
USE_HTTPS=False
PORT=5000
```

Acesse: `http://localhost:5000`

### Opção 3: Limpar cache e cookies

1. Pressione **Ctrl+Shift+Delete**
2. Limpe **Cookies** e **Cache**
3. Feche e reabra o navegador
4. Acesse novamente: `https://localhost:5000`

---

## 🔍 Diagnóstico

### 1. Verificar Console do Navegador

1. Pressione **F12** no navegador
2. Vá para a aba **Console**
3. Veja se há erros em vermelho

### 2. Verificar Aba Network (Rede)

1. Pressione **F12** no navegador
2. Vá para a aba **Network**
3. Recarregue a página (F5)
4. Veja quais requisições estão falhando

### 3. Verificar se o servidor está rodando

No terminal onde o servidor está rodando, você deve ver:
```
🔒 HTTPS ativado
Acesse: https://127.0.0.1:5000
```

---

## 💡 Solução Recomendada para Desenvolvimento

**Para desenvolvimento local, use HTTP** (mais simples e sem problemas):

1. Edite o arquivo `.env`:
   ```env
   USE_HTTPS=False
   PORT=5000
   ```

2. Reinicie o servidor:
   ```bash
   python servidor.py
   ```

3. Acesse: `http://localhost:5000`

**Vantagens:**
- ✅ Sem problemas com certificados
- ✅ Sem avisos de segurança
- ✅ Cookies funcionam normalmente
- ✅ Mais rápido para desenvolvimento

**Para produção, use HTTPS com certificado válido (Let's Encrypt).**

---

## 🐛 Erros Comuns

### Erro: "ERR_SSL_PROTOCOL_ERROR"
**Solução:** Gere novos certificados ou use HTTP.

### Erro: "Página em branco após aceitar certificado"
**Solução:** Adicione `ALLOW_INSECURE_COOKIES=True` ao `.env` ou use HTTP.

### Erro: "Cookies não são enviados"
**Solução:** Adicione `ALLOW_INSECURE_COOKIES=True` ao `.env`.

---

## 📝 Configuração Final Recomendada

### Desenvolvimento (`.env`):
```env
USE_HTTPS=False
PORT=5000
SECRET_KEY=sua_chave_secreta_aqui
```

### Produção (`.env`):
```env
USE_HTTPS=True
SSL_CERT_PATH=/etc/letsencrypt/live/seu-dominio.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/seu-dominio.com/privkey.pem
PORT=443
SECRET_KEY=sua_chave_secreta_aqui
ALLOW_INSECURE_COOKIES=False
```

