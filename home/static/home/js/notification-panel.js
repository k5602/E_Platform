/**
 * Notification Panel
 *
 * This script handles the notification panel functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize notification panel
    initNotificationPanel();
});

/**
 * Initialize notification panel
 */
function initNotificationPanel() {
    const notificationBell = document.getElementById('notification-bell');
    const notificationPanel = document.getElementById('notification-panel');
    const markAllReadBtn = document.getElementById('mark-all-read-btn');

    if (!notificationBell || !notificationPanel) {
        console.error('Notification elements not found');
        return;
    }

    // Toggle notification panel on bell click
    notificationBell.addEventListener('click', function(e) {
        e.stopPropagation();
        toggleNotificationPanel();
    });

    // Close panel when clicking outside
    document.addEventListener('click', function(e) {
        if (notificationPanel.classList.contains('active') &&
            !notificationPanel.contains(e.target) &&
            !notificationBell.contains(e.target)) {
            notificationPanel.classList.remove('active');
        }
    });

    // Mark all as read button
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            markAllNotificationsAsRead();
        });
    }
}

/**
 * Toggle notification panel
 */
function toggleNotificationPanel() {
    const panel = document.getElementById('notification-panel');

    if (panel) {
        panel.classList.toggle('active');

        // Load notifications if panel is now active
        if (panel.classList.contains('active')) {
            loadNotifications();
        }
    }
}

/**
 * Load notifications into the panel
 */
function loadNotifications() {
    const panelBody = document.getElementById('notification-panel-body');

    if (!panelBody) {
        return;
    }

    // Show loading spinner
    panelBody.innerHTML = `
        <div class="loading-spinner">
            <div class="spinner"></div>
            <p>جاري التحميل...</p>
        </div>
    `;

    // Fetch notifications
    fetch('/home/api/notifications/?limit=5', {
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
        // Clear loading spinner
        panelBody.innerHTML = '';

        if (data.notifications && data.notifications.length > 0) {
            // Create notification items
            data.notifications.forEach(notification => {
                const item = createNotificationItem(notification);
                panelBody.appendChild(item);
            });
        } else {
            // No notifications
            panelBody.innerHTML = `
                <div class="no-notifications">
                    <img src="/static/home/images/no-notifications.svg" alt="لا توجد إشعارات" class="no-notifications-icon">
                    <p>لا توجد إشعارات حاليا</p>
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('Error loading notifications:', error);
        panelBody.innerHTML = `
            <div class="no-notifications error">
                <p>حدث خطأ أثناء تحميل الإشعارات</p>
            </div>
        `;
    });
}

/**
 * Create a notification item element
 * @param {Object} notification - The notification data
 * @returns {HTMLElement} The notification item element
 */
function createNotificationItem(notification) {
    const item = document.createElement('div');
    item.className = `notification-item ${notification.notification_type} ${notification.is_read ? '' : 'unread'}`;
    item.dataset.id = notification.id;

    // Icon based on notification type
    let iconSvg = '';
    if (notification.notification_type === 'mention') {
        iconSvg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/></svg>';
    } else if (notification.notification_type === 'comment') {
        iconSvg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M21 6h-2v9H6v2c0 .55.45 1 1 1h11l4 4V7c0-.55-.45-1-1-1zm-4 6V3c0-.55-.45-1-1-1H3c-.55 0-1 .45-1 1v14l4-4h10c.55 0 1-.45 1-1z"/></svg>';
    } else if (notification.notification_type === 'like') {
        iconSvg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>';
    }

    // Create notification content
    item.innerHTML = `
        <div class="notification-icon">
            ${iconSvg}
        </div>
        <div class="notification-content">
            <p class="notification-text">${notification.text}</p>
            <p class="notification-time">${formatTimeAgo(notification.created_at)}</p>
        </div>
    `;

    // Add click event to navigate to the notification source
    item.addEventListener('click', function() {
        // Mark as read if not already
        if (!notification.is_read) {
            markNotificationAsRead(notification.id);
        }

        // Navigate to the appropriate page
        if (notification.post_id) {
            window.location.href = `/home/#post-${notification.post_id}`;
        } else {
            window.location.href = '/home/notifications/';
        }
    });

    return item;
}

/**
 * Mark a notification as read
 * @param {number} notificationId - The ID of the notification to mark as read
 */
function markNotificationAsRead(notificationId) {
    fetch(`/home/api/notifications/mark-read/${notificationId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
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
        // Update UI
        const item = document.querySelector(`.notification-item[data-id="${notificationId}"]`);
        if (item) {
            item.classList.remove('unread');
        }

        // Update notification count
        fetchNotificationCount();
    })
    .catch(error => {
        console.error('Error marking notification as read:', error);
    });
}

/**
 * Mark all notifications as read
 */
function markAllNotificationsAsRead() {
    fetch('/home/api/notifications/mark-read/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
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
        // Update UI - remove unread class from all items
        const items = document.querySelectorAll('.notification-item.unread');
        items.forEach(item => {
            item.classList.remove('unread');
        });

        // Update notification count
        updateNotificationCount(0);

        // Show success message
        if (typeof showToast === 'function') {
            showToast('All notifications marked as read', 'success');
        }
    })
    .catch(error => {
        console.error('Error marking all notifications as read:', error);
    });
}

/**
 * Fetch the unread notification count
 */
function fetchNotificationCount() {
    fetch('/home/api/notifications/count/', {
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
        updateNotificationCount(data.unread_count);
    })
    .catch(error => {
        console.error('Error fetching notification count:', error);
    });
}

/**
 * Update the notification count in the UI
 * @param {number} count - The number of unread notifications
 */
function updateNotificationCount(count) {
    const badge = document.getElementById('notification-badge');

    if (badge) {
        if (count > 0) {
            badge.textContent = count;
            badge.classList.remove('hidden');
        } else {
            badge.textContent = '';
            badge.classList.add('hidden');
        }
    }
}

/**
 * Format a timestamp as a relative time string (e.g., "2 hours ago")
 * @param {string} timestamp - The ISO timestamp to format
 * @returns {string} The formatted relative time
 */
function formatTimeAgo(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);

    if (seconds < 60) {
        return 'just now';
    }

    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) {
        return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
    }

    const hours = Math.floor(minutes / 60);
    if (hours < 24) {
        return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
    }

    const days = Math.floor(hours / 24);
    if (days < 30) {
        return `${days} day${days !== 1 ? 's' : ''} ago`;
    }

    const months = Math.floor(days / 30);
    if (months < 12) {
        return `${months} month${months !== 1 ? 's' : ''} ago`;
    }

    const years = Math.floor(months / 12);
    return `${years} year${years !== 1 ? 's' : ''} ago`;
}

/**
 * Get a cookie by name
 * @param {string} name - The name of the cookie to get
 * @returns {string} The cookie value
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

/**
 * Get the authentication token from localStorage
 * @returns {string} The authentication token
 */
function getAuthToken() {
    // In a real implementation, this would get the token from localStorage or a secure cookie
    // For now, we'll return an empty string and rely on session authentication
    return '';
}

// Make loadNotifications available globally
window.loadNotifications = loadNotifications;
