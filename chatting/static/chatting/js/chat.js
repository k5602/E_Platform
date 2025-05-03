/**
 * Chat functionality for real-time messaging
 * Enhanced with improved UI/UX and dark mode support
 */

let chatSocket = null;
let currentConversationId = null;
let currentUserId = null;
let otherUserId = null;
let typingTimeout = null;

// Track reconnection attempts
let reconnectAttempts = 0;
const maxReconnectAttempts = 10;
const baseReconnectDelay = 1000; // 1 second

/**
 * Initialize the WebSocket connection for chat
 */
function initializeChatWebsocket() {
    // Close any existing connection
    if (chatSocket !== null) {
        chatSocket.close();
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

    const wsUrl = `${wsProtocol}//${wsHost}/ws/chat/`;

    console.log('Attempting to connect to WebSocket at:', wsUrl);

    // Log the current URL for debugging
    console.log('Current page URL:', window.location.href);

    try {
        chatSocket = new WebSocket(wsUrl);

        // WebSocket event handlers
        chatSocket.onopen = function() {
            console.log('Chat WebSocket connection established');

            // Reset reconnect attempts on successful connection
            reconnectAttempts = 0;

            // Show connection status
            showConnectionStatus('connected');

            // If we were reconnecting, send any pending messages
            sendPendingMessages();
        };

        chatSocket.onmessage = function(e) {
            try {
                const data = JSON.parse(e.data);
                handleWebSocketMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        chatSocket.onclose = function(event) {
            // Check if the close was clean (code 1000 or 1001)
            const wasClean = event.code === 1000 || event.code === 1001;

            console.log(`Chat WebSocket connection closed. Code: ${event.code}, Clean: ${wasClean}, Reason: ${event.reason}`);

            // Show disconnected status
            showConnectionStatus('disconnected');

            // Only attempt to reconnect if it wasn't a clean close and we haven't exceeded max attempts
            if (!wasClean && reconnectAttempts < maxReconnectAttempts) {
                // Use exponential backoff for reconnection
                const delay = Math.min(baseReconnectDelay * Math.pow(1.5, reconnectAttempts), 30000);
                reconnectAttempts++;

                console.log(`Attempting to reconnect (${reconnectAttempts}/${maxReconnectAttempts}) in ${delay}ms`);

                // Show toast notification
                if (event.code === 1006) {
                    // Code 1006 is "Abnormal Closure" which often means the server is not available
                    showToast(`WebSocket server not available. Make sure Daphne is running on port 8001. Attempting to reconnect (${reconnectAttempts}/${maxReconnectAttempts})...`, 'error');

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
                    showToast(`Connection lost. Attempting to reconnect (${reconnectAttempts}/${maxReconnectAttempts})...`, 'warning');
                }

                setTimeout(function() {
                    initializeChatWebsocket();
                }, delay);
            } else if (reconnectAttempts >= maxReconnectAttempts) {
                showToast('Unable to reconnect after multiple attempts. Please refresh the page or check if the WebSocket server is running.', 'error');
            }
        };

        chatSocket.onerror = function(e) {
            console.error('Chat WebSocket error:', e);

            // Log more detailed information
            console.log('WebSocket readyState:', chatSocket.readyState);
            console.log('WebSocket URL:', wsUrl);

            // Show error status
            showConnectionStatus('error');

            // Show toast notification
            showToast('Connection error. Trying to reconnect...', 'error');

            // Note: We don't need to manually reconnect here as the onclose handler will be called after an error
        };
    } catch (error) {
        console.error('Error creating WebSocket connection:', error);

        // Attempt to reconnect with exponential backoff
        if (reconnectAttempts < maxReconnectAttempts) {
            const delay = Math.min(baseReconnectDelay * Math.pow(1.5, reconnectAttempts), 30000);
            reconnectAttempts++;

            setTimeout(function() {
                initializeChatWebsocket();
            }, delay);
        }
    }

    return chatSocket;
}

/**
 * Show connection status to the user
 */
function showConnectionStatus(status) {
    // Check if we're on a chat page
    const messageList = document.getElementById('message-list');
    if (!messageList) return;

    // Remove any existing status messages
    const existingStatus = document.querySelector('.connection-status');
    if (existingStatus) {
        existingStatus.remove();
    }

    let statusMessage = '';
    let statusClass = '';

    switch (status) {
        case 'connected':
            // No need to show a message when connected
            return;
        case 'disconnected':
            statusMessage = 'Connection lost. Reconnecting...';
            statusClass = 'warning';
            break;
        case 'error':
            statusMessage = 'Connection error. Trying to reconnect...';
            statusClass = 'error';
            break;
    }

    // Create and add the status message
    const statusElement = document.createElement('div');
    statusElement.className = `connection-status ${statusClass}`;
    statusElement.textContent = statusMessage;

    // Add to the top of the message list
    messageList.prepend(statusElement);

    // Auto-remove after 5 seconds if it's a connected message
    if (status === 'connected') {
        setTimeout(() => {
            statusElement.remove();
        }, 5000);
    }
}

/**
 * Store messages when offline and send them when reconnected
 */
let pendingMessages = [];

function sendPendingMessages() {
    if (pendingMessages.length > 0 && chatSocket && chatSocket.readyState === WebSocket.OPEN) {
        console.log(`Sending ${pendingMessages.length} pending messages`);

        pendingMessages.forEach(message => {
            chatSocket.send(JSON.stringify(message));
        });

        // Clear the pending messages
        pendingMessages = [];
    }
}

/**
 * Initialize a conversation and its event listeners
 */
function initializeConversation(conversationId, userId, otherUser) {
    currentConversationId = conversationId;
    currentUserId = userId;
    otherUserId = otherUser;

    console.log(`Initializing conversation: ${conversationId} between user ${userId} and ${otherUser}`);

    // Hide typing indicator initially
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.style.display = 'none';
    } else {
        console.warn('Typing indicator element not found');
    }

    // Form submission event
    const messageForm = document.getElementById('message-form');
    if (messageForm) {
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            sendMessage();
        });
    } else {
        console.warn('Message form element not found');
    }

    // Typing indicator
    const messageInput = document.getElementById('message-input');
    if (messageInput) {
        messageInput.addEventListener('input', function() {
            sendTypingIndicator(true);

            // Clear existing timeout
            if (typingTimeout) {
                clearTimeout(typingTimeout);
            }

            // Set a new timeout to stop typing
            typingTimeout = setTimeout(function() {
                sendTypingIndicator(false);
            }, 3000);
        });
    } else {
        console.warn('Message input element not found');
    }

    // Mark messages as read when the page loads
    markMessagesAsRead();
}

/**
 * Handle incoming WebSocket messages
 */
function handleWebSocketMessage(data) {
    const messageType = data.type;

    switch (messageType) {
        case 'chat_message':
            handleChatMessage(data);
            break;
        case 'new_message_notification':
            handleNewMessageNotification(data);
            break;
        case 'typing_indicator':
            handleTypingIndicator(data);
            break;
        case 'messages_read':
            handleMessagesRead(data);
            break;
        case 'user_status':
            handleUserStatusUpdate(data);
            break;
        default:
            console.log('Unknown message type:', messageType);
    }
}

/**
 * Handle a new chat message
 */
function handleChatMessage(data) {
    // Only process if we are in the correct conversation
    if (currentConversationId && data.conversation_id === currentConversationId) {
        const message = data.message;
        addMessageToChat(message);

        // If the message is from the other user, mark it as read
        if (message.sender_id !== currentUserId) {
            markMessagesAsRead();
        }
    }
}

/**
 * Handle a new message notification (when in a different conversation or chat home)
 */
function handleNewMessageNotification(data) {
    const conversationId = data.conversation_id;

    // Update the conversation list if we're not in that conversation
    if (currentConversationId !== conversationId) {
        // Try to find the conversation item in the list
        const conversationItem = document.querySelector(`.conversation-item[href*="${conversationId}"]`);

        if (conversationItem) {
            // Update the unread badge
            let unreadBadge = conversationItem.querySelector('.unread-badge');
            if (!unreadBadge) {
                // Create a new badge
                const previewElement = conversationItem.querySelector('.conversation-preview');
                unreadBadge = document.createElement('span');
                unreadBadge.className = 'unread-badge';
                unreadBadge.textContent = '1';
                previewElement.appendChild(unreadBadge);
            } else {
                // Update existing badge
                const count = parseInt(unreadBadge.textContent) || 0;
                unreadBadge.textContent = count + 1;
            }

            // Update the preview text
            const previewText = conversationItem.querySelector('.conversation-preview span');
            if (previewText) {
                previewText.textContent = data.message.content.substring(0, 30);
            }

            // Move the conversation to the top of the list
            const conversationList = document.getElementById('conversation-list');
            if (conversationList) {
                conversationList.prepend(conversationItem);
            }
        }
    }
}

/**
 * Handle typing indicator updates
 */
function handleTypingIndicator(data) {
    if (currentConversationId && data.conversation_id === currentConversationId) {
        const typingIndicator = document.getElementById('typing-indicator');

        if (data.is_typing) {
            typingIndicator.style.display = 'block';
        } else {
            typingIndicator.style.display = 'none';
        }
    }
}

/**
 * Handle messages read updates
 */
function handleMessagesRead(data) {
    if (currentConversationId && data.conversation_id === currentConversationId) {
        // Update read indicators for all messages
        const messages = document.querySelectorAll('.message-item.outgoing');
        messages.forEach(function(messageElement) {
            const statusElement = messageElement.querySelector('.message-status');
            if (statusElement) {
                statusElement.innerHTML = '<i class="fas fa-check-double read-indicator"></i>';
            }
        });
    }
}

/**
 * Handle user status updates
 */
function handleUserStatusUpdate(data) {
    const userId = data.user_id;
    const isOnline = data.status;
    const lastSeen = data.last_seen;

    // Update status indicators for this user
    const statusIndicators = document.querySelectorAll(`.status-indicator[data-user-id="${userId}"]`);

    statusIndicators.forEach(function(indicator) {
        if (isOnline) {
            indicator.classList.add('online');
            indicator.classList.remove('offline');
        } else {
            indicator.classList.add('offline');
            indicator.classList.remove('online');
        }
    });

    // Update the status text in conversation header if this is the current conversation
    if (otherUserId && userId === otherUserId) {
        const statusText = document.querySelector('.status-text');
        if (statusText) {
            if (isOnline) {
                statusText.textContent = 'Online';
            } else if (lastSeen) {
                // Format the last seen time
                const lastSeenDate = new Date(lastSeen);
                const now = new Date();
                const diffMs = now - lastSeenDate;
                const diffMins = Math.round(diffMs / 60000);
                const diffHours = Math.round(diffMs / 3600000);
                const diffDays = Math.round(diffMs / 86400000);

                let lastSeenText = '';
                if (diffMins < 1) {
                    lastSeenText = 'Just now';
                } else if (diffMins < 60) {
                    lastSeenText = `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
                } else if (diffHours < 24) {
                    lastSeenText = `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
                } else if (diffDays < 7) {
                    lastSeenText = `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
                } else {
                    // Format as date
                    const options = { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
                    lastSeenText = lastSeenDate.toLocaleDateString(undefined, options);
                }

                statusText.textContent = `Last seen ${lastSeenText}`;
            } else {
                statusText.textContent = 'Offline';
            }
        }
    }
}

/**
 * Send a new message
 */
function sendMessage() {
    const messageInput = document.getElementById('message-input');
    if (!messageInput) {
        console.error('Message input element not found');
        showToast('Error: Could not find message input', 'error');
        return;
    }

    const content = messageInput.value.trim();

    if (!currentConversationId) {
        console.error('No conversation ID set');
        showToast('Error: No active conversation', 'error');
        return;
    }

    if (content) {
        const messageData = {
            'type': 'chat_message',
            'conversation_id': currentConversationId,
            'content': content
        };

        // Check if we're connected
        if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
            try {
                // Send the message through WebSocket
                chatSocket.send(JSON.stringify(messageData));
                console.log('Message sent:', messageData);

                // Add a temporary message to the UI
                const tempMessage = {
                    sender_id: currentUserId,
                    content: content,
                    timestamp: new Date().toISOString(),
                    is_read: false
                };
                addMessageToChat(tempMessage);
            } catch (error) {
                console.error('Error sending message:', error);
                showToast('Error sending message. Please try again.', 'error');
            }
        } else {
            console.log('WebSocket not connected, storing message for later');
            // We're offline, store the message to send later
            pendingMessages.push(messageData);

            // Add a temporary message to the UI with offline indicator
            const tempMessage = {
                sender_id: currentUserId,
                content: content,
                timestamp: new Date().toISOString(),
                is_read: false,
                is_pending: true
            };
            addMessageToChat(tempMessage);

            // Show offline toast
            showToast('You are currently offline. Message will be sent when connection is restored.', 'warning');
        }

        // Clear the input
        messageInput.value = '';

        // Reset typing indicator
        if (typingTimeout) {
            clearTimeout(typingTimeout);
        }
        sendTypingIndicator(false);

        // Focus the input again
        messageInput.focus();
    }
}

/**
 * Show a toast notification
 */
function showToast(message, type = 'info') {
    console.log(`Toast: ${type} - ${message}`);

    // Check if the global showToastNotification function exists (from main site)
    if (typeof window.showToastNotification === 'function') {
        // Use the global toast function
        window.showToastNotification(message, type);
        return;
    }

    // If we're here, the global function doesn't exist, so we'll use our own implementation

    // Fallback implementation if global function doesn't exist
    // Check if toast container exists, create if not
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }

    // Create toast element with proper structure
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    // Create icon element
    const iconElement = document.createElement('div');
    iconElement.className = 'toast-icon';

    // Set icon based on type
    let iconSvg = '';
    switch (type) {
        case 'success':
            iconSvg = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>';
            break;
        case 'error':
            iconSvg = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>';
            break;
        case 'warning':
            iconSvg = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>';
            break;
        default: // info
            iconSvg = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>';
    }

    iconElement.innerHTML = iconSvg;

    // Create content element
    const contentElement = document.createElement('div');
    contentElement.className = 'toast-content';
    contentElement.innerHTML = `<p>${message}</p>`;

    // Create close button
    const closeButton = document.createElement('button');
    closeButton.className = 'toast-close';
    closeButton.setAttribute('aria-label', 'Close notification');
    closeButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';

    // Add event listener to close button
    closeButton.addEventListener('click', () => {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
        }, 300);
    });

    // Assemble the toast
    toast.appendChild(iconElement);
    toast.appendChild(contentElement);
    toast.appendChild(closeButton);

    // Add to container
    toastContainer.appendChild(toast);

    // Show the toast
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, 300);
        }
    }, 5000);
}

/**
 * Send a typing indicator update
 */
function sendTypingIndicator(isTyping) {
    if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
        chatSocket.send(JSON.stringify({
            'type': 'typing',
            'conversation_id': currentConversationId,
            'is_typing': isTyping
        }));
    }
}

/**
 * Mark messages as read
 */
function markMessagesAsRead() {
    if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
        chatSocket.send(JSON.stringify({
            'type': 'read_messages',
            'conversation_id': currentConversationId
        }));

        // Remove unread badge from this conversation in the list
        const conversationItem = document.querySelector(`.conversation-item[href*="${currentConversationId}"]`);
        if (conversationItem) {
            const unreadBadge = conversationItem.querySelector('.unread-badge');
            if (unreadBadge) {
                unreadBadge.remove();
            }
        }
    }
}

/**
 * Add a message to the chat UI
 */
function addMessageToChat(message) {
    try {
        const messageList = document.getElementById('message-list');
        if (!messageList) {
            console.error('Message list element not found');
            return;
        }

        if (!message) {
            console.error('No message data provided');
            return;
        }

        if (!message.content) {
            console.warn('Message has no content');
            return;
        }

        if (!currentUserId) {
            console.warn('Current user ID not set');
        }

        const isOutgoing = message.sender_id === currentUserId;
        console.log(`Adding ${isOutgoing ? 'outgoing' : 'incoming'} message:`, message);

        // Create the message element
        const messageElement = document.createElement('div');
        messageElement.className = `message-item ${isOutgoing ? 'outgoing' : 'incoming'}`;

        // Add data attributes for potential future reference
        if (message.id) {
            messageElement.dataset.messageId = message.id;
        }

        // Create the message content
        const contentElement = document.createElement('div');
        contentElement.className = 'message-content';
        contentElement.textContent = message.content;

        // Create the message meta information
        const metaElement = document.createElement('div');
        metaElement.className = 'message-meta';

        // Add timestamp
        const timeElement = document.createElement('span');
        timeElement.className = 'message-time';

        // Format the timestamp
        try {
            const timestamp = new Date(message.timestamp);
            const hours = timestamp.getHours();
            const minutes = timestamp.getMinutes();
            const ampm = hours >= 12 ? 'PM' : 'AM';
            const formattedHours = hours % 12 || 12;
            const formattedMinutes = minutes < 10 ? '0' + minutes : minutes;
            timeElement.textContent = `${formattedHours}:${formattedMinutes} ${ampm}`;
        } catch (error) {
            console.warn('Error formatting timestamp:', error);
            timeElement.textContent = 'Just now';
        }

        // Add read status for outgoing messages
        if (isOutgoing) {
            const statusElement = document.createElement('span');
            statusElement.className = 'message-status';

            const statusIcon = document.createElement('i');

            if (message.is_pending) {
                // Show clock icon for pending messages
                statusIcon.className = 'fas fa-clock pending-indicator';
                statusElement.setAttribute('aria-label', 'Pending');

                // Add a tooltip
                statusElement.title = 'Message will be sent when you are back online';
            } else if (message.is_read) {
                statusIcon.className = 'fas fa-check-double read-indicator';
                statusElement.setAttribute('aria-label', 'Read');
            } else {
                statusIcon.className = 'fas fa-check';
                statusElement.setAttribute('aria-label', 'Sent');
            }

            statusElement.appendChild(statusIcon);
            metaElement.appendChild(statusElement);
        }

        // Assemble the message element
        metaElement.prepend(timeElement);
        messageElement.appendChild(contentElement);
        messageElement.appendChild(metaElement);

        // Add ARIA attributes for accessibility
        messageElement.setAttribute('role', 'article');
        messageElement.setAttribute('aria-label',
            `${isOutgoing ? 'You' : 'Other user'} at ${timeElement.textContent}`);

        // Check if we need to remove the empty message placeholder
        const emptyMessages = messageList.querySelector('.empty-messages');
        if (emptyMessages) {
            emptyMessages.remove();
        }

        // Add the message to the chat
        messageList.appendChild(messageElement);

        // Scroll to the new message
        messageList.scrollTop = messageList.scrollHeight;

        // Add animation class after a small delay (for better animation)
        setTimeout(() => {
            messageElement.classList.add('visible');
        }, 10);
    } catch (error) {
        console.error('Error adding message to chat:', error);
    }
}

// Handle network status changes
window.addEventListener('online', function() {
    console.log('Network connection restored');
    showToast('You are back online', 'success');

    // Reconnect WebSocket if needed
    if (!chatSocket || chatSocket.readyState !== WebSocket.OPEN) {
        initializeChatWebsocket();
    }

    // Send any pending messages
    sendPendingMessages();
});

window.addEventListener('offline', function() {
    console.log('Network connection lost');
    showToast('You are offline. Messages will be sent when you reconnect.', 'warning');

    // Update UI to show offline status
    showConnectionStatus('disconnected');
});

// Check initial network status when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Check initial network status
    if (!navigator.onLine) {
        showToast('You are currently offline. Messages will be sent when you reconnect.', 'warning');
    }

    // Initialize mobile menu toggle for chat sidebar
    const menuToggle = document.querySelector('.menu-toggle');
    const chatSidebar = document.querySelector('.contacts');
    const sidebarOverlay = document.querySelector('.sidebar-overlay');

    if (menuToggle && chatSidebar) {
        console.log('Found menu toggle and chat sidebar');
        menuToggle.addEventListener('click', function() {
            chatSidebar.classList.toggle('active');
            if (sidebarOverlay) {
                sidebarOverlay.classList.toggle('active');
            }
        });

        if (sidebarOverlay) {
            sidebarOverlay.addEventListener('click', function() {
                chatSidebar.classList.remove('active');
                sidebarOverlay.classList.remove('active');
            });
        }
    } else {
        console.log('Mobile menu elements not found:', {
            menuToggle: !!menuToggle,
            chatSidebar: !!chatSidebar,
            sidebarOverlay: !!sidebarOverlay
        });
    }

    // Add animation classes to message items
    const messageItems = document.querySelectorAll('.message-item');
    if (messageItems.length > 0) {
        messageItems.forEach(function(item, index) {
            setTimeout(function() {
                item.classList.add('visible');
            }, index * 100); // Stagger the animations
        });
    }
});