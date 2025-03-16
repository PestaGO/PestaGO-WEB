import os
import cv2
import numpy as np
import uuid
import tempfile
from django.conf import settings
from ultralytics import YOLO
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import time
from pathlib import Path
import torch

# Check PyTorch version and import add_safe_globals if available
HAS_SAFE_GLOBALS = False
try:
    from torch.serialization import add_safe_globals
    HAS_SAFE_GLOBALS = True
    
    # Add the necessary YOLOv8 classes to the safe globals list
    try:
        from ultralytics.nn.tasks import DetectionModel
        add_safe_globals([DetectionModel])
    except (ImportError, AttributeError):
        # Fallback if the specific class can't be imported
        pass
except ImportError:
    # Using an older version of PyTorch that doesn't have add_safe_globals
    pass

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
            cls._instance._cleanup_old_files()
        return cls._instance
    
    def load_model(self):
        """Load the YOLOv8 model."""
        if self.model is None:
            model_path = settings.MODEL_PATH
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found at {model_path}")
            
            try:
                # For PyTorch < 2.6, this should work directly
                if not HAS_SAFE_GLOBALS:
                    self.model = YOLO(model_path)
                else:
                    # For PyTorch >= 2.6, try with the new approach
                    self.model = YOLO(model_path)
            except Exception as e:
                # Fallback to loading with weights_only=False if needed
                print(f"Error loading model with default settings: {e}")
                print("Attempting to load with weights_only=False...")
                
                # Set environment variable to allow loading with weights_only=False
                os.environ["TORCH_LOAD_WEIGHTS_ONLY"] = "0"
                try:
                    self.model = YOLO(model_path)
                    print("Model loaded successfully with weights_only=False")
                except Exception as fallback_error:
                    raise RuntimeError(f"Failed to load model: {fallback_error}")
                finally:
                    # Reset environment variable
                    os.environ.pop("TORCH_LOAD_WEIGHTS_ONLY", None)
            
            print(f"Model loaded successfully from {model_path}")
        return self.model
    
    def cleanup_old_files(self):
        """Clean up temporary files older than 15 minutes."""
        current_time = time.time()
        for file_path in Path(self.temp_dir).glob("*"):
            if current_time - file_path.stat().st_mtime > 900:  # 15 minutes
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
        """Make predictions on an image and return annotated image with results."""
        # Ensure model is loaded
        self.load_model()
        
        # Read image
        img = cv2.imread(image_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Make prediction
        predictions = self.model.predict(
            source=image_path,
            conf=CONFIDENCE_THRESHOLD,
            iou=IOU_THRESHOLD,
            max_det=MAX_DETECTIONS,
            agnostic_nms=True,
            verbose=False
        )[0]
        
        # Process results
        results = {cls: {'count': 0, 'confidences': []} for cls in CLASSES}
        
        # Draw bounding boxes and collect statistics
        for box in predictions.boxes:
            cls = int(box.cls[0].cpu().numpy())
            conf = float(box.conf[0].cpu().numpy())
            class_name = predictions.names[cls]
            
            # Additional confidence check (redundant with model prediction conf but kept for consistency)
            if conf < CONFIDENCE_THRESHOLD:
                continue
                
            if class_name in results:
                results[class_name]['count'] += 1
                results[class_name]['confidences'].append(conf)
                
                # Draw bounding box
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                cv2.rectangle(img,
                            (int(x1), int(y1)),
                            (int(x2), int(y2)),
                            COLORS[class_name],
                            2)
                
                # Draw label
                label = f'{class_name} {conf:.2%}'
                cv2.putText(img,
                        label,
                        (int(x1), int(y1)-10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        COLORS[class_name],
                        2)
        
        # Calculate average confidences
        for class_name, data in results.items():
            if data['count'] > 0:
                data['avg_confidence'] = sum(data['confidences']) / data['count']
            else:
                data['avg_confidence'] = 0.0
        
        return img, results
    
    def get_status(self, results):
        """Return the overall status of the leaf based on prediction results."""
        if results['Infected Leaf']['count'] > 0 or results['Disease Part']['count'] > 0:
            return "Infected"
        return "Healthy"
    
    def save_result_image(self, img, results):
        """Save the annotated image with results and return the file path and base64 data."""
        # Convert numpy array to PIL Image
        pil_img = Image.fromarray(img)
        
        # Save to buffer for base64 encoding
        buf = io.BytesIO()
        pil_img.save(buf, format='PNG')
        buf.seek(0)
        
        # Generate base64 data
        base64_data = base64.b64encode(buf.getvalue()).decode('utf-8')
        
        # Also save to a temporary file
        result_filename = f"result_{uuid.uuid4()}.png"
        result_path = os.path.join(self.temp_dir, result_filename)
        with open(result_path, 'wb') as f:
            f.write(buf.getvalue())
        
        return result_path, base64_data 