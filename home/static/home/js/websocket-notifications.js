/**
 * WebSocket Notifications Client
 * 
 * This script handles real-time notifications using WebSockets.
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize WebSocket connection if user is logged in
    const userId = document.body.getAttribute('data-user-id');
    if (userId) {
        initializeWebSocket(userId);
    }
});

/**
 * Initialize WebSocket connection for notifications
 * @param {string} userId - The ID of the current user
 */
function initializeWebSocket(userId) {
    // Determine WebSocket protocol (wss for HTTPS, ws for HTTP)
    const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const host = window.location.host;
    const wsUrl = `${protocol}${host}/ws/notifications/${userId}/`;
    
    // Create WebSocket connection
    const socket = new WebSocket(wsUrl);
    
    // Connection opened
    socket.addEventListener('open', function(event) {
        console.log('WebSocket connection established');
    });
    
    // Listen for messages
    socket.addEventListener('message', function(event) {
        const data = JSON.parse(event.data);
        console.log('WebSocket message received:', data);
        
        // Handle different message types
        if (data.type === 'notification') {
            // New notification received
            handleNewNotification(data.notification);
        } else if (data.type === 'unread_count') {
            // Update unread notification count
            updateNotificationCount(data.count);
        }
    });
    
    // Connection closed
    socket.addEventListener('close', function(event) {
        console.log('WebSocket connection closed');
        // Try to reconnect after a delay
        setTimeout(() => {
            console.log('Attempting to reconnect WebSocket...');
            initializeWebSocket(userId);
        }, 5000);
    });
    
    // Connection error
    socket.addEventListener('error', function(event) {
        console.error('WebSocket error:', event);
    });
    
    // Store socket in window object for global access
    window.notificationSocket = socket;
    
    // Add event listeners for notification actions
    setupNotificationActions();
}

/**
 * Handle a new notification
 * @param {Object} notification - The notification data
 */
function handleNewNotification(notification) {
    // Show toast notification
    if (typeof window.showToast === 'function') {
        window.showToast(notification.text, 'info');
    }
    
    // Update notification UI if the notifications panel is open
    const notificationsPanel = document.getElementById('notifications-panel');
    if (notificationsPanel && notificationsPanel.classList.contains('active')) {
        // Refresh notifications list
        if (typeof window.loadNotifications === 'function') {
            window.loadNotifications();
        }
    }
}

/**
 * Update the notification count in the UI
 * @param {number} count - The number of unread notifications
 */
function updateNotificationCount(count) {
    const notificationBadge = document.getElementById('notification-badge');
    if (notificationBadge) {
        if (count > 0) {
            notificationBadge.textContent = count;
            notificationBadge.classList.remove('hidden');
        } else {
            notificationBadge.textContent = '';
            notificationBadge.classList.add('hidden');
        }
    }
}

/**
 * Set up event listeners for notification actions
 */
function setupNotificationActions() {
    // Mark notification as read
    document.addEventListener('click', function(event) {
        const markReadBtn = event.target.closest('.mark-notification-read');
        if (markReadBtn && window.notificationSocket) {
            const notificationId = markReadBtn.getAttribute('data-notification-id');
            if (notificationId) {
                window.notificationSocket.send(JSON.stringify({
                    type: 'mark_read',
                    notification_id: notificationId
                }));
            }
        }
    });
    
    // Mark all notifications as read
    const markAllReadBtn = document.getElementById('mark-all-notifications-read');
    if (markAllReadBtn && window.notificationSocket) {
        markAllReadBtn.addEventListener('click', function() {
            window.notificationSocket.send(JSON.stringify({
                type: 'mark_all_read'
            }));
            
            // Refresh notifications list
            if (typeof window.loadNotifications === 'function') {
                window.loadNotifications();
            }
        });
    }
}
