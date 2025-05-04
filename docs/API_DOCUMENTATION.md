# E-Platform REST API Documentation

This document provides information about the REST API for the E-Platform educational application.

## Features

- **Authentication**: JWT-based authentication for secure API access
- **Posts**: Create, read, update, and delete posts with media attachments
- **Comments**: Add and manage comments on posts
- **Likes**: Like and unlike posts
- **Notifications**: Real-time notifications for mentions, comments, and likes
- **User Search**: Search for users by username or name
- **Profile Pictures**: Upload and manage user profile pictures
- **Advanced Search**: Search posts and comments with filtering and sorting options
- **WebSockets**: Real-time updates for notifications

## Base URL

All API endpoints are relative to the base URL:

```
http://localhost:8000/
```

For production, this would be your domain name.

## Authentication

The API uses JWT (JSON Web Token) authentication. To authenticate, you need to:

1. Register a user or login with existing credentials
2. Include the JWT token in the Authorization header of your requests:

```
Authorization: Bearer <your_access_token>
```

### Authentication Endpoints

#### Register a new user

**Endpoint:** `POST /api/auth/register/`

**Request Body:**
```json
{
  "username": "your_username",
  "email": "your_email@example.com",
  "password": "your_password",
  "password2": "your_password",
  "first_name": "Your",
  "last_name": "Name",
  "user_type": "student",
  "birthdate": "2000-01-01"
}
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "username": "your_username",
    "email": "your_email@example.com",
    "first_name": "Your",
    "last_name": "Name",
    "user_type": "student",
    "birthdate": "2000-01-01",
    "date_joined": "2023-06-01T12:00:00Z",
    "is_active": true
  },
  "refresh": "your_refresh_token",
  "access": "your_access_token",
  "message": "User registered successfully"
}
```

#### Login

**Endpoint:** `POST /api/auth/login/`

**Request Body:**
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "username": "your_username",
    "email": "your_email@example.com",
    "first_name": "Your",
    "last_name": "Name",
    "user_type": "student",
    "birthdate": "2000-01-01",
    "date_joined": "2023-06-01T12:00:00Z",
    "is_active": true
  },
  "refresh": "your_refresh_token",
  "access": "your_access_token",
  "message": "Login successful"
}
```

#### Refresh Token

**Endpoint:** `POST /api/auth/refresh/`

**Request Body:**
```json
{
  "refresh": "your_refresh_token"
}
```

**Response:**
```json
{
  "access": "your_new_access_token"
}
```

#### Get User Profile

**Endpoint:** `GET /api/auth/profile/`

**Headers:**
```
Authorization: Bearer your_access_token
```

**Response:**
```json
{
  "id": 1,
  "username": "your_username",
  "email": "your_email@example.com",
  "first_name": "Your",
  "last_name": "Name",
  "user_type": "student",
  "birthdate": "2000-01-01",
  "date_joined": "2023-06-01T12:00:00Z",
  "is_active": true
}
```

#### Update User Profile

**Endpoint:** `PUT /api/auth/profile/`

**Headers:**
```
Authorization: Bearer your_access_token
```

**Request Body:**
```json
{
  "email": "new_email@example.com",
  "first_name": "New",
  "last_name": "Name",
  "birthdate": "2000-01-01"
}
```

**Response:**
```json
{
  "id": 1,
  "username": "your_username",
  "email": "new_email@example.com",
  "first_name": "New",
  "last_name": "Name",
  "user_type": "student",
  "birthdate": "2000-01-01"
}
```

## Posts

### Post Endpoints

#### List Posts

**Endpoint:** `GET /api/posts/`

**Headers:**
```
Authorization: Bearer your_access_token
```

**Response:**
```json
[
  {
    "id": 1,
    "user": {
      "id": 1,
      "username": "your_username",
      "first_name": "Your",
      "last_name": "Name",
      "user_type": "student"
    },
    "content": "This is a post with @mention",
    "formatted_content": "This is a post with <a href=\"#\" class=\"mention\" data-username=\"mention\">@mention</a>",
    "image": "http://localhost:8000/media/posts/images/image.jpg",
    "video": null,
    "document": null,
    "created_at": "2023-06-01T12:00:00Z",
    "updated_at": "2023-06-01T12:00:00Z",
    "comments_count": 2,
    "likes_count": 5,
    "is_liked": true
  }
]
```

#### Create Post

**Endpoint:** `POST /api/posts/`

**Headers:**
```
Authorization: Bearer your_access_token
Content-Type: multipart/form-data
```

**Request Body:**
```
content: This is a new post with @mention
image: [file upload]
video: [file upload]
document: [file upload]
```

**Response:**
```json
{
  "id": 2,
  "user": {
    "id": 1,
    "username": "your_username",
    "first_name": "Your",
    "last_name": "Name",
    "user_type": "student"
  },
  "content": "This is a new post with @mention",
  "formatted_content": "This is a new post with <a href=\"#\" class=\"mention\" data-username=\"mention\">@mention</a>",
  "image": "http://localhost:8000/media/posts/images/image.jpg",
  "video": null,
  "document": null,
  "created_at": "2023-06-01T12:00:00Z",
  "updated_at": "2023-06-01T12:00:00Z",
  "comments_count": 0,
  "likes_count": 0,
  "is_liked": false
}
```

#### Get Post Detail

**Endpoint:** `GET /api/posts/{post_id}/`

**Headers:**
```
Authorization: Bearer your_access_token
```

**Response:**
```json
{
  "id": 1,
  "user": {
    "id": 1,
    "username": "your_username",
    "first_name": "Your",
    "last_name": "Name",
    "user_type": "student"
  },
  "content": "This is a post with @mention",
  "formatted_content": "This is a post with <a href=\"#\" class=\"mention\" data-username=\"mention\">@mention</a>",
  "image": "http://localhost:8000/media/posts/images/image.jpg",
  "video": null,
  "document": null,
  "created_at": "2023-06-01T12:00:00Z",
  "updated_at": "2023-06-01T12:00:00Z",
  "comments_count": 2,
  "likes_count": 5,
  "is_liked": true,
  "comments": [
    {
      "id": 1,
      "user": {
        "id": 2,
        "username": "another_user",
        "first_name": "Another",
        "last_name": "User",
        "user_type": "student"
      },
      "post": 1,
      "content": "This is a comment",
      "formatted_content": "This is a comment",
      "created_at": "2023-06-01T12:30:00Z"
    }
  ]
}
```

#### Update Post

**Endpoint:** `PUT /api/posts/{post_id}/`

**Headers:**
```
Authorization: Bearer your_access_token
Content-Type: multipart/form-data
```

**Request Body:**
```
content: Updated post content
```

**Response:**
```json
{
  "id": 1,
  "user": {
    "id": 1,
    "username": "your_username",
    "first_name": "Your",
    "last_name": "Name",
    "user_type": "student"
  },
  "content": "Updated post content",
  "formatted_content": "Updated post content",
  "image": "http://localhost:8000/media/posts/images/image.jpg",
  "video": null,
  "document": null,
  "created_at": "2023-06-01T12:00:00Z",
  "updated_at": "2023-06-01T13:00:00Z",
  "comments_count": 2,
  "likes_count": 5,
  "is_liked": true
}
```

#### Delete Post

**Endpoint:** `DELETE /api/posts/{post_id}/`

**Headers:**
```
Authorization: Bearer your_access_token
```

**Response:**
```
204 No Content
```

#### Like/Unlike Post

**Endpoint:** `POST /api/posts/{post_id}/like/`

**Headers:**
```
Authorization: Bearer your_access_token
```

**Response:**
```json
{
  "status": "success",
  "liked": true,
  "like_count": 6
}
```

#### Get Post Comments

**Endpoint:** `GET /api/posts/{post_id}/comments/`

**Headers:**
```
Authorization: Bearer your_access_token
```

**Response:**
```json
[
  {
    "id": 1,
    "user": {
      "id": 2,
      "username": "another_user",
      "first_name": "Another",
      "last_name": "User",
      "user_type": "student"
    },
    "post": 1,
    "content": "This is a comment",
    "formatted_content": "This is a comment",
    "created_at": "2023-06-01T12:30:00Z"
  }
]
```

#### Add Comment to Post

**Endpoint:** `POST /api/posts/{post_id}/comments/`

**Headers:**
```
Authorization: Bearer your_access_token
```

**Request Body:**
```json
{
  "content": "This is a new comment with @mention"
}
```

**Response:**
```json
{
  "id": 2,
  "user": {
    "id": 1,
    "username": "your_username",
    "first_name": "Your",
    "last_name": "Name",
    "user_type": "student"
  },
  "post": 1,
  "content": "This is a new comment with @mention",
  "formatted_content": "This is a new comment with <a href=\"#\" class=\"mention\" data-username=\"mention\">@mention</a>",
  "created_at": "2023-06-01T13:30:00Z"
}
```

## Comments

### Comment Endpoints

#### List Comments

**Endpoint:** `GET /api/comments/`

**Headers:**
```
Authorization: Bearer your_access_token
```

**Query Parameters:**
```
post_id: 1  # Optional, to filter comments by post
```

**Response:**
```json
[
  {
    "id": 1,
    "user": {
      "id": 2,
      "username": "another_user",
      "first_name": "Another",
      "last_name": "User",
      "user_type": "student"
    },
    "post": 1,
    "content": "This is a comment",
    "formatted_content": "This is a comment",
    "created_at": "2023-06-01T12:30:00Z"
  }
]
```

#### Create Comment

**Endpoint:** `POST /api/comments/`

**Headers:**
```
Authorization: Bearer your_access_token
```

**Request Body:**
```json
{
  "post": 1,
  "content": "This is a new comment with @mention"
}
```

**Response:**
```json
{
  "id": 2,
  "user": {
    "id": 1,
    "username": "your_username",
    "first_name": "Your",
    "last_name": "Name",
    "user_type": "student"
  },
  "post": 1,
  "content": "This is a new comment with @mention",
  "formatted_content": "This is a new comment with <a href=\"#\" class=\"mention\" data-username=\"mention\">@mention</a>",
  "created_at": "2023-06-01T13:30:00Z"
}
```

#### Get Comment Detail

**Endpoint:** `GET /api/comments/{comment_id}/`

**Headers:**
```
Authorization: Bearer your_access_token
```

**Response:**
```json
{
  "id": 1,
  "user": {
    "id": 2,
    "username": "another_user",
    "first_name": "Another",
    "last_name": "User",
    "user_type": "student"
  },
  "post": 1,
  "content": "This is a comment",
  "formatted_content": "This is a comment",
  "created_at": "2023-06-01T12:30:00Z"
}
```

#### Update Comment

**Endpoint:** `PUT /api/comments/{comment_id}/`

**Headers:**
```
Authorization: Bearer your_access_token
```

**Request Body:**
```json
{
  "content": "Updated comment content"
}
```

**Response:**
```json
{
  "id": 1,
  "user": {
    "id": 2,
    "username": "another_user",
    "first_name": "Another",
    "last_name": "User",
    "user_type": "student"
  },
  "post": 1,
  "content": "Updated comment content",
  "formatted_content": "Updated comment content",
  "created_at": "2023-06-01T12:30:00Z"
}
```

#### Delete Comment

**Endpoint:** `DELETE /api/comments/{comment_id}/`

**Headers:**
```
Authorization: Bearer your_access_token
```

**Response:**
```
204 No Content
```

## Notifications

### Notification Endpoints

#### List Notifications

**Endpoint:** `GET /api/notifications/`

**Headers:**
```
Authorization: Bearer your_access_token
```

**Response:**
```json
[
  {
    "id": 1,
    "recipient": {
      "id": 1,
      "username": "your_username",
      "first_name": "Your",
      "last_name": "Name",
      "user_type": "student"
    },
    "sender": {
      "id": 2,
      "username": "another_user",
      "first_name": "Another",
      "last_name": "User",
      "user_type": "student"
    },
    "notification_type": "mention",
    "text": "Another User mentioned you in a comment",
    "is_read": false,
    "created_at": "2023-06-01T12:30:00Z",
    "post": 1,
    "comment": 1
  }
]
```

#### Get Notification Detail

**Endpoint:** `GET /api/notifications/{notification_id}/`

**Headers:**
```
Authorization: Bearer your_access_token
```

**Response:**
```json
{
  "id": 1,
  "recipient": {
    "id": 1,
    "username": "your_username",
    "first_name": "Your",
    "last_name": "Name",
    "user_type": "student"
  },
  "sender": {
    "id": 2,
    "username": "another_user",
    "first_name": "Another",
    "last_name": "User",
    "user_type": "student"
  },
  "notification_type": "mention",
  "text": "Another User mentioned you in a comment",
  "is_read": false,
  "created_at": "2023-06-01T12:30:00Z",
  "post": 1,
  "comment": 1
}
```

#### Mark Notification as Read

**Endpoint:** `POST /api/notifications/{notification_id}/mark_read/`

**Headers:**
```
Authorization: Bearer your_access_token
```

**Response:**
```json
{
  "status": "success"
}
```

#### Mark All Notifications as Read

**Endpoint:** `POST /api/notifications/mark_all_read/`

**Headers:**
```
Authorization: Bearer your_access_token
```

**Response:**
```json
{
  "status": "success"
}
```

#### Get Unread Notification Count

**Endpoint:** `GET /api/notifications/unread_count/`

**Headers:**
```
Authorization: Bearer your_access_token
```

**Response:**
```json
{
  "status": "success",
  "unread_count": 5
}
```

## User Search

### User Search Endpoint

#### Search Users

**Endpoint:** `GET /api/users/search/`

**Headers:**
```
Authorization: Bearer your_access_token
```

**Query Parameters:**
```
q: search_query  # Optional, search term
```

**Response:**
```json
[
  {
    "id": 2,
    "username": "another_user",
    "first_name": "Another",
    "last_name": "User",
    "full_name": "Another User",
    "user_type": "student"
  }
]
```

## Error Responses

The API returns appropriate HTTP status codes and error messages:

- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error

Example error response:

```json
{
  "detail": "Authentication credentials were not provided."
}
```

Or for validation errors:

```json
{
  "username": [
    "A user with that username already exists."
  ],
  "password": [
    "This password is too common."
  ]
}
```

## Testing the API

You can test the API using tools like:

1. **Postman**: Import the provided collection to test all endpoints
2. **cURL**: Use command-line requests
3. **Python**: Use the provided `test_api.py` script

Example using the test script:

```bash
python test_api.py
```

## Flutter Integration

To integrate with a Flutter app:

1. Use the `http` or `dio` package to make API requests
2. Store JWT tokens securely using `flutter_secure_storage`
3. Create models that match the API response structure
4. Implement authentication flow with login/register screens
5. Create repositories for each resource type (posts, comments, etc.)

Example Flutter code for login:

```dart
Future<User> login(String username, String password) async {
  final response = await http.post(
    Uri.parse('$baseUrl/api/auth/login/'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'username': username,
      'password': password,
    }),
  );

  if (response.statusCode == 200) {
    final data = jsonDecode(response.body);
    // Save tokens
    await secureStorage.write(key: 'access_token', value: data['access']);
    await secureStorage.write(key: 'refresh_token', value: data['refresh']);

    // Return user data
    return User.fromJson(data['user']);
  } else {
    throw Exception('Failed to login');
  }
}
```

## Profile Picture Upload

### Upload Profile Picture

**Endpoint:** `POST /api/auth/profile/upload-picture/`

**Headers:**
```
Authorization: Bearer your_access_token
Content-Type: multipart/form-data
```

**Request Body:**
```
profile_picture: [file upload]
```

**Response:**
```json
{
  "message": "Profile picture uploaded successfully",
  "profile_picture": "http://localhost:8000/media/profile_pictures/profile_1_123456.jpg"
}
```

## Advanced Search

### Search Posts

**Endpoint:** `GET /api/posts/search/`

**Headers:**
```
Authorization: Bearer your_access_token
```

**Query Parameters:**
```
q: Search term for content
user: Username to filter by
date_from: Start date (YYYY-MM-DD)
date_to: End date (YYYY-MM-DD)
has_media: true/false
min_likes: Minimum number of likes
min_comments: Minimum number of comments
sort_by: created_at, likes, comments
order: asc, desc
```

**Response:**
```json
{
  "count": 10,
  "next": "http://localhost:8000/api/posts/search/?page=2&q=example",
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": {
        "id": 1,
        "username": "your_username",
        "first_name": "Your",
        "last_name": "Name",
        "user_type": "student"
      },
      "content": "This is a post with example content",
      "formatted_content": "This is a post with example content",
      "image": "http://localhost:8000/media/posts/images/image.jpg",
      "video": null,
      "document": null,
      "created_at": "2023-06-01T12:00:00Z",
      "updated_at": "2023-06-01T12:00:00Z",
      "comments_count": 2,
      "likes_count": 5,
      "is_liked": true
    }
  ]
}
```

## Filtering and Sorting

All list endpoints now support filtering and sorting:

### Posts

**Endpoint:** `GET /api/posts/`

**Query Parameters:**
```
search: Search term
user_id: Filter by user ID
start_date: Filter by start date (YYYY-MM-DD)
end_date: Filter by end date (YYYY-MM-DD)
has_image: true/false
has_video: true/false
has_document: true/false
ordering: created_at, -created_at, likes__count, -likes__count, comments__count, -comments__count
```

### Comments

**Endpoint:** `GET /api/comments/`

**Query Parameters:**
```
search: Search term
post_id: Filter by post ID
user_id: Filter by user ID
start_date: Filter by start date (YYYY-MM-DD)
end_date: Filter by end date (YYYY-MM-DD)
ordering: created_at, -created_at
```

### Notifications

**Endpoint:** `GET /api/notifications/`

**Query Parameters:**
```
search: Search term
is_read: true/false
type: mention, comment, like
start_date: Filter by start date (YYYY-MM-DD)
end_date: Filter by end date (YYYY-MM-DD)
ordering: created_at, -created_at, is_read, -is_read
```

## WebSockets

The API now supports real-time notifications using WebSockets.

### WebSocket Connection

**WebSocket URL:** `ws://localhost:8000/ws/notifications/{user_id}/`

**Connection Example (JavaScript):**
```javascript
const socket = new WebSocket(`ws://localhost:8000/ws/notifications/${userId}/`);

socket.addEventListener('open', function(event) {
    console.log('WebSocket connection established');
});

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
```

### WebSocket Messages

#### Notification Message

```json
{
  "type": "notification",
  "notification": {
    "id": 1,
    "recipient": "your_username",
    "sender": "another_user",
    "notification_type": "mention",
    "text": "Another User mentioned you in a comment",
    "is_read": false,
    "created_at": "2023-06-01T12:30:00Z",
    "post_id": 1,
    "comment_id": 1
  }
}
```

#### Unread Count Message

```json
{
  "type": "unread_count",
  "count": 5
}
```

### WebSocket Commands

#### Mark Notification as Read

```json
{
  "type": "mark_read",
  "notification_id": 1
}
```

#### Mark All Notifications as Read

```json
{
  "type": "mark_all_read"
}
```
