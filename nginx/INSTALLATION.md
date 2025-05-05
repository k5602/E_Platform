# E_Platform Nginx Installation Guide

This guide provides step-by-step instructions for setting up Nginx as a reverse proxy for E_Platform, replacing the dual server architecture with a single entry point.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Steps](#installation-steps)
3. [Manual Installation](#manual-installation)
4. [Testing the Setup](#testing-the-setup)
5. [Securing Your Installation](#securing-your-installation)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

Before you begin, make sure you have:

- A Linux server (this guide is tested on Arch Linux, but should work on Ubuntu/Debian with minor adjustments)
- Root or sudo access
- E_Platform codebase installed and working with the dual-server setup
- Python virtual environment with all dependencies installed
- PostgreSQL database configured (if using PostgreSQL)
- Redis server installed (required for Django Channels)

Required packages:
- Nginx
- Redis
- Python packages: Django, Channels, Daphne, Gunicorn

## Installation Steps

### 1. Automated Installation

The easiest way to install is using the provided deployment script:

```bash
# Navigate to your project directory
cd /mnt/4BC9EBFC28ECC8F5/Others/Projects/E_Platform

# Make the script executable
chmod +x nginx/deploy_complete.sh

# Run the deployment script as root
sudo bash nginx/deploy_complete.sh
```

The script will:
- Install required packages (Nginx, Redis)
- Create necessary directories
- Copy configuration files
- Set up systemd services
- Start all required services
- Test the configuration

### 2. Verify Installation

After running the deployment script, verify that everything is working:

```bash
# Run the test script
bash nginx/test_complete.sh
```

This will check if all services are running and if the basic functionality is working.

## Manual Installation

If you prefer to install manually or the automated script doesn't work for your environment, follow these steps:

### 1. Install Required Packages

```bash
# Arch Linux
sudo pacman -Sy nginx redis

# Ubuntu/Debian
sudo apt update
sudo apt install nginx redis-server

# Fedora/RHEL
sudo dnf install nginx redis
```

### 2. Create Directories

```bash
# Create log directory
sudo mkdir -p /var/log/eplatform
sudo chmod 755 /var/log/eplatform
sudo chown http:http /var/log/eplatform  # Use www-data:www-data on Ubuntu/Debian
```

### 3. Copy Configuration Files

```bash
# Copy Nginx configuration
sudo cp nginx/nginx.conf /etc/nginx/nginx.conf
sudo cp nginx/eplatform_complete.conf /etc/nginx/sites-available/eplatform.conf

# Create symbolic link to enable the site
sudo mkdir -p /etc/nginx/sites-enabled
sudo ln -sf /etc/nginx/sites-available/eplatform.conf /etc/nginx/sites-enabled/eplatform.conf
```

### 4. Set Up Systemd Services

```bash
# Copy service files
sudo cp nginx/eplatform-django-service.conf /etc/systemd/system/eplatform-django.service
sudo cp nginx/eplatform-daphne-service.conf /etc/systemd/system/eplatform-daphne.service

# Reload systemd
sudo systemctl daemon-reload
```

### 5. Start Services

```bash
# Enable and start Redis
sudo systemctl enable redis
sudo systemctl start redis

# Enable and start Django and Daphne services
sudo systemctl enable eplatform-django
sudo systemctl enable eplatform-daphne
sudo systemctl start eplatform-django
sudo systemctl start eplatform-daphne

# Test Nginx configuration
sudo nginx -t

# Start Nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

## Testing the Setup

### 1. Basic Tests

Run the test script to perform basic tests:

```bash
bash nginx/test_complete.sh
```

### 2. Manual Testing

For a more thorough test:

1. Open your browser and navigate to your domain or IP address
2. Try logging in to the application
3. Test the chat functionality to verify WebSocket connections
4. Check if static files (CSS, JS, images) are loading correctly
5. Test the admin interface at `/admin/`

### 3. Check Logs for Errors

```bash
# Nginx error log
sudo tail -f /var/log/nginx/error.log

# Application-specific logs
sudo tail -f /var/log/eplatform/gunicorn-error.log
sudo tail -f /var/log/eplatform/daphne-access.log
```

## Securing Your Installation

### 1. Set Up SSL/HTTPS

For production environments, you should enable HTTPS:

1. Obtain SSL certificates (e.g., using Let's Encrypt)
2. Uncomment and configure the HTTPS server block in `eplatform.conf`
3. Update certificate paths in the configuration
4. Enable HSTS for additional security

### 2. Firewall Configuration

Configure your firewall to only allow necessary ports:

```bash
# Using ufw (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8000/tcp  # Block direct access to Django
sudo ufw deny 8001/tcp  # Block direct access to Daphne
```

### 3. Additional Security Measures

1. Set up fail2ban to protect against brute force attacks
2. Configure rate limiting in Nginx (already included in the configuration)
3. Keep all software updated regularly
4. Consider using a Web Application Firewall (WAF)

## Troubleshooting

If you encounter issues, refer to the [TROUBLESHOOTING.md](TROUBLESHOOTING.md) guide for detailed troubleshooting steps.

Common issues include:
- 502 Bad Gateway errors
- WebSocket connection failures
- Static files not loading
- Permission problems

For each issue, the troubleshooting guide provides specific steps to diagnose and resolve the problem.
