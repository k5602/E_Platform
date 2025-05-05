# E_Platform Simplified Nginx Deployment

This directory contains simplified scripts for deploying and managing the E_Platform with Nginx as a reverse proxy.

## Overview

The E_Platform uses Nginx as a reverse proxy to route traffic to:
- Django/Gunicorn for HTTP requests (port 8000)
- Daphne for WebSocket connections (port 8001)
- Static and media files served directly by Nginx

## Simplified Scripts

We've consolidated the numerous scripts into just two main scripts:

1. **deploy.sh** - Unified deployment script that:
   - Detects your local network IP address
   - Configures Nginx as a reverse proxy
   - Sets up systemd services for Django and Daphne
   - Collects static files
   - Configures firewall rules
   - Starts all services

2. **test_fix.sh** - Combined testing and fixing script that:
   - Tests HTTP and WebSocket connections
   - Checks service status
   - Examines logs for errors
   - Fixes common issues automatically
   - Provides detailed diagnostics

## Usage

### Deployment

To deploy E_Platform with Nginx:

```bash
# Deploy with automatic IP detection
sudo bash nginx/deploy.sh

# Deploy with a specific IP address
sudo bash nginx/deploy.sh --ip 192.168.1.100
```

### Testing and Fixing

To test your deployment and fix common issues:

```bash
# Run tests and fix issues
sudo bash nginx/test_fix.sh

# Run tests only (no fixes)
sudo bash nginx/test_fix.sh --test-only

# Skip tests and go straight to fixing
sudo bash nginx/test_fix.sh --fix-only
```

## Network Access

After deployment, your E_Platform will be accessible at:
- Local access: http://localhost
- Network access: http://YOUR_IP_ADDRESS
- WebSocket test page: http://YOUR_IP_ADDRESS/static/websocket_test.html

## Troubleshooting

If you encounter issues:

1. Run the test_fix.sh script to diagnose and fix common problems
2. Check the service logs:
   - Nginx: `journalctl -u nginx`
   - Django: `journalctl -u eplatform-django`
   - Daphne: `journalctl -u eplatform-daphne`
   - Redis: `journalctl -u redis`
3. Verify that ports 80, 8000, and 8001 are not being used by other services

## Notes

- These scripts require root privileges (sudo)
- The deployment is configured for local network use
- For production deployment, you should enable HTTPS by uncommenting and configuring the SSL section in the Nginx configuration
