/**
 * WebSocket Notifications Client
 *
 * This script handles real-time notifications using WebSockets with improved
 * error handling and reconnection logic.
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize WebSocket connection if user is logged in
    const userId = document.body.getAttribute('data-user-id');
    if (userId) {
        // Create WebSocket manager
        window.wsManager = new WebSocketManager(userId);
        window.wsManager.connect();

        // Add page visibility change handler to reconnect when page becomes visible again
        document.addEventListener('visibilitychange', function() {
            if (!document.hidden && window.wsManager) {
                // Check if connection is not active and reconnect
                if (window.wsManager.socket === null ||
                    window.wsManager.socket.readyState === WebSocket.CLOSED ||
                    window.wsManager.socket.readyState === WebSocket.CLOSING) {
                    console.log('Page became visible, attempting to reconnect WebSocket');
                    window.wsManager.reconnect();
                }
            }
        });
    }
});

/**
 * WebSocket Manager Class
 * Handles WebSocket connection, reconnection, and message processing
 */
class WebSocketManager {
    /**
     * Create a new WebSocket manager
     * @param {string} userId - The ID of the current user
     */
    constructor(userId) {
        this.userId = userId;
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.baseReconnectDelay = 1000; // Start with 1 second
        this.reconnectTimer = null;
        this.isConnecting = false;
        this.connectionStatus = 'disconnected'; // disconnected, connecting, connected, reconnecting, failed
        this.pollingActive = false;
        this.pollingInterval = null;

        // Heartbeat mechanism to detect connection issues
        this.heartbeatInterval = null;
        this.heartbeatMissed = 0;
        this.maxHeartbeatMisses = 3;
        this.heartbeatDelay = 30000; // 30 seconds

        // Create WebSocket URL
        const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        const host = window.location.host;

        // Get CSRF token from cookie or Django's csrftoken input
        const csrfToken = this.getCSRFToken();

        // With Nginx as reverse proxy, we use the same host for both HTTP and WebSockets
        console.log('Using WebSocket host:', host);
        console.log('Using Nginx reverse proxy for routing');

        // Add CSRF token to WebSocket URL as a query parameter
        this.wsUrl = `${protocol}${host}/ws/notifications/${userId}/?csrf_token=${csrfToken}`;

        // Bind methods to this instance
        this.connect = this.connect.bind(this);
        this.disconnect = this.disconnect.bind(this);
        this.reconnect = this.reconnect.bind(this);
        this.handleOpen = this.handleOpen.bind(this);
        this.handleMessage = this.handleMessage.bind(this);
        this.handleClose = this.handleClose.bind(this);
        this.handleError = this.handleError.bind(this);
        this.startPolling = this.startPolling.bind(this);
        this.stopPolling = this.stopPolling.bind(this);
        this.startHeartbeat = this.startHeartbeat.bind(this);
        this.stopHeartbeat = this.stopHeartbeat.bind(this);
        this.checkHeartbeat = this.checkHeartbeat.bind(this);

        // Log initialization
        console.log(`WebSocket manager initialized for user ${userId}`);
    }

    /**
     * Connect to the WebSocket server
     */
    connect() {
        if (this.isConnecting || this.connectionStatus === 'connected') {
            console.log('WebSocket connection already in progress or established');
            return;
        }

        try {
            this.isConnecting = true;
            this.connectionStatus = 'connecting';
            this.updateConnectionStatusUI();

            console.log(`Connecting to WebSocket at: ${this.wsUrl}`);

            // Create new WebSocket connection
            this.socket = new WebSocket(this.wsUrl);

            // Set up event listeners
            this.socket.addEventListener('open', this.handleOpen);
            this.socket.addEventListener('message', this.handleMessage);
            this.socket.addEventListener('close', this.handleClose);
            this.socket.addEventListener('error', this.handleError);

            // Store socket in window object for global access
            window.notificationSocket = this.socket;

            // Add event listeners for notification actions
            setupNotificationActions();

        } catch (error) {
            console.error('Error initializing WebSocket:', error);
            this.isConnecting = false;
            this.connectionStatus = 'failed';
            this.updateConnectionStatusUI();
            this.startPolling();
        }
    }

    /**
     * Disconnect from the WebSocket server
     */
    disconnect() {
        if (this.socket) {
            console.log('Manually disconnecting WebSocket');
            this.socket.close(1000, 'User initiated disconnect');
            this.socket = null;
        }

        // Stop heartbeat
        this.stopHeartbeat();

        // Clear reconnect timer
        this.clearReconnectTimer();

        this.connectionStatus = 'disconnected';
        this.updateConnectionStatusUI();
    }

    /**
     * Reconnect to the WebSocket server with exponential backoff
     */
    reconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log(`Maximum reconnection attempts (${this.maxReconnectAttempts}) reached. Falling back to polling.`);
            this.connectionStatus = 'failed';
            this.updateConnectionStatusUI();
            this.startPolling();
            return;
        }

        // For first attempt, use a fixed short delay to improve user experience
        let delay;
        if (this.reconnectAttempts === 0) {
            delay = 1000; // 1 second for first attempt
        } else {
            // Calculate delay with exponential backoff and some randomness for subsequent attempts
            delay = Math.min(
                30000, // Max 30 seconds
                this.baseReconnectDelay * Math.pow(1.5, this.reconnectAttempts) * (1 + Math.random() * 0.1)
            );
        }

        this.reconnectAttempts++;
        this.connectionStatus = 'reconnecting';
        this.updateConnectionStatusUI();

        console.log(`Reconnecting in ${Math.round(delay / 1000)} seconds (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

        // Show reconnection toast if available
        if (typeof window.showToast === 'function') {
            window.showToast(`Reconnecting to notifications in ${Math.round(delay / 1000)} seconds...`, 'info');
        }

        this.clearReconnectTimer();
        this.reconnectTimer = setTimeout(() => {
            // Check if the page is still active before attempting to reconnect
            if (!document.hidden) {
                this.connect();
            } else {
                // If page is hidden, wait until it becomes visible again
                const visibilityHandler = () => {
                    if (!document.hidden) {
                        document.removeEventListener('visibilitychange', visibilityHandler);
                        this.connect();
                    }
                };
                document.addEventListener('visibilitychange', visibilityHandler);
            }
        }, delay);
    }

    /**
     * Clear any active reconnect timer
     */
    clearReconnectTimer() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
    }

    /**
     * Handle WebSocket open event
     */
    handleOpen() {
        console.log('WebSocket connection established');
        this.isConnecting = false;
        this.connectionStatus = 'connected';

        // Store the reconnect attempts before resetting
        const wasReconnecting = this.reconnectAttempts > 0;

        // Reset reconnect attempts on successful connection
        this.reconnectAttempts = 0;
        this.updateConnectionStatusUI();

        // Stop polling if it was active
        this.stopPolling();

        // Start heartbeat to detect connection issues
        this.startHeartbeat();

        // Show connection success toast if available and this was a reconnection
        if (typeof window.showToast === 'function' && wasReconnecting) {
            window.showToast('Notification connection restored', 'success');
        }
    }

    /**
     * Start the heartbeat mechanism to detect connection issues
     */
    startHeartbeat() {
        this.stopHeartbeat(); // Clear any existing heartbeat
        this.heartbeatMissed = 0;

        // Set up heartbeat interval
        this.heartbeatInterval = setInterval(() => {
            this.checkHeartbeat();
        }, this.heartbeatDelay);

        console.log(`Heartbeat started with interval of ${this.heartbeatDelay}ms`);
    }

    /**
     * Stop the heartbeat mechanism
     */
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
            console.log('Heartbeat stopped');
        }
    }

    /**
     * Check connection status with heartbeat
     */
    checkHeartbeat() {
        // Only check if we have an active socket
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
            console.log('Heartbeat check: WebSocket not connected');
            this.heartbeatMissed++;

            if (this.heartbeatMissed >= this.maxHeartbeatMisses) {
                console.log(`Heartbeat failed ${this.heartbeatMissed} times, reconnecting...`);
                this.stopHeartbeat();

                // Force close and reconnect
                if (this.socket) {
                    this.socket.close();
                }

                this.reconnect();
            }
            return;
        }

        // If connected, try to send a ping
        try {
            // Send a ping message to check connection
            if (this.sendMessage({ type: 'ping' })) {
                // Reset missed heartbeats if we successfully sent a message
                this.heartbeatMissed = 0;
            } else {
                this.heartbeatMissed++;
                console.log(`Heartbeat message failed to send, missed: ${this.heartbeatMissed}/${this.maxHeartbeatMisses}`);
            }
        } catch (error) {
            this.heartbeatMissed++;
            console.error('Error during heartbeat check:', error);
        }

        // If we've missed too many heartbeats, reconnect
        if (this.heartbeatMissed >= this.maxHeartbeatMisses) {
            console.log(`Heartbeat failed ${this.heartbeatMissed} times, reconnecting...`);
            this.stopHeartbeat();

            // Force close and reconnect
            if (this.socket) {
                this.socket.close();
            }

            this.reconnect();
        }
    }

    /**
     * Handle WebSocket message event
     * @param {MessageEvent} event - The message event
     */
    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('WebSocket message received:', data);

            // Check for error messages
            if (data.status === 'error') {
                console.error('WebSocket error message:', data.message);
                if (typeof window.showToast === 'function') {
                    window.showToast(`Notification error: ${data.message}`, 'error');
                }
                return;
            }

            // Handle different message types
            switch (data.type) {
                case 'notification':
                    handleNewNotification(data.notification);
                    break;

                case 'unread_count':
                    updateNotificationCount(data.count);
                    break;

                case 'pong':
                    // Server responded to our ping, connection is healthy
                    console.log('Received pong from server, connection is healthy');
                    this.heartbeatMissed = 0;
                    break;

                case 'error':
                    console.error('WebSocket error:', data.message);
                    break;

                default:
                    console.log(`Unknown message type: ${data.type}`);
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }

    /**
     * Handle WebSocket close event
     * @param {CloseEvent} event - The close event
     */
    handleClose(event) {
        this.isConnecting = false;
        console.log(`WebSocket connection closed with code: ${event.code}, reason: ${event.reason || 'No reason provided'}`);

        // Stop heartbeat when connection is closed
        this.stopHeartbeat();

        // Check if this is a normal closure or abnormal
        if (event.code === 1000) {
            // Normal closure - user initiated or server clean shutdown
            this.connectionStatus = 'disconnected';
            this.updateConnectionStatusUI();
            console.log('Normal WebSocket closure, not attempting to reconnect');
        } else if (event.code === 1001) {
            // Going away - page is being unloaded
            this.connectionStatus = 'disconnected';
            this.updateConnectionStatusUI();
            console.log('Page is unloading, not attempting to reconnect');
        } else if (event.code === 1006) {
            // Abnormal closure - likely network issue
            console.log('Abnormal closure detected, attempting to reconnect...');
            // Use a shorter delay for network issues
            this.reconnectAttempts = 0; // Reset to ensure we start with a short delay
            this.reconnect();
        } else {
            // Other closure codes
            console.log(`WebSocket closed with code ${event.code}, attempting to reconnect...`);
            this.reconnect();
        }
    }

    /**
     * Handle WebSocket error event
     * @param {Event} event - The error event
     */
    handleError(event) {
        console.error('WebSocket error:', event);
        this.isConnecting = false;

        // WebSocket errors are followed by a close event, so we'll handle reconnection there
    }

    /**
     * Start polling for notifications as a fallback
     */
    startPolling() {
        if (this.pollingActive) {
            return;
        }

        console.log('Starting notification polling as WebSocket fallback');
        this.pollingActive = true;

        // Clear any existing polling interval
        this.stopPolling();

        // Function to fetch notification count
        const fetchNotificationCount = () => {
            fetch('/home/api/notifications/count/', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    updateNotificationCount(data.count);
                }
            })
            .catch(error => {
                console.error('Error polling for notifications:', error);
            });
        };

        // Fetch immediately
        fetchNotificationCount();

        // Then set up interval (every 30 seconds)
        this.pollingInterval = setInterval(fetchNotificationCount, 30000);

        // Show polling fallback toast if available
        if (typeof window.showToast === 'function') {
            window.showToast('Using polling for notifications (WebSocket unavailable)', 'warning');
        }
    }

    /**
     * Stop polling for notifications
     */
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
        this.pollingActive = false;
    }

    /**
     * Update UI elements to reflect connection status
     */
    updateConnectionStatusUI() {
        // Find status indicator element if it exists
        const statusIndicator = document.getElementById('ws-connection-status');
        if (!statusIndicator) {
            return;
        }

        // Update status indicator based on connection status
        statusIndicator.className = `connection-status ${this.connectionStatus}`;

        // Update text based on status
        switch (this.connectionStatus) {
            case 'connected':
                statusIndicator.textContent = 'Connected';
                break;
            case 'connecting':
                statusIndicator.textContent = 'Connecting...';
                break;
            case 'reconnecting':
                statusIndicator.textContent = `Reconnecting (${this.reconnectAttempts}/${this.maxReconnectAttempts})`;
                break;
            case 'disconnected':
                statusIndicator.textContent = 'Disconnected';
                break;
            case 'failed':
                statusIndicator.textContent = 'Connection Failed';
                break;
        }
    }

    /**
     * Get CSRF token from cookie or Django's csrftoken input
     * @returns {string} - The CSRF token
     */
    getCSRFToken() {
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

    /**
     * Send a message through the WebSocket
     * @param {Object} message - The message to send
     * @returns {boolean} - Whether the message was sent successfully
     */
    sendMessage(message) {
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
            console.error('Cannot send message: WebSocket is not connected');
            return false;
        }

        try {
            this.socket.send(JSON.stringify(message));
            return true;
        } catch (error) {
            console.error('Error sending WebSocket message:', error);
            return false;
        }
    }
}

/**
 * Fallback method to poll for notifications when WebSocket fails
 * @deprecated Use WebSocketManager.startPolling() instead
 */
function startPollingNotifications() {
    console.warn('startPollingNotifications is deprecated. Use WebSocketManager.startPolling() instead');
    if (window.wsManager) {
        window.wsManager.startPolling();
    } else {
        console.log('Starting legacy notification polling as WebSocket fallback');

        // Clear any existing polling interval
        if (window.notificationPollInterval) {
            clearInterval(window.notificationPollInterval);
        }

        // Function to fetch notification count
        const fetchNotificationCount = () => {
            fetch('/home/api/notifications/count/', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    updateNotificationCount(data.count);
                }
            })
            .catch(error => {
                console.error('Error polling for notifications:', error);
            });
        };

        // Fetch immediately
        fetchNotificationCount();

        // Then set up interval (every 30 seconds)
        window.notificationPollInterval = setInterval(fetchNotificationCount, 30000);
    }
}

/**
 * Handle a new notification
 * @param {Object} notification - The notification data
 */
function handleNewNotification(notification) {
    // Log notification details
    console.log('New notification received:', notification);

    // Show toast notification with appropriate styling based on type
    if (typeof window.showToast === 'function') {
        let toastType = 'info';

        // Set toast type based on notification type
        switch (notification.notification_type) {
            case 'mention':
                toastType = 'primary';
                break;
            case 'comment':
                toastType = 'info';
                break;
            case 'like':
                toastType = 'success';
                break;
        }

        window.showToast(notification.text, toastType);
    }

    // Update notification UI if the notifications panel is open
    const notificationsPanel = document.getElementById('notifications-panel');
    if (notificationsPanel && notificationsPanel.classList.contains('active')) {
        // Refresh notifications list
        if (typeof window.loadNotifications === 'function') {
            window.loadNotifications();
        }
    } else {
        // If panel is not open, update the badge count
        // This is a fallback in case the separate unread_count message doesn't arrive
        const currentCount = getNotificationCount();
        if (currentCount !== null) {
            updateNotificationCount(currentCount + 1);
        }
    }

    // Play notification sound if available
    playNotificationSound();
}

/**
 * Get the current notification count from the badge
 * @returns {number|null} The current count or null if not available
 */
function getNotificationCount() {
    const badge = document.getElementById('notification-badge');
    if (!badge || badge.classList.contains('hidden')) {
        return 0;
    }

    const count = parseInt(badge.textContent, 10);
    return isNaN(count) ? 0 : count;
}

/**
 * Update the notification count in the UI
 * @param {number} count - The number of unread notifications
 */
function updateNotificationCount(count) {
    const notificationBadge = document.getElementById('notification-badge');
    if (!notificationBadge) {
        console.warn('Notification badge element not found');
        return;
    }

    // Get previous count for comparison
    const previousCount = getNotificationCount();

    // Update the badge
    if (count > 0) {
        notificationBadge.textContent = count;
        notificationBadge.classList.remove('hidden');

        // If count increased and it's not the initial load, play sound
        if (previousCount !== null && count > previousCount && previousCount > 0) {
            playNotificationSound();
        }

        // Add a pulse animation if count increased
        if (previousCount !== null && count > previousCount) {
            notificationBadge.classList.add('pulse');
            setTimeout(() => {
                notificationBadge.classList.remove('pulse');
            }, 1000);
        }
    } else {
        notificationBadge.textContent = '';
        notificationBadge.classList.add('hidden');
    }

    // Update page title if supported
    updatePageTitle(count);
}

/**
 * Update the page title to show notification count
 * @param {number} count - The number of unread notifications
 */
function updatePageTitle(count) {
    // Only update if count is positive
    if (count > 0) {
        const originalTitle = document.title.replace(/^\(\d+\) /, '');
        document.title = `(${count}) ${originalTitle}`;
    } else {
        // Remove any existing count from title
        document.title = document.title.replace(/^\(\d+\) /, '');
    }
}

/**
 * Play a notification sound
 */
function playNotificationSound() {
    // Check if notification sounds are enabled in user preferences
    const soundsEnabled = localStorage.getItem('notification_sounds_enabled') !== 'false';
    if (!soundsEnabled) {
        return;
    }

    // Try to play the notification sound if it exists
    try {
        const audioElement = document.getElementById('notification-sound');
        if (audioElement) {
            // Reset the audio to the beginning
            audioElement.currentTime = 0;

            // Play the sound
            audioElement.play().catch(error => {
                console.warn('Could not play notification sound:', error);
            });
        } else {
            // Create an audio element if it doesn't exist
            const newAudio = document.createElement('audio');
            newAudio.id = 'notification-sound';
            newAudio.src = '/static/home/sounds/notification.mp3';
            newAudio.volume = 0.5;
            newAudio.style.display = 'none';
            document.body.appendChild(newAudio);

            // Try to play it
            newAudio.play().catch(error => {
                console.warn('Could not play notification sound:', error);
            });
        }
    } catch (error) {
        console.error('Error playing notification sound:', error);
    }
}

/**
 * Set up event listeners for notification actions
 */
function setupNotificationActions() {
    // Mark notification as read
    document.addEventListener('click', function(event) {
        const markReadBtn = event.target.closest('.mark-notification-read');
        if (!markReadBtn) return;

        const notificationId = markReadBtn.getAttribute('data-notification-id');
        if (!notificationId) return;

        // Use WebSocketManager if available
        if (window.wsManager) {
            const success = window.wsManager.sendMessage({
                type: 'mark_read',
                notification_id: notificationId
            });

            if (!success && typeof window.showToast === 'function') {
                window.showToast('Could not mark notification as read: WebSocket not connected', 'error');

                // Fallback to HTTP request
                markNotificationReadViaHttp(notificationId);
            }
        }
        // Legacy fallback
        else if (window.notificationSocket && window.notificationSocket.readyState === WebSocket.OPEN) {
            try {
                window.notificationSocket.send(JSON.stringify({
                    type: 'mark_read',
                    notification_id: notificationId
                }));
            } catch (error) {
                console.error('Error sending mark_read message:', error);
                if (typeof window.showToast === 'function') {
                    window.showToast('Error marking notification as read', 'error');
                }

                // Fallback to HTTP request
                markNotificationReadViaHttp(notificationId);
            }
        }
        // No WebSocket available, use HTTP
        else {
            markNotificationReadViaHttp(notificationId);
        }
    });

    // Mark all notifications as read
    const markAllReadBtn = document.getElementById('mark-all-notifications-read');
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', function() {
            // Use WebSocketManager if available
            if (window.wsManager) {
                const success = window.wsManager.sendMessage({
                    type: 'mark_all_read'
                });

                if (!success && typeof window.showToast === 'function') {
                    window.showToast('Could not mark all notifications as read: WebSocket not connected', 'error');

                    // Fallback to HTTP request
                    markAllNotificationsReadViaHttp();
                }
            }
            // Legacy fallback
            else if (window.notificationSocket && window.notificationSocket.readyState === WebSocket.OPEN) {
                try {
                    window.notificationSocket.send(JSON.stringify({
                        type: 'mark_all_read'
                    }));
                } catch (error) {
                    console.error('Error sending mark_all_read message:', error);
                    if (typeof window.showToast === 'function') {
                        window.showToast('Error marking all notifications as read', 'error');
                    }

                    // Fallback to HTTP request
                    markAllNotificationsReadViaHttp();
                }
            }
            // No WebSocket available, use HTTP
            else {
                markAllNotificationsReadViaHttp();
            }

            // Refresh notifications list
            if (typeof window.loadNotifications === 'function') {
                window.loadNotifications();
            }
        });
    }

    // Add connection status indicator to the UI if it doesn't exist
    if (!document.getElementById('ws-connection-status')) {
        const notificationBell = document.getElementById('notification-bell');
        if (notificationBell) {
            const statusIndicator = document.createElement('div');
            statusIndicator.id = 'ws-connection-status';
            statusIndicator.className = 'connection-status disconnected';
            statusIndicator.style.display = 'none'; // Hide by default, only show in dev mode
            notificationBell.appendChild(statusIndicator);

            // Add styles for the connection status indicator
            const style = document.createElement('style');
            style.textContent = `
                .connection-status {
                    position: absolute;
                    bottom: -5px;
                    right: -5px;
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    border: 1px solid white;
                }
                .connection-status.connected {
                    background-color: #4CAF50;
                }
                .connection-status.connecting, .connection-status.reconnecting {
                    background-color: #FFC107;
                }
                .connection-status.disconnected, .connection-status.failed {
                    background-color: #F44336;
                }
            `;
            document.head.appendChild(style);

            // Show indicator in development mode
            if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                statusIndicator.style.display = 'block';
            }
        }
    }
}

/**
 * Mark a notification as read via HTTP request (fallback)
 * @param {string|number} notificationId - The ID of the notification to mark as read
 */
function markNotificationReadViaHttp(notificationId) {
    fetch(`/home/api/notifications/mark-read/${notificationId}/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken')
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            // Update UI
            const item = document.querySelector(`.notification-item[data-id="${notificationId}"]`);
            if (item) {
                item.classList.remove('unread');
            }

            // Update notification count
            if (data.unread_count !== undefined) {
                updateNotificationCount(data.unread_count);
            }

            if (typeof window.showToast === 'function') {
                window.showToast('Notification marked as read', 'success');
            }
        }
    })
    .catch(error => {
        console.error('Error marking notification as read:', error);
        if (typeof window.showToast === 'function') {
            window.showToast('Error marking notification as read', 'error');
        }
    });
}

/**
 * Mark all notifications as read via HTTP request (fallback)
 */
function markAllNotificationsReadViaHttp() {
    fetch('/home/api/notifications/mark-all-read/', {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken')
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            // Update UI - mark all items as read
            const items = document.querySelectorAll('.notification-item.unread');
            items.forEach(item => {
                item.classList.remove('unread');
            });

            // Update notification count
            updateNotificationCount(0);

            if (typeof window.showToast === 'function') {
                window.showToast('All notifications marked as read', 'success');
            }
        }
    })
    .catch(error => {
        console.error('Error marking all notifications as read:', error);
        if (typeof window.showToast === 'function') {
            window.showToast('Error marking all notifications as read', 'error');
        }
    });
}

/**
 * Get CSRF token from cookies
 * @returns {string} CSRF token
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
