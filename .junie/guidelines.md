# E-Platform Development Guidelines

This document provides essential information for developers working on the E-Platform project.

## Build/Configuration Instructions

### Environment Setup

1. **Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Database Configuration**

   The application supports both PostgreSQL (default) and SQLite:

   **PostgreSQL Setup**:
   ```bash
   # Create database and user
   CREATE DATABASE e_platform_db;
   CREATE USER zero WITH PASSWORD '82821931003';
   GRANT ALL PRIVILEGES ON DATABASE e_platform_db TO zero;
   ```

   **Run with PostgreSQL**:
   ```bash
   ./run_with_postgresql.sh
   ```

   Or set environment variables manually:
   ```bash
   export DB_ENGINE=postgresql
   export DB_NAME=e_platform_db
   export DB_USER=zero
   export DB_PASSWORD=82821931003
   export DB_HOST=localhost
   export DB_PORT=5432
   python manage.py migrate
   python manage.py runserver
   ```

   **SQLite (Alternative)**:
   ```bash
   export DB_ENGINE=sqlite3
   python manage.py migrate
   python manage.py runserver
   ```

3. **WebSocket Configuration**

   The project uses Django Channels for WebSockets:
    - Development: In-memory channel layer (default)
    - Production: Redis channel layer (recommended)

   To configure Redis for production:
   ```python
   # In settings.py
   CHANNEL_LAYERS = {
       'default': {
           'BACKEND': 'channels_redis.core.RedisChannelLayer',
           'CONFIG': {
               'hosts': [('127.0.0.1', 6379)],
           },
       },
   }
   ```

## Testing Information

### Running Tests

1. **Run All Tests**
   ```bash
   python manage.py test
   ```

2. **Run Tests for a Specific App**
   ```bash
   python manage.py test home
   ```

3. **Run a Specific Test Class**
   ```bash
   python manage.py test home.tests.PostModelTest
   ```

4. **Run a Specific Test Method**
   ```bash
   python manage.py test home.tests.PostModelTest.test_post_creation
   ```

### Writing Tests

The project follows Django's standard testing practices:

1. **Model Tests**

   Example of a model test:
   ```python
   from django.test import TestCase
   from django.contrib.auth import get_user_model
   from home.models import Post

   class PostModelTest(TestCase):
       def setUp(self):
           User = get_user_model()
           self.user = User.objects.create_user(
               username='testuser',
               email='test@example.com',
               password='testpassword123'
           )
           self.post = Post.objects.create(
               user=self.user,
               content='This is a test post'
           )

       def test_post_creation(self):
           self.assertEqual(self.post.content, 'This is a test post')
           self.assertEqual(self.post.user, self.user)
   ```

2. **View Tests**

   For view tests, use Django's test client:
   ```python
   from django.test import TestCase
   from django.urls import reverse
   from django.contrib.auth import get_user_model

   class HomeViewTest(TestCase):
       def setUp(self):
           User = get_user_model()
           self.user = User.objects.create_user(
               username='testuser',
               email='test@example.com',
               password='testpassword123'
           )
           self.client.login(username='testuser', password='testpassword123')

       def test_home_view_status_code(self):
           response = self.client.get(reverse('home'))
           self.assertEqual(response.status_code, 200)
   ```

3. **API Tests**

   For API tests, use Django REST Framework's APIClient:
   ```python
   from rest_framework.test import APITestCase
   from django.urls import reverse
   from django.contrib.auth import get_user_model

   class PostAPITest(APITestCase):
       def setUp(self):
           User = get_user_model()
           self.user = User.objects.create_user(
               username='testuser',
               email='test@example.com',
               password='testpassword123'
           )
           self.client.force_authenticate(user=self.user)

       def test_create_post(self):
           url = reverse('api:post-list')
           data = {'content': 'Test post content'}
           response = self.client.post(url, data, format='json')
           self.assertEqual(response.status_code, 201)
   ```

### Test Database

Tests use an isolated SQLite database by default, even if PostgreSQL is configured for development. This ensures tests
run quickly and don't affect your development database.

## Development Guidelines

### Project Structure

The project follows a standard Django structure with the following apps:

- **authentication**: User management and authentication
- **home**: Main platform interface and social feed
- **chatting**: Real-time messaging system with WebSockets
- **Ai_prototype**: Foundation for AI integration (in development)

### Code Style

1. **Python Style**
    - Follow PEP 8 guidelines
    - Use docstrings for classes and methods
    - Use meaningful variable and function names

2. **Django Best Practices**
    - Use Django's ORM for database operations
    - Keep views focused on a single responsibility
    - Use Django forms for input validation
    - Use Django's built-in security features

3. **Model Relationships**
    - Use appropriate relationship types (ForeignKey, ManyToMany)
    - Define related_name for reverse relationships
    - Use on_delete appropriately (CASCADE, SET_NULL, etc.)

### WebSocket Development

When working with WebSockets:

1. Create a consumer class in a `consumers.py` file
2. Define routing in a `routing.py` file
3. Register the routing in the project's `asgi.py`

Example consumer:

```python
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive_json(self, content):
        # Handle received message
        pass
```

### Error Handling

The project uses a custom middleware for global error handling:

- `home.middleware.GlobalErrorMiddleware`

When adding new functionality, ensure proper error handling and logging.

### Logging

The project has comprehensive logging configuration:

- Different log levels (DEBUG, INFO, ERROR)
- File and console handlers
- App-specific loggers

Use the logging system for debugging and monitoring:

```python
import logging

logger = logging.getLogger(__name__)
logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message")
```