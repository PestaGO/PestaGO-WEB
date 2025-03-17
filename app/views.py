from django.shortcuts import render, redirect
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os
import json
import uuid
import time
import base64
import re
from datetime import datetime

from .services import LeafDiseaseDetector

def home(request):
    """Home page view with logo, navigation buttons, and about section."""
    # Clear any previous prediction data from session
    if 'prediction_results' in request.session:
        del request.session['prediction_results']
    
    return render(request, 'app/home.html')

@csrf_exempt
def predict(request):
    """Handle image prediction.
    
    Note: Disease Part detections are only considered valid if they are located
    inside an Infected Leaf bounding box. This ensures more accurate disease
    detection by eliminating false positives outside of infected areas.
    """
    if request.method == 'POST':
        # Check if we have a file upload or camera capture
        has_file = 'image' in request.FILES
        has_camera_image = request.POST.get('camera_image', '').strip()
        
        if not has_file and not has_camera_image:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': "No image provided. Please upload an image or take a photo.",
                })
            return render(request, 'app/home.html', {
                'error': "No image provided. Please upload an image or take a photo.",
            })
        
        try:
            # Initialize detector
            detector = LeafDiseaseDetector()
            
            if has_file:
                # Process uploaded file
                uploaded_file = request.FILES['image']
                
                # Validate file type
                valid_extensions = ['.jpg', '.jpeg', '.png']
                ext = os.path.splitext(uploaded_file.name)[1].lower()
                if ext not in valid_extensions:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': f"Unsupported file format. Please upload a {', '.join(valid_extensions)} file.",
                        })
                    return render(request, 'app/home.html', {
                        'error': f"Unsupported file format. Please upload a {', '.join(valid_extensions)} file.",
                    })
                
                # Validate file size (limit to 10MB)
                if uploaded_file.size > 10 * 1024 * 1024:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': "The image file is too large. Please upload an image smaller than 10MB.",
                        })
                    return render(request, 'app/home.html', {
                        'error': "The image file is too large. Please upload an image smaller than 10MB.",
                    })
                
                # Save uploaded image
                image_path = detector.save_uploaded_image(uploaded_file)
            else:
                # Process camera capture
                # Extract the base64 data from the data URL
                camera_image = request.POST.get('camera_image')
                if not camera_image.startswith('data:image'):
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': "Invalid camera image data.",
                        })
                    return render(request, 'app/home.html', {
                        'error': "Invalid camera image data.",
                    })
                
                # Extract the base64 data
                image_data = re.sub('^data:image/.+;base64,', '', camera_image)
                
                # Save the image to a temporary file
                filename = f"{uuid.uuid4()}.jpg"
                image_path = os.path.join(detector.temp_dir, filename)
                
                with open(image_path, 'wb') as f:
                    f.write(base64.b64decode(image_data))
            
            # Make prediction
            img, results = detector.predict_image(image_path)
            
            # Save result image and get base64 data
            result_path, result_base64 = detector.save_result_image(img, results)
            
            # Get overall status
            status = detector.get_status(results)
            
            # Create prediction result dictionary
            prediction_result = {
                'id': str(uuid.uuid4()),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': status,
                'image_path': image_path,
                'result_path': result_path,
                'result_base64': result_base64,
                'healthy_count': results['Healthy']['count'],
                'infected_leaf_count': results['Infected Leaf']['count'],
                'disease_part_count': results['Disease Part']['count'],
                'healthy_confidence': results['Healthy']['avg_confidence'] * 100 if results['Healthy']['count'] > 0 else 0,
                'infected_leaf_confidence': results['Infected Leaf']['avg_confidence'] * 100 if results['Infected Leaf']['count'] > 0 else 0,
                'disease_part_confidence': results['Disease Part']['avg_confidence'] * 100 if results['Disease Part']['count'] > 0 else 0,
            }
            
            # Store in session
            request.session['prediction_results'] = prediction_result
            
            # Return JSON response for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'redirect_url': '/result/',
                    'status': status,
                    'healthy_count': results['Healthy']['count'],
                    'infected_leaf_count': results['Infected Leaf']['count'],
                    'disease_part_count': results['Disease Part']['count'],
                })
            
            # Redirect to result page for regular form submissions
            return redirect('result')
            
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e),
                })
            
            return render(request, 'app/home.html', {
                'error': f"Error processing image: {str(e)}",
            })
    
    # Redirect to home for GET requests
    return redirect('home')

def result(request):
    """Display detailed prediction results."""
    # Get prediction results from session
    prediction_results = request.session.get('prediction_results')
    
    if not prediction_results:
        return redirect('home')
    
    return render(request, 'app/result.html', {
        'prediction': prediction_results,
    })

def serve_image(request, image_type):
    """Serve image files from temporary storage."""
    prediction_results = request.session.get('prediction_results')
    
    if not prediction_results:
        return redirect('home')
    
    if image_type == 'original':
        image_path = prediction_results.get('image_path')
    elif image_type == 'result':
        image_path = prediction_results.get('result_path')
    else:
        return redirect('home')
    
    if not image_path or not os.path.exists(image_path):
        return redirect('home')
    
    return FileResponse(open(image_path, 'rb'))
