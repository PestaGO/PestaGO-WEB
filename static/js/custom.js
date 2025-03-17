// Custom JavaScript for Mangosteen Leaf Disease Detection

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Add smooth scrolling to all links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Ensure logo container is visible on page load
    showSection('logo-container');
    
    // Prevent zooming on double tap for mobile
    document.addEventListener('dblclick', function(e) {
        e.preventDefault();
    }, { passive: false });
    
    // Set active navigation item
    function setActiveNavItem(itemId) {
        document.querySelectorAll('.mobile-nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.getElementById(itemId).classList.add('active');
    }
    
    // Show section and hide others
    function showSection(sectionId) {
        // Hide all sections
        const sections = ['logo-container', 'gallery-section', 'about-section', 'camera-section'];
        sections.forEach(section => {
            const element = document.getElementById(section);
            if (element) {
                element.style.display = 'none';
            }
        });
        
        // Show the selected section
        const selectedSection = document.getElementById(sectionId);
        if (selectedSection) {
            selectedSection.style.display = 'block';
        }
        
        // Ensure the logo container is completely hidden when showing other sections
        if (sectionId !== 'logo-container') {
            const logoContainer = document.getElementById('logo-container');
            if (logoContainer) {
                logoContainer.style.display = 'none';
                logoContainer.style.visibility = 'hidden';
                logoContainer.style.position = 'absolute';
                logoContainer.style.zIndex = '-1';
            }
        }
    }
    
    // Camera and image handling functionality
    const logoContainer = document.getElementById('logo-container');
    const gallerySection = document.getElementById('gallery-section');
    const aboutSection = document.getElementById('about-section');
    const cameraSection = document.getElementById('camera-section');
    const cameraPreview = document.getElementById('camera-preview');
    const cameraCanvas = document.getElementById('camera-canvas');
    const captureBtn = document.getElementById('capture-btn');
    const retakeBtn = document.getElementById('retake-btn');
    const cameraImageData = document.getElementById('camera-image-data');
    const previewContainer = document.getElementById('preview-container');
    const previewImage = document.getElementById('preview-image');
    const imageUpload = document.getElementById('image-upload');
    const predictionForm = document.getElementById('prediction-form');
    const loadingSpinner = document.getElementById('loading-spinner');
    const submitBtn = document.getElementById('submit-btn');
    const submitContainer = document.getElementById('submit-container');
    
    let stream = null;
    let hasCapture = false;
    
    // Camera button click handler
    const cameraBtn = document.getElementById('camera-btn');
    if (cameraBtn) {
        cameraBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            if (gallerySection) {
                // Show gallery section (which contains the camera area)
                showSection('gallery-section');
                
                // Show camera section
                document.getElementById('camera-section').style.display = 'block';
                previewContainer.style.display = 'none';
                
                // Start camera
                startCamera();
            } else {
                // Navigate to home page if we're not already there
                window.location.href = homeUrl + "#camera-section";
            }
            
            // Update active state
            setActiveNavItem('camera-btn');
        });
    }
    
    // Gallery button click handler
    const galleryBtn = document.getElementById('gallery-btn');
    if (galleryBtn) {
        galleryBtn.addEventListener('click', function(e) {
            // If we're not on the home page, let the default navigation happen
            if (window.location.pathname !== '/') {
                return;
            }
            
            e.preventDefault();
            
            // Don't show gallery section yet - wait for image selection
            // Instead, just trigger file input click
            const fileInput = document.getElementById('image-upload');
            if (fileInput) {
                fileInput.click();
            }
            
            // Update active state
            setActiveNavItem('gallery-btn');
        });
    }
    
    // About button click handler
    const aboutBtn = document.getElementById('about-btn');
    if (aboutBtn) {
        aboutBtn.addEventListener('click', function(e) {
            // If we're not on the home page, let the default navigation happen
            if (window.location.pathname !== '/') {
                return;
            }
            
            e.preventDefault();
            
            // Show about section
            showSection('about-section');
            
            // Update active state
            setActiveNavItem('about-btn');
        });
    }
    
    // Image upload change handler
    if (imageUpload) {
        imageUpload.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    // Show gallery section
                    showSection('gallery-section');
                    
                    // Hide camera section, show preview
                    if (cameraSection) cameraSection.style.display = 'none';
                    previewImage.src = e.target.result;
                    previewContainer.style.display = 'block';
                    submitContainer.style.display = 'block';
                    
                    // Reset camera data
                    cameraImageData.value = '';
                    hasCapture = false;
                    
                    // Update active state
                    setActiveNavItem('gallery-btn');
                };
                
                reader.readAsDataURL(this.files[0]);
            } else {
                // User canceled file selection
                // Keep showing the logo container
                showSection('logo-container');
            }
        });
    }
    
    // Start camera
    function startCamera() {
        if (!cameraPreview) return;
        
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            navigator.mediaDevices.getUserMedia({ 
                video: { 
                    facingMode: { ideal: 'environment' },
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                } 
            })
            .then(function(mediaStream) {
                stream = mediaStream;
                cameraPreview.srcObject = mediaStream;
                cameraPreview.style.display = 'block';
                cameraCanvas.style.display = 'none';
                captureBtn.style.display = 'inline-block';
                retakeBtn.style.display = 'none';
                submitContainer.style.display = 'none';
                cameraPreview.play();
            })
            .catch(function(error) {
                console.error('Error accessing camera:', error);
                alert('Unable to access camera. Please check permissions or try uploading an image instead.');
            });
        } else {
            alert('Your browser does not support camera access. Please try uploading an image instead.');
        }
    }
    
    // Stop camera
    function stopCamera() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
        }
        if (cameraPreview) cameraPreview.style.display = 'none';
    }
    
    // Capture photo
    if (captureBtn) {
        captureBtn.addEventListener('click', function() {
            if (stream) {
                const context = cameraCanvas.getContext('2d');
                
                // Set canvas dimensions to match video
                cameraCanvas.width = cameraPreview.videoWidth;
                cameraCanvas.height = cameraPreview.videoHeight;
                
                // Draw video frame to canvas
                context.drawImage(cameraPreview, 0, 0, cameraCanvas.width, cameraCanvas.height);
                
                // Convert canvas to data URL
                const imageData = cameraCanvas.toDataURL('image/jpeg', 0.9);
                cameraImageData.value = imageData;
                
                // Show canvas with captured image
                cameraPreview.style.display = 'none';
                cameraCanvas.style.display = 'block';
                captureBtn.style.display = 'none';
                retakeBtn.style.display = 'inline-block';
                submitContainer.style.display = 'block';
                
                hasCapture = true;
            }
        });
    }
    
    // Retake photo
    if (retakeBtn) {
        retakeBtn.addEventListener('click', function() {
            cameraPreview.style.display = 'block';
            cameraCanvas.style.display = 'none';
            captureBtn.style.display = 'inline-block';
            retakeBtn.style.display = 'none';
            submitContainer.style.display = 'none';
            cameraImageData.value = '';
            hasCapture = false;
        });
    }
    
    // Form submission
    if (predictionForm) {
        predictionForm.addEventListener('submit', function(e) {
            // Check if we have either a file upload or camera capture
            if (!imageUpload.files.length && !hasCapture) {
                e.preventDefault();
                alert('Please upload an image or take a photo first.');
                return false;
            }
            
            // Show loading spinner
            loadingSpinner.style.display = 'block';
            submitBtn.disabled = true;
            
            // If using camera, we need to stop it
            stopCamera();
            
            return true;
        });
    }
});

// jQuery functionality
$(document).ready(function() {
    // Add animation class to cards
    $('.card').addClass('animate-fade-in');

    // Make upload area smaller when image is selected
    $('#image-upload').change(function() {
        const file = this.files[0];
        if (file) {
            // Shrink the upload area
            $('#upload-area').addClass('upload-area-small');
            $('#upload-area h4').text('Change Image');
            $('#upload-area p').hide();
            $('#upload-area .upload-icon').addClass('upload-icon-small');
            
            // Preview the image
            const reader = new FileReader();
            reader.onload = function(e) {
                $('#preview-container').html('<img src="' + e.target.result + '" class="img-fluid rounded" />');
                $('#preview-container').show();
            }
            reader.readAsDataURL(file);
        }
    });
    
    // Form submission with AJAX
    $('#prediction-form').submit(function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        
        // Show loading spinner
        $('#loading-spinner').show();
        $('#submit-btn').prop('disabled', true);
        
        $.ajax({
            url: $(this).attr('action'),
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            success: function(response) {
                if (response.success) {
                    window.location.href = response.redirect_url;
                } else {
                    showToast('Error', response.error, 'danger');
                    $('#error-message').text(response.error).show();
                    $('#loading-spinner').hide();
                    $('#submit-btn').prop('disabled', false);
                }
            },
            error: function(xhr, status, error) {
                showToast('Error', 'An error occurred. Please try again.', 'danger');
                $('#error-message').text('An error occurred. Please try again.').show();
                $('#loading-spinner').hide();
                $('#submit-btn').prop('disabled', false);
            }
        });
    });
    
    // Image zoom functionality for result images
    const resultImages = document.querySelectorAll('.result-image');
    resultImages.forEach(img => {
        // Remove any existing click listeners first
        img.replaceWith(img.cloneNode(true));
    });
    
    // Re-select the images after replacing them (to clear event listeners)
    document.querySelectorAll('.result-image').forEach(img => {
        img.addEventListener('click', function() {
            if (document.getElementById('imageZoomModal')) {
                const zoomedImage = document.getElementById('zoomedImage');
                zoomedImage.src = this.src;
                
                const modalElement = document.getElementById('imageZoomModal');
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
                
                // Clean up when modal is hidden
                $(modalElement).one('hidden.bs.modal', function() {
                    zoomedImage.src = '';
                });
            }
        });
    });
    
    // Copy to clipboard functionality
    const copyButtons = document.querySelectorAll('.btn-copy');
    copyButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const textToCopy = this.getAttribute('data-copy-text');
            if (!textToCopy) return;
            
            navigator.clipboard.writeText(textToCopy).then(() => {
                // Show success message
                if (window.showToast) {
                    window.showToast('Success', 'Copied to clipboard!', 'success');
                }
            }).catch(err => {
                console.error('Failed to copy text: ', err);
                if (window.showToast) {
                    window.showToast('Error', 'Failed to copy to clipboard', 'danger');
                }
            });
        });
    });
    
    // Drag and drop functionality
    const uploadArea = document.getElementById('upload-area');
    if (uploadArea) {
        const fileInput = document.getElementById('image-upload');
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight() {
            uploadArea.classList.add('border-primary');
        }
        
        function unhighlight() {
            uploadArea.classList.remove('border-primary');
        }
        
        uploadArea.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            fileInput.files = files;
            
            // Trigger change event
            const event = new Event('change');
            fileInput.dispatchEvent(event);
        }
    }
    
    // Form validation enhancement
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // Dark mode toggle
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        // Check for saved theme preference or use preferred color scheme
        const savedTheme = localStorage.getItem('theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
            document.body.classList.add('dark-mode');
            darkModeToggle.checked = true;
        }
        
        // Toggle dark mode
        darkModeToggle.addEventListener('change', function() {
            if (this.checked) {
                document.body.classList.add('dark-mode');
                localStorage.setItem('theme', 'dark');
            } else {
                document.body.classList.remove('dark-mode');
                localStorage.setItem('theme', 'light');
            }
        });
    }
});

// Toast notification function (global)
window.showToast = function(title, message, type) {
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <strong>${title}:</strong> ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '1050';
        document.body.appendChild(container);
    }
    
    $('#toast-container').append(toastHtml);
    const toastElement = $('.toast').last();
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 5000
    });
    toast.show();
}; 