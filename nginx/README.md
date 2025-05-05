# E_Platform Nginx Reverse Proxy Setup

This directory contains configuration files and scripts to set up Nginx as a reverse proxy for the E_Platform application, replacing the dual server architecture (Django-Daphne) with a single entry point.

## Files

- `eplatform.conf` - Nginx server configuration
- `eplatform-django.service` - Systemd service for Django
- `eplatform-daphne.service` - Systemd service for Daphne
- `deploy_nginx.sh` - Deployment script
- `test_setup.sh` - Testing script

## Prerequisites

- Arch Linux
- Nginx installed (`sudo pacman -S nginx`)
- Python virtual environment with Django, Daphne, and Gunicorn installed
- Redis server for Channels (already part of your setup)

## Setup Instructions

1. **Edit Configuration Files**

   Before deployment, edit the following files to match your environment:

   - `eplatform-django.service`: Update user, group, and paths
   - `eplatform-daphne.service`: Update user, group, and paths
   - `eplatform.conf`: Update server_name and paths

2. **Deploy the Configuration**

   Run the deployment script as root:

   ```bash
   sudo bash deploy_nginx.sh
   ```

3. **Test the Setup**

   Run the test script:

   ```bash
   sudo bash test_setup.sh
   ```

4. **Manual Testing**

   - Open your browser and navigate to your domain
   - Check if static files are loading
   - Test the chat functionality to verify WebSocket connections
   - Check browser console for any WebSocket errors

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failures**

   - Check Nginx error logs: `sudo tail -f /var/log/nginx/eplatform_error.log`
   - Verify Daphne is running: `systemctl status eplatform-daphne.service`
   - Ensure WebSocket path is correct in Nginx config

2. **Static Files Not Loading**

   - Check file permissions
   - Verify paths in Nginx configuration
   - Run `collectstatic` if needed: `python manage.py collectstatic`

3. **502 Bad Gateway**

   - Check if backend services are running
   - Verify ports in Nginx configuration match service ports

## Security Considerations

- Enable HTTPS by uncommenting the HTTPS server block and configuring SSL certificates
- Consider using Let's Encrypt for free SSL certificates
- Implement rate limiting for sensitive endpoints
- Set up proper firewall rules

## Performance Tuning

- Enable Nginx caching for static assets
- Configure worker processes based on CPU cores
- Adjust buffer sizes for optimal performance
- Consider using HTTP/2 for improved performance (requires HTTPS)

## Maintenance

- Regularly check logs for errors
- Update SSL certificates before they expire
- Monitor resource usage and adjust configuration as needed
