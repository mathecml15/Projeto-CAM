"""
================================================================================
OBJECT DETECTOR - Detecção de objetos usando IA (YOLOv8)
================================================================================

Este arquivo contém a classe ObjectDetector que usa YOLOv8 para detectar
objetos nas imagens. YOLOv8 é uma rede neural pré-treinada que pode detectar
80 tipos diferentes de objetos (pessoas, carros, animais, etc.).

COMO FUNCIONA:
1. Carrega um modelo YOLOv8 pré-treinado
2. Processa cada frame da câmera
3. Detecta objetos e retorna suas posições e tipos
4. Desenha retângulos e labels no frame
"""

from ultralytics import YOLO
import cv2
import numpy as np


class ObjectDetector:
    """
    Classe que gerencia a detecção de objetos usando YOLOv8.
    """
    
    def __init__(self, model_path='yolov8n.pt', conf_threshold=0.5):
        """
        Inicializa o detector de objetos.
        
        model_path: Caminho para o modelo YOLO (ou nome do modelo pré-treinado)
                   - 'yolov8n.pt' = nano (mais rápido, menor precisão)
                   - 'yolov8s.pt' = small (médio)
                   - 'yolov8m.pt' = medium (melhor precisão)
                   - 'yolov8l.pt' = large (muito bom)
                   - 'yolov8x.pt' = extra large (melhor, mas mais lento)
        
        conf_threshold: Limiar de confiança (0.0 a 1.0)
                       Valores maiores = só detecta objetos com alta certeza
                       Valores menores = detecta mais objetos (mas pode ter falsos positivos)
        """
        print(f"Carregando modelo YOLO: {model_path}")
        
        # Carrega o modelo YOLO
        # Se o arquivo não existir, ele baixa automaticamente
        self.model = YOLO(model_path)
        
        # Limiar de confiança
        self.conf_threshold = conf_threshold
        
        # Lista de classes que o YOLO pode detectar (80 classes do COCO dataset)
        # Você pode filtrar apenas algumas classes se quiser
        self.classes_to_detect = None  # None = detecta todas as classes
        
        print(f"Modelo YOLO carregado com sucesso!")
        print(f"Limiar de confiança: {conf_threshold}")
    
    def set_classes_filter(self, class_names):
        """
        Define quais classes de objetos devem ser detectadas.
        
        class_names: Lista com nomes das classes (ex: ['person', 'car', 'dog'])
                    None = detecta todas as classes
        
        Classes comuns:
        - 'person' = pessoa
        - 'car' = carro
        - 'bicycle' = bicicleta
        - 'motorcycle' = moto
        - 'bus' = ônibus
        - 'truck' = caminhão
        - 'dog' = cachorro
        - 'cat' = gato
        - 'bird' = pássaro
        - 'chair' = cadeira
        - 'couch' = sofá
        - 'laptop' = notebook
        - 'cell phone' = celular
        - etc.
        """
        self.classes_to_detect = class_names
        if class_names:
            print(f"Filtrando detecções para: {', '.join(class_names)}")
        else:
            print("Detectando todas as classes")
    
    def detect(self, frame):
        """
        Detecta objetos em um frame.
        
        frame: Imagem em formato numpy array (BGR)
        
        Retorna: (frame_anotado, detections)
                 - frame_anotado: Frame com retângulos e labels desenhados
                 - detections: Lista de detecções, cada uma com:
                   {
                       'class': nome da classe (ex: 'person'),
                       'confidence': nível de confiança (0.0 a 1.0),
                       'bbox': [x1, y1, x2, y2] coordenadas do retângulo
                   }
        """
        # Faz a detecção usando o modelo YOLO
        # conf: limiar de confiança
        # classes: filtra classes (None = todas)
        results = self.model(frame, conf=self.conf_threshold, classes=None)
        
        # Lista para armazenar as detecções
        detections = []
        
        # Cria uma cópia do frame para desenhar as detecções
        frame_anotado = frame.copy()
        
        # Processa os resultados
        for result in results:
            # Pega as caixas delimitadoras (bounding boxes)
            boxes = result.boxes
            
            # Para cada detecção
            for box in boxes:
                # Pega as coordenadas do retângulo
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                # Pega a confiança (certeza da detecção)
                confidence = float(box.conf[0].cpu().numpy())
                
                # Pega o ID da classe e converte para nome
                class_id = int(box.cls[0].cpu().numpy())
                class_name = self.model.names[class_id]
                
                # Se estamos filtrando classes, verifica se esta classe está na lista
                if self.classes_to_detect is not None:
                    if class_name not in self.classes_to_detect:
                        continue  # Pula esta detecção
                
                # Adiciona à lista de detecções
                detections.append({
                    'class': class_name,
                    'confidence': confidence,
                    'bbox': [x1, y1, x2, y2]
                })
                
                # Desenha o retângulo no frame
                # Cor: verde para pessoa, azul para outros objetos
                color = (0, 255, 0) if class_name == 'person' else (255, 0, 0)
                cv2.rectangle(frame_anotado, (x1, y1), (x2, y2), color, 2)
                
                # Cria o texto do label (nome da classe + confiança)
                label = f"{class_name} {confidence:.2f}"
                
                # Calcula o tamanho do texto
                (text_width, text_height), _ = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
                )
                
                # Desenha um retângulo de fundo para o texto (para melhor legibilidade)
                cv2.rectangle(
                    frame_anotado,
                    (x1, y1 - text_height - 10),
                    (x1 + text_width, y1),
                    color,
                    -1
                )
                
                # Desenha o texto do label
                cv2.putText(
                    frame_anotado,
                    label,
                    (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),  # Cor branca para o texto
                    2
                )
        
        return frame_anotado, detections
    
    def detect_specific_class(self, frame, class_name):
        """
        Detecta apenas um tipo específico de objeto.
        
        frame: Imagem em formato numpy array
        class_name: Nome da classe a detectar (ex: 'person')
        
        Retorna: (frame_anotado, detections, count)
                 - count: Quantidade de objetos detectados
        """
        # Faz a detecção normal
        frame_anotado, detections = self.detect(frame)
        
        # Filtra apenas a classe desejada
        filtered_detections = [
            d for d in detections if d['class'] == class_name
        ]
        
        return frame_anotado, filtered_detections, len(filtered_detections)

