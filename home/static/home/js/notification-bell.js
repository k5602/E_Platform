/**
 * Notification Bell
 * 
 * This script handles the notification bell functionality
 * without creating any duplicate elements
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing notification bell');
    
    // Check if notification bell already exists
    const notificationBell = document.getElementById('notification-bell');
    if (!notificationBell) {
        console.error('Notification bell not found');
        return;
    }
    
    // Start polling for notification count
    pollNotificationCount();
});

/**
 * Poll for notification count
 */
function pollNotificationCount() {
    // Check for new notifications every 30 seconds
    const POLLING_INTERVAL = 30000;
    let lastCount = 0;
    
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
            if (data.status === 'success') {
                const newCount = data.unread_count;
                
                // If count increased, show toast for new notification
                if (newCount > lastCount && lastCount > 0) {
                    showNewNotificationToast();
                }
                
                // Update the count in the UI
                updateNotificationCount(newCount);
                lastCount = newCount;
            }
        })
        .catch(error => {
            console.error('Error fetching notification count:', error);
        });
    }
    
    function showNewNotificationToast() {
        // Show toast notification for new notification
        if (typeof window.showToast === 'function') {
            window.showToast('You have a new notification', 'info');
        }
    }
    
    // Initial fetch
    fetchNotificationCount();
    
    // Set up polling
    setInterval(fetchNotificationCount, POLLING_INTERVAL);
}

/**
 * Update notification count badge
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
