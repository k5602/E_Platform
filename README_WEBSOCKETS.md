# WebSocket Setup for E_Platform

## Overview

E_Platform uses WebSockets for real-time features like chat and notifications. To enable these features, you need to run both the Django development server (for HTTP requests) and the Daphne server (for WebSocket connections).

## Running the Servers

### Option 1: Automatic Terminal Detection (Recommended)

The easiest way to run both servers is to use the auto-detecting script:

```bash
./run_with_terminal.sh
```

This script automatically detects your terminal emulator (KDE Konsole, GNOME Terminal, XFCE Terminal, XTerm) and launches both servers in separate tabs or windows. If no supported terminal is found, it falls back to tmux or provides manual instructions.

### Option 2: KDE Konsole Users

If you're using KDE Konsole, you can use this dedicated script:

```bash
./run_with_konsole.sh
```

This will open two tabs in Konsole, one for each server.

### Option 3: Tmux Users

If you prefer tmux, you can use:

```bash
./run_servers.sh
```

This script uses tmux to run both servers in split panes:
- Left pane: Django development server (port 8000) for HTTP requests and static files
- Right pane: Daphne server (port 8001) for WebSocket connections only

**Note:** This requires tmux to be installed. If it's not installed, you can install it with:
```bash
sudo apt-get install tmux  # For Ubuntu/Debian
# or
brew install tmux  # For macOS with Homebrew
```

### Option 4: Run Servers Manually

If you prefer to run the servers manually, you'll need two terminal windows:

#### Terminal 1: Django Development Server (HTTP)

```bash
./run_django_server.sh
```

Or manually:

```bash
source .venv/bin/activate
python manage.py runserver
```

This server handles regular HTTP requests like page loads, API calls, and static files.

#### Terminal 2: Daphne Server (WebSockets)

```bash
./run_websocket_server.sh
```

Or manually:

```bash
source .venv/bin/activate
daphne -p 8001 E_Platform.asgi:application
```

## Important Notes

1. **Static Files**: The Daphne server (port 8001) does not serve static files (CSS, JS, images). All static file requests should go through the Django development server (port 8000).

2. **WebSocket Connections**: The JavaScript code is configured to automatically connect to the WebSocket server on port 8001 when running in development mode.

## Troubleshooting

1. **WebSocket Connection Errors**: If you see WebSocket connection errors in the browser console (like "WebSocket connection failed with code 1006"), it means the Daphne server is not running. Make sure to start it using the instructions above.

2. **Missing CSS/JS**: If the site appears without styling or JavaScript functionality, make sure the Django development server is running on port 8000.

3. **Port Conflicts**: If either port (8000 or 8001) is already in use, you'll need to stop the conflicting process or use different ports.

## Production Deployment

For production, you should use a proper ASGI server setup that handles both HTTP and WebSocket connections through a single port. Options include:

- Daphne behind a reverse proxy (Nginx/Apache)
- Uvicorn with Gunicorn workers
- Hypercorn

Consult the Django Channels documentation for more information on production deployments.
