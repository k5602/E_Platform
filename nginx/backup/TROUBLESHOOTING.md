# E_Platform Nginx Troubleshooting Guide

This guide helps you diagnose and fix common issues with the Nginx reverse proxy setup for E_Platform.

## Table of Contents

1. [Checking Service Status](#checking-service-status)
2. [Viewing Logs](#viewing-logs)
3. [Common Issues](#common-issues)
4. [WebSocket Issues](#websocket-issues)
5. [Static Files Issues](#static-files-issues)
6. [SSL/HTTPS Issues](#sslhttps-issues)
7. [Performance Issues](#performance-issues)

## Checking Service Status

First, check if all required services are running:

```bash
# Check Nginx status
sudo systemctl status nginx

# Check Django service status
sudo systemctl status eplatform-django

# Check Daphne service status
sudo systemctl status eplatform-daphne

# Check Redis status (required for WebSockets)
sudo systemctl status redis
```

If any service is not running, try starting it:

```bash
sudo systemctl start nginx
sudo systemctl start eplatform-django
sudo systemctl start eplatform-daphne
sudo systemctl start redis
```

## Viewing Logs

Check logs to identify specific errors:

### Nginx Logs

```bash
# Main error log
sudo tail -f /var/log/nginx/error.log

# Access log
sudo tail -f /var/log/nginx/access.log

# E_Platform specific logs
sudo tail -f /var/log/nginx/eplatform_access.log
sudo tail -f /var/log/nginx/eplatform_error.log
```

### Django and Daphne Logs

```bash
# Django (Gunicorn) logs
sudo tail -f /var/log/eplatform/gunicorn-access.log
sudo tail -f /var/log/eplatform/gunicorn-error.log

# Daphne logs
sudo tail -f /var/log/eplatform/daphne-access.log

# Systemd service logs
sudo journalctl -u eplatform-django
sudo journalctl -u eplatform-daphne
```

## Common Issues

### 502 Bad Gateway

This usually means Nginx can't connect to the backend services (Django or Daphne).

**Possible causes and solutions:**

1. **Backend service not running**
   - Check if Django and Daphne services are running
   - Start them if needed: `sudo systemctl start eplatform-django eplatform-daphne`

2. **Wrong backend address or port**
   - Verify the `proxy_pass` directives in your Nginx config
   - Make sure Django is running on 127.0.0.1:8000 and Daphne on 127.0.0.1:8001

3. **Firewall blocking connections**
   - Check if firewall is blocking internal connections
   - Allow connections to ports 8000 and 8001: `sudo ufw allow 8000/tcp` and `sudo ufw allow 8001/tcp`

### 404 Not Found

**Possible causes and solutions:**

1. **Wrong URL configuration**
   - Check your Django URLs configuration
   - Verify the location blocks in Nginx config

2. **Static files not found**
   - Make sure you've run `python manage.py collectstatic`
   - Check the path in the `location /static/` block in Nginx config

### Permission Issues

**Possible causes and solutions:**

1. **Log directory permissions**
   - Make sure the log directory exists and has correct permissions:
   ```bash
   sudo mkdir -p /var/log/eplatform
   sudo chmod 755 /var/log/eplatform
   sudo chown http:http /var/log/eplatform
   ```

2. **Static files permissions**
   - Make sure Nginx can read your static files:
   ```bash
   sudo chmod -R 755 /path/to/staticfiles
   ```

## WebSocket Issues

WebSocket connections are more complex and can fail for various reasons:

1. **Connection refused or timeout**
   - Make sure Daphne is running: `sudo systemctl status eplatform-daphne`
   - Check if Redis is running: `sudo systemctl status redis`
   - Verify WebSocket URL in client-side code

2. **WebSocket handshake failing**
   - Check browser console for WebSocket errors
   - Verify the WebSocket configuration in Nginx:
   ```
   proxy_http_version 1.1;
   proxy_set_header Upgrade $http_upgrade;
   proxy_set_header Connection "upgrade";
   ```

3. **CSRF protection issues**
   - Check if CSRF token is being passed in WebSocket URL
   - Verify CSRF middleware in Django settings

4. **Connection closing unexpectedly**
   - Increase timeout values in Nginx config:
   ```
   proxy_read_timeout 86400;
   proxy_send_timeout 86400;
   ```
   - Check for any errors in Daphne logs

## Static Files Issues

1. **Files not found (404)**
   - Run `python manage.py collectstatic`
   - Check the path in Nginx config
   - Verify file permissions

2. **CSS/JS not loading properly**
   - Check browser console for specific errors
   - Verify MIME types in Nginx config
   - Check if files are being compressed correctly

## SSL/HTTPS Issues

1. **SSL certificate errors**
   - Verify certificate and key paths in Nginx config
   - Check certificate validity: `sudo openssl x509 -in /path/to/cert.pem -text -noout`
   - Make sure certificate chain is complete

2. **Mixed content warnings**
   - Update hardcoded HTTP URLs in your application to use HTTPS
   - Use relative URLs where possible
   - Add Content-Security-Policy headers

## Performance Issues

1. **Slow response times**
   - Enable Gzip compression
   - Add caching for static files
   - Increase worker processes in Nginx config
   - Optimize Django and database settings

2. **High CPU or memory usage**
   - Adjust worker processes and connections in Nginx config
   - Limit the number of Gunicorn workers
   - Check for memory leaks in your application

## Advanced Debugging

For more complex issues, you can use these tools:

```bash
# Test Nginx configuration
sudo nginx -t

# Check open ports
sudo netstat -tulpn | grep -E ':(80|443|8000|8001)'

# Check connections to specific port
sudo tcpdump -i lo port 8001

# Monitor system resources
htop
```

If you're still experiencing issues after trying these solutions, please check the Django and Daphne documentation or seek help from the community.
