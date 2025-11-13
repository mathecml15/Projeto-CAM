# 📦 Como Instalar o FFmpeg no Projeto

Este guia explica como configurar o FFmpeg para uso no sistema de exportação de vídeos.

## 🎯 Por que usar FFmpeg?

O FFmpeg oferece:
- ✅ Conversões mais rápidas
- ✅ Melhor qualidade de vídeo
- ✅ Mais opções de compressão
- ✅ Suporte a mais formatos

**Nota:** O sistema funciona sem FFmpeg (usa OpenCV), mas funciona **muito melhor** com ele!

## 📥 Como Instalar

### Opção 1: Baixar e Extrair na Pasta do Projeto (Recomendado)

1. **Baixe o FFmpeg:**
   - Windows: https://www.gyan.dev/ffmpeg/builds/
   - Escolha a versão "ffmpeg-release-essentials.zip"

2. **Extraia o arquivo:**
   - Extraia o conteúdo do ZIP

3. **Organize na pasta do projeto:**
   - Copie a pasta `bin` do FFmpeg extraído
   - Cole em: `Projeto/tools/ffmpeg/bin/`
   - Deve ficar assim:
     ```
     Projeto/
     ├── tools/
     │   └── ffmpeg/
     │       └── bin/
     │           ├── ffmpeg.exe  ← Aqui!
     │           ├── ffplay.exe
     │           └── ffprobe.exe
     ```

4. **Verifique:**
   - O arquivo `ffmpeg.exe` deve estar em `tools/ffmpeg/bin/ffmpeg.exe`

### Opção 2: Instalar no Sistema (PATH)

Se preferir instalar globalmente no Windows:

1. Baixe o FFmpeg (mesmo link acima)
2. Extraia em uma pasta (ex: `C:\ffmpeg`)
3. Adicione `C:\ffmpeg\bin` ao PATH do Windows
4. Reinicie o terminal/PowerShell

## ✅ Verificar se Está Funcionando

Após instalar, reinicie o servidor e acesse `/export`. O sistema detectará automaticamente o FFmpeg.

Você também pode testar manualmente:

```powershell
# Se estiver na pasta do projeto:
.\tools\ffmpeg\bin\ffmpeg.exe -version

# Ou se estiver no PATH:
ffmpeg -version
```

## 🔍 Onde o Sistema Procura o FFmpeg?

O sistema procura nesta ordem:

1. `tools/ffmpeg/bin/ffmpeg.exe` (Windows)
2. `tools/ffmpeg/bin/ffmpeg` (Linux/Mac)
3. `ffmpeg/bin/ffmpeg.exe` (estrutura alternativa)
4. PATH do sistema (se instalado globalmente)

## 📝 Notas

- O FFmpeg é **opcional** - o sistema funciona sem ele
- Se não encontrar FFmpeg, usa OpenCV (mais lento)
- O arquivo `ffmpeg.exe` tem cerca de 80-100 MB
- Você pode adicionar `tools/ffmpeg/` ao `.gitignore` se não quiser commitar

## 🐛 Problemas Comuns

**Erro: "ffmpeg não encontrado"**
- Verifique se o arquivo está em `tools/ffmpeg/bin/ffmpeg.exe`
- Verifique se o nome do arquivo está correto (ffmpeg.exe no Windows)

**Conversão muito lenta**
- Isso significa que está usando OpenCV (fallback)
- Instale o FFmpeg para melhorar a velocidade

**Erro de permissão**
- Certifique-se de que o arquivo `ffmpeg.exe` tem permissão de execução

