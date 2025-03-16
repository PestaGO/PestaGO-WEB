from django.shortcuts import render, redirect
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os
import json
import uuid
import time
from datetime import datetime

from .services import LeafDiseaseDetector

def home(request):
    """Home page view."""
    # Clear any previous prediction data from session
    if 'prediction_results' in request.session:
        del request.session['prediction_results']
    
    return render(request, 'app/home.html')

@csrf_exempt
def predict(request):
    """Handle image prediction."""
    if request.method == 'POST':
        if 'image' not in request.FILES:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': "No image file uploaded.",
                })
            return render(request, 'app/home.html', {
                'error': "No image file uploaded.",
            })
        
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
        
        try:
            # Initialize detector and save uploaded image
            detector = LeafDiseaseDetector()
            image_path = detector.save_uploaded_image(uploaded_file)
            
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
                    'redirect_url': '/prediction_detail/',
                    'status': status,
                    'healthy_count': results['Healthy']['count'],
                    'infected_leaf_count': results['Infected Leaf']['count'],
                    'disease_part_count': results['Disease Part']['count'],
                })
            
            # Redirect to result page for regular form submissions
            return redirect('prediction_detail')
            
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

def prediction_detail(request):
    """Display detailed prediction results."""
    # Get prediction results from session
    prediction_results = request.session.get('prediction_results')
    
    if not prediction_results:
        return redirect('home')
    
    return render(request, 'app/prediction_detail.html', {
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

def about(request):
    """About page view."""
    return render(request, 'app/about.html')
