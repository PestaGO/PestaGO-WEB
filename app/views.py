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
import gc
import torch
from django.core.files.base import ContentFile

from .services import LeafDiseaseDetector

def home(request):
    """Home page view with logo, navigation buttons, and about section."""
    # Clear any previous prediction data from session
    if 'prediction_results' in request.session:
        del request.session['prediction_results']
    
    # Check which section to display based on URL hash or AJAX request
    section = request.GET.get('section', 'home')
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Set the appropriate template based on the section
    if is_ajax:
        if section == 'gallery':
            return render(request, 'app/sections/gallery.html')
        elif section == 'camera':
            return render(request, 'app/sections/camera.html')
        elif section == 'about':
            return render(request, 'app/sections/about.html')
        else:
            return render(request, 'app/sections/home.html')
    
    # For non-AJAX requests, render the full page with all sections
    # The JavaScript will handle showing/hiding sections based on the hash
    context = {
        'active_section': section,
        'cache_timestamp': datetime.now().timestamp()  # For cache busting when needed
    }
    
    return render(request, 'app/base.html', context)

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
            return render(request, 'app/base.html', {
                'error': "No image provided. Please upload an image or take a photo.",
                'active_section': 'gallery'
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
                    return render(request, 'app/base.html', {
                        'error': f"Unsupported file format. Please upload a {', '.join(valid_extensions)} file.",
                        'active_section': 'gallery'
                    })
                
                # Save uploaded image - this will handle any file size
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
                    return render(request, 'app/base.html', {
                        'error': "Invalid camera image data.",
                        'active_section': 'gallery'
                    })
                
                # Extract the base64 data
                image_data = re.sub('^data:image/.+;base64,', '', camera_image)
                
                # Create a temporary file-like object from the base64 data
                image_file = ContentFile(base64.b64decode(image_data), name='camera_capture.jpg')
                
                # Save the image using the same method as gallery uploads
                image_path = detector.save_uploaded_image(image_file)
            
            # Start timer to measure processing time
            start_time = time.time()
            
            # Make prediction
            img, results = detector.predict_image(image_path)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            print(f"Image processing completed in {processing_time:.2f} seconds")
            
            # Save result image and get base64 data
            result_path, result_base64 = detector.save_result_image(img, results)
            
            # Get overall status
            status = detector.get_status(results)
            
            # Create prediction result dictionary - store minimal data
            prediction_result = {
                'id': str(uuid.uuid4()),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': status,
                'image_path': image_path,
                'result_path': result_path,
                # Don't store base64 data in session to reduce memory usage
                'healthy_count': results['Healthy']['count'],
                'infected_leaf_count': results['Infected Leaf']['count'],
                'disease_part_count': results['Disease Part']['count'],
                'healthy_confidence': results['Healthy']['avg_confidence'] * 100 if results['Healthy']['count'] > 0 else 0,
                'infected_leaf_confidence': results['Infected Leaf']['avg_confidence'] * 100 if results['Infected Leaf']['count'] > 0 else 0,
                'disease_part_confidence': results['Disease Part']['avg_confidence'] * 100 if results['Disease Part']['count'] > 0 else 0,
                'processing_time': f"{processing_time:.2f}"
            }
            
            # Store in session
            request.session['prediction_results'] = prediction_result
            
            # Free references to large objects to help garbage collection
            img = None
            results = None
            
            # Clean up memory
            gc.collect()
            if hasattr(torch, 'cuda') and torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Return JSON response for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'redirect_url': '/result/',
                    'status': status,
                    'healthy_count': prediction_result['healthy_count'],
                    'infected_leaf_count': prediction_result['infected_leaf_count'],
                    'disease_part_count': prediction_result['disease_part_count'],
                    'processing_time': prediction_result['processing_time']
                })
            
            # Redirect to result page for regular form submissions
            return redirect('result')
            
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e),
                })
            
            return render(request, 'app/base.html', {
                'error': f"Error processing image: {str(e)}",
                'active_section': 'gallery'
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
        'active_section': None  # Explicitly set no active section for result page
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
