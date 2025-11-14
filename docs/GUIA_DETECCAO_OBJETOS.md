# 🎯 Guia de Detecção de Objetos com IA

## 📋 O que é Detecção de Objetos?

A detecção de objetos é uma tecnologia de IA que identifica e localiza objetos em imagens ou vídeos. No seu projeto VMS, isso permite:

- **Detectar pessoas, carros, animais, etc.** em tempo real
- **Gravar automaticamente** quando objetos específicos aparecem
- **Ver retângulos e labels** ao redor dos objetos detectados no stream ao vivo
- **Melhorar a segurança** identificando objetos relevantes

## 🚀 Como Instalar

### 1. Instale as dependências:

```bash
pip install ultralytics
```

Ou instale todas as dependências do projeto:

```bash
pip install -r requirements.txt
```

### 2. O modelo YOLO será baixado automaticamente

Na primeira vez que você usar a detecção de objetos, o YOLOv8 será baixado automaticamente (cerca de 6-10 MB para o modelo nano).

## ⚙️ Configuração

Edite o arquivo `config.py` para configurar a detecção de objetos:

### Ativar/Desativar por padrão:

```python
OBJECT_DETECTION_ENABLED = True  # True = ativado, False = desativado
```

### Escolher o modelo:

```python
YOLO_MODEL = 'yolov8n.pt'  # Recomendado para CPU
```

**Opções de modelos:**
- `yolov8n.pt` - **Nano** (mais rápido, menor precisão) - ⭐ Recomendado para CPU
- `yolov8s.pt` - Small (médio)
- `yolov8m.pt` - Medium (melhor precisão)
- `yolov8l.pt` - Large (muito bom)
- `yolov8x.pt` - Extra Large (melhor, mas mais lento) - Recomendado para GPU

### Ajustar sensibilidade:

```python
OBJECT_CONFIDENCE_THRESHOLD = 0.5  # 0.0 a 1.0
```

- **Valores maiores (0.7-0.9)**: Só detecta objetos com alta certeza (menos falsos positivos)
- **Valores menores (0.3-0.5)**: Detecta mais objetos (pode ter mais falsos positivos)

### Filtrar classes de objetos:

```python
OBJECT_CLASSES_FILTER = ['person', 'car', 'dog']  # Só detecta pessoas, carros e cachorros
# ou
OBJECT_CLASSES_FILTER = None  # Detecta todas as 80 classes
```

### Gravar automaticamente quando detectar objetos:

```python
AUTO_RECORD_ON_OBJECTS = ['person']  # Grava quando detectar pessoas
# ou
AUTO_RECORD_ON_OBJECTS = None  # Não grava automaticamente
```

## 📚 Classes de Objetos Disponíveis

O YOLOv8 pode detectar 80 tipos de objetos diferentes. Alguns exemplos:

### Pessoas e Animais:
- `person` - Pessoa
- `dog` - Cachorro
- `cat` - Gato
- `bird` - Pássaro
- `horse` - Cavalo
- `cow` - Vaca
- `sheep` - Ovelha

### Veículos:
- `car` - Carro
- `motorcycle` - Moto
- `bicycle` - Bicicleta
- `bus` - Ônibus
- `truck` - Caminhão
- `train` - Trem
- `airplane` - Avião

### Objetos Comuns:
- `chair` - Cadeira
- `couch` - Sofá
- `bed` - Cama
- `laptop` - Notebook
- `cell phone` - Celular
- `book` - Livro
- `cup` - Copo
- `bottle` - Garrafa
- `keyboard` - Teclado
- `mouse` - Mouse (computador)

### Outros:
- `backpack` - Mochila
- `handbag` - Bolsa
- `umbrella` - Guarda-chuva
- `sports ball` - Bola esportiva
- `skateboard` - Skate
- `surfboard` - Prancha de surf

**Lista completa:** O YOLOv8 detecta 80 classes do dataset COCO. Você pode ver todas no código do YOLO ou na documentação oficial.

## 🎮 Como Usar

### 1. Ativar via Interface Web (em desenvolvimento)

Quando a interface for atualizada, você poderá clicar em um botão "Ligar Detecção de Objetos" para cada câmera.

### 2. Ativar via Configuração

Edite `config.py` e defina:

```python
OBJECT_DETECTION_ENABLED = True
```

Reinicie o servidor.

### 3. Ativar via API

Faça uma requisição POST:

```bash
curl -X POST http://localhost:5000/toggle_object_detection/webcam
```

## 💡 Exemplos de Uso

### Exemplo 1: Detectar apenas pessoas

```python
# config.py
OBJECT_DETECTION_ENABLED = True
OBJECT_CLASSES_FILTER = ['person']
AUTO_RECORD_ON_OBJECTS = ['person']  # Grava quando detectar pessoas
```

### Exemplo 2: Detectar carros e motos

```python
# config.py
OBJECT_DETECTION_ENABLED = True
OBJECT_CLASSES_FILTER = ['car', 'motorcycle', 'bus', 'truck']
AUTO_RECORD_ON_OBJECTS = ['car', 'motorcycle']  # Grava quando detectar carros ou motos
```

### Exemplo 3: Detectar animais de estimação

```python
# config.py
OBJECT_DETECTION_ENABLED = True
OBJECT_CLASSES_FILTER = ['dog', 'cat', 'bird']
AUTO_RECORD_ON_OBJECTS = ['dog', 'cat']  # Grava quando detectar cachorros ou gatos
```

### Exemplo 4: Detectar tudo com alta precisão

```python
# config.py
OBJECT_DETECTION_ENABLED = True
OBJECT_CLASSES_FILTER = None  # Detecta todas as classes
OBJECT_CONFIDENCE_THRESHOLD = 0.7  # Alta precisão
AUTO_RECORD_ON_OBJECTS = None  # Não grava automaticamente
```

## ⚡ Performance

### CPU (Processador comum):

- **Modelo Nano (yolov8n.pt)**: ~15-30 FPS (recomendado)
- **Modelo Small (yolov8s.pt)**: ~10-20 FPS
- **Modelo Medium (yolov8m.pt)**: ~5-10 FPS

### GPU (Placa de vídeo):

- **Modelo Nano**: ~60+ FPS
- **Modelo Small**: ~40-60 FPS
- **Modelo Medium**: ~30-40 FPS
- **Modelo Large**: ~20-30 FPS

**Nota:** O sistema processa detecção a cada 0.5 segundos (2 FPS) por padrão para não sobrecarregar. Você pode ajustar isso no código se necessário.

## 🔧 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'ultralytics'"

**Solução:** Instale o ultralytics:

```bash
pip install ultralytics
```

### Detecção muito lenta

**Soluções:**
1. Use o modelo nano: `YOLO_MODEL = 'yolov8n.pt'`
2. Aumente o intervalo de detecção (edite `detection_interval` no código)
3. Filtre classes: `OBJECT_CLASSES_FILTER = ['person']` (só detecta pessoas)
4. Use uma GPU se disponível

### Muitos falsos positivos

**Soluções:**
1. Aumente o limiar de confiança: `OBJECT_CONFIDENCE_THRESHOLD = 0.7`
2. Use um modelo maior (small, medium, etc.)

### Não detecta objetos

**Soluções:**
1. Verifique se a detecção está ativada
2. Diminua o limiar de confiança: `OBJECT_CONFIDENCE_THRESHOLD = 0.3`
3. Verifique se a iluminação está boa
4. Certifique-se de que os objetos estão visíveis na câmera

## 📖 Mais Informações

- **Documentação YOLOv8**: https://docs.ultralytics.com/
- **Lista completa de classes**: https://github.com/ultralytics/ultralytics
- **Exemplos de uso**: https://github.com/ultralytics/ultralytics/tree/main/examples

## 🎓 Aprendendo Mais

Se você quiser entender melhor como funciona:

1. **YOLO (You Only Look Once)**: Algoritmo de detecção de objetos em tempo real
2. **Rede Neural Convolucional (CNN)**: Tipo de IA usada para reconhecer padrões em imagens
3. **Transfer Learning**: Técnica de usar um modelo pré-treinado (YOLO foi treinado com milhões de imagens)

## 💬 Dúvidas?

Se tiver dúvidas ou problemas, verifique:
1. Os logs do servidor (mensagens de erro)
2. A documentação do YOLOv8
3. Os comentários no código (`object_detector.py` e `camera_worker.py`)

