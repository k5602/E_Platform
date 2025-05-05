# E_Platform Quick Fix Guide

This guide provides quick solutions for the issues identified in your Nginx setup.

## Issue 1: Daphne Service Not Running

The Daphne service is failing with exit code 2, which typically indicates a command-line error or missing dependency.

### Quick Fix:

```bash
# Run the Daphne fix script
sudo bash nginx/fix_daphne.sh
```

This script will:
1. Install/upgrade Daphne and its dependencies
2. Test if Daphne works with your ASGI application
3. Create a simplified service file
4. Restart the service

## Issue 2: Static Files Not Found

The test is failing to find static files, particularly CSS files.

### Quick Fix:

```bash
# Run the static files collection script
bash nginx/collect_static.sh
```

This script will:
1. Create the staticfiles directory if it doesn't exist
2. Run Django's collectstatic command
3. Set proper permissions
4. Verify that CSS files were collected

## Issue 3: Missing `nc` Command

The test script is failing because the `nc` (netcat) command is not installed.

### Quick Fix:

```bash
# Install netcat
sudo pacman -S openbsd-netcat
```

## Issue 4: HTTP Requests Failing

The test is showing 302 redirects and 404 errors for HTTP requests.

### Quick Fix:

The updated test script now handles 302 redirects properly, as these are expected for login-protected pages. For 404 errors, make sure your Django URLs are configured correctly.

## Complete Fix Sequence

Run these commands in order to fix all issues:

```bash
# 1. Install netcat
sudo pacman -S openbsd-netcat

# 2. Fix Daphne service
sudo bash nginx/fix_daphne.sh

# 3. Collect static files
bash nginx/collect_static.sh

# 4. Restart all services
sudo systemctl restart redis
sudo systemctl restart eplatform-django
sudo systemctl restart eplatform-daphne
sudo systemctl restart nginx

# 5. Run the test script again
sudo bash nginx/test_enhanced.sh
```

## Verifying the Fix

After running the fix sequence, check the status of all services:

```bash
sudo systemctl status nginx
sudo systemctl status eplatform-django
sudo systemctl status eplatform-daphne
sudo systemctl status redis
```

All services should show as "active (running)".

## Still Having Issues?

If you're still experiencing problems after applying these fixes:

1. Check the detailed logs:
   ```bash
   sudo journalctl -u eplatform-daphne -n 50
   sudo tail -f /var/log/eplatform/gunicorn-error.log
   sudo tail -f /var/log/nginx/eplatform_error.log
   ```

2. Verify Redis is working:
   ```bash
   redis-cli ping
   ```
   Should return "PONG"

3. Check if your Django project has the necessary Channels configuration in settings.py:
   ```python
   CHANNEL_LAYERS = {
       'default': {
           'BACKEND': 'channels_redis.core.RedisChannelLayer',
           'CONFIG': {
               'hosts': [('127.0.0.1', 6379)],
           },
       },
   }
   ```
