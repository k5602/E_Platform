/**
 * Notifications page functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize notifications
    initializeNotifications();
    
    // Initialize mark all as read button
    initializeMarkAllReadButton();
});

/**
 * Initialize notifications list
 */
function initializeNotifications() {
    const notificationsList = document.getElementById('notifications-list');
    const noNotifications = document.getElementById('no-notifications');
    
    if (!notificationsList) return;
    
    // Fetch notifications
    fetch('/home/api/notifications/', {
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success' || data.notifications) {
            // Clear loading spinner
            notificationsList.innerHTML = '';
            
            if (!data.notifications || data.notifications.length === 0) {
                // Show no notifications message
                notificationsList.classList.add('hidden');
                if (noNotifications) {
                    noNotifications.classList.remove('hidden');
                } else {
                    notificationsList.innerHTML = `
                        <div class="no-notifications">
                            <img src="/static/home/images/no-notifications.svg" alt="لا توجد إشعارات" class="no-notifications-icon">
                            <p>لا توجد إشعارات حاليا</p>
                        </div>
                    `;
                }
            } else {
                // Show notifications list
                if (noNotifications) {
                    noNotifications.classList.add('hidden');
                }
                notificationsList.classList.remove('hidden');
                
                // Render notifications
                data.notifications.forEach(notification => {
                    const notificationElement = createNotificationElement(notification);
                    notificationsList.appendChild(notificationElement);
                });
                
                // Initialize mark as read buttons
                initializeMarkAsReadButtons();
            }
        } else {
            console.error('Failed to fetch notifications:', data.message);
            notificationsList.innerHTML = `
                <div class="notification-error">
                    <p>حدث خطأ أثناء تحميل الإشعارات</p>
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('Error fetching notifications:', error);
        notificationsList.innerHTML = `
            <div class="notification-error">
                <p>حدث خطأ أثناء تحميل الإشعارات. يرجى المحاولة مرة أخرى</p>
            </div>
        `;
    });
}

/**
 * Create a notification element
 */
function createNotificationElement(notification) {
    const notificationElement = document.createElement('div');
    notificationElement.className = `notification-item ${notification.type} ${notification.is_read ? 'read' : 'unread'}`;
    notificationElement.dataset.id = notification.id;
    
    // Create content preview if available
    let contentPreview = '';
    if (notification.post && notification.post.content_preview) {
        contentPreview = `<p class="notification-preview">${notification.post.content_preview}</p>`;
    } else if (notification.comment && notification.comment.content_preview) {
        contentPreview = `<p class="notification-preview">${notification.comment.content_preview}</p>`;
    }
    
    notificationElement.innerHTML = `
        <div class="notification-icon">
            ${getNotificationIcon(notification.type)}
        </div>
        <div class="notification-content">
            <p class="notification-text">${notification.text}</p>
            ${contentPreview}
            <p class="notification-time">${notification.time_ago}</p>
        </div>
        ${!notification.is_read ? `
        <button class="mark-read-btn" title="Mark as read" data-id="${notification.id}">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
        </button>
        ` : ''}
    `;
    
    return notificationElement;
}

/**
 * Get notification icon based on type
 */
function getNotificationIcon(type) {
    switch (type) {
        case 'mention':
            return `
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="4"></circle>
                    <path d="M16 8v5a3 3 0 0 0 6 0v-1a10 10 0 1 0-3.92 7.94"></path>
                </svg>
            `;
        case 'comment':
            return `
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
            `;
        case 'like':
            return `
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                </svg>
            `;
        default:
            return `
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                    <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                </svg>
            `;
    }
}

/**
 * Initialize mark as read buttons
 */
function initializeMarkAsReadButtons() {
    const markReadButtons = document.querySelectorAll('.mark-read-btn');
    
    markReadButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const notificationId = this.dataset.id;
            markNotificationAsRead(notificationId);
        });
    });
}

/**
 * Mark a notification as read
 */
function markNotificationAsRead(notificationId) {
    fetch(`/home/api/notifications/mark-read/${notificationId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Update UI
            const notificationElement = document.querySelector(`.notification-item[data-id="${notificationId}"]`);
            if (notificationElement) {
                notificationElement.classList.remove('unread');
                notificationElement.classList.add('read');
                
                // Remove mark as read button
                const markReadButton = notificationElement.querySelector('.mark-read-btn');
                if (markReadButton) {
                    markReadButton.remove();
                }
            }
            
            // Show success toast
            if (typeof window.showToast === 'function') {
                window.showToast('Notification marked as read', 'success');
            }
        } else {
            console.error('Failed to mark notification as read:', data.message);
            
            // Show error toast
            if (typeof window.showToast === 'function') {
                window.showToast('Failed to mark notification as read', 'error');
            }
        }
    })
    .catch(error => {
        console.error('Error marking notification as read:', error);
        
        // Show error toast
        if (typeof window.showToast === 'function') {
            window.showToast('An error occurred. Please try again.', 'error');
        }
    });
}

/**
 * Initialize mark all as read button
 */
function initializeMarkAllReadButton() {
    const markAllReadButton = document.getElementById('mark-all-read-btn');
    
    if (!markAllReadButton) return;
    
    markAllReadButton.addEventListener('click', function() {
        markAllNotificationsAsRead();
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
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Update UI
            const unreadNotifications = document.querySelectorAll('.notification-item.unread');
            unreadNotifications.forEach(notification => {
                notification.classList.remove('unread');
                notification.classList.add('read');
                
                // Remove mark as read button
                const markReadButton = notification.querySelector('.mark-read-btn');
                if (markReadButton) {
                    markReadButton.remove();
                }
            });
            
            // Show success toast
            if (typeof window.showToast === 'function') {
                window.showToast('All notifications marked as read', 'success');
            }
        } else {
            console.error('Failed to mark all notifications as read:', data.message);
            
            // Show error toast
            if (typeof window.showToast === 'function') {
                window.showToast('Failed to mark all notifications as read', 'error');
            }
        }
    })
    .catch(error => {
        console.error('Error marking all notifications as read:', error);
        
        // Show error toast
        if (typeof window.showToast === 'function') {
            window.showToast('An error occurred. Please try again.', 'error');
        }
    });
}

/**
 * Helper function to get CSRF token
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
