/**
 * Chat functionality for real-time messaging
 * Enhanced with improved UI/UX, performance, and accessibility
 *
 * @version 2.0.0
 * @author E-Platform Team
 */

// ===== CONSTANTS =====
// Configuration constants
const CONFIG = {
    // WebSocket settings
    WS: {
        MAX_RECONNECT_ATTEMPTS: 10,
        BASE_RECONNECT_DELAY: 1000, // 1 second
        MAX_RECONNECT_DELAY: 30000, // 30 seconds
    },
    // Message settings
    MESSAGE: {
        MAX_LENGTH: 5000,
        THROTTLE_DELAY: 500, // 500ms between messages to prevent spam
        TYPING_TIMEOUT: 3000, // 3 seconds
    },
    // File settings
    FILE: {
        MAX_SIZE: 5 * 1024 * 1024, // 5MB
        ALLOWED_TYPES: 'image/*,.pdf,.doc,.docx,.txt,.xls,.xlsx,.ppt,.pptx',
    },
    // UI settings
    UI: {
        TOAST_DURATION: 5000, // 5 seconds
        ANIMATION_DELAY: 10, // 10ms
        STAGGER_DELAY: 100, // 100ms between animations
    }
};

// ===== GLOBAL STATE =====
// Define global state object to keep track of application state
const ChatState = {
    // WebSocket connection
    socket: null,
    reconnectAttempts: 0,
    lastMessageTime: 0,
    pendingMessages: [],

    // Current conversation
    currentConversationId: null,
    currentUserId: null,
    otherUserId: null,
    typingTimeout: null,

    // UI state
    isEmojiPickerOpen: false,
    isSidebarOpen: false,

    // Event listeners registry for easy cleanup
    eventListeners: {},

    // Initialize global state
    init() {
        this.socket = null;
        this.reconnectAttempts = 0;
        this.lastMessageTime = 0;
        this.pendingMessages = [];
        this.currentConversationId = null;
        this.currentUserId = null;
        this.otherUserId = null;
        this.typingTimeout = null;
        this.isEmojiPickerOpen = false;
        this.isSidebarOpen = false;
        this.eventListeners = {};
    }
};

// Initialize state
ChatState.init();

// Make socket and reconnect attempts available globally for backward compatibility
window.chatSocket = null;
window.reconnectAttempts = 0;
window.maxReconnectAttempts = CONFIG.WS.MAX_RECONNECT_ATTEMPTS;
window.chatBaseReconnectDelay = CONFIG.WS.BASE_RECONNECT_DELAY;

/**
 * Get CSRF token from cookie or Django's csrftoken input
 * @returns {string} CSRF token or empty string if not found
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
 * Initialize the WebSocket connection for chat with improved error handling and reconnection
 * @returns {WebSocket} The WebSocket connection
 */
function initializeChatWebsocket() {
    console.log('Initializing WebSocket connection...');

    // Close any existing connection
    if (ChatState.socket !== null) {
        try {
            ChatState.socket.close();
            console.log('Closed existing WebSocket connection');
        } catch (error) {
            console.error('Error closing existing WebSocket connection:', error);
        }
    }

    // Create a new WebSocket connection with CSRF protection
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsPath = '/ws/chat/';
    const wsHost = window.location.host;
    const csrfToken = getCSRFToken();
    const wsUrl = `${wsProtocol}//${wsHost}${wsPath}?csrf_token=${csrfToken}`;

    console.log('Connecting to WebSocket at:', wsUrl);

    try {
        // Create new WebSocket connection
        ChatState.socket = new WebSocket(wsUrl);

        // Update global reference for backward compatibility
        window.chatSocket = ChatState.socket;

        // Set up event handlers with improved error handling
        setupWebSocketEventHandlers(ChatState.socket, wsUrl);

        return ChatState.socket;
    } catch (error) {
        console.error('Error creating WebSocket connection:', error);
        handleWebSocketConnectionError();
        return null;
    }
}

/**
 * Set up event handlers for WebSocket connection
 * @param {WebSocket} socket - The WebSocket connection
 * @param {string} wsUrl - The WebSocket URL for debugging
 */
function setupWebSocketEventHandlers(socket, wsUrl) {
    if (!socket) return;

    // Connection opened
    socket.onopen = function() {
        console.log('WebSocket connection established');

        // Reset reconnect attempts on successful connection
        ChatState.reconnectAttempts = 0;
        window.reconnectAttempts = 0;

        // Show connection status
        showConnectionStatus('connected');

        // Send any pending messages
        sendPendingMessages();

        // Add manual reconnect button if it exists
        const reconnectButton = document.getElementById('manual-reconnect');
        if (reconnectButton) {
            reconnectButton.style.display = 'none';
        }
    };

    // Message received
    socket.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    };

    // Connection closed
    socket.onclose = function(event) {
        // Check if the close was clean (code 1000 or 1001)
        const wasClean = event.code === 1000 || event.code === 1001;

        console.log(`WebSocket connection closed. Code: ${event.code}, Clean: ${wasClean}`);

        // Show disconnected status
        showConnectionStatus('disconnected');

        // Only attempt to reconnect if it wasn't a clean close and we haven't exceeded max attempts
        if (!wasClean && ChatState.reconnectAttempts < CONFIG.WS.MAX_RECONNECT_ATTEMPTS) {
            handleWebSocketReconnection(event);
        } else if (ChatState.reconnectAttempts >= CONFIG.WS.MAX_RECONNECT_ATTEMPTS) {
            showMaxReconnectAttemptsReached();
        }
    };

    // Connection error
    socket.onerror = function(error) {
        console.error('WebSocket error:', error);

        // Show error status
        showConnectionStatus('error');

        // Show toast notification
        showToast('Connection error. Trying to reconnect...', 'error');

        // Note: We don't need to manually reconnect here as the onclose handler will be called after an error
    };
}

/**
 * Handle WebSocket connection error
 */
function handleWebSocketConnectionError() {
    // Attempt to reconnect with exponential backoff
    if (ChatState.reconnectAttempts < CONFIG.WS.MAX_RECONNECT_ATTEMPTS) {
        const delay = calculateReconnectDelay(ChatState.reconnectAttempts);
        ChatState.reconnectAttempts++;
        window.reconnectAttempts = ChatState.reconnectAttempts;

        showToast(`Error creating WebSocket connection. Attempting to reconnect (${ChatState.reconnectAttempts}/${CONFIG.WS.MAX_RECONNECT_ATTEMPTS})...`, 'error');

        setTimeout(function() {
            initializeChatWebsocket();
        }, delay);
    } else {
        showMaxReconnectAttemptsReached();
    }
}

/**
 * Handle WebSocket reconnection with exponential backoff
 * @param {CloseEvent} event - The WebSocket close event
 */
function handleWebSocketReconnection(event) {
    // Calculate delay with exponential backoff
    const delay = calculateReconnectDelay(ChatState.reconnectAttempts);
    ChatState.reconnectAttempts++;
    window.reconnectAttempts = ChatState.reconnectAttempts;

    console.log(`Attempting to reconnect (${ChatState.reconnectAttempts}/${CONFIG.WS.MAX_RECONNECT_ATTEMPTS}) in ${delay}ms`);

    // Show appropriate message based on error code
    if (event.code === 1006) {
        // Code 1006 is "Abnormal Closure" which often means the server is not available
        showToast(`WebSocket server not available. Attempting to reconnect (${ChatState.reconnectAttempts}/${CONFIG.WS.MAX_RECONNECT_ATTEMPTS})...`, 'error');
    } else {
        showToast(`Connection lost. Attempting to reconnect (${ChatState.reconnectAttempts}/${CONFIG.WS.MAX_RECONNECT_ATTEMPTS})...`, 'warning');
    }

    setTimeout(function() {
        initializeChatWebsocket();
    }, delay);
}

/**
 * Calculate reconnect delay with exponential backoff
 * @param {number} attempts - Number of reconnect attempts
 * @returns {number} Delay in milliseconds
 */
function calculateReconnectDelay(attempts) {
    return Math.min(
        CONFIG.WS.BASE_RECONNECT_DELAY * Math.pow(1.5, attempts),
        CONFIG.WS.MAX_RECONNECT_DELAY
    );
}

/**
 * Show message when max reconnect attempts are reached
 */
function showMaxReconnectAttemptsReached() {
    showToast('Unable to reconnect after multiple attempts. Please try manual reconnection or refresh the page.', 'error');

    // Show manual reconnect button if it exists
    const reconnectButton = document.getElementById('manual-reconnect');
    if (reconnectButton) {
        reconnectButton.style.display = 'block';

        // Add event listener if not already added
        if (!reconnectButton.hasAttribute('data-listener-added')) {
            reconnectButton.addEventListener('click', function() {
                // Reset reconnect attempts and try again
                ChatState.reconnectAttempts = 0;
                window.reconnectAttempts = 0;
                initializeChatWebsocket();
                reconnectButton.style.display = 'none';
            });
            reconnectButton.setAttribute('data-listener-added', 'true');
        }
    }
}

/**
 * Show connection status to the user with improved accessibility
 * @param {string} status - The connection status ('connected', 'disconnected', 'error')
 */
function showConnectionStatus(status) {
    // Check if we're on a chat page
    const messageList = document.getElementById('message-list');
    if (!messageList) return;

    // Get or create the status container
    let statusContainer = document.getElementById('connection-status-container');
    if (!statusContainer) {
        statusContainer = document.createElement('div');
        statusContainer.id = 'connection-status-container';
        statusContainer.setAttribute('aria-live', 'polite');
        statusContainer.setAttribute('role', 'status');
        messageList.parentNode.insertBefore(statusContainer, messageList);
    }

    // Clear existing status messages
    statusContainer.innerHTML = '';

    // Determine status message and class
    let statusMessage = '';
    let statusClass = '';
    let statusIcon = '';

    switch (status) {
        case 'connected':
            statusMessage = 'Connected to chat server';
            statusClass = 'success';
            statusIcon = '<i class="fas fa-check-circle" aria-hidden="true"></i>';
            break;
        case 'disconnected':
            statusMessage = 'Connection lost. Reconnecting...';
            statusClass = 'warning';
            statusIcon = '<i class="fas fa-exclamation-triangle" aria-hidden="true"></i>';
            break;
        case 'error':
            statusMessage = 'Connection error. Trying to reconnect...';
            statusClass = 'error';
            statusIcon = '<i class="fas fa-times-circle" aria-hidden="true"></i>';
            break;
        default:
            return; // Unknown status, don't show anything
    }

    // Create the status element
    const statusElement = document.createElement('div');
    statusElement.className = `connection-status ${statusClass}`;
    statusElement.innerHTML = `
        ${statusIcon}
        <span class="status-message">${statusMessage}</span>
    `;

    // Add manual reconnect button for error and disconnected states
    if (status === 'error' || (status === 'disconnected' && ChatState.reconnectAttempts >= CONFIG.WS.MAX_RECONNECT_ATTEMPTS)) {
        const reconnectButton = document.createElement('button');
        reconnectButton.id = 'manual-reconnect';
        reconnectButton.className = 'reconnect-button';
        reconnectButton.innerHTML = '<i class="fas fa-sync-alt" aria-hidden="true"></i> Reconnect';
        reconnectButton.setAttribute('aria-label', 'Manually reconnect to chat server');

        reconnectButton.addEventListener('click', function() {
            // Reset reconnect attempts and try again
            ChatState.reconnectAttempts = 0;
            window.reconnectAttempts = 0;
            initializeChatWebsocket();
            statusContainer.innerHTML = '';
            showToast('Attempting to reconnect...', 'info');
        });

        statusElement.appendChild(reconnectButton);
    }

    // Add to the status container
    statusContainer.appendChild(statusElement);

    // Auto-remove success message after 5 seconds
    if (status === 'connected') {
        setTimeout(() => {
            if (statusElement.parentNode) {
                statusElement.classList.add('fade-out');
                setTimeout(() => {
                    if (statusElement.parentNode) {
                        statusElement.remove();
                    }
                }, 500); // Fade out animation duration
            }
        }, CONFIG.UI.TOAST_DURATION);
    }
}

/**
 * Store messages when offline and send them when reconnected
 */
function sendPendingMessages() {
    // Check if we have any pending messages
    if (ChatState.pendingMessages.length === 0) {
        console.log('No pending messages to send');
        return;
    }

    // Check WebSocket connection status
    if (!ChatState.socket) {
        console.warn('Cannot send pending messages: WebSocket not initialized');
        // Try to initialize the WebSocket
        initializeChatWebsocket();
        return;
    }

    // Send pending messages if WebSocket is open
    if (ChatState.socket.readyState === WebSocket.OPEN) {
        console.log(`Sending ${ChatState.pendingMessages.length} pending messages`);

        // Create a copy of the pending messages array
        const messagesToSend = [...ChatState.pendingMessages];

        // Clear the pending messages array before sending
        ChatState.pendingMessages = [];

        // Send each message
        messagesToSend.forEach(message => {
            try {
                ChatState.socket.send(JSON.stringify(message));
                console.log('Pending message sent:', message);

                // Update UI for this message if it's in the current conversation
                if (message.type === 'chat_message' && message.conversation_id === ChatState.currentConversationId) {
                    // Find the pending message in the UI and update its status
                    updatePendingMessageUI(message);
                }
            } catch (error) {
                console.error('Error sending pending message:', error);
                // Add the message back to the pending messages array
                ChatState.pendingMessages.push(message);
            }
        });

        // Show success message if all messages were sent
        if (ChatState.pendingMessages.length === 0) {
            console.log('All pending messages sent successfully');
            showToast('Your offline messages have been sent', 'success');
        } else {
            console.warn(`${ChatState.pendingMessages.length} messages could not be sent and will be retried later`);
        }
    } else {
        console.warn('Cannot send pending messages: WebSocket not open (readyState:', ChatState.socket.readyState, ')');
    }
}

/**
 * Update the UI for a pending message that has been sent
 * @param {Object} message - The message that was sent
 */
function updatePendingMessageUI(message) {
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

/**
 * Initialize a conversation and its event listeners with improved event handling
 * @param {number} conversationId - The ID of the conversation
 * @param {number} userId - The ID of the current user
 * @param {number} otherUser - The ID of the other user in the conversation
 */
function initializeConversation(conversationId, userId, otherUser) {
    // Store conversation information in state
    ChatState.currentConversationId = conversationId;
    ChatState.currentUserId = userId;
    ChatState.otherUserId = otherUser;

    // Update global variables for backward compatibility
    window.currentConversationId = conversationId;
    window.currentUserId = userId;
    window.otherUserId = otherUser;

    console.log(`Initializing conversation: ${conversationId} between user ${userId} and ${otherUser}`);

    // Make sure WebSocket is initialized
    if (!ChatState.socket || ChatState.socket.readyState === WebSocket.CLOSED) {
        console.log('WebSocket not initialized or closed, initializing now');
        initializeChatWebsocket();
    }

    // Hide typing indicator initially
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.style.display = 'none';
    }

    // Set up event listeners using delegation instead of cloning
    setupMessageFormListeners();
    setupMessageInputListeners();
    setupSendButtonListener();

    // Mark messages as read when the page loads
    markMessagesAsRead();

    // Send any pending messages
    sendPendingMessages();

    // Initialize emoji picker and file attachment
    if (typeof initializeEmojiPicker === 'function') {
        initializeEmojiPicker();
    }

    if (typeof initializeFileAttachment === 'function') {
        initializeFileAttachment();
    }

    // Initialize message actions (edit, delete)
    if (typeof initializeMessageActions === 'function') {
        initializeMessageActions();
    }

    console.log('Conversation initialization complete');
}

/**
 * Set up event listeners for the message form using event delegation
 */
function setupMessageFormListeners() {
    const messageForm = document.getElementById('message-form');
    if (!messageForm) {
        console.warn('Message form element not found');
        return;
    }

    // Remove existing listener if it exists
    if (ChatState.eventListeners.messageForm) {
        messageForm.removeEventListener('submit', ChatState.eventListeners.messageForm);
    }

    // Create new listener
    const submitHandler = function(e) {
        e.preventDefault();
        sendMessage();
    };

    // Add the listener
    messageForm.addEventListener('submit', submitHandler);

    // Store reference to the listener
    ChatState.eventListeners.messageForm = submitHandler;
}

/**
 * Set up event listeners for the message input
 */
function setupMessageInputListeners() {
    const messageInput = document.getElementById('message-input');
    if (!messageInput) {
        console.warn('Message input element not found');
        return;
    }

    // Focus the input field
    setTimeout(() => {
        messageInput.focus();
    }, 500);

    // Remove existing listeners if they exist
    if (ChatState.eventListeners.messageInputTyping) {
        messageInput.removeEventListener('input', ChatState.eventListeners.messageInputTyping);
    }

    if (ChatState.eventListeners.messageInputKeypress) {
        messageInput.removeEventListener('keypress', ChatState.eventListeners.messageInputKeypress);
    }

    // Create new listeners
    const typingHandler = function() {
        sendTypingIndicator(true);

        // Clear existing timeout
        if (ChatState.typingTimeout) {
            clearTimeout(ChatState.typingTimeout);
        }

        // Set a new timeout to stop typing
        ChatState.typingTimeout = setTimeout(function() {
            sendTypingIndicator(false);
        }, CONFIG.MESSAGE.TYPING_TIMEOUT);
    };

    const keypressHandler = function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    // Add the listeners
    messageInput.addEventListener('input', typingHandler);
    messageInput.addEventListener('keypress', keypressHandler);

    // Store references to the listeners
    ChatState.eventListeners.messageInputTyping = typingHandler;
    ChatState.eventListeners.messageInputKeypress = keypressHandler;
}

/**
 * Set up event listener for the send button
 */
function setupSendButtonListener() {
    const sendButton = document.getElementById('send-button');
    if (!sendButton) {
        console.warn('Send button element not found');
        return;
    }

    // Remove existing listener if it exists
    if (ChatState.eventListeners.sendButton) {
        sendButton.removeEventListener('click', ChatState.eventListeners.sendButton);
    }

    // Create new listener
    const clickHandler = function(e) {
        e.preventDefault();
        sendMessage();
    };

    // Add the listener
    sendButton.addEventListener('click', clickHandler);

    // Store reference to the listener
    ChatState.eventListeners.sendButton = clickHandler;
}

/**
 * Handle incoming WebSocket messages with improved error handling
 * @param {Object} data - The parsed message data
 */
function handleWebSocketMessage(data) {
    if (!data || !data.type) {
        console.error('Invalid WebSocket message received:', data);
        return;
    }

    const messageType = data.type;

    try {
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
    } catch (error) {
        console.error(`Error handling message of type ${messageType}:`, error);
    }
}

/**
 * Handle a new chat message
 * @param {Object} data - The message data
 */
function handleChatMessage(data) {
    // Only process if we are in the correct conversation
    if (ChatState.currentConversationId && data.conversation_id === ChatState.currentConversationId) {
        const message = data.message;

        // Validate message data
        if (!message) {
            console.error('Invalid message data received:', data);
            return;
        }

        // Add message to chat
        addMessageToChat(message);

        // If the message is from the other user, mark it as read
        if (message.sender_id !== ChatState.currentUserId) {
            markMessagesAsRead();

            // Play notification sound if enabled
            playMessageSound();
        }
    }
}

/**
 * Play a notification sound for new messages
 */
function playMessageSound() {
    // Check if sound is enabled in user preferences
    const soundEnabled = localStorage.getItem('chat_sound_enabled') !== 'false';

    if (soundEnabled && document.hidden) {
        try {
            const audio = new Audio('/static/chatting/sounds/message.mp3');
            audio.volume = 0.5;
            audio.play().catch(error => {
                // Autoplay might be blocked by browser policy
                console.log('Could not play notification sound:', error);
            });
        } catch (error) {
            console.error('Error playing notification sound:', error);
        }
    }
}

/**
 * Handle a new message notification (when in a different conversation or chat home)
 * @param {Object} data - The notification data
 */
function handleNewMessageNotification(data) {
    const conversationId = data.conversation_id;

    // Update the conversation list if we're not in that conversation
    if (ChatState.currentConversationId !== conversationId) {
        updateConversationListItem(conversationId, data.message);

        // Show browser notification if enabled and page is not visible
        if (document.hidden) {
            showBrowserNotification(data.message);
        }
    }
}

/**
 * Update a conversation list item with new message information
 * @param {number} conversationId - The conversation ID
 * @param {Object} message - The message data
 */
function updateConversationListItem(conversationId, message) {
    // Try to find the conversation item in the list
    const conversationItem = document.querySelector(`.conversation-item[href*="${conversationId}"]`);
    if (!conversationItem) return;

    // Update the unread badge
    updateUnreadBadge(conversationItem);

    // Update the preview text
    updatePreviewText(conversationItem, message);

    // Move the conversation to the top of the list
    moveConversationToTop(conversationItem);
}

/**
 * Update the unread badge on a conversation item
 * @param {Element} conversationItem - The conversation list item
 */
function updateUnreadBadge(conversationItem) {
    let unreadBadge = conversationItem.querySelector('.unread-badge');

    if (!unreadBadge) {
        // Create a new badge
        const previewElement = conversationItem.querySelector('.conversation-preview');
        if (!previewElement) return;

        unreadBadge = document.createElement('span');
        unreadBadge.className = 'unread-badge';
        unreadBadge.setAttribute('aria-label', '1 unread message');
        unreadBadge.textContent = '1';
        previewElement.appendChild(unreadBadge);
    } else {
        // Update existing badge
        const count = parseInt(unreadBadge.textContent) || 0;
        const newCount = count + 1;
        unreadBadge.textContent = newCount;
        unreadBadge.setAttribute('aria-label', `${newCount} unread messages`);
    }
}

/**
 * Update the preview text on a conversation item
 * @param {Element} conversationItem - The conversation list item
 * @param {Object} message - The message data
 */
function updatePreviewText(conversationItem, message) {
    const previewText = conversationItem.querySelector('.conversation-preview span');
    if (previewText && message.content) {
        // Truncate message content for preview
        const maxLength = 30;
        const truncated = message.content.length > maxLength ?
            message.content.substring(0, maxLength) + '...' :
            message.content;

        previewText.textContent = truncated;
    }
}

/**
 * Move a conversation item to the top of the list
 * @param {Element} conversationItem - The conversation list item
 */
function moveConversationToTop(conversationItem) {
    const conversationList = document.getElementById('conversation-list');
    if (conversationList && conversationItem !== conversationList.firstChild) {
        // Add animation class
        conversationItem.classList.add('highlight-conversation');

        // Move to top
        conversationList.prepend(conversationItem);

        // Remove animation class after animation completes
        setTimeout(() => {
            conversationItem.classList.remove('highlight-conversation');
        }, 2000);
    }
}

/**
 * Show a browser notification for a new message
 * @param {Object} message - The message data
 */
function showBrowserNotification(message) {
    // Check if notifications are enabled
    const notificationsEnabled = localStorage.getItem('chat_notifications_enabled') !== 'false';

    if (notificationsEnabled && 'Notification' in window) {
        // Check permission
        if (Notification.permission === 'granted') {
            createNotification(message);
        } else if (Notification.permission !== 'denied') {
            // Request permission
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    createNotification(message);
                }
            });
        }
    }
}

/**
 * Create and show a browser notification
 * @param {Object} message - The message data
 */
function createNotification(message) {
    try {
        const senderName = message.sender_name || 'Someone';
        const content = message.content || 'sent you a message';

        const notification = new Notification('New Message', {
            body: `${senderName}: ${content.substring(0, 50)}${content.length > 50 ? '...' : ''}`,
            icon: '/static/chatting/images/notification-icon.png'
        });

        // Close notification after 5 seconds
        setTimeout(() => {
            notification.close();
        }, 5000);

        // Handle notification click
        notification.onclick = function() {
            window.focus();
            if (message.conversation_id) {
                window.location.href = `/chat/conversation/${message.conversation_id}/`;
            }
        };
    } catch (error) {
        console.error('Error creating notification:', error);
    }
}

/**
 * Handle typing indicator updates with improved reliability
 * @param {Object} data - The typing indicator data
 */
function handleTypingIndicator(data) {
    // Only process if we are in the correct conversation
    if (!ChatState.currentConversationId || data.conversation_id !== ChatState.currentConversationId) {
        return;
    }

    const typingIndicator = document.getElementById('typing-indicator');
    if (!typingIndicator) return;

    // Only show typing indicator if it's from the other user
    if (data.user_id !== ChatState.currentUserId) {
        if (data.is_typing) {
            showTypingIndicator(typingIndicator);
        } else {
            hideTypingIndicator(typingIndicator);
        }
    }
}

/**
 * Show the typing indicator with animation
 * @param {Element} typingIndicator - The typing indicator element
 */
function showTypingIndicator(typingIndicator) {
    // Make sure the typing indicator is visible
    typingIndicator.style.display = 'flex';
    typingIndicator.classList.add('active');

    // Set ARIA attributes for accessibility
    typingIndicator.setAttribute('aria-hidden', 'false');

    // Auto-hide after 10 seconds in case we don't get the "stopped typing" event
    if (ChatState.typingIndicatorTimeout) {
        clearTimeout(ChatState.typingIndicatorTimeout);
    }

    ChatState.typingIndicatorTimeout = setTimeout(() => {
        hideTypingIndicator(typingIndicator);
    }, 10000);
}

/**
 * Hide the typing indicator with animation
 * @param {Element} typingIndicator - The typing indicator element
 */
function hideTypingIndicator(typingIndicator) {
    typingIndicator.classList.remove('active');

    // Use a short timeout to allow for fade-out animation
    setTimeout(() => {
        typingIndicator.style.display = 'none';
        typingIndicator.setAttribute('aria-hidden', 'true');
    }, 300);

    // Clear any existing timeout
    if (ChatState.typingIndicatorTimeout) {
        clearTimeout(ChatState.typingIndicatorTimeout);
        ChatState.typingIndicatorTimeout = null;
    }
}

/**
 * Handle messages read updates
 * @param {Object} data - The read status data
 */
function handleMessagesRead(data) {
    if (ChatState.currentConversationId && data.conversation_id === ChatState.currentConversationId) {
        updateMessageReadStatus();
    }
}

/**
 * Update read status indicators for all outgoing messages
 */
function updateMessageReadStatus() {
    const messages = document.querySelectorAll('.message-item.outgoing');

    messages.forEach(function(messageElement) {
        const statusElement = messageElement.querySelector('.message-status');
        if (statusElement) {
            // Update with read indicator icon
            statusElement.innerHTML = '<i class="fas fa-check-double read-indicator" aria-label="Read"></i>';

            // Add tooltip
            statusElement.title = 'Read';
        }
    });
}

/**
 * Format a timestamp into a human-readable last seen time
 * @param {string} timestamp - The timestamp to format
 * @returns {string} Formatted time string
 */
function formatLastSeen(timestamp) {
    try {
        // Parse the timestamp
        const date = new Date(timestamp);

        // Check if the date is valid
        if (isNaN(date.getTime())) {
            console.error('Invalid timestamp:', timestamp);
            return 'recently';
        }

        const now = new Date();
        const diffMs = now - date;
        const diffSec = Math.floor(diffMs / 1000);
        const diffMin = Math.floor(diffSec / 60);
        const diffHour = Math.floor(diffMin / 60);
        const diffDay = Math.floor(diffHour / 24);

        // Format based on how long ago
        if (diffSec < 60) {
            return 'just now';
        } else if (diffMin < 60) {
            return `${diffMin} ${diffMin === 1 ? 'minute' : 'minutes'} ago`;
        } else if (diffHour < 24) {
            return `${diffHour} ${diffHour === 1 ? 'hour' : 'hours'} ago`;
        } else if (diffDay < 7) {
            return `${diffDay} ${diffDay === 1 ? 'day' : 'days'} ago`;
        } else {
            // Format as date
            const options = { month: 'short', day: 'numeric', hour: 'numeric', minute: 'numeric' };
            return date.toLocaleDateString(undefined, options);
        }
    } catch (error) {
        console.error('Error formatting last seen time:', error);
        return 'recently';
    }
}

/**
 * Handle user status updates with improved accessibility
 * @param {Object} data - The user status data
 */
function handleUserStatusUpdate(data) {
    if (!data || !data.user_id) {
        console.error('Invalid user status data:', data);
        return;
    }

    const userId = data.user_id;
    const isOnline = data.status;
    const lastSeen = data.last_seen;

    // Update status indicators
    updateStatusIndicators(userId, isOnline);

    // Update conversation list status
    updateConversationListStatus(userId, isOnline, lastSeen);

    // Update conversation header status
    updateConversationHeaderStatus(userId, isOnline, lastSeen);
}

/**
 * Update status indicators for a user
 * @param {number} userId - The user ID
 * @param {boolean} isOnline - Whether the user is online
 */
function updateStatusIndicators(userId, isOnline) {
    const statusIndicators = document.querySelectorAll(`.status-indicator[data-user-id="${userId}"]`);

    statusIndicators.forEach(function(indicator) {
        // Update class
        indicator.classList.toggle('online', isOnline);
        indicator.classList.toggle('offline', !isOnline);

        // Update ARIA attributes
        indicator.setAttribute('aria-label', isOnline ? 'Online' : 'Offline');
    });
}

/**
 * Update conversation list status for a user
 * @param {number} userId - The user ID
 * @param {boolean} isOnline - Whether the user is online
 * @param {string} lastSeen - Last seen timestamp
 */
function updateConversationListStatus(userId, isOnline, lastSeen) {
    const conversationItems = document.querySelectorAll(`.conversation-item[href*="${userId}"]`);

    conversationItems.forEach(function(item) {
        // Set the user ID as a data attribute if it's not already there
        if (!item.dataset.userId) {
            item.dataset.userId = userId;
        }

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
}

/**
 * Update conversation header status for a user
 * @param {number} userId - The user ID
 * @param {boolean} isOnline - Whether the user is online
 * @param {string} lastSeen - Last seen timestamp
 */
function updateConversationHeaderStatus(userId, isOnline, lastSeen) {
    // Only update if this is the current conversation partner
    if (ChatState.otherUserId && userId === ChatState.otherUserId) {
        const statusText = document.querySelector('.status-text');
        if (statusText) {
            // Update text content
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

            // Update ARIA attributes for accessibility
            statusText.setAttribute('aria-live', 'polite');
        }
    }
}

/**
 * Send a new message with throttling to prevent spam
 */
function sendMessage() {
    // Get message input
    const messageInput = document.getElementById('message-input');
    if (!messageInput) {
        showToast('Error: Could not find message input', 'error');
        return;
    }

    // Get message content
    const content = messageInput.value.trim();

    // Validate conversation ID
    if (!ChatState.currentConversationId) {
        showToast('Error: No active conversation', 'error');
        return;
    }

    // Skip if empty message
    if (!content) {
        return;
    }

    // Check message length
    if (content.length > CONFIG.MESSAGE.MAX_LENGTH) {
        showToast(`Message is too long. Maximum length is ${CONFIG.MESSAGE.MAX_LENGTH} characters.`, 'error');
        return;
    }

    // Implement message throttling to prevent spam
    const now = Date.now();
    if (now - ChatState.lastMessageTime < CONFIG.MESSAGE.THROTTLE_DELAY) {
        showToast('Please wait a moment before sending another message.', 'warning');
        return;
    }

    // Update last message time
    ChatState.lastMessageTime = now;

    // Create message data
    const messageData = {
        'type': 'chat_message',
        'conversation_id': ChatState.currentConversationId,
        'content': content,
        'temp_id': 'temp_' + now + '_' + Math.floor(Math.random() * 1000)
    };

    // Send message based on connection state
    if (sendMessageBasedOnConnectionState(messageData, content)) {
        // Clear the input and reset typing indicator if message was processed
        messageInput.value = '';
        resetTypingIndicator();
        messageInput.focus();
    }
}

/**
 * Send a message based on the current WebSocket connection state
 * @param {Object} messageData - The message data to send
 * @param {string} content - The message content
 * @returns {boolean} Whether the message was processed
 */
function sendMessageBasedOnConnectionState(messageData, content) {
    // Check WebSocket connection status
    if (!ChatState.socket) {
        // WebSocket not initialized, try to initialize it
        initializeChatWebsocket();
        handleOfflineMessage(messageData, content);
        return true;
    }

    // Handle based on WebSocket state
    switch (ChatState.socket.readyState) {
        case WebSocket.OPEN:
            // Connected, send directly
            return sendMessageViaWebSocket(messageData, content);

        case WebSocket.CONNECTING:
            // Connecting, store for later
            handleConnectingMessage(messageData, content);
            return true;

        case WebSocket.CLOSED:
        case WebSocket.CLOSING:
            // Closed or closing, store for later and try to reconnect
            initializeChatWebsocket();
            handleOfflineMessage(messageData, content);
            return true;

        default:
            // Unknown state, try REST API
            sendMessageViaRESTAPI(ChatState.currentConversationId, content);
            return true;
    }
}

/**
 * Send a message via WebSocket
 * @param {Object} messageData - The message data to send
 * @param {string} content - The message content
 * @returns {boolean} Whether the message was sent successfully
 */
function sendMessageViaWebSocket(messageData, content) {
    try {
        // Send the message
        ChatState.socket.send(JSON.stringify(messageData));

        // Add a temporary message to the UI
        const tempMessage = {
            sender_id: ChatState.currentUserId,
            content: content,
            timestamp: new Date().toISOString(),
            is_read: false,
            temp_id: messageData.temp_id
        };
        addMessageToChat(tempMessage);

        return true;
    } catch (error) {
        console.error('Error sending message via WebSocket:', error);
        showToast('Error sending message. Trying REST API fallback...', 'warning');

        // Fallback to REST API
        sendMessageViaRESTAPI(ChatState.currentConversationId, content);
        return true;
    }
}

/**
 * Handle a message when WebSocket is connecting
 * @param {Object} messageData - The message data
 * @param {string} content - The message content
 */
function handleConnectingMessage(messageData, content) {
    // Store the message to send after connection is established
    ChatState.pendingMessages.push(messageData);

    // Add a temporary message to the UI with pending indicator
    const tempMessage = {
        sender_id: ChatState.currentUserId,
        content: content,
        timestamp: new Date().toISOString(),
        is_read: false,
        is_pending: true,
        temp_id: messageData.temp_id
    };
    addMessageToChat(tempMessage);

    // Show connecting toast
    showToast('Connecting to chat server. Your message will be sent when connected.', 'info');
}

/**
 * Handle a message when offline
 * @param {Object} messageData - The message data
 * @param {string} content - The message content
 */
function handleOfflineMessage(messageData, content) {
    // Store the message to send after connection is established
    ChatState.pendingMessages.push(messageData);

    // Add a temporary message to the UI with pending indicator
    const tempMessage = {
        sender_id: ChatState.currentUserId,
        content: content,
        timestamp: new Date().toISOString(),
        is_read: false,
        is_pending: true,
        temp_id: messageData.temp_id
    };
    addMessageToChat(tempMessage);

    // Show offline toast
    showToast('You are currently offline. Message will be sent when connection is restored.', 'warning');
}

/**
 * Reset typing indicator state
 */
function resetTypingIndicator() {
    if (ChatState.typingTimeout) {
        clearTimeout(ChatState.typingTimeout);
        ChatState.typingTimeout = null;
    }
    sendTypingIndicator(false);
}

/**
 * Send a message via REST API as a fallback when WebSocket is not available
 * @param {number} conversationId - The conversation ID
 * @param {string} content - The message content
 */
function sendMessageViaRESTAPI(conversationId, content) {
    console.log('Sending message via REST API:', {conversationId, content});

    // Generate a temporary ID for this message
    const tempId = 'temp_rest_' + Date.now() + '_' + Math.floor(Math.random() * 1000);

    // Add a temporary message to the UI with pending indicator
    const tempMessage = {
        sender_id: ChatState.currentUserId,
        content: content,
        timestamp: new Date().toISOString(),
        is_read: false,
        is_pending: true,
        temp_id: tempId
    };
    addMessageToChat(tempMessage);

    // Get CSRF token for the POST request
    const csrfToken = getCSRFToken();

    // Implement exponential backoff for REST API requests
    sendWithRetry(`/api/chat/conversations/${conversationId}/add_message/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({content: content})
    }, 0, tempId);
}

/**
 * Send a request with exponential backoff retry
 * @param {string} url - The URL to send the request to
 * @param {Object} options - The fetch options
 * @param {number} retryCount - The current retry count
 * @param {string} tempId - The temporary message ID
 */
function sendWithRetry(url, options, retryCount, tempId) {
    const MAX_RETRIES = 3;
    const RETRY_DELAY = 1000; // Start with 1 second

    fetch(url, options)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Message sent via REST API:', data);
            showToast('Message sent successfully', 'success');

            // Update the temporary message in the UI
            updateTempMessageWithSuccess(tempId, data.id);
        })
        .catch(error => {
            console.error(`Error sending message via REST API (attempt ${retryCount + 1}):`, error);

            if (retryCount < MAX_RETRIES) {
                // Calculate delay with exponential backoff
                const delay = RETRY_DELAY * Math.pow(2, retryCount);
                console.log(`Retrying in ${delay}ms...`);

                // Show retry toast
                showToast(`Connection issue. Retrying in ${delay/1000} seconds...`, 'warning');

                // Retry after delay
                setTimeout(() => {
                    sendWithRetry(url, options, retryCount + 1, tempId);
                }, delay);
            } else {
                // Max retries reached
                showToast('Failed to send message after multiple attempts. Please try again later.', 'error');

                // Update UI to show failure
                updateTempMessageWithFailure(tempId);
            }
        });
}

/**
 * Update a temporary message with success status
 * @param {string} tempId - The temporary message ID
 * @param {number} realId - The real message ID from the server
 */
function updateTempMessageWithSuccess(tempId, realId) {
    const messageElement = document.querySelector(`.message-item[data-temp-id="${tempId}"]`);
    if (messageElement) {
        // Remove pending class
        messageElement.classList.remove('pending');

        // Update data attribute
        messageElement.removeAttribute('data-temp-id');
        messageElement.setAttribute('data-message-id', realId);

        // Update status icon
        const statusElement = messageElement.querySelector('.message-status');
        if (statusElement) {
            statusElement.innerHTML = '<i class="fas fa-check" aria-label="Sent"></i>';
            statusElement.title = 'Sent';
        }
    }
}

/**
 * Update a temporary message with failure status
 * @param {string} tempId - The temporary message ID
 */
function updateTempMessageWithFailure(tempId) {
    const messageElement = document.querySelector(`.message-item[data-temp-id="${tempId}"]`);
    if (messageElement) {
        // Add failure class
        messageElement.classList.add('failed');
        messageElement.classList.remove('pending');

        // Update status icon
        const statusElement = messageElement.querySelector('.message-status');
        if (statusElement) {
            statusElement.innerHTML = '<i class="fas fa-exclamation-circle" aria-label="Failed to send"></i>';
            statusElement.title = 'Failed to send. Click to retry.';

            // Add retry functionality
            statusElement.style.cursor = 'pointer';
            statusElement.addEventListener('click', () => {
                const content = messageElement.querySelector('.message-content').textContent;
                // Remove the failed message
                messageElement.remove();
                // Try sending again
                sendMessageViaRESTAPI(ChatState.currentConversationId, content);
            });
        }
    }
}

/**
 * Show a toast notification with improved accessibility
 * @param {string} message - The message to show
 * @param {string} type - The type of toast ('info', 'success', 'warning', 'error')
 */
function showToast(message, type = 'info') {
    // Try to use the global toast function if available
    if (typeof window.showToastNotification === 'function') {
        window.showToastNotification(message, type);
        return;
    }

    // Create or get toast container
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        toastContainer.setAttribute('aria-live', 'polite');
        toastContainer.setAttribute('role', 'log');
        document.body.appendChild(toastContainer);
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.setAttribute('role', 'status');

    // Set appropriate ARIA attributes based on type
    if (type === 'error') {
        toast.setAttribute('aria-live', 'assertive');
    }

    // Create icon based on type
    const iconElement = document.createElement('div');
    iconElement.className = 'toast-icon';
    iconElement.setAttribute('aria-hidden', 'true');

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

    // Create close button with improved accessibility
    const closeButton = document.createElement('button');
    closeButton.className = 'toast-close';
    closeButton.setAttribute('aria-label', 'Close notification');
    closeButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';

    // Add event listener to close button
    closeButton.addEventListener('click', () => {
        closeToast(toast);
    });

    // Add keyboard support
    toast.setAttribute('tabindex', '0');
    toast.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeToast(toast);
        }
    });

    // Assemble the toast
    toast.appendChild(iconElement);
    toast.appendChild(contentElement);
    toast.appendChild(closeButton);

    // Add to container
    toastContainer.appendChild(toast);

    // Show the toast with animation
    requestAnimationFrame(() => {
        toast.classList.add('show');
    });

    // Auto-remove after duration
    const duration = CONFIG.UI.TOAST_DURATION;
    const toastTimeout = setTimeout(() => {
        closeToast(toast);
    }, duration);

    // Store timeout ID on the element for potential early removal
    toast.dataset.timeoutId = toastTimeout;
}

/**
 * Close a toast notification with animation
 * @param {Element} toast - The toast element to close
 */
function closeToast(toast) {
    // Clear any existing timeout
    if (toast.dataset.timeoutId) {
        clearTimeout(parseInt(toast.dataset.timeoutId));
    }

    // Remove show class to trigger fade-out animation
    toast.classList.remove('show');

    // Remove from DOM after animation completes
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 300); // Animation duration
}

/**
 * Send a typing indicator update with improved reliability
 * @param {boolean} isTyping - Whether the user is typing
 */
function sendTypingIndicator(isTyping) {
    // Only send typing indicator if we have a conversation ID
    if (!ChatState.currentConversationId) {
        return;
    }

    // Prepare the typing indicator data
    const typingData = {
        'type': 'typing_indicator',
        'conversation_id': ChatState.currentConversationId,
        'is_typing': isTyping
    };

    // Check WebSocket connection status
    if (!ChatState.socket) {
        // WebSocket not initialized, try to initialize it
        initializeChatWebsocket();
        return;
    }

    // Only send if WebSocket is open
    if (ChatState.socket.readyState === WebSocket.OPEN) {
        try {
            ChatState.socket.send(JSON.stringify(typingData));

            // Log with visual indicator for debugging
            if (isTyping) {
                console.log('%c Typing indicator sent ✓ ', 'background: #4CAF50; color: white; padding: 2px 5px; border-radius: 3px;');
            } else {
                console.log('%c Stopped typing indicator sent ✓ ', 'background: #FF9800; color: white; padding: 2px 5px; border-radius: 3px;');
            }
        } catch (error) {
            console.error('Error sending typing indicator:', error);
        }
    } else if (ChatState.socket.readyState === WebSocket.CLOSED) {
        // Try to reconnect if closed
        initializeChatWebsocket();
    }
}

/**
 * Mark messages as read with improved reliability
 */
function markMessagesAsRead() {
    // Only mark messages as read if we have a conversation ID
    if (!ChatState.currentConversationId) {
        return;
    }

    // Prepare the read messages data
    const readData = {
        'type': 'read_messages',
        'conversation_id': ChatState.currentConversationId
    };

    // Check WebSocket connection status
    if (!ChatState.socket || ChatState.socket.readyState !== WebSocket.OPEN) {
        // WebSocket not available or not open, use REST API fallback
        markMessagesAsReadViaAPI(ChatState.currentConversationId);
        return;
    }

    // Send read messages notification via WebSocket
    try {
        ChatState.socket.send(JSON.stringify(readData));

        // Update UI to reflect read status
        removeUnreadBadge(ChatState.currentConversationId);
    } catch (error) {
        console.error('Error marking messages as read via WebSocket:', error);

        // Fallback to REST API
        markMessagesAsReadViaAPI(ChatState.currentConversationId);
    }
}

/**
 * Mark messages as read via REST API with improved error handling
 * @param {number} conversationId - The conversation ID
 */
function markMessagesAsReadViaAPI(conversationId) {
    if (!conversationId) {
        return;
    }

    // Get CSRF token for the POST request
    const csrfToken = getCSRFToken();

    // Create the request with retry logic
    fetch(`/api/chat/conversations/${conversationId}/mark_read/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        // Add credentials to ensure cookies are sent
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Update UI to reflect read status
        removeUnreadBadge(conversationId);
    })
    .catch(error => {
        console.error('Error marking messages as read via API:', error);

        // We don't retry here as this is not critical functionality
        // and will be attempted again when new messages arrive
    });
}

/**
 * Remove unread badge from a conversation in the list
 * @param {number} conversationId - The conversation ID
 */
function removeUnreadBadge(conversationId) {
    const conversationItem = document.querySelector(`.conversation-item[href*="${conversationId}"]`);
    if (!conversationItem) return;

    const unreadBadge = conversationItem.querySelector('.unread-badge');
    if (unreadBadge) {
        // Add fade-out animation
        unreadBadge.classList.add('fade-out');

        // Remove after animation completes
        setTimeout(() => {
            if (unreadBadge.parentNode) {
                unreadBadge.remove();
            }
        }, 300);
    }
}

/**
 * Add a message to the chat UI with improved rendering and accessibility
 * @param {Object} message - The message object to add
 */
function addMessageToChat(message) {
    try {
        // Validate message and required elements
        const messageList = document.getElementById('message-list');
        if (!messageList) {
            console.error('Message list element not found');
            return;
        }

        if (!message) {
            console.error('No message data provided');
            return;
        }

        if (!message.content && !message.is_file && !message.file_attachment && !message.file_name) {
            console.warn('Message has no content or file attachment');
            return;
        }

        if (!ChatState.currentUserId) {
            console.warn('Current user ID not set');
        }

        // Check for duplicate messages
        if (message.id) {
            // If the message has an ID, check if it's already in the DOM
            const existingMessage = document.querySelector(`.message-item[data-message-id="${message.id}"]`);
            if (existingMessage) {
                // Update existing message instead of adding a new one
                updateExistingMessage(existingMessage, message);
                return;
            }
        } else if (message.temp_id) {
            // If it has a temp_id, check for that
            const existingMessage = document.querySelector(`.message-item[data-temp-id="${message.temp_id}"]`);
            if (existingMessage) {
                // Update existing message instead of adding a new one
                updateExistingMessage(existingMessage, message);
                return;
            }
        }

        const isOutgoing = message.sender_id === ChatState.currentUserId;
        console.log(`Adding ${isOutgoing ? 'outgoing' : 'incoming'} message:`, message);

        // Create the message element with improved accessibility
        const messageElement = document.createElement('div');
        messageElement.className = `message-item ${isOutgoing ? 'outgoing' : 'incoming'}`;

        // Add ARIA attributes for accessibility
        messageElement.setAttribute('role', 'article');

        // Add pending class if the message is pending
        if (message.is_pending) {
            messageElement.classList.add('pending');
        }

        // Add data attributes for potential future reference
        if (message.id) {
            messageElement.dataset.messageId = message.id;
        }

        // Add temp ID if available (for tracking temporary messages)
        if (message.temp_id) {
            messageElement.dataset.tempId = message.temp_id;
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
        messageElement.setAttribute('aria-label',
            `${isOutgoing ? 'You' : 'Other user'} at ${timeElement.textContent}`);

        // Check if we need to remove the empty message placeholder
        const emptyMessages = messageList.querySelector('.empty-messages');
        if (emptyMessages) {
            emptyMessages.remove();
        }

        // Add the message to the chat with animation
        messageElement.style.opacity = '0';
        messageElement.style.transform = 'translateY(10px)';
        messageList.appendChild(messageElement);

        // Trigger animation after a small delay
        setTimeout(() => {
            messageElement.style.opacity = '1';
            messageElement.style.transform = 'translateY(0)';
            messageElement.classList.add('visible');
        }, CONFIG.UI.ANIMATION_DELAY);

        // Scroll to the new message with smooth behavior
        scrollToBottom(messageList);

        // If this is an incoming message and we're visible, mark it as read
        if (!isOutgoing && document.visibilityState === 'visible') {
            markMessagesAsRead();

            // Play notification sound if enabled
            if (document.hidden) {
                playMessageSound();
            }
        }
    } catch (error) {
        console.error('Error adding message to chat:', error);
    }
}

/**
 * Update an existing message in the UI
 * @param {Element} messageElement - The message element to update
 * @param {Object} message - The updated message data
 */
function updateExistingMessage(messageElement, message) {
    try {
        // Update content if it changed
        const contentElement = messageElement.querySelector('.message-content');
        if (contentElement && message.content && !message.is_file) {
            // For regular text messages, update the content
            contentElement.textContent = message.content;

            // Re-apply URL formatting if needed
            applyUrlFormatting(contentElement, message.content);
        }

        // Update status for outgoing messages
        if (messageElement.classList.contains('outgoing')) {
            const statusElement = messageElement.querySelector('.message-status');
            if (statusElement) {
                // Update status icon
                if (message.is_pending) {
                    statusElement.innerHTML = '<i class="fas fa-clock" aria-label="Pending"></i>';
                    statusElement.title = 'Pending';
                } else if (message.is_read) {
                    statusElement.innerHTML = '<i class="fas fa-check-double read-indicator" aria-label="Read"></i>';
                    statusElement.title = 'Read';
                } else {
                    statusElement.innerHTML = '<i class="fas fa-check" aria-label="Sent"></i>';
                    statusElement.title = 'Sent';
                }
            }
        }

        // Update classes
        if (message.is_pending) {
            messageElement.classList.add('pending');
        } else {
            messageElement.classList.remove('pending');
        }

        // Update data attributes
        if (message.id) {
            messageElement.dataset.messageId = message.id;
            // Remove temp ID if real ID is now available
            if (messageElement.dataset.tempId) {
                delete messageElement.dataset.tempId;
            }
        }

        console.log('Updated existing message:', message);
    } catch (error) {
        console.error('Error updating existing message:', error);
    }
}

/**
 * Apply URL formatting to message content
 * @param {Element} contentElement - The content element
 * @param {string} text - The text to format
 */
function applyUrlFormatting(contentElement, text) {
    // Clear the element
    contentElement.innerHTML = '';

    // Use a safe URL regex pattern
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    let lastIndex = 0;
    let match;

    // Process each URL match
    while ((match = urlRegex.exec(text)) !== null) {
        // Add text before the URL
        if (match.index > lastIndex) {
            contentElement.appendChild(
                document.createTextNode(text.substring(lastIndex, match.index))
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
    if (lastIndex < text.length) {
        contentElement.appendChild(
            document.createTextNode(text.substring(lastIndex))
        );
    }
}

/**
 * Scroll to the bottom of the message list with smooth animation
 * @param {Element} messageList - The message list element
 */
function scrollToBottom(messageList) {
    // Check if user is already near bottom before scrolling
    const isNearBottom = messageList.scrollHeight - messageList.clientHeight - messageList.scrollTop < 100;

    if (isNearBottom) {
        messageList.scrollTo({
            top: messageList.scrollHeight,
            behavior: 'smooth'
        });
    } else {
        // If user has scrolled up, show a "new message" indicator instead of auto-scrolling
        showNewMessageIndicator();
    }
}

/**
 * Show a "new message" indicator when user has scrolled up
 */
function showNewMessageIndicator() {
    let indicator = document.getElementById('new-message-indicator');

    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'new-message-indicator';
        indicator.className = 'new-message-indicator';
        indicator.innerHTML = '<i class="fas fa-arrow-down"></i> New message';
        indicator.setAttribute('role', 'button');
        indicator.setAttribute('tabindex', '0');

        // Add click handler to scroll to bottom
        indicator.addEventListener('click', () => {
            const messageList = document.getElementById('message-list');
            if (messageList) {
                messageList.scrollTo({
                    top: messageList.scrollHeight,
                    behavior: 'smooth'
                });
                indicator.style.display = 'none';
            }
        });

        // Add keyboard handler
        indicator.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                indicator.click();
            }
        });

        // Add to page
        const chatContainer = document.querySelector('.chat-container');
        if (chatContainer) {
            chatContainer.appendChild(indicator);
        }
    }

    // Show the indicator
    indicator.style.display = 'flex';

    // Auto-hide after 5 seconds
    setTimeout(() => {
        if (indicator) {
            indicator.style.display = 'none';
        }
    }, 5000);
}

/**
 * Play a notification sound for new messages
 */
function playMessageSound() {
    // Check if sound is enabled in user preferences
    const soundEnabled = localStorage.getItem('chat_sound_enabled') !== 'false';

    if (soundEnabled) {
        try {
            const audio = new Audio('/static/chatting/sounds/message.mp3');
            audio.volume = 0.5;
            audio.play().catch(error => {
                // Autoplay might be blocked by browser policy
                console.log('Could not play notification sound:', error);
            });
        } catch (error) {
            console.error('Error playing notification sound:', error);
        }
    }
}

// Handle network status changes with improved user feedback
window.addEventListener('online', function() {
    console.log('Network connection restored');
    showToast('You are back online', 'success');

    // Reconnect WebSocket if needed
    if (!ChatState.socket || ChatState.socket.readyState !== WebSocket.OPEN) {
        // Reset reconnect attempts
        ChatState.reconnectAttempts = 0;
        window.reconnectAttempts = 0;

        // Initialize WebSocket
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

    // Add offline indicator to the page
    addOfflineIndicator();
});

/**
 * Add an offline indicator to the page
 */
function addOfflineIndicator() {
    // Remove any existing indicator
    removeOfflineIndicator();

    // Create offline indicator
    const indicator = document.createElement('div');
    indicator.id = 'offline-indicator';
    indicator.className = 'offline-indicator';
    indicator.innerHTML = '<i class="fas fa-wifi"></i> You are offline';
    indicator.setAttribute('role', 'status');
    indicator.setAttribute('aria-live', 'polite');

    // Add to page
    document.body.appendChild(indicator);
}

/**
 * Remove the offline indicator
 */
function removeOfflineIndicator() {
    const indicator = document.getElementById('offline-indicator');
    if (indicator) {
        indicator.remove();
    }
}

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
 * Initialize emoji picker functionality with improved accessibility
 */
function initializeEmojiPicker() {
    // Get all required elements
    const emojiButton = document.getElementById('emoji-button');
    const emojiPicker = document.getElementById('emoji-picker');
    const closeEmojiButton = document.getElementById('close-emoji');
    const emojis = document.querySelectorAll('.emoji');

    // Get the message input
    const messageInput = document.getElementById('message-input');

    // Check if elements exist
    if (!emojiButton || !emojiPicker) {
        return;
    }

    // Clean up existing event listeners if they exist
    if (ChatState.eventListeners.emojiButton) {
        emojiButton.removeEventListener('click', ChatState.eventListeners.emojiButton);
    }

    if (ChatState.eventListeners.closeEmojiButton && closeEmojiButton) {
        closeEmojiButton.removeEventListener('click', ChatState.eventListeners.closeEmojiButton);
    }

    if (ChatState.eventListeners.documentClickForEmoji) {
        document.removeEventListener('click', ChatState.eventListeners.documentClickForEmoji);
    }

    // Make sure emoji picker is initially hidden and has the correct styles
    emojiPicker.style.display = 'none';
    emojiPicker.classList.remove('active');

    // Add ARIA attributes for accessibility
    emojiButton.setAttribute('aria-expanded', 'false');
    emojiButton.setAttribute('aria-controls', 'emoji-picker');
    emojiPicker.setAttribute('role', 'dialog');
    emojiPicker.setAttribute('aria-label', 'Emoji picker');

    // Create click handler for emoji button
    const emojiButtonHandler = function(e) {
        e.preventDefault();
        e.stopPropagation();

        // Toggle visibility
        const isVisible = emojiPicker.style.display !== 'none' && emojiPicker.classList.contains('active');

        if (!isVisible) {
            showEmojiPicker();
        } else {
            hideEmojiPicker();
        }

        return false;
    };

    // Add event listener
    emojiButton.addEventListener('click', emojiButtonHandler);
    ChatState.eventListeners.emojiButton = emojiButtonHandler;

    // Close emoji picker button
    if (closeEmojiButton) {
        const closeEmojiButtonHandler = function(e) {
            e.preventDefault();
            e.stopPropagation();
            hideEmojiPicker();
            return false;
        };

        closeEmojiButton.addEventListener('click', closeEmojiButtonHandler);
        ChatState.eventListeners.closeEmojiButton = closeEmojiButtonHandler;
    }

    // Add emoji to message input when clicked
    emojis.forEach(function(emoji) {
        // Remove existing event listener if it exists
        if (emoji.onclick) {
            emoji.removeEventListener('click', emoji.onclick);
        }

        // Create new event listener
        const emojiClickHandler = function(e) {
            e.preventDefault();
            e.stopPropagation();

            const emojiChar = this.getAttribute('data-emoji');

            if (!messageInput) {
                return false;
            }

            // Insert emoji at cursor position
            insertEmojiAtCursor(messageInput, emojiChar);

            // Hide emoji picker
            hideEmojiPicker();

            return false;
        };

        emoji.addEventListener('click', emojiClickHandler);

        // Add keyboard support
        emoji.setAttribute('tabindex', '0');
        emoji.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });
    });

    // Close emoji picker when clicking outside
    const documentClickHandler = function(e) {
        if (emojiPicker && emojiPicker.style.display !== 'none' &&
            !emojiPicker.contains(e.target) && e.target !== emojiButton) {
            hideEmojiPicker();
        }
    };

    document.addEventListener('click', documentClickHandler);
    ChatState.eventListeners.documentClickForEmoji = documentClickHandler;

    // Add keyboard support for closing with Escape key
    emojiPicker.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            hideEmojiPicker();
        }
    });

    // Helper function to show emoji picker
    function showEmojiPicker() {
        emojiPicker.style.display = 'block';
        emojiPicker.classList.add('active');
        emojiButton.setAttribute('aria-expanded', 'true');
        ChatState.isEmojiPickerOpen = true;

        // Focus the first emoji for keyboard navigation
        setTimeout(() => {
            const firstEmoji = emojiPicker.querySelector('.emoji');
            if (firstEmoji) {
                firstEmoji.focus();
            }
        }, 100);

        // Implement focus trap
        implementFocusTrap(emojiPicker);
    }

    // Helper function to hide emoji picker
    function hideEmojiPicker() {
        emojiPicker.style.display = 'none';
        emojiPicker.classList.remove('active');
        emojiButton.setAttribute('aria-expanded', 'false');
        ChatState.isEmojiPickerOpen = false;

        // Return focus to emoji button
        emojiButton.focus();
    }

    // Helper function to insert emoji at cursor position
    function insertEmojiAtCursor(input, emoji) {
        if (!input) return;

        // Get cursor position
        const cursorPos = input.selectionStart;
        const textBefore = input.value.substring(0, cursorPos);
        const textAfter = input.value.substring(cursorPos);

        // Insert emoji
        input.value = textBefore + emoji + textAfter;
        input.focus();

        // Update cursor position
        input.selectionStart = cursorPos + emoji.length;
        input.selectionEnd = cursorPos + emoji.length;

        // Trigger input event to activate typing indicator
        input.dispatchEvent(new Event('input', { bubbles: true }));
    }

    // Helper function to implement focus trap
    function implementFocusTrap(element) {
        // Get all focusable elements
        const focusableElements = element.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');

        if (focusableElements.length === 0) return;

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        // Add event listener for tab key
        element.addEventListener('keydown', function(e) {
            if (e.key === 'Tab') {
                // Shift + Tab
                if (e.shiftKey && document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                }
                // Tab
                else if (!e.shiftKey && document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement.focus();
                }
            }
        });
    }
}

/**
 * Initialize file attachment functionality with improved UX and accessibility
 */
function initializeFileAttachment() {
    // Get required elements
    const attachmentButton = document.getElementById('attachment-button');
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');

    // Check if elements exist
    if (!attachmentButton || !messageForm) {
        return;
    }

    // Clean up existing event listeners if they exist
    if (ChatState.eventListeners.attachmentButton) {
        attachmentButton.removeEventListener('click', ChatState.eventListeners.attachmentButton);
    }

    // Add ARIA attributes for accessibility
    attachmentButton.setAttribute('aria-label', 'Attach file');
    attachmentButton.setAttribute('title', 'Attach file');

    // Create or get file input element
    let fileInput = document.getElementById('file-input');
    if (!fileInput) {
        fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.id = 'file-input';
        fileInput.accept = CONFIG.FILE.ALLOWED_TYPES;
        fileInput.style.display = 'none';
        fileInput.setAttribute('aria-hidden', 'true');

        // Add file input to form
        messageForm.appendChild(fileInput);
    }

    // Create click handler for attachment button
    const attachmentButtonHandler = function(e) {
        e.preventDefault();
        e.stopPropagation();

        // Reset the file input to ensure change event fires even if selecting the same file
        fileInput.value = '';
        fileInput.click();

        return false;
    };

    // Add event listener
    attachmentButton.addEventListener('click', attachmentButtonHandler);
    ChatState.eventListeners.attachmentButton = attachmentButtonHandler;

    // Handle file selection with improved validation and preview
    fileInput.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            const file = this.files[0];

            // Validate file
            if (!validateFile(file)) {
                this.value = '';
                return;
            }

            // Create and show file preview
            createFilePreview(file, messageForm, messageInput, fileInput);
        }
    });

    // Override form submission to handle file
    messageForm.addEventListener('submit', function(e) {
        e.preventDefault();

        // Check if we have a file to send
        if (fileInput.files && fileInput.files[0]) {
            const file = fileInput.files[0];
            const messageText = messageInput ? messageInput.value.trim() : '';

            // Send file with optional message
            sendFileMessage(file, messageText);

            // Reset file input and UI
            resetFileUpload(fileInput, messageInput);
        } else {
            // No file, send regular message
            sendMessage();
        }

        return false;
    });

    // Add drag and drop support
    setupDragAndDrop(messageForm, fileInput);
}

/**
 * Validate a file before upload
 * @param {File} file - The file to validate
 * @returns {boolean} Whether the file is valid
 */
function validateFile(file) {
    // Check file size
    if (file.size > CONFIG.FILE.MAX_SIZE) {
        const maxSizeMB = CONFIG.FILE.MAX_SIZE / (1024 * 1024);
        showToast(`File size exceeds ${maxSizeMB}MB limit`, 'error');
        return false;
    }

    // Check file type
    const allowedExtensions = CONFIG.FILE.ALLOWED_TYPES.split(',');
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();

    let isAllowed = false;

    // Check if file type matches any allowed extension or MIME type pattern
    for (const ext of allowedExtensions) {
        if (ext.startsWith('image/') && file.type.startsWith('image/')) {
            isAllowed = true;
            break;
        } else if (ext === fileExtension) {
            isAllowed = true;
            break;
        }
    }

    if (!isAllowed) {
        showToast('File type not allowed', 'error');
        return false;
    }

    return true;
}

/**
 * Create and show file preview
 * @param {File} file - The file to preview
 * @param {Element} messageForm - The message form element
 * @param {Element} messageInput - The message input element
 * @param {Element} fileInput - The file input element
 */
function createFilePreview(file, messageForm, messageInput, fileInput) {
    // Remove any existing preview
    const existingPreview = document.querySelector('.attachment-preview');
    if (existingPreview) {
        existingPreview.remove();
    }

    // Create attachment preview
    const attachmentPreview = document.createElement('div');
    attachmentPreview.className = 'attachment-preview';
    attachmentPreview.setAttribute('role', 'region');
    attachmentPreview.setAttribute('aria-label', 'File attachment preview');

    // Determine file icon based on type
    const fileIcon = getFileIcon(file);

    // Format file size
    const fileSize = formatFileSize(file.size);

    // Create preview content
    attachmentPreview.innerHTML = `
        <div class="file-icon">
            <i class="fas ${fileIcon}" aria-hidden="true"></i>
        </div>
        <div class="file-info">
            <div class="file-name">${escapeHTML(file.name)}</div>
            <div class="file-size">${fileSize}</div>
        </div>
        <div class="file-actions">
            <button type="button" class="remove-file" aria-label="Remove file">
                <i class="fas fa-times" aria-hidden="true"></i>
            </button>
            <button type="button" class="send-file" aria-label="Send file">
                <i class="fas fa-paper-plane" aria-hidden="true"></i> Send
            </button>
        </div>
    `;

    // Add preview before message input
    const messageInputContainer = document.querySelector('.message-input-container');
    if (messageInputContainer) {
        messageInputContainer.insertBefore(attachmentPreview, messageForm);
    }

    // Handle remove button
    const removeButton = attachmentPreview.querySelector('.remove-file');
    removeButton.addEventListener('click', function(e) {
        e.preventDefault();
        attachmentPreview.remove();
        fileInput.value = '';
    });

    // Handle send button
    const sendButton = attachmentPreview.querySelector('.send-file');
    sendButton.addEventListener('click', function(e) {
        e.preventDefault();

        // Get message text
        const messageText = messageInput ? messageInput.value.trim() : '';

        // Send the file
        sendFileMessage(file, messageText);

        // Reset file input and UI
        resetFileUpload(fileInput, messageInput);
    });

    // Add image preview for image files
    if (file.type.startsWith('image/')) {
        addImagePreview(file, attachmentPreview);
    }

    // Focus on message input for optional message
    if (messageInput) {
        messageInput.focus();
    }
}

/**
 * Add image preview for image files
 * @param {File} file - The image file
 * @param {Element} previewContainer - The preview container element
 */
function addImagePreview(file, previewContainer) {
    // Create image preview element
    const imagePreview = document.createElement('div');
    imagePreview.className = 'image-preview';

    // Create image element
    const img = document.createElement('img');
    img.alt = 'Image preview';

    // Read file as data URL
    const reader = new FileReader();
    reader.onload = function(e) {
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);

    // Add image to preview
    imagePreview.appendChild(img);

    // Add to preview container before the file info
    const fileInfo = previewContainer.querySelector('.file-info');
    if (fileInfo) {
        previewContainer.insertBefore(imagePreview, fileInfo);
    } else {
        previewContainer.appendChild(imagePreview);
    }
}

/**
 * Get file icon based on file type
 * @param {File} file - The file
 * @returns {string} Font Awesome icon class
 */
function getFileIcon(file) {
    let fileIcon = 'fa-file';

    if (file.type.startsWith('image/')) {
        fileIcon = 'fa-file-image';
    } else if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
        fileIcon = 'fa-file-pdf';
    } else if (file.type.includes('word') || file.name.endsWith('.doc') || file.name.endsWith('.docx')) {
        fileIcon = 'fa-file-word';
    } else if (file.type.includes('excel') || file.name.endsWith('.xls') || file.name.endsWith('.xlsx')) {
        fileIcon = 'fa-file-excel';
    } else if (file.type.includes('powerpoint') || file.name.endsWith('.ppt') || file.name.endsWith('.pptx')) {
        fileIcon = 'fa-file-powerpoint';
    } else if (file.name.endsWith('.txt')) {
        fileIcon = 'fa-file-alt';
    }

    return fileIcon;
}

/**
 * Format file size in human-readable format
 * @param {number} size - File size in bytes
 * @returns {string} Formatted file size
 */
function formatFileSize(size) {
    if (size < 1024) {
        return size + ' B';
    } else if (size < 1024 * 1024) {
        return Math.round(size / 1024) + ' KB';
    } else {
        return Math.round(size / (1024 * 1024) * 10) / 10 + ' MB';
    }
}

/**
 * Reset file upload UI
 * @param {Element} fileInput - The file input element
 * @param {Element} messageInput - The message input element
 */
function resetFileUpload(fileInput, messageInput) {
    // Reset file input
    fileInput.value = '';

    // Remove preview
    const preview = document.querySelector('.attachment-preview');
    if (preview) {
        preview.remove();
    }

    // Clear message input
    if (messageInput) {
        messageInput.value = '';
        messageInput.focus();
    }
}

/**
 * Set up drag and drop support for file uploads
 * @param {Element} messageForm - The message form element
 * @param {Element} fileInput - The file input element
 */
function setupDragAndDrop(messageForm, fileInput) {
    const dropZone = document.querySelector('.chat-container');
    if (!dropZone) return;

    // Add drag and drop event listeners
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Highlight drop zone when dragging over
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
        dropZone.classList.add('drag-over');
    }

    function unhighlight() {
        dropZone.classList.remove('drag-over');
    }

    // Handle dropped files
    dropZone.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;

        if (files.length > 0) {
            fileInput.files = files;

            // Trigger change event
            const event = new Event('change', { bubbles: true });
            fileInput.dispatchEvent(event);
        }
    }
}

/**
 * Send a file message with progress tracking
 * @param {File} file - The file to send
 * @param {string} messageText - Optional message text to include with the file
 */
function sendFileMessage(file, messageText) {
    // Only send if we have a conversation ID
    if (!ChatState.currentConversationId) {
        showToast('Cannot send file: No active conversation', 'error');
        return;
    }

    // Generate a temporary ID for this message
    const tempId = 'temp_file_' + Date.now() + '_' + Math.floor(Math.random() * 1000);

    // Add a temporary message to the UI with pending indicator
    const tempMessage = {
        sender_id: ChatState.currentUserId,
        content: messageText || 'Sending file: ' + file.name,
        timestamp: new Date().toISOString(),
        is_read: false,
        is_pending: true,
        is_file: true,
        file_name: file.name,
        file_type: file.type.startsWith('image/') ? 'image' : 'document',
        temp_id: tempId
    };

    // Add message to chat
    addMessageToChat(tempMessage);

    // Create FormData to send the file
    const formData = new FormData();
    formData.append('file_attachment', file);
    formData.append('content', messageText || '');

    // Get CSRF token
    const csrfToken = getCSRFToken();

    // Create XMLHttpRequest to track upload progress
    const xhr = new XMLHttpRequest();

    // Set up progress tracking
    xhr.upload.addEventListener('progress', function(e) {
        if (e.lengthComputable) {
            const percentComplete = Math.round((e.loaded / e.total) * 100);
            updateFileUploadProgress(tempId, percentComplete);
        }
    });

    // Handle successful completion
    xhr.addEventListener('load', function() {
        if (xhr.status >= 200 && xhr.status < 300) {
            try {
                const data = JSON.parse(xhr.responseText);
                handleFileUploadSuccess(data, tempId);
            } catch (error) {
                console.error('Error parsing response:', error);
                handleFileUploadError(error, tempId, file);
            }
        } else {
            const error = new Error(`Server responded with status: ${xhr.status}`);
            handleFileUploadError(error, tempId, file);
        }
    });

    // Handle errors
    xhr.addEventListener('error', function() {
        const error = new Error('Network error occurred during file upload');
        handleFileUploadError(error, tempId, file);
    });

    // Handle timeouts
    xhr.addEventListener('timeout', function() {
        const error = new Error('File upload timed out');
        handleFileUploadError(error, tempId, file);
    });

    // Handle aborts
    xhr.addEventListener('abort', function() {
        const error = new Error('File upload was aborted');
        handleFileUploadError(error, tempId, file);
    });

    // Open and send the request
    xhr.open('POST', `/api/chat/conversations/${ChatState.currentConversationId}/add_message/`);
    xhr.setRequestHeader('X-CSRFToken', csrfToken);
    xhr.send(formData);

    // Show initial toast
    showToast('Sending file...', 'info');
}

/**
 * Update file upload progress in the UI
 * @param {string} tempId - The temporary message ID
 * @param {number} percent - The upload progress percentage
 */
function updateFileUploadProgress(tempId, percent) {
    const messageElement = document.querySelector(`.message-item[data-temp-id="${tempId}"]`);
    if (!messageElement) return;

    // Get or create progress bar
    let progressBar = messageElement.querySelector('.upload-progress');
    if (!progressBar) {
        // Create progress container
        const progressContainer = document.createElement('div');
        progressContainer.className = 'upload-progress-container';

        // Create progress bar
        progressBar = document.createElement('div');
        progressBar.className = 'upload-progress';

        // Create progress text
        const progressText = document.createElement('span');
        progressText.className = 'upload-progress-text';

        // Add to container
        progressContainer.appendChild(progressBar);
        progressContainer.appendChild(progressText);

        // Add to message
        const messageBubble = messageElement.querySelector('.message-bubble') || messageElement;
        messageBubble.appendChild(progressContainer);
    }

    // Update progress
    progressBar.style.width = `${percent}%`;

    // Update text
    const progressText = messageElement.querySelector('.upload-progress-text');
    if (progressText) {
        progressText.textContent = `${percent}%`;
    }

    // Update status text
    const statusElement = messageElement.querySelector('.message-status');
    if (statusElement) {
        statusElement.innerHTML = '<i class="fas fa-upload" aria-label="Uploading"></i>';
        statusElement.title = `Uploading: ${percent}%`;
    }
}

/**
 * Handle successful file upload
 * @param {Object} data - The server response data
 * @param {string} tempId - The temporary message ID
 */
function handleFileUploadSuccess(data, tempId) {
    // Show success toast
    showToast('File sent successfully', 'success');

    // Check if file_url is present in the response
    if (!data.file_url && data.file_attachment) {
        // If file_url is missing but file_attachment exists, construct the URL
        data.file_url = '/media/' + data.file_attachment;
    }

    // Add the message to the chat UI (will update existing message)
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
}

/**
 * Handle file upload error
 * @param {Error} error - The error object
 * @param {string} tempId - The temporary message ID
 * @param {File} file - The file that failed to upload
 */
function handleFileUploadError(error, tempId, file) {
    console.error('Error sending file:', error);
    showToast('Error sending file. Please try again.', 'error');

    // Log file information
    console.error('File information:', {
        name: file.name,
        type: file.type,
        size: file.size
    });

    // Update the message to show error
    const messageElement = document.querySelector(`.message-item[data-temp-id="${tempId}"]`);
    if (messageElement) {
        // Add error class
        messageElement.classList.add('error');
        messageElement.classList.remove('pending');

        // Update status icon
        const statusElement = messageElement.querySelector('.message-status');
        if (statusElement) {
            statusElement.innerHTML = '<i class="fas fa-exclamation-circle" aria-label="Failed to send"></i>';
            statusElement.title = 'Failed to send. Click to retry.';

            // Add retry functionality
            statusElement.style.cursor = 'pointer';
            statusElement.addEventListener('click', () => {
                // Get file input
                const fileInput = document.getElementById('file-input');
                if (!fileInput || !fileInput.files || !fileInput.files[0]) {
                    showToast('Please select the file again to retry', 'warning');
                    return;
                }

                // Get message text
                const content = messageElement.querySelector('.message-content').textContent;

                // Remove the failed message
                messageElement.remove();

                // Try sending again
                sendFileMessage(fileInput.files[0], content);
            });
        }

        // Remove progress bar
        const progressContainer = messageElement.querySelector('.upload-progress-container');
        if (progressContainer) {
            progressContainer.remove();
        }
    }
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

    // Delegate event listener for message actions
    messageList.addEventListener('click', function (e) {
        // Handle edit button clicks
        if (e.target.closest('.edit-message')) {
            e.preventDefault();
            e.stopPropagation();

            try {
                const messageItem = e.target.closest('.message-item');
                if (!messageItem) return;

                const messageContent = messageItem.querySelector('.message-content');
                if (!messageContent) return;

                const originalText = messageContent.textContent;

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
                if (textarea) {
                    textarea.focus();
                    textarea.setSelectionRange(textarea.value.length, textarea.value.length);
                }
            } catch (error) {
                console.error('Error handling edit button click:', error);
            }
        }

        // Handle delete button clicks
        if (e.target.closest('.delete-message')) {
            e.preventDefault();
            e.stopPropagation();

            try {
                const messageItem = e.target.closest('.message-item');
                if (!messageItem) return;

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
            } catch (error) {
                console.error('Error handling delete button click:', error);
            }
        }

        // Handle save edit button clicks
        if (e.target.closest('.save-edit')) {
            e.preventDefault();
            e.stopPropagation();

            try {
                const messageItem = e.target.closest('.message-item');
                if (!messageItem) return;

                const messageContent = messageItem.querySelector('.message-content');
                if (!messageContent) return;

                const textarea = messageContent.querySelector('.edit-textarea');
                if (!textarea) return;

                const newText = textarea.value.trim();

                if (newText) {
                    // For now, just update the UI
                    // In a real implementation, you would send an update request to the server
                    messageContent.innerHTML = newText;
                    messageItem.classList.remove('editing');

                    showToast('Message updated locally. Server-side editing coming in the next update!', 'info');
                } else {
                    showToast('Message cannot be empty', 'error');
                }
            } catch (error) {
                console.error('Error handling save edit button click:', error);
            }
        }

        // Handle cancel edit button clicks
        if (e.target.closest('.cancel-edit')) {
            e.preventDefault();
            e.stopPropagation();

            try {
                const messageItem = e.target.closest('.message-item');
                if (!messageItem) return;

                const messageContent = messageItem.querySelector('.message-content');
                if (!messageContent) return;

                const textarea = messageContent.querySelector('.edit-textarea');
                if (!textarea) return;

                const originalText = textarea.value;

                // Restore original content
                messageContent.innerHTML = originalText;
                messageItem.classList.remove('editing');
            } catch (error) {
                console.error('Error handling cancel edit button click:', error);
            }
        }
    });
}
