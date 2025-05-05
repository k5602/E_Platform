# E_Platform Common Troubleshooting Guide

This guide addresses common issues encountered when setting up Nginx as a reverse proxy for E_Platform.

## Issue: Daphne Service Not Running

**Symptoms:**
- WebSocket connections fail
- Test script shows "eplatform-daphne is not running"
- WebSocket-dependent features don't work

**Solutions:**

1. **Run the fix script:**
   ```bash
   sudo bash nginx/fix_daphne.sh
   ```

2. **Manual checks:**
   ```bash
   # Check service status
   sudo systemctl status eplatform-daphne
   
   # Check logs
   sudo journalctl -u eplatform-daphne -n 50
   
   # Verify Daphne is installed
   source .venv/bin/activate
   which daphne
   
   # Install if missing
   pip install daphne
   ```

3. **Common causes:**
   - Redis not running (required for Channels)
   - Permission issues with log files
   - Missing Daphne package
   - ASGI configuration errors

## Issue: Static Files Not Found

**Symptoms:**
- 404 errors for CSS, JS, or image files
- Unstyled pages
- Error logs showing "No such file or directory" for static files

**Solutions:**

1. **Run the collect static script:**
   ```bash
   bash nginx/collect_static.sh
   ```

2. **Manual collection:**
   ```bash
   cd /mnt/4BC9EBFC28ECC8F5/Others/Projects/E_Platform
   source .venv/bin/activate
   python manage.py collectstatic --noinput
   ```

3. **Check paths:**
   - Verify the `staticfiles` directory exists
   - Check Nginx configuration for correct static file path
   - Ensure permissions are set correctly

4. **Verify STATIC_ROOT in settings.py:**
   ```python
   STATIC_ROOT = BASE_DIR / 'staticfiles'
   ```

## Issue: HTTP Requests Failing

**Symptoms:**
- 302 redirects when expecting 200 responses
- 404 errors for API endpoints
- Test script showing HTTP request failures

**Solutions:**

1. **For 302 redirects:**
   - This is normal for pages that require login
   - Update test script to follow redirects or expect 302 for protected pages
   - Try accessing with authenticated session

2. **For 404 errors:**
   - Check URL patterns in Django settings
   - Verify API endpoints exist and are correctly configured
   - Check for typos in URLs

3. **Check Django logs:**
   ```bash
   sudo tail -f /var/log/eplatform/gunicorn-error.log
   ```

## Issue: Missing `nc` Command

**Symptoms:**
- Test script shows "nc: command not found"
- Port checking fails

**Solutions:**

1. **Install netcat:**
   ```bash
   # Arch Linux
   sudo pacman -S openbsd-netcat
   
   # Ubuntu/Debian
   sudo apt install netcat-openbsd
   
   # Fedora/RHEL
   sudo dnf install nc
   ```

2. **Alternative:**
   - The updated test script includes a fallback method using /dev/tcp
   - No action needed if using the updated script

## Issue: Django/Gunicorn Workers Exiting

**Symptoms:**
- Logs showing "Worker exited with code 1"
- Application crashes or restarts frequently
- 500 errors in browser

**Solutions:**

1. **Check detailed logs:**
   ```bash
   sudo tail -n 100 /var/log/eplatform/gunicorn-error.log
   ```

2. **Common causes:**
   - Database connection issues
   - Import errors in Django code
   - Memory issues
   - Permission problems

3. **Increase worker timeout:**
   Edit `nginx/eplatform-django-enhanced.service`:
   ```
   ExecStart=... --timeout 180 ...
   ```

4. **Restart the service:**
   ```bash
   sudo systemctl restart eplatform-django
   ```

## Issue: Redis Connection Problems

**Symptoms:**
- WebSocket connections fail
- Daphne service fails to start
- Logs showing Redis connection errors

**Solutions:**

1. **Check Redis status:**
   ```bash
   sudo systemctl status redis
   ```

2. **Start Redis if not running:**
   ```bash
   sudo systemctl start redis
   ```

3. **Verify Redis configuration:**
   ```bash
   # Check if Redis is listening
   ss -tlnp | grep 6379
   
   # Test Redis connection
   redis-cli ping
   ```

4. **Check Django Channels configuration:**
   Verify `CHANNEL_LAYERS` in `settings.py` points to the correct Redis instance.

## Issue: Permission Problems

**Symptoms:**
- "Permission denied" errors in logs
- Services fail to start
- Can't write to log files

**Solutions:**

1. **Fix log directory permissions:**
   ```bash
   sudo mkdir -p /var/log/eplatform
   sudo chown -R zero:zero /var/log/eplatform
   sudo chmod 755 /var/log/eplatform
   ```

2. **Fix project directory permissions:**
   ```bash
   sudo chown -R zero:zero /mnt/4BC9EBFC28ECC8F5/Others/Projects/E_Platform
   ```

3. **Check systemd service user:**
   Ensure the User and Group in service files match your system user.

## Running All Fixes

To address multiple issues at once, run these commands in order:

```bash
# 1. Install netcat
sudo pacman -S openbsd-netcat

# 2. Collect static files
bash nginx/collect_static.sh

# 3. Fix Daphne service
sudo bash nginx/fix_daphne.sh

# 4. Restart all services
sudo systemctl restart redis
sudo systemctl restart eplatform-django
sudo systemctl restart eplatform-daphne
sudo systemctl restart nginx

# 5. Run the test script again
sudo bash nginx/test_enhanced.sh
```

If you continue to experience issues, please check the detailed logs and refer to the main troubleshooting guide.
