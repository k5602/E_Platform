/**
 * Standalone Notification Bell
 * This script adds a notification bell directly to the DOM
 * to ensure it's always visible regardless of other scripts
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing standalone notification bell');
    
    // Find the main navigation
    const mainNav = document.querySelector('.main_nav');
    if (!mainNav) {
        console.error('Main navigation not found');
        return;
    }
    
    // Check if notification bell already exists
    if (document.getElementById('notification-bell')) {
        console.log('Notification bell already exists');
        return;
    }
    
    // Create notification bell element
    const notificationBell = document.createElement('div');
    notificationBell.className = 'notification-bell';
    notificationBell.id = 'notification-bell';
    notificationBell.style.display = 'flex';
    notificationBell.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
        </svg>
        <span class="notification-count" id="notification-count" style="display: none;">0</span>
    `;
    
    // Create notification dropdown
    const notificationDropdown = document.createElement('div');
    notificationDropdown.className = 'notification-dropdown';
    notificationDropdown.id = 'notification-dropdown';
    notificationDropdown.innerHTML = `
        <div class="notification-dropdown-header">
            <h3 class="notification-dropdown-title">Notifications</h3>
            <button class="notification-dropdown-mark-all" id="mark-all-read-btn">Mark all as read</button>
        </div>
        <div class="notification-dropdown-list" id="notification-dropdown-list">
            <div class="notification-dropdown-empty">
                Loading notifications...
            </div>
        </div>
        <div class="notification-dropdown-footer">
            <a href="/home/notifications/" class="notification-dropdown-view-all">View all notifications</a>
        </div>
    `;
    
    // Add notification bell and dropdown to main navigation
    mainNav.appendChild(notificationBell);
    notificationBell.appendChild(notificationDropdown);
    
    // Toggle dropdown on click
    notificationBell.addEventListener('click', function(e) {
        e.stopPropagation();
        
        const dropdown = document.getElementById('notification-dropdown');
        dropdown.classList.toggle('show');
        
        // Load notifications if dropdown is shown
        if (dropdown.classList.contains('show')) {
            loadNotificationsDropdown();
        }
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        const dropdown = document.getElementById('notification-dropdown');
        if (dropdown && dropdown.classList.contains('show')) {
            dropdown.classList.remove('show');
        }
    });
    
    // Initialize mark all as read button
    const markAllReadBtn = document.getElementById('mark-all-read-btn');
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            markAllNotificationsAsRead();
        });
    }
    
    // Start polling for notification count
    pollNotificationCount();
    
    /**
     * Load notifications for dropdown
     */
    function loadNotificationsDropdown() {
        const notificationList = document.getElementById('notification-dropdown-list');
        if (!notificationList) return;
        
        // Fetch notifications
        fetch('/home/api/notifications/', {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                if (data.notifications.length === 0) {
                    notificationList.innerHTML = `
                        <div class="notification-dropdown-empty">
                            You don't have any notifications yet
                        </div>
                    `;
                } else {
                    notificationList.innerHTML = '';
                    
                    // Show only the 5 most recent notifications
                    const recentNotifications = data.notifications.slice(0, 5);
                    
                    recentNotifications.forEach(notification => {
                        const notificationItem = document.createElement('div');
                        notificationItem.className = `notification-dropdown-item ${notification.is_read ? 'read' : 'unread'}`;
                        notificationItem.dataset.id = notification.id;
                        
                        notificationItem.innerHTML = `
                            <p class="notification-dropdown-text">${notification.text}</p>
                            <p class="notification-dropdown-time">${notification.time_ago}</p>
                        `;
                        
                        // Mark as read when clicked
                        notificationItem.addEventListener('click', function(e) {
                            e.stopPropagation();
                            markNotificationAsRead(notification.id);
                            
                            // Navigate to appropriate page based on notification type
                            if (notification.post) {
                                window.location.href = '/home/#post-' + notification.post.id;
                            } else {
                                window.location.href = '/home/notifications/';
                            }
                        });
                        
                        notificationList.appendChild(notificationItem);
                    });
                }
                
                // Update notification count
                updateNotificationCount(data.unread_count);
            } else {
                console.error('Failed to fetch notifications:', data.message);
                notificationList.innerHTML = `
                    <div class="notification-dropdown-empty">
                        Failed to load notifications
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error fetching notifications:', error);
            notificationList.innerHTML = `
                <div class="notification-dropdown-empty">
                    An error occurred while loading notifications
                </div>
            `;
        });
    }
    
    /**
     * Poll for notification count
     */
    function pollNotificationCount() {
        // Check for new notifications every 15 seconds
        const POLLING_INTERVAL = 15000;
        let lastCount = 0;
        
        function fetchNotificationCount() {
            fetch('/home/api/notifications/count/', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    const newCount = data.unread_count;
                    console.log(`Notification count: ${newCount} (previous: ${lastCount})`);
                    
                    // If count increased, fetch the latest notifications to show toast
                    if (newCount > lastCount && lastCount > 0) {
                        fetchLatestNotifications();
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
        
        function fetchLatestNotifications() {
            fetch('/home/api/notifications/', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success' && data.notifications.length > 0) {
                    // Get the most recent notification
                    const latestNotification = data.notifications[0];
                    
                    // Show toast for the new notification
                    if (typeof window.showToast === 'function') {
                        window.showToast(latestNotification.text, 'info');
                    } else {
                        console.error('showToast function not available');
                    }
                }
            })
            .catch(error => {
                console.error('Error fetching latest notifications:', error);
            });
        }
        
        // Initial fetch
        fetchNotificationCount();
        
        // Set up polling
        setInterval(fetchNotificationCount, POLLING_INTERVAL);
    }
    
    /**
     * Update notification count badge
     */
    function updateNotificationCount(count) {
        const countElement = document.getElementById('notification-count');
        if (!countElement) {
            console.error('Notification count element not found');
            return;
        }
        
        console.log(`Updating notification count: ${count}`);
        
        if (count > 0) {
            countElement.textContent = count > 99 ? '99+' : count;
            countElement.style.display = 'flex';
            
            // Make the notification bell more noticeable
            const bell = document.getElementById('notification-bell');
            if (bell) {
                // Add a pulsing effect to the bell
                bell.classList.add('has-notifications');
                
                // Make sure the bell is visible
                bell.style.display = 'flex';
            } else {
                console.error('Notification bell element not found');
            }
            
            // Store current count
            countElement.dataset.count = count;
        } else {
            countElement.style.display = 'none';
            countElement.dataset.count = '0';
            
            // Remove the pulsing effect from the bell
            const bell = document.getElementById('notification-bell');
            if (bell) {
                bell.classList.remove('has-notifications');
            }
        }
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
                const notificationItem = document.querySelector(`.notification-dropdown-item[data-id="${notificationId}"]`);
                if (notificationItem) {
                    notificationItem.classList.remove('unread');
                    notificationItem.classList.add('read');
                }
                
                // Update notification count
                updateNotificationCount(data.unread_count);
            }
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
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Update UI
                const unreadNotifications = document.querySelectorAll('.notification-dropdown-item.unread');
                unreadNotifications.forEach(notification => {
                    notification.classList.remove('unread');
                    notification.classList.add('read');
                });
                
                // Update notification count
                updateNotificationCount(0);
                
                // Show success toast
                if (typeof window.showToast === 'function') {
                    window.showToast('All notifications marked as read', 'success');
                }
            }
        })
        .catch(error => {
            console.error('Error marking all notifications as read:', error);
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
});
