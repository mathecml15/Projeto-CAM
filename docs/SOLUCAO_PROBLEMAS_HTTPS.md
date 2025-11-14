# 🔧 Solução de Problemas com HTTPS

Este guia ajuda a resolver problemas comuns ao usar HTTPS.

## ❌ Problema: Página não carrega após aceitar certificado

### Sintomas:
- Você aceita o aviso de segurança do certificado auto-assinado
- A página fica em branco ou não carrega
- O navegador mostra "Carregando..." mas nunca termina

### Causas Possíveis:

#### 1. **Cookies de Sessão não são Enviados**

**Problema:** Com `SESSION_COOKIE_SECURE=True`, os cookies só são enviados via HTTPS. Se o navegador não confia completamente no certificado, pode não enviar os cookies.

**Solução Temporária (Desenvolvimento):**
```env
# No arquivo .env, desative SESSION_COOKIE_SECURE temporariamente
USE_HTTPS=True
SESSION_COOKIE_SECURE=False  # Adicione esta linha (apenas para desenvolvimento!)
```

**⚠️ ATENÇÃO:** Não use `SESSION_COOKIE_SECURE=False` em produção!

#### 2. **Loop de Redirecionamento**

**Problema:** Se você não está logado e tenta acessar uma página protegida, pode haver um loop de redirecionamento.

**Solução:**
1. Acesse diretamente: `https://localhost:5000/login`
2. Faça login
3. Depois acesse outras páginas

#### 3. **Mixed Content (Conteúdo Misto)**

**Problema:** Algum recurso (CSS, JS, imagens) está sendo carregado via HTTP em vez de HTTPS.

**Solução:**
1. Abra o Console do Navegador (F12)
2. Verifique se há erros de "Mixed Content"
3. Certifique-se de que todos os recursos usam HTTPS

#### 4. **Certificado Inválido**

**Problema:** O certificado pode estar corrompido ou inválido.

**Solução:**
1. Delete os certificados antigos:
   ```bash
   del cert.pem key.pem  # Windows
   rm cert.pem key.pem   # Linux/Mac
   ```

2. Gere novos certificados:
   ```bash
   python gerar_certificado_ssl.py
   ```

3. Reinicie o servidor

---

## 🔍 Diagnóstico

### 1. Verificar se o Servidor Está Rodando

Abra o terminal e veja se há mensagens de erro:
```bash
python servidor.py
```

### 2. Verificar Console do Navegador

1. Pressione **F12** no navegador
2. Vá para a aba **Console**
3. Veja se há erros em vermelho

### 3. Verificar Aba Network (Rede)

1. Pressione **F12** no navegador
2. Vá para a aba **Network** (Rede)
3. Recarregue a página (F5)
4. Veja quais requisições estão falhando (em vermelho)

### 4. Testar com Script Python

Execute o script de teste:
```bash
python test_https.py
```

---

## 🛠️ Soluções Rápidas

### Solução 1: Desativar HTTPS Temporariamente

Se você só quer testar o sistema sem HTTPS:

```env
# No arquivo .env
USE_HTTPS=False
```

Reinicie o servidor e acesse: `http://localhost:5000`

### Solução 2: Usar HTTP para Desenvolvimento

Para desenvolvimento local, HTTP é mais simples:

```env
USE_HTTPS=False
PORT=5000
```

### Solução 3: Verificar Certificados

Certifique-se de que os certificados existem e estão corretos:

```bash
# Windows
dir cert.pem key.pem

# Linux/Mac
ls -la cert.pem key.pem
```

Se não existirem, gere novos:
```bash
python gerar_certificado_ssl.py
```

### Solução 4: Limpar Cache do Navegador

1. Pressione **Ctrl+Shift+Delete**
2. Limpe cookies e cache
3. Feche e reabra o navegador
4. Acesse novamente: `https://localhost:5000`

### Solução 5: Tentar Outro Navegador

Alguns navegadores são mais rigorosos com certificados auto-assinados:
- **Chrome:** Mais rigoroso
- **Firefox:** Mais flexível
- **Edge:** Intermediário

Tente usar Firefox para desenvolvimento.

---

## 📝 Configuração Recomendada para Desenvolvimento

Para desenvolvimento local, use HTTP (mais simples):

```env
# .env
USE_HTTPS=False
PORT=5000
SECRET_KEY=sua_chave_secreta_aqui
```

Para produção, use HTTPS com certificado válido:

```env
# .env
USE_HTTPS=True
SSL_CERT_PATH=/etc/letsencrypt/live/seu-dominio.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/seu-dominio.com/privkey.pem
PORT=443
SECRET_KEY=sua_chave_secreta_aqui
```

---

## 🐛 Erros Comuns

### Erro: "ERR_SSL_PROTOCOL_ERROR"

**Causa:** Certificado inválido ou servidor não está usando HTTPS corretamente.

**Solução:**
1. Verifique se `USE_HTTPS=True` no .env
2. Verifique se os certificados existem
3. Gere novos certificados

### Erro: "NET::ERR_CERT_AUTHORITY_INVALID"

**Causa:** Certificado auto-assinado (normal em desenvolvimento).

**Solução:**
1. Clique em "Avançado"
2. Clique em "Continuar para localhost (não seguro)"
3. Isso é normal para desenvolvimento!

### Erro: "ERR_CONNECTION_REFUSED"

**Causa:** Servidor não está rodando ou porta errada.

**Solução:**
1. Verifique se o servidor está rodando
2. Verifique a porta no .env
3. Tente: `http://localhost:5000` primeiro

---

## 💡 Dicas

1. **Desenvolvimento:** Use HTTP (mais simples)
2. **Produção:** Use HTTPS com certificado válido (Let's Encrypt)
3. **Teste Local:** Certificado auto-assinado é suficiente
4. **Navegador:** Firefox é mais flexível com certificados auto-assinados

---

## 📚 Referências

- [Flask SSL Context](https://flask.palletsprojects.com/en/latest/deploying/configuration/#ssl-context)
- [Let's Encrypt](https://letsencrypt.org/)
- [Mixed Content](https://developer.mozilla.org/en-US/docs/Web/Security/Mixed_content)

