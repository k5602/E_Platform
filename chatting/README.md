# Real-time Chat System

This module provides real-time chat functionality for the E-Platform project. It allows users to send direct messages to each other, view who's online, and manage conversations.

## Features

- **Real-time Messaging:** Send and receive messages instantly using WebSockets
- **Online Status Indicators:** See when users are online or offline with last seen timestamps
- **Conversation Management:** View and manage all your conversations
- **Message History:** Access complete message history for each conversation
- **Typing Indicators:** See when someone is typing a message
- **Read Receipts:** Know when your messages have been read
- **Offline Support:** Messages are queued when offline and sent when connection is restored
- **Toast Notifications:** User-friendly notifications for various events
- **Responsive Design:** Works on desktop and mobile devices
- **Accessibility:** ARIA attributes and keyboard navigation support
- **Dark/Light Mode Support:** Integrated with the platform's theme system

## Technical Implementation

### Backend Components

- **Models:**
  - `Conversation`: Represents a chat between two users
  - `Message`: Stores individual messages within conversations
  - `UserStatus`: Tracks online/offline status of users

- **WebSockets:**
  - Uses Django Channels for real-time WebSocket connections
  - Separate consumers for chat messages and online status

- **REST API:**
  - Endpoints for retrieving conversations and message history
  - Support for pagination of message history

### Frontend Components

- **Chat Interface:**
  - Conversation list with unread message indicators
  - Message input with support for Enter key to send
  - Typing indicators and online status display
  - Responsive design for all screen sizes

- **WebSocket Integration:**
  - Automatic reconnection if connection is lost
  - Real-time updates for new messages and online status

## Setup Instructions

1. Ensure Django Channels is installed and configured:
   ```
   pip install channels daphne
   ```

2. Run migrations to create the database tables:
   ```
   python manage.py migrate chatting
   ```

3. Configure ASGI routing as specified in `E_Platform/asgi.py`

4. Access the chat system at `/chat/`

## API Documentation

### WebSocket Endpoints

- `/ws/chat/` - Unified endpoint for chat messages, typing indicators, and online status updates

### REST API Endpoints

- `GET /api/chat/conversations/` - List all conversations
- `GET /api/chat/conversations/<id>/` - View specific conversation with messages
- `POST /api/chat/conversations/start_conversation/` - Start a new conversation
- `POST /api/chat/conversations/<id>/add_message/` - Add a message to conversation
- `GET /api/chat/users/` - List all users with online status
- `GET /api/chat/users/<id>/status/` - Check specific user's online status

## Usage in Templates

### Adding Chat Button to User Profiles

Method 1: Using the include tag:
```html
{% include "chatting/message_button.html" with profile_user=user_object %}
```

Method 2: Direct implementation:
```html
<a href="{% url 'chatting:start_conversation' profile_user.id %}" class="profile-action-btn chat-btn">
    <i class="material-icons">chat</i>
    <span>Chat with {{ profile_user.first_name }}</span>
</a>
```

### Displaying Online Status

```html
<span class="status-indicator {% if user.chat_status.is_online %}online{% else %}offline{% endif %}"
      data-user-id="{{ user.id }}"
      aria-hidden="true"></span>
<span class="status-text" aria-live="polite">
    {% if user.chat_status.is_online %}
        Online
    {% else %}
        {% if user.chat_status.last_active %}
            Last seen {{ user.chat_status.last_active|timesince }} ago
        {% else %}
            Offline
        {% endif %}
    {% endif %}
</span>
```

### Initializing WebSocket Connection

```html
<script src="{% static 'chatting/js/chat.js' %}"></script>
<script>
    document.addEventListener('DOMContentLoaded', function() {
        // Initialize WebSocket connection
        const chatSocket = initializeChatWebsocket();
    });
</script>
```

## Integration with Existing Systems

The chat system integrates with:
- User authentication system
- The platform's theme system (light/dark mode)
- Notification system
- User profile system

## Future Enhancements

Planned features for future development:
- Group chat support
- Media sharing (images, files, videos)
- Message reactions and emoji support
- Message search functionality
- End-to-end encryption
- Voice and video calls
- Message forwarding and deletion
- Read-only mode for archived conversations