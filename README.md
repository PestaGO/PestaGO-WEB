# Mangosteen Leaf Disease Detection

An AI-powered web application for detecting diseases in mangosteen leaves using YOLOv8.

## Features

- **AI-Powered Detection**: Utilizes YOLOv8, a state-of-the-art object detection model, to identify healthy leaves, infected leaves, and disease parts.
- **User-Friendly Interface**: Simple drag-and-drop interface for uploading images.
- **Detailed Analysis**: Provides comprehensive results including detection visualizations and statistics.
- **Responsive Design**: Works on desktop and mobile devices.
- **No Database Required**: Processes images on-the-fly without storing data.

## Technology Stack

- **Backend**: Django (Python web framework)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **AI Model**: YOLOv8 (Ultralytics)
- **Image Processing**: OpenCV, PIL

## Installation

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/mangosteen-leaf-disease-detection.git
   cd mangosteen-leaf-disease-detection
   ```

2. Create a virtual environment:
   ```bash
   python -m venv env
   ```

3. Activate the virtual environment:
   - On Windows:
     ```bash
     env\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source env/bin/activate
     ```

4. Run the setup script:
   ```bash
   python setup.py
   ```
   
   This script will:
   - Create necessary directories
   - Copy model weights (if available)
   - Install dependencies
   - Collect static files
   - Optionally start the development server

5. If you didn't start the server through the setup script, run:
   ```bash
   python manage.py runserver
   ```

6. Access the application at `http://127.0.0.1:8000/`

## Usage

1. **Upload an Image**: Drag and drop or click to upload a mangosteen leaf image.
2. **View Results**: After processing, the application will display:
   - The original image with bounding boxes around detected objects
   - Detection statistics (healthy leaves, infected leaves, disease parts)
   - Overall status and recommendations

## Model Information

The YOLOv8 model was trained on a dataset of mangosteen leaf images with three classes:
- Healthy leaf
- Infected leaf
- Disease part

The model achieves high accuracy in detecting these classes, with metrics:
- mAP50: 0.987
- mAP50-95: 0.960

## Deployment

For production deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Project Structure

```
mangosteen-leaf-disease-detection/
├── app/                    # Django application
├── main/                   # Django project settings
├── media/                  # Media files (temporary uploads)
├── model_weights/          # YOLOv8 model weights
├── static/                 # Static files (CSS, JS)
├── templates/              # HTML templates
├── .env.example            # Example environment variables
├── DEPLOYMENT.md           # Deployment guide
├── manage.py               # Django management script
├── README.md               # This file
└── requirements.txt        # Python dependencies
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) for the object detection model
- [Django](https://www.djangoproject.com/) for the web framework
- [Bootstrap](https://getbootstrap.com/) for the frontend components 