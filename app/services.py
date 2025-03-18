import os
import cv2
import numpy as np
import uuid
import tempfile
from django.conf import settings
from ultralytics import YOLO
from PIL import Image
import io
import base64
import time
from pathlib import Path
import torch
import gc

# Constants
CONFIDENCE_THRESHOLD = 0.6
IOU_THRESHOLD = 0.5
MAX_DETECTIONS = 50
CLASSES = ['Healthy', 'Infected Leaf', 'Disease Part']
COLORS = {
    'Healthy': (0, 255, 0),      # Green
    'Infected Leaf': (255, 165, 0),  # Orange
    'Disease Part': (255, 0, 0)   # Red
}

class LeafDiseaseDetector:
    """Service for detecting mangosteen leaf diseases using YOLOv8."""
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to avoid loading the model multiple times."""
        if cls._instance is None:
            cls._instance = super(LeafDiseaseDetector, cls).__new__(cls)
            cls._instance.model = None
            cls._instance.temp_dir = tempfile.mkdtemp(prefix="leaf_disease_")
            # Create a cleanup method to remove old files
            cls._instance.cleanup_old_files()
        return cls._instance
    
    def load_model(self):
        """Load the YOLOv8 model."""
        if self.model is None:
            # Force garbage collection before loading model
            gc.collect()
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            
            model_path = settings.MODEL_PATH
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found at {model_path}")
            
            try:
                # Load model with task-specific parameters to reduce memory
                self.model = YOLO(model_path, task='detect')
                
                # Set model to evaluation mode and optimize for inference
                if hasattr(self.model, 'model') and hasattr(self.model.model, 'eval'):
                    self.model.model.eval()
                
                # Use half precision if available (reduces memory by ~2x)
                if torch.cuda.is_available():
                    if hasattr(self.model, 'model') and hasattr(self.model.model, 'half'):
                        self.model.model.half()
                
                print(f"Model loaded successfully from {model_path}")
            except Exception as e:
                print(f"Error loading model: {e}")
                # Fallback to loading with weights_only=True
                try:
                    self.model = YOLO(model_path, task='detect')
                    print("Model loaded with fallback method")
                except Exception as fallback_error:
                    raise RuntimeError(f"Failed to load model: {fallback_error}")
        
        return self.model
    
    def cleanup_old_files(self):
        """Clean up temporary files older than 5 minutes."""
        current_time = time.time()
        for file_path in Path(self.temp_dir).glob("*"):
            if current_time - file_path.stat().st_mtime > 300:  # 5 minutes
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error cleaning up {file_path}: {e}")
    
    def save_uploaded_image(self, uploaded_file):
        """Save an uploaded image to a temporary location and return the path."""
        # Generate a unique filename
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(self.temp_dir, filename)
        
        # Save the file
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        return file_path
    
    def predict_image(self, image_path):
        """Make predictions on a single image."""
        # Ensure model is loaded
        if self.model is None:
            self.load_model()
            
        img = cv2.imread(image_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        predictions = self.model.predict(
            source=image_path,
            conf=CONFIDENCE_THRESHOLD,
            iou=IOU_THRESHOLD,
            max_det=MAX_DETECTIONS,
            agnostic_nms=True,
            verbose=False
        )[0]

        """Process predictions."""
        results = {cls: {'count': 0, 'confidences': [], 'avg_confidence': 0.0} for cls in CLASSES}

        # First, collect all Disease Part boxes
        disease_part_boxes = []
        for box in predictions.boxes:
            cls = int(box.cls[0].cpu().numpy())
            class_name = predictions.names[cls]
            if class_name == 'Disease Part':
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                disease_part_boxes.append((x1, y1, x2, y2))

        # Then, collect all Infected Leaf boxes and filter them
        valid_infected_leaf_boxes = []
        for box in predictions.boxes:
            cls = int(box.cls[0].cpu().numpy())
            class_name = predictions.names[cls]
            if class_name == 'Infected Leaf':
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                # Check if this infected leaf contains any disease parts
                has_disease_part = False
                for d_x1, d_y1, d_x2, d_y2 in disease_part_boxes:
                    # Check if disease part box center is inside this infected leaf box
                    disease_center_x = (d_x1 + d_x2) / 2
                    disease_center_y = (d_y1 + d_y2) / 2
                    if (x1 <= disease_center_x <= x2 and y1 <= disease_center_y <= y2):
                        has_disease_part = True
                        break
                if has_disease_part:
                    valid_infected_leaf_boxes.append((x1, y1, x2, y2))

        # Process all detections
        for box in predictions.boxes:
            cls = int(box.cls[0].cpu().numpy())
            conf = float(box.conf[0].cpu().numpy())
            class_name = predictions.names[cls]

            # Apply stricter confidence threshold (0.6) to filter out low-confidence detections
            if conf < CONFIDENCE_THRESHOLD:
                continue

            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

            # Skip Infected Leaf detections that don't contain Disease Parts
            if class_name == 'Infected Leaf':
                box_coords = (x1, y1, x2, y2)
                if box_coords not in valid_infected_leaf_boxes:
                    continue

            # Skip Disease Part detections that are not inside any valid Infected Leaf
            if class_name == 'Disease Part':
                is_inside_infected = False
                for leaf_x1, leaf_y1, leaf_x2, leaf_y2 in valid_infected_leaf_boxes:
                    # Check if disease part box center is inside infected leaf box
                    disease_center_x = (x1 + x2) / 2
                    disease_center_y = (y1 + y2) / 2
                    if (leaf_x1 <= disease_center_x <= leaf_x2 and
                        leaf_y1 <= disease_center_y <= leaf_y2):
                        is_inside_infected = True
                        break
                if not is_inside_infected:
                    continue

            if class_name in results:
                results[class_name]['count'] += 1
                results[class_name]['confidences'].append(conf)

                """Draw bounding box and label on image."""
                cv2.rectangle(img,
                            (int(x1), int(y1)),
                            (int(x2), int(y2)),
                            COLORS[class_name],
                            2)

                label = f'{class_name} {conf:.2%}'
                cv2.putText(img,
                        label,
                        (int(x1), int(y1)-10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        COLORS[class_name],
                        2)

        # After processing all detections, calculate average confidence for each class
        for class_name in CLASSES:
            if results[class_name]['confidences']:
                results[class_name]['avg_confidence'] = sum(results[class_name]['confidences']) / len(results[class_name]['confidences'])

        return img, results
    
    def get_status(self, results):
        """Return the overall status of the leaf based on prediction results."""
        total_detections = results['Healthy']['count'] + results['Infected Leaf']['count'] + results['Disease Part']['count']
        
        if total_detections == 0:
            return "No Detected Leaf"
        elif results['Infected Leaf']['count'] > 0 or results['Disease Part']['count'] > 0:
            return "Infected"
        else:
            return "Healthy"
    
    def save_result_image(self, img, results):
        """Save the annotated image with results and return the file path and base64 data."""
        # Convert numpy array to PIL Image
        pil_img = Image.fromarray(img)
        
        # Optimize image size - resize if too large
        max_dim = 1024
        if max(pil_img.width, pil_img.height) > max_dim:
            if pil_img.width > pil_img.height:
                new_width = max_dim
                new_height = int(pil_img.height * (max_dim / pil_img.width))
            else:
                new_height = max_dim
                new_width = int(pil_img.width * (max_dim / pil_img.height))
            pil_img = pil_img.resize((new_width, new_height), Image.LANCZOS)
        
        # Save to buffer with compression
        buf = io.BytesIO()
        pil_img.save(buf, format='JPEG', quality=85, optimize=True)
        buf.seek(0)
        
        # Generate base64 data
        base64_data = base64.b64encode(buf.getvalue()).decode('utf-8')
        
        # Also save to a temporary file
        result_filename = f"result_{uuid.uuid4()}.jpg"
        result_path = os.path.join(self.temp_dir, result_filename)
        with open(result_path, 'wb') as f:
            f.write(buf.getvalue())
        
        return result_path, base64_data 