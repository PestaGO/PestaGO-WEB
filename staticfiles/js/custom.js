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
});

// jQuery functionality (from base.html)
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
        img.addEventListener('click', function() {
            // For the imageZoomModal (used in base.html)
            if (document.getElementById('imageZoomModal')) {
                const modal = new bootstrap.Modal(document.getElementById('imageZoomModal'));
                document.getElementById('zoomedImage').src = this.src;
                modal.show();
            }
            
            // For the imageModal (used in prediction_detail.html)
            if (document.getElementById('imageModal')) {
                const imgSrc = this.getAttribute('src');
                document.getElementById('modalImage').setAttribute('src', imgSrc);
                const modal = new bootstrap.Modal(document.getElementById('imageModal'));
                modal.show();
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