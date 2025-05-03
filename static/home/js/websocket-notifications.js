/**
 * WebSocket Notifications Handler
 *
 * This script handles real-time notifications via WebSockets.
 */

let notificationSocket = null;
let reconnectAttempts = 0;
const maxReconnectAttempts = 10;
const baseReconnectDelay = 1000; // 1 second

document.addEventListener('DOMContentLoaded', function() {
    // Get the user ID from the data attribute on the body element
    const userId = document.body.getAttribute('data-user-id');

    if (!userId) {
        console.warn('No user ID found, WebSocket notifications will not be initialized');
        return;
    }

    initializeNotificationWebsocket(userId);
});

/**
 * Initialize the WebSocket connection for notifications
 */
function initializeNotificationWebsocket(userId) {
    // Close any existing connection
    if (notificationSocket !== null) {
        notificationSocket.close();
    }

    // Create a new WebSocket connection
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

    // In development mode, we use a dual-server setup:
    // - Django development server on port 8000 for HTTP and static files
    // - Daphne server on port 8001 for WebSockets only
    let wsHost = window.location.host;

    // Handle local development and network testing
    if (wsHost.includes(':8000')) {
        // In development, use port 8001 for WebSockets
        wsHost = wsHost.replace(':8000', ':8001');
        console.log('Development mode detected, using WebSocket host:', wsHost);
        console.log('IMPORTANT: Make sure both servers are running:');
        console.log('1. Django server on port 8000 for HTTP and static files');
        console.log('2. Daphne server on port 8001 for WebSockets');
        console.log('Run ./run_servers.sh to start both servers together');
    }

    // Get CSRF token from cookie or Django's csrftoken input
    function getCSRFToken() {
        // Try to get from cookie first
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];

        if (cookieValue) {
            return cookieValue;
        }

        // If not in cookie, try to get from hidden input
        const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (csrfInput) {
            return csrfInput.value;
        }

        console.error('CSRF token not found. WebSocket connection may fail.');
        return '';
    }

    // Add CSRF token to WebSocket URL as a query parameter
    const csrfToken = getCSRFToken();
    const wsUrl = `${wsProtocol}//${wsHost}/ws/notifications/${userId}/?csrf_token=${csrfToken}`;

    console.log('Attempting to connect to notification WebSocket at:', wsUrl);

    try {
        notificationSocket = new WebSocket(wsUrl);

        notificationSocket.onopen = function() {
            console.log('Notification WebSocket connection established');
            reconnectAttempts = 0;
        };

        notificationSocket.onmessage = function(e) {
            try {
                const data = JSON.parse(e.data);
                handleNotificationMessage(data);
            } catch (error) {
                console.error('Error parsing notification WebSocket message:', error);
            }
        };

        notificationSocket.onclose = function(event) {
            // Check if the close was clean (code 1000 or 1001)
            const wasClean = event.code === 1000 || event.code === 1001;

            console.log(`Notification WebSocket connection closed. Code: ${event.code}, Clean: ${wasClean}, Reason: ${event.reason}`);

            // Only attempt to reconnect if it wasn't a clean close and we haven't exceeded max attempts
            if (!wasClean && reconnectAttempts < maxReconnectAttempts) {
                // Use exponential backoff for reconnection
                const delay = Math.min(baseReconnectDelay * Math.pow(1.5, reconnectAttempts), 30000);
                reconnectAttempts++;

                console.log(`Attempting to reconnect (${reconnectAttempts}/${maxReconnectAttempts}) in ${delay}ms`);

                // Show toast notification if available
                if (typeof showToastNotification === 'function') {
                    if (event.code === 1006) {
                        // Code 1006 is "Abnormal Closure" which often means the server is not available
                        showToastNotification(`WebSocket server not available. Make sure Daphne is running on port 8001.`, 'error');

                        // Add a more detailed message to the console
                        console.error(`
                            WebSocket connection failed with code 1006 (Abnormal Closure).
                            This usually means the WebSocket server (Daphne) is not running.

                            To fix this issue:
                            1. Open a terminal
                            2. Navigate to your project directory
                            3. Activate your virtual environment
                            4. Run: daphne -p 8001 E_Platform.asgi:application

                            Keep the Django development server running on port 8000 for regular HTTP requests.
                        `);
                    } else {
                        showToastNotification(`Notification connection lost. Reconnecting...`, 'warning');
                    }
                }

                setTimeout(function() {
                    initializeNotificationWebsocket(userId);
                }, delay);
            } else if (reconnectAttempts >= maxReconnectAttempts) {
                if (typeof showToastNotification === 'function') {
                    showToastNotification('Unable to reconnect to notification server after multiple attempts.', 'error');
                }
            }
        };

        notificationSocket.onerror = function(e) {
            console.error('Notification WebSocket error:', e);
        };
    } catch (error) {
        console.error('Error creating notification WebSocket connection:', error);

        // Attempt to reconnect with exponential backoff
        if (reconnectAttempts < maxReconnectAttempts) {
            const delay = Math.min(baseReconnectDelay * Math.pow(1.5, reconnectAttempts), 30000);
            reconnectAttempts++;

            setTimeout(function() {
                initializeNotificationWebsocket(userId);
            }, delay);
        }
    }

    return notificationSocket;
}

/**
 * Handle incoming notification messages
 */
function handleNotificationMessage(data) {
    const messageType = data.type;

    switch (messageType) {
        case 'notification':
            handleNewNotification(data.notification);
            break;
        case 'unread_count':
            updateNotificationBadge(data.count);
            break;
        case 'error':
            console.error('Notification WebSocket error:', data.message);
            break;
        default:
            console.log('Unknown notification message type:', messageType);
    }
}

/**
 * Handle a new notification
 */
function handleNewNotification(notification) {
    // Update the notification badge
    updateNotificationBadge();

    // Show a toast notification if the function is available
    if (typeof showToastNotification === 'function') {
        showToastNotification(notification.content, 'info');
    }

    // Update the notification panel if it exists
    const notificationPanel = document.getElementById('notification-panel');
    if (notificationPanel && typeof refreshNotifications === 'function') {
        refreshNotifications();
    }
}

/**
 * Update the notification badge count
 */
function updateNotificationBadge(count) {
    // If count is not provided, fetch it from the API
    if (count === undefined) {
        fetch('/home/api/notifications/count/')
            .then(response => response.json())
            .then(data => {
                updateNotificationBadgeUI(data.count);
            })
            .catch(error => {
                console.error('Error fetching notification count:', error);
            });
    } else {
        updateNotificationBadgeUI(count);
    }
}

/**
 * Update the notification badge UI
 */
function updateNotificationBadgeUI(count) {
    const badge = document.getElementById('notification-badge');
    if (!badge) return;

    if (count > 0) {
        badge.textContent = count > 99 ? '99+' : count;
        badge.classList.add('show');
    } else {
        badge.textContent = '';
        badge.classList.remove('show');
    }
}
