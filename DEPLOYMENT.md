# Deployment Guide for Mangosteen Leaf Disease Detection

This guide provides instructions for deploying the Mangosteen Leaf Disease Detection application in a production environment.

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- virtualenv or venv
- Git
- Web server (Nginx or Apache)

## Deployment Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/mangosteen-leaf-disease-detection.git
cd mangosteen-leaf-disease-detection
```

### 2. Set Up Virtual Environment

```bash
python -m venv env
```

Activate the virtual environment:

- On Windows:
  ```bash
  env\Scripts\activate
  ```
- On macOS/Linux:
  ```bash
  source env/bin/activate
  ```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file and edit it with your production settings:

```bash
cp .env.example .env
```

Edit the `.env` file and set the following variables:

```
DEBUG=False
SECRET_KEY=your_secure_secret_key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### 5. Create Sessions Directory

Create a directory to store session files:

```bash
mkdir -p sessions
chmod 700 sessions  # Restrict permissions for security
```

### 6. Copy Model Weights

Ensure the YOLOv8 model weights are in the correct location:

```bash
mkdir -p model_weights
# Copy your trained model weights to this directory
cp /path/to/your/best.pt model_weights/
```

### 7. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 8. Configure Web Server

#### Nginx Configuration Example

Create a new Nginx configuration file:

```bash
sudo nano /etc/nginx/sites-available/mangosteen
```

Add the following configuration:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    
    # Static files
    location /static/ {
        alias /path/to/your/project/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }
    
    # Media files
    location /media/ {
        alias /path/to/your/project/media/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }
    
    # Proxy requests to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the configuration:

```bash
sudo ln -s /etc/nginx/sites-available/mangosteen /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 9. Set Up Gunicorn

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/mangosteen.service
```

Add the following configuration:

```ini
[Unit]
Description=Gunicorn daemon for Mangosteen Leaf Disease Detection
After=network.target

[Service]
User=yourusername
Group=yourusername
WorkingDirectory=/path/to/your/project
ExecStart=/path/to/your/project/env/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 main.wsgi:application
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable mangosteen
sudo systemctl start mangosteen
```

### 10. Set Up SSL Certificate

Use Let's Encrypt to obtain a free SSL certificate:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 11. Monitoring and Maintenance

- Set up regular backups of your media files and session files
- Configure log rotation for application logs
- Set up monitoring for the application and server
- Implement a CI/CD pipeline for automated deployments

## Troubleshooting

### Common Issues

1. **Static files not loading**: Check your STATIC_ROOT and STATICFILES_DIRS settings, and ensure you've run collectstatic.

2. **Permission errors**: Ensure the web server has read access to static files and read/write access to media and sessions directories.

3. **502 Bad Gateway**: Check if Gunicorn is running and listening on the correct port.

## Performance Optimization

- Enable Gzip compression in Nginx
- Use a CDN for static assets
- Implement caching for frequently accessed pages
- Optimize image sizes before upload

## Security Considerations

- Keep all dependencies updated
- Enable HTTPS and configure proper SSL settings
- Implement rate limiting to prevent abuse
- Regularly update your server and application

## Conclusion

Following this guide should result in a secure, production-ready deployment of the Mangosteen Leaf Disease Detection application. For further assistance, refer to the Django deployment documentation or contact the project maintainers.