/**
 * Chat functionality for real-time messaging
 * Enhanced with improved UI/UX and dark mode support
 */

// Define chatSocket as a global variable
window.chatSocket = null;
let currentConversationId = null;
let currentUserId = null;
let otherUserId = null;
let typingTimeout = null;

// Track reconnection attempts
window.reconnectAttempts = 0;
window.maxReconnectAttempts = 10; // Make this a window property to avoid redeclaration conflicts
// Use window property to avoid redeclaration conflicts with other scripts
window.chatBaseReconnectDelay = 1000; // 1 second

/**
 * Get CSRF token from cookie or Django's csrftoken input
 */
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

/**
 * Initialize the WebSocket connection for chat
 */
function initializeChatWebsocket() {
    console.log('Initializing WebSocket connection...');
    // Close any existing connection
    if (window.chatSocket !== null && window.chatSocket !== undefined) {
        try {
            window.chatSocket.close();
            console.log('Closed existing WebSocket connection');
        } catch (error) {
            console.error('Error closing existing WebSocket connection:', error);
        }
    }

    // Create a new WebSocket connection with CSRF protection
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

    let wsPath = '/ws/chat/';
    let wsHost = window.location.host;

    // With Nginx as reverse proxy, we use the same host for both HTTP and WebSockets
    console.log('Using WebSocket host:', wsHost);
    console.log('Using Nginx reverse proxy for routing');



    // Add CSRF token to WebSocket URL as a query parameter
    const csrfToken = getCSRFToken();

    // Try multiple URL formats to ensure compatibility with server routing
    // First try with trailing slash (which is the primary format in routing.py)
    const wsUrl = `${wsProtocol}//${wsHost}${wsPath}?csrf_token=${csrfToken}`;

    console.log('Attempting to connect to WebSocket at:', wsUrl);
    console.log('CSRF Token:', csrfToken);
    console.log('WebSocket Protocol:', wsProtocol);
    console.log('WebSocket Host:', wsHost);

    // Log the current URL for debugging
    console.log('Current page URL:', window.location.href);

    try {
        // Make sure we're using the global chatSocket variable
        window.chatSocket = new WebSocket(wsUrl);
        console.log('WebSocket created:', window.chatSocket);

        // Add error handler
        window.chatSocket.onerror = function(error) {
            console.error('WebSocket error:', error);
            showToast('WebSocket connection error. Check console for details.', 'error');
        };

        // WebSocket event handlers
        window.chatSocket.onopen = function() {
            console.log('Chat WebSocket connection established');
            console.log('WebSocket readyState:', window.chatSocket.readyState);

            // Reset reconnect attempts on successful connection
            window.reconnectAttempts = 0;

            // Show connection status
            showConnectionStatus('connected');

            // If we were reconnecting, send any pending messages
            sendPendingMessages();
        };

        window.chatSocket.onmessage = function(e) {
            try {
                const data = JSON.parse(e.data);
                handleWebSocketMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        window.chatSocket.onclose = function(event) {
            // Check if the close was clean (code 1000 or 1001)
            const wasClean = event.code === 1000 || event.code === 1001;

            console.log(`Chat WebSocket connection closed. Code: ${event.code}, Clean: ${wasClean}, Reason: ${event.reason}`);

            // Log more detailed information about the close event
            console.log('WebSocket close event details:', {
                code: event.code,
                reason: event.reason,
                wasClean: event.wasClean,
                type: event.type,
                target: event.target.url
            });

            // Show disconnected status
            showConnectionStatus('disconnected');

            // Only attempt to reconnect if it wasn't a clean close and we haven't exceeded max attempts
            if (!wasClean && window.reconnectAttempts < window.maxReconnectAttempts) {
                // Use exponential backoff for reconnection
                const delay = Math.min(window.chatBaseReconnectDelay * Math.pow(1.5, window.reconnectAttempts), 30000);
                window.reconnectAttempts++;

                console.log(`Attempting to reconnect (${window.reconnectAttempts}/${window.maxReconnectAttempts}) in ${delay}ms`);

                // Show toast notification
                if (event.code === 1006) {
                    // Code 1006 is "Abnormal Closure" which often means the server is not available
                    showToast(`WebSocket server not available. Make sure Daphne is running on port 8001. Attempting to reconnect (${window.reconnectAttempts}/${window.maxReconnectAttempts})...`, 'error');

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
                    showToast(`Connection lost. Attempting to reconnect (${window.reconnectAttempts}/${window.maxReconnectAttempts})...`, 'warning');
                }

                setTimeout(function() {
                    initializeChatWebsocket();
                }, delay);
            } else if (window.reconnectAttempts >= window.maxReconnectAttempts) {
                showToast('Unable to reconnect after multiple attempts. Please refresh the page or check if the WebSocket server is running.', 'error');
            }
        };

        window.chatSocket.onerror = function(e) {
            console.error('Chat WebSocket error:', e);

            // Log more detailed information
            console.log('WebSocket readyState:', window.chatSocket ? window.chatSocket.readyState : 'N/A');
            console.log('WebSocket URL:', wsUrl);

            // Show error status
            showConnectionStatus('error');

            // Show toast notification
            showToast('Connection error. Trying to reconnect...', 'error');

            // Note: We don't need to manually reconnect here as the onclose handler will be called after an error
        };
    } catch (error) {
        console.error('Error creating WebSocket connection:', error);
        console.error('Error details:', error.message);
        console.error('Stack trace:', error.stack);

        // Attempt to reconnect with exponential backoff
        if (window.reconnectAttempts < window.maxReconnectAttempts) {
            const delay = Math.min(window.chatBaseReconnectDelay * Math.pow(1.5, window.reconnectAttempts), 30000);
            window.reconnectAttempts++;

            showToast(`Error creating WebSocket connection. Attempting to reconnect (${window.reconnectAttempts}/${window.maxReconnectAttempts})...`, 'error');

            setTimeout(function() {
                initializeChatWebsocket();
            }, delay);
        }
    }

    return window.chatSocket;
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
    // Check if we have any pending messages
    if (pendingMessages.length === 0) {
        console.log('No pending messages to send');
        return;
    }

    // Check WebSocket connection status
    if (!window.chatSocket) {
        console.warn('Cannot send pending messages: WebSocket not initialized');
        // Try to initialize the WebSocket
        window.chatSocket = initializeChatWebsocket();
        return;
    }

    // Send pending messages if WebSocket is open
    if (window.chatSocket.readyState === WebSocket.OPEN) {
        console.log(`Sending ${pendingMessages.length} pending messages`);

        // Create a copy of the pending messages array
        const messagesToSend = [...pendingMessages];

        // Clear the pending messages array before sending
        // This prevents messages from being added to the array while we're sending
        pendingMessages = [];

        // Send each message
        messagesToSend.forEach(message => {
            try {
                window.chatSocket.send(JSON.stringify(message));
                console.log('Pending message sent:', message);

                // Update UI for this message if it's in the current conversation
                if (message.type === 'chat_message' && message.conversation_id === currentConversationId) {
                    // Find the pending message in the UI and update its status
                    const messageElements = document.querySelectorAll('.message-item.outgoing.pending');
                    messageElements.forEach(element => {
                        const contentElement = element.querySelector('.message-content');
                        if (contentElement && contentElement.textContent === message.content) {
                            // Remove pending class and update status icon
                            element.classList.remove('pending');
                            const statusElement = element.querySelector('.message-status');
                            if (statusElement) {
                                statusElement.innerHTML = '<i class="fas fa-check"></i>';
                            }
                        }
                    });
                }
            } catch (error) {
                console.error('Error sending pending message:', error);
                // Add the message back to the pending messages array
                pendingMessages.push(message);
            }
        });

        // Show success message if all messages were sent
        if (pendingMessages.length === 0) {
            console.log('All pending messages sent successfully');
            showToast('Your offline messages have been sent', 'success');
        } else {
            console.warn(`${pendingMessages.length} messages could not be sent and will be retried later`);
        }
    } else {
        console.warn('Cannot send pending messages: WebSocket not open (readyState:', window.chatSocket.readyState, ')');
    }
}

/**
 * Initialize a conversation and its event listeners
 */
function initializeConversation(conversationId, userId, otherUser) {
    // Store conversation information in global variables
    currentConversationId = conversationId;
    currentUserId = userId;
    otherUserId = otherUser;

    console.log(`Initializing conversation: ${conversationId} between user ${userId} and ${otherUser}`);

    // Make sure WebSocket is initialized
    if (!window.chatSocket || window.chatSocket.readyState === WebSocket.CLOSED) {
        console.log('WebSocket not initialized or closed, initializing now');
        window.chatSocket = initializeChatWebsocket();
    }

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
        // Remove any existing event listeners to prevent duplicates
        const newMessageForm = messageForm.cloneNode(true);
        messageForm.parentNode.replaceChild(newMessageForm, messageForm);

        // Add event listener to the new form
        newMessageForm.addEventListener('submit', function (e) {
            console.log('Form submitted');
            e.preventDefault();
            sendMessage();
            console.log('Form submission prevented');
        });

        // Store reference to the new form
        window.messageForm = newMessageForm;
    } else {
        console.warn('Message form element not found');
    }

    // Typing indicator
    const messageInput = document.getElementById('message-input');
    if (messageInput) {
        // Focus the input field
        setTimeout(() => {
            messageInput.focus();
        }, 500);

        // Remove any existing event listeners to prevent duplicates
        const newMessageInput = messageInput.cloneNode(true);
        messageInput.parentNode.replaceChild(newMessageInput, messageInput);

        // Add input event listener for typing indicator
        newMessageInput.addEventListener('input', function () {
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

        // Add keypress event listener for Enter key
        newMessageInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                console.log('Enter key pressed');
                e.preventDefault();
                sendMessage();
                console.log('Enter key press prevented');
            }
        });

        // Store reference to the new input
        window.messageInput = newMessageInput;
    } else {
        console.warn('Message input element not found');
    }

    // Add send button click event
    const sendButton = document.getElementById('send-button');
    if (sendButton) {
        // Remove any existing event listeners to prevent duplicates
        const newSendButton = sendButton.cloneNode(true);
        sendButton.parentNode.replaceChild(newSendButton, sendButton);

        // Add event listener to the new button
        newSendButton.addEventListener('click', function (e) {
            console.log('Send button clicked');
            e.preventDefault();
            sendMessage();
        });
    }

    // Mark messages as read when the page loads
    markMessagesAsRead();

    // Send any pending messages
    sendPendingMessages();

    console.log('Conversation initialization complete');
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

        if (!typingIndicator) {
            console.error('Typing indicator element not found');
            return;
        }

        if (data.is_typing) {
            // Make sure the typing indicator is visible
            typingIndicator.style.display = 'flex';
            typingIndicator.classList.add('active');

            // Auto-hide after 10 seconds in case we don't get the "stopped typing" event
            if (window.typingTimeout) {
                clearTimeout(window.typingTimeout);
            }

            window.typingTimeout = setTimeout(() => {
                typingIndicator.classList.remove('active');
                typingIndicator.style.display = 'none';
            }, 10000);
        } else {
            typingIndicator.classList.remove('active');
            typingIndicator.style.display = 'none';

            if (window.typingTimeout) {
                clearTimeout(window.typingTimeout);
            }
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
 * Format last seen timestamp
 */
function formatLastSeen(timestamp) {
    if (!timestamp) return 'Unknown';

    const lastSeenDate = new Date(timestamp);
    const now = new Date();
    const diffMs = now - lastSeenDate;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

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
        // Format as date with time
        const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
        lastSeenText = lastSeenDate.toLocaleDateString(undefined, options);
    }

    return lastSeenText;
}

/**
 * Handle user status updates
 */
function handleUserStatusUpdate(data) {
    const userId = data.user_id;
    const isOnline = data.status;
    const lastSeen = data.last_seen;

    console.log('User status update received:', data);

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

    // Update status in conversation list
    const conversationItems = document.querySelectorAll(`.conversation-item[data-user-id="${userId}"]`);
    conversationItems.forEach(function(item) {
        const statusText = item.querySelector('.conversation-preview span');
        if (statusText) {
            if (isOnline) {
                statusText.textContent = 'Online';
            } else if (lastSeen) {
                statusText.textContent = `Last seen ${formatLastSeen(lastSeen)}`;
            } else {
                statusText.textContent = 'Offline';
            }
        }
    });

    // Update the status text in conversation header if this is the current conversation
    if (otherUserId && userId === otherUserId) {
        const statusText = document.querySelector('.status-text');
        if (statusText) {
            if (isOnline) {
                statusText.textContent = 'Online';
                statusText.classList.add('online');
            } else if (lastSeen) {
                statusText.textContent = `Last seen ${formatLastSeen(lastSeen)}`;
                statusText.classList.remove('online');
            } else {
                statusText.textContent = 'Offline';
                statusText.classList.remove('online');
            }
        }
    }

    // Also update user status in the conversation header
    const userStatus = document.querySelector('.user-status');
    if (userStatus && userStatus.closest('.conversation-header') &&
        userStatus.closest('.conversation-header').getAttribute('data-user-id') === userId.toString()) {
        if (isOnline) {
            userStatus.textContent = 'Online';
            userStatus.classList.add('online');
        } else if (lastSeen) {
            userStatus.textContent = `Last seen ${formatLastSeen(lastSeen)}`;
            userStatus.classList.remove('online');
        } else {
            userStatus.textContent = 'Offline';
            userStatus.classList.remove('online');
        }
    }
}

/**
 * Send a new message
 */
function sendMessage() {
    console.log('sendMessage function called');
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

        // Check if we're connected - use window.chatSocket to ensure we're using the global variable
        console.log('Checking WebSocket connection:', window.chatSocket ? 'exists' : 'null');
        console.log('WebSocket readyState:', window.chatSocket ? window.chatSocket.readyState : 'N/A');

        // If WebSocket is not initialized or closed, try to initialize it
        if (!window.chatSocket || window.chatSocket.readyState === WebSocket.CLOSED) {
            console.log('WebSocket not initialized or closed, initializing now');
            window.chatSocket = initializeChatWebsocket();

            // Store the message to send after connection is established
            pendingMessages.push(messageData);

            // Add a temporary message to the UI with pending indicator
            const tempMessage = {
                sender_id: currentUserId,
                content: content,
                timestamp: new Date().toISOString(),
                is_read: false,
                is_pending: true
            };
            addMessageToChat(tempMessage);

            // Clear the input
            messageInput.value = '';

            // Reset typing indicator
            if (typingTimeout) {
                clearTimeout(typingTimeout);
            }
            sendTypingIndicator(false);

            // Focus the input again
            messageInput.focus();

            return;
        }

        if (window.chatSocket && window.chatSocket.readyState === WebSocket.OPEN) {
            console.log('WebSocket is open, sending message');
            try {
                // Send the message through WebSocket - use window.chatSocket to ensure we're using the global variable
                window.chatSocket.send(JSON.stringify(messageData));
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
                showToast('Error sending message. Trying REST API fallback...', 'warning');

                // Fallback to REST API
                sendMessageViaRESTAPI(currentConversationId, content);
            }
        } else if (window.chatSocket && window.chatSocket.readyState === WebSocket.CONNECTING) {
            console.log('WebSocket is connecting, storing message for later');
            // We're connecting, store the message to send later
            pendingMessages.push(messageData);

            // Add a temporary message to the UI with pending indicator
            const tempMessage = {
                sender_id: currentUserId,
                content: content,
                timestamp: new Date().toISOString(),
                is_read: false,
                is_pending: true
            };
            addMessageToChat(tempMessage);

            // Show connecting toast
            showToast('Connecting to chat server. Your message will be sent when connected.', 'info');
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
 * Send a message via REST API as a fallback when WebSocket is not available
 */
function sendMessageViaRESTAPI(conversationId, content) {
    console.log('Sending message via REST API:', {conversationId, content});

    // Get CSRF token for the POST request
    const csrfToken = getCSRFToken();

    // Create the request
    fetch(`/api/chat/conversations/${conversationId}/add_message/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({content: content})
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Message sent via REST API:', data);
            showToast('Message sent successfully', 'success');

            // Add the message to the UI if it's not already there
            const tempMessage = {
                sender_id: currentUserId,
                content: content,
                timestamp: new Date().toISOString(),
                is_read: false,
                id: data.id
            };
            addMessageToChat(tempMessage);
        })
        .catch(error => {
            console.error('Error sending message via REST API:', error);
            showToast('Error sending message. Please try again later.', 'error');
        });
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
    // Only send typing indicator if we have a conversation ID
    if (!currentConversationId) {
        console.warn('Cannot send typing indicator: No conversation ID set');
        return;
    }

    // Prepare the typing indicator data
    const typingData = {
        'type': 'typing',
        'conversation_id': currentConversationId,
        'is_typing': isTyping
    };

    console.log('Sending typing indicator:', isTyping ? 'typing' : 'stopped typing');

    // Check WebSocket connection status
    if (!window.chatSocket) {
        console.warn('Cannot send typing indicator: WebSocket not initialized');
        // Try to initialize the WebSocket
        window.chatSocket = initializeChatWebsocket();
        return;
    }

    // Send typing indicator if WebSocket is open
    if (window.chatSocket.readyState === WebSocket.OPEN) {
        try {
            window.chatSocket.send(JSON.stringify(typingData));
            console.log('Typing indicator sent:', isTyping);
        } catch (error) {
            console.error('Error sending typing indicator:', error);
        }
    } else {
        console.warn('Cannot send typing indicator: WebSocket not open (readyState:', window.chatSocket.readyState, ')');

        // Try to reconnect WebSocket
        if (window.chatSocket.readyState === WebSocket.CLOSED) {
            console.log('WebSocket is closed, attempting to reconnect...');
            window.chatSocket = initializeChatWebsocket();
        }
    }
}

/**
 * Mark messages as read
 */
function markMessagesAsRead() {
    // Only mark messages as read if we have a conversation ID
    if (!currentConversationId) {
        console.warn('Cannot mark messages as read: No conversation ID set');
        return;
    }

    // Prepare the read messages data
    const readData = {
        'type': 'read_messages',
        'conversation_id': currentConversationId
    };

    // Check WebSocket connection status
    if (!window.chatSocket) {
        console.warn('Cannot mark messages as read: WebSocket not initialized');
        // Try to initialize the WebSocket
        initializeChatWebsocket();

        // Also mark messages as read via REST API as a fallback
        markMessagesAsReadViaAPI(currentConversationId);
        return;
    }

    // Send read messages notification if WebSocket is open
    if (window.chatSocket.readyState === WebSocket.OPEN) {
        try {
            window.chatSocket.send(JSON.stringify(readData));
            console.log('Messages marked as read for conversation:', currentConversationId);

            // Remove unread badge from this conversation in the list
            const conversationItem = document.querySelector(`.conversation-item[href*="${currentConversationId}"]`);
            if (conversationItem) {
                const unreadBadge = conversationItem.querySelector('.unread-badge');
                if (unreadBadge) {
                    unreadBadge.remove();
                }
            }
        } catch (error) {
            console.error('Error marking messages as read:', error);
        }
    } else {
        console.warn('Cannot mark messages as read: WebSocket not open (readyState:', window.chatSocket.readyState, ')');
    }
}

/**
 * Mark messages as read via REST API (fallback when WebSocket is not available)
 */
function markMessagesAsReadViaAPI(conversationId) {
    if (!conversationId) {
        console.warn('Cannot mark messages as read: No conversation ID provided');
        return;
    }

    console.log('Marking messages as read via REST API for conversation:', conversationId);

    // Get CSRF token for the POST request
    const csrfToken = getCSRFToken();

    // Create the request
    fetch(`/api/chat/conversations/${conversationId}/mark_read/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Messages marked as read via API:', data);

        // Remove unread badge from this conversation in the list
        const conversationItem = document.querySelector(`.conversation-item[href*="${conversationId}"]`);
        if (conversationItem) {
            const unreadBadge = conversationItem.querySelector('.unread-badge');
            if (unreadBadge) {
                unreadBadge.remove();
            }
        }
    })
    .catch(error => {
        console.error('Error marking messages as read via API:', error);
    });
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

        // Check if this is a file message
        if (message.is_file || message.file_attachment || message.file_name) {
            // This is a file message
            const fileType = message.file_type || (message.file_attachment && message.file_attachment.includes('image') ? 'image' : 'document');
            const fileName = message.file_name || 'Attachment';

            // Create file attachment element
            const fileUrl = message.file_url || (message.file_attachment ? '/media/' + message.file_attachment : null);
            console.log('File URL for display:', fileUrl);

            if (fileType === 'image' && fileUrl) {
                // For images, show a preview
                const imgElement = document.createElement('img');
                imgElement.className = 'message-image';
                imgElement.src = fileUrl;
                imgElement.alt = fileName;
                imgElement.addEventListener('click', () => {
                    // Open image in new tab when clicked
                    window.open(fileUrl, '_blank');
                });
                contentElement.appendChild(imgElement);
            } else {
                // For other files, show an icon and filename
                const fileElement = document.createElement('div');
                fileElement.className = 'message-file';

                // Determine file icon based on type
                let fileIconClass = 'fa-file';
                if (fileType === 'image') {
                    fileIconClass = 'fa-file-image';
                } else if (fileType === 'document' || fileName.endsWith('.pdf')) {
                    fileIconClass = 'fa-file-pdf';
                } else if (fileName.endsWith('.doc') || fileName.endsWith('.docx')) {
                    fileIconClass = 'fa-file-word';
                } else if (fileName.endsWith('.txt')) {
                    fileIconClass = 'fa-file-alt';
                }

                fileElement.innerHTML = `
                    <i class="fas ${fileIconClass}"></i>
                    <span class="file-name">${fileName}</span>
                `;

                // Add click handler to download if we have a URL
                if (fileUrl) {
                    fileElement.addEventListener('click', () => {
                        window.open(fileUrl, '_blank');
                    });
                    fileElement.style.cursor = 'pointer';
                }

                contentElement.appendChild(fileElement);
            }

            // Add message text if any
            if (message.content && message.content !== fileName) {
                const textElement = document.createElement('div');
                textElement.className = 'message-text';
                textElement.textContent = message.content;
                contentElement.appendChild(textElement);
            }
        } else {
            // Regular text message
            // Use textContent instead of innerHTML to prevent XSS attacks
            contentElement.textContent = message.content;
        }

        // Apply simple text formatting (convert URLs to links)
        if (message.content) {
            // First create the text node safely
            contentElement.textContent = message.content;

            // Then find and replace URLs with actual links
            const contentText = contentElement.textContent;
            contentElement.innerHTML = '';  // Clear the element

            // Use a safe URL regex pattern
            const urlRegex = /(https?:\/\/[^\s]+)/g;
            let lastIndex = 0;
            let match;

            // Process each URL match
            while ((match = urlRegex.exec(contentText)) !== null) {
                // Add text before the URL
                if (match.index > lastIndex) {
                    contentElement.appendChild(
                        document.createTextNode(contentText.substring(lastIndex, match.index))
                    );
                }

                // Create a safe link element
                const link = document.createElement('a');
                link.href = match[0];
                link.textContent = match[0];
                link.target = '_blank';
                link.rel = 'noopener noreferrer';  // Security best practice for external links

                // Add the link
                contentElement.appendChild(link);

                lastIndex = match.index + match[0].length;
            }

            // Add any remaining text
            if (lastIndex < contentText.length) {
                contentElement.appendChild(
                    document.createTextNode(contentText.substring(lastIndex))
                );
            }
        }

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
    if (!window.chatSocket || window.chatSocket.readyState !== WebSocket.OPEN) {
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

/**
 * Initialize mobile menu functionality
 */
function initializeMobileMenu() {
    const menuToggle = document.querySelector('.menu-toggle');
    const chatSidebar = document.querySelector('.chat-sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');

    if (menuToggle && chatSidebar) {
        console.log('Found menu toggle and chat sidebar');

        // Toggle sidebar when menu button is clicked
        menuToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            // Toggle active class on sidebar
            chatSidebar.classList.toggle('active');

            // Toggle active class on overlay
            if (sidebarOverlay) {
                sidebarOverlay.classList.toggle('active');
            }

            // Update ARIA attributes for accessibility
            const isExpanded = chatSidebar.classList.contains('active');
            menuToggle.setAttribute('aria-expanded', isExpanded);
        });

        // Close sidebar when overlay is clicked
        if (sidebarOverlay) {
            sidebarOverlay.addEventListener('click', function() {
                chatSidebar.classList.remove('active');
                sidebarOverlay.classList.remove('active');
                menuToggle.setAttribute('aria-expanded', 'false');
            });
        }

        // Handle escape key to close sidebar
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && chatSidebar.classList.contains('active')) {
                chatSidebar.classList.remove('active');
                if (sidebarOverlay) {
                    sidebarOverlay.classList.remove('active');
                }
                menuToggle.setAttribute('aria-expanded', 'false');
            }
        });

        // Add scrollbar to sidebar content on low-resolution screens
        if (window.matchMedia('(max-height: 700px)').matches) {
            const conversationList = chatSidebar.querySelector('.conversation-list');
            if (conversationList) {
                conversationList.classList.add('low-res-scroll');
            }
        }
    } else {
        console.log('Mobile menu elements not found:', {
            menuToggle: !!menuToggle,
            chatSidebar: !!chatSidebar,
            sidebarOverlay: !!sidebarOverlay
        });
    }
}

// Check initial network status when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Check initial network status
    if (!navigator.onLine) {
        showToast('You are currently offline. Messages will be sent when you reconnect.', 'warning');
    }

    // Initialize mobile menu
    initializeMobileMenu();

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

/**
 * Initialize emoji picker functionality
 */
function initializeEmojiPicker() {
    const emojiButton = document.getElementById('emoji-button');
    const emojiPicker = document.getElementById('emoji-picker');
    const closeEmojiButton = document.getElementById('close-emoji');
    const emojis = document.querySelectorAll('.emoji');
    const messageInput = document.getElementById('message-input');

    if (!emojiButton || !emojiPicker) {
        console.log('Emoji picker elements not found');
        return;
    }

    console.log('Initializing emoji picker with button:', emojiButton);

    // Remove any existing event listeners to prevent duplicates
    const newEmojiButton = emojiButton.cloneNode(true);
    emojiButton.parentNode.replaceChild(newEmojiButton, emojiButton);

    // Toggle emoji picker with the new button
    newEmojiButton.addEventListener('click', function (e) {
        console.log('Emoji button clicked');
        e.preventDefault();
        e.stopPropagation();
        emojiPicker.classList.toggle('active');
    });

    // Close emoji picker
    if (closeEmojiButton) {
        const newCloseButton = closeEmojiButton.cloneNode(true);
        closeEmojiButton.parentNode.replaceChild(newCloseButton, closeEmojiButton);

        newCloseButton.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            emojiPicker.classList.remove('active');
        });
    }

    // Add emoji to message input
    emojis.forEach(function (emoji) {
        emoji.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();

            const emojiChar = this.getAttribute('data-emoji');
            if (!messageInput) {
                console.error('Message input not found');
                return;
            }

            const cursorPos = messageInput.selectionStart;
            const textBefore = messageInput.value.substring(0, cursorPos);
            const textAfter = messageInput.value.substring(cursorPos);

            messageInput.value = textBefore + emojiChar + textAfter;
            messageInput.focus();
            messageInput.selectionStart = cursorPos + emojiChar.length;
            messageInput.selectionEnd = cursorPos + emojiChar.length;

            // Trigger input event to activate typing indicator
            const inputEvent = new Event('input', { bubbles: true });
            messageInput.dispatchEvent(inputEvent);

            // Close emoji picker
            emojiPicker.classList.remove('active');
        });
    });

    // Close emoji picker when clicking outside
    document.addEventListener('click', function (e) {
        if (emojiPicker && !emojiPicker.contains(e.target) && e.target !== newEmojiButton) {
            emojiPicker.classList.remove('active');
        }
    });
}

/**
 * Initialize file attachment functionality
 */
function initializeFileAttachment() {
    const attachmentButton = document.getElementById('attachment-button');
    const messageForm = document.getElementById('message-form');

    if (!attachmentButton || !messageForm) {
        console.log('File attachment elements not found');
        return;
    }

    attachmentButton.addEventListener('click', function () {
        // Create a file input element
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = 'image/*,.pdf,.doc,.docx,.txt';
        fileInput.style.display = 'none';

        // Add file input to form
        messageForm.appendChild(fileInput);

        // Trigger file selection
        fileInput.click();

        // Handle file selection
        fileInput.addEventListener('change', function () {
            if (fileInput.files.length > 0) {
                const file = fileInput.files[0];

                // Check file size (max 5MB)
                if (file.size > 5 * 1024 * 1024) {
                    showToast('File size exceeds 5MB limit', 'error');
                    return;
                }

                // Create attachment preview
                const attachmentPreview = document.createElement('div');
                attachmentPreview.className = 'attachment-preview';

                // Determine file icon based on type
                let fileIcon = 'fa-file';
                if (file.type.startsWith('image/')) {
                    fileIcon = 'fa-file-image';
                } else if (file.type === 'application/pdf') {
                    fileIcon = 'fa-file-pdf';
                } else if (file.type.includes('word') || file.type.includes('doc')) {
                    fileIcon = 'fa-file-word';
                } else if (file.type === 'text/plain') {
                    fileIcon = 'fa-file-alt';
                }

                // Format file size
                const fileSize = file.size < 1024 * 1024
                    ? Math.round(file.size / 1024) + ' KB'
                    : Math.round(file.size / (1024 * 1024) * 10) / 10 + ' MB';

                // Set preview content
                attachmentPreview.innerHTML = `
                    <div class="file-icon">
                        <i class="fas ${fileIcon}"></i>
                    </div>
                    <div class="file-info">
                        <div class="file-name">${file.name}</div>
                        <div class="file-size">${fileSize}</div>
                    </div>
                    <button type="button" class="remove-file" aria-label="Remove file">
                        <i class="fas fa-times"></i>
                    </button>
                `;

                // Add preview before message input
                const messageInputContainer = document.querySelector('.message-input-container');
                messageInputContainer.insertBefore(attachmentPreview, messageForm);

                // Handle remove button
                const removeButton = attachmentPreview.querySelector('.remove-file');
                removeButton.addEventListener('click', function () {
                    attachmentPreview.remove();
                    fileInput.value = '';
                });

                // Prepare to send the file
                const messageInput = document.getElementById('message-input');
                const messageText = messageInput ? messageInput.value.trim() : '';

                // Send the file with optional message text
                sendFileMessage(file, messageText);

                // Clear the message input
                if (messageInput) {
                    messageInput.value = '';
                }
            }

            // Remove the file input from the form
            setTimeout(() => {
                fileInput.remove();
            }, 1000);
        });
    });
}

/**
 * Send a file message
 */
function sendFileMessage(file, messageText) {
    // Only send if we have a conversation ID
    if (!currentConversationId) {
        console.warn('Cannot send file: No conversation ID set');
        showToast('Cannot send file: No active conversation', 'error');
        return;
    }

    console.log('Sending file:', file.name, 'with message:', messageText);

    // Create FormData to send the file
    const formData = new FormData();

    // Make sure to append the file with the correct field name
    formData.append('file_attachment', file);

    // Always append content field, even if empty
    // This ensures the server receives the content parameter
    formData.append('content', messageText || '');

    // Log the FormData contents for debugging
    console.log('FormData created with file:', file.name);
    console.log('File size:', file.size, 'bytes');
    console.log('File type:', file.type);

    // Show sending indicator
    showToast('Sending file...', 'info');

    // Add a temporary message to the UI with pending indicator
    const tempMessage = {
        sender_id: currentUserId,
        content: messageText || 'Sending file: ' + file.name,
        timestamp: new Date().toISOString(),
        is_read: false,
        is_pending: true,
        is_file: true,
        file_name: file.name,
        file_type: file.type.startsWith('image/') ? 'image' : 'document'
    };
    addMessageToChat(tempMessage);

    // Get CSRF token
    const csrfToken = getCSRFToken();
    console.log('Using CSRF token:', csrfToken);

    // Send the file using the REST API
    fetch(`/api/chat/conversations/${currentConversationId}/add_message/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken
            // Do NOT set Content-Type header when sending FormData
            // The browser will set it automatically with the correct boundary
        }
    })
    .then(response => {
        console.log('Server response status:', response.status);
        if (!response.ok) {
            throw new Error(`Server responded with status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('File sent successfully:', data);
        showToast('File sent successfully', 'success');

        // Check if file_url is present in the response
        if (!data.file_url && data.file_attachment) {
            // If file_url is missing but file_attachment exists, construct the URL
            data.file_url = '/media/' + data.file_attachment;
            console.log('Constructed file URL:', data.file_url);
        }

        // Add the message to the chat UI
        addMessageToChat(data);

        // Remove any attachment preview
        const attachmentPreview = document.querySelector('.attachment-preview');
        if (attachmentPreview) {
            attachmentPreview.remove();
        }

        // Clear the message input
        const messageInput = document.getElementById('message-input');
        if (messageInput) {
            messageInput.value = '';
            messageInput.focus();
        }
    })
    .catch(error => {
        console.error('Error sending file:', error);
        showToast('Error sending file. Please try again.', 'error');

        // Remove the temporary message
        const pendingMessages = document.querySelectorAll('.message-item.outgoing.pending');
        pendingMessages.forEach(msg => {
            if (msg.querySelector('.message-content').textContent.includes(file.name)) {
                msg.remove();
            }
        });
    });
}

/**
 * Get CSRF token from cookie or Django's csrftoken input
 */
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

    console.error('CSRF token not found. File upload may fail.');
    return '';
}

/**
 * Initialize message actions (edit, delete)
 */
function initializeMessageActions() {
    const messageList = document.getElementById('message-list');

    if (!messageList) {
        console.log('Message list element not found');
        return;
    }

    // Delegate event listener for message action toggles
    messageList.addEventListener('click', function (e) {
        // Handle action toggle button clicks
        if (e.target.closest('.message-action-toggle')) {
            const toggle = e.target.closest('.message-action-toggle');
            const menu = toggle.nextElementSibling;

            // Close all other open menus
            document.querySelectorAll('.message-actions-menu.active').forEach(function (openMenu) {
                if (openMenu !== menu) {
                    openMenu.classList.remove('active');
                }
            });

            // Toggle this menu
            menu.classList.toggle('active');

            // Prevent event from bubbling up
            e.stopPropagation();
        }

        // Handle edit button clicks
        if (e.target.closest('.edit-message')) {
            const messageItem = e.target.closest('.message-item');
            const messageContent = messageItem.querySelector('.message-content');
            const originalText = messageContent.textContent;
            const messageId = messageItem.dataset.messageId;

            // Add editing class to message
            messageItem.classList.add('editing');

            // Replace content with editable input
            messageContent.innerHTML = `
                <textarea class="edit-textarea">${originalText}</textarea>
                <div class="edit-actions">
                    <button type="button" class="cancel-edit">Cancel</button>
                    <button type="button" class="save-edit">Save</button>
                </div>
            `;

            // Focus the textarea
            const textarea = messageContent.querySelector('.edit-textarea');
            textarea.focus();
            textarea.setSelectionRange(textarea.value.length, textarea.value.length);

            // Close the menu
            e.target.closest('.message-actions-menu').classList.remove('active');

            // Prevent event from bubbling up
            e.stopPropagation();
        }

        // Handle delete button clicks
        if (e.target.closest('.delete-message')) {
            const messageItem = e.target.closest('.message-item');
            const messageId = messageItem.dataset.messageId;

            // Show confirmation dialog
            if (confirm('Are you sure you want to delete this message?')) {
                // For now, just remove the message from the UI
                // In a real implementation, you would send a delete request to the server
                messageItem.style.opacity = '0.5';
                setTimeout(() => {
                    messageItem.remove();
                }, 300);

                showToast('Message deleted locally. Server-side deletion coming in the next update!', 'info');
            }

            // Close the menu
            e.target.closest('.message-actions-menu').classList.remove('active');

            // Prevent event from bubbling up
            e.stopPropagation();
        }

        // Handle save edit button clicks
        if (e.target.closest('.save-edit')) {
            const messageItem = e.target.closest('.message-item');
            const messageContent = messageItem.querySelector('.message-content');
            const textarea = messageContent.querySelector('.edit-textarea');
            const newText = textarea.value.trim();
            const messageId = messageItem.dataset.messageId;

            if (newText) {
                // For now, just update the UI
                // In a real implementation, you would send an update request to the server
                messageContent.innerHTML = newText;
                messageItem.classList.remove('editing');

                showToast('Message updated locally. Server-side editing coming in the next update!', 'info');
            } else {
                showToast('Message cannot be empty', 'error');
            }

            // Prevent event from bubbling up
            e.stopPropagation();
        }

        // Handle cancel edit button clicks
        if (e.target.closest('.cancel-edit')) {
            const messageItem = e.target.closest('.message-item');
            const messageContent = messageItem.querySelector('.message-content');
            const originalText = messageContent.querySelector('.edit-textarea').value;

            // Restore original content
            messageContent.innerHTML = originalText;
            messageItem.classList.remove('editing');

            // Prevent event from bubbling up
            e.stopPropagation();
        }
    });

    // Close menus when clicking outside
    document.addEventListener('click', function () {
        document.querySelectorAll('.message-actions-menu.active').forEach(function (menu) {
            menu.classList.remove('active');
        });
    });
}
