/**
 * Messages Badge Handler
 * 
 * This script handles the unread messages count badge in the navigation bar.
 */

document.addEventListener('DOMContentLoaded', function() {
    const messagesBadge = document.getElementById('messages-badge');
    
    if (!messagesBadge) return;
    
    // Function to update the unread messages count
    function updateUnreadMessagesCount() {
        // Make an API call to get the unread messages count
        fetch('/chat/api/unread-count/')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                const count = data.unread_count || 0;
                
                // Update the badge
                if (count > 0) {
                    messagesBadge.textContent = count > 99 ? '99+' : count;
                    messagesBadge.classList.add('show');
                } else {
                    messagesBadge.textContent = '';
                    messagesBadge.classList.remove('show');
                }
            })
            .catch(error => {
                console.error('Error fetching unread messages count:', error);
            });
    }
    
    // Update the count when the page loads
    updateUnreadMessagesCount();
    
    // Update the count every 30 seconds
    setInterval(updateUnreadMessagesCount, 30000);
    
    // Listen for WebSocket messages about new messages
    if (window.chatSocket) {
        window.chatSocket.addEventListener('message', function(event) {
            const data = JSON.parse(event.data);
            
            if (data.type === 'new_message_notification') {
                // Update the count when a new message notification is received
                updateUnreadMessagesCount();
            }
        });
    }
});
