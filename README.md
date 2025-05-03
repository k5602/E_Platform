# E-Platform: AI-Augmented Educational Platform

A comprehensive Django-based educational platform with AI augmentation, designed to provide a modern learning experience with social features, real-time interactions, and content sharing capabilities.

## Project Overview

E-Platform is a prototype educational platform built with Django that integrates traditional learning management system (LMS) features with modern social networking capabilities and AI augmentation. The platform is designed to facilitate learning, collaboration, and knowledge sharing among students and instructors in an interactive environment.

## Core Architecture

### Technology Stack

- **Backend**: Django 5.x (Python web framework)
- **Database**: PostgreSQL (Relational database)
- **Frontend**: HTML, CSS, JavaScript with responsive design
- **API**: Django REST Framework for RESTful API endpoints
- **Real-time Communication**: Django Channels with WebSockets
- **Authentication**: Custom user model with JWT authentication
- **AI Integration**: Prototype AI module for future enhancements

### System Components

1. **Authentication System**
   - Custom user model extending Django's AbstractUser
   - User types: Student, Instructor, Administrator
   - Secure login/signup with form validation
   - JWT-based authentication for API access

2. **Core Applications**
   - `authentication`: User management and authentication
   - `home`: Main platform interface and social feed
   - `chatting`: Real-time messaging system with WebSockets
   - `Ai_prototype`: Foundation for AI integration (in development)


3. **Database Design**
   - Relational PostgreSQL database
   - Custom models for users, posts, comments, subjects, quizzes, etc.
   - Optimized queries and relationships

4. **API Architecture**
   - RESTful API design with Django REST Framework
   - JWT authentication for secure access
   - Comprehensive endpoints for all platform features
   - Mobile app integration support (Flutter)

5. **WebSocket Implementation**
   - Real-time notifications system
   - Asynchronous communication via Django Channels
   - In-memory channel layer for development (Redis for production)

## Key Features

### User Management & Authentication

- **Custom User Model**: Extended Django's AbstractUser with additional fields:
  - User type (student, instructor, admin)
  - Profile picture
  - Birthdate
- **Authentication Forms**: Custom forms with enhanced validation
- **JWT Authentication**: Secure API access with token-based authentication

### Social Learning Environment

- **Post System**: Create, read, update, and delete posts with:
  - Text content with @mentions
  - Media attachments (images, videos, documents)
  - Like and comment functionality
- **Notification System**: Real-time notifications for:
  - Mentions in posts/comments
  - Likes and comments on posts
  - Subject enrollments and quiz completions

### Educational Features

- **Subject Management**:
  - Subject creation and enrollment
  - Material organization and sharing
  - Instructor-student interaction

- **Quiz System**:
  - Comprehensive quiz creation and management
  - Multiple question types (multiple choice, true/false, short answer)
  - Automated scoring and feedback
  - Time limits and randomization options

- **User Profiles**:
  - Detailed educational profiles
  - Skills, experience, and certification tracking
  - Privacy controls for profile information

### UI/UX Features

- **Responsive Design**: Mobile-first approach with breakpoints
- **Dark/Light Mode**: Theme toggle with localStorage persistence
- **Toast Notifications**: Non-intrusive user feedback
- **Modern Input Styling**: Consistent design language
- **Real-time Updates**: Dynamic content without page reloads

### Real-time Communication

- **WebSocket Integration**: Real-time updates using Django Channels
- **Notification Center**: Centralized notification management
- **Unread Counts**: Visual indicators for unread notifications
- **Instant Feedback**: Immediate UI updates for user actions

## AI Augmentation (Prototype)

The platform includes an `Ai_prototype` app that serves as the foundation for future AI integration. While currently in early development, the planned AI features include:

### Planned AI Features

1. **Intelligent Content Recommendations**:
   - Personalized learning materials based on user behavior
   - Subject recommendations based on user profile and interests
   - Smart content discovery

2. **Automated Assessment**:
   - AI-powered grading for short answer questions
   - Plagiarism detection in submissions
   - Performance analysis and improvement suggestions

3. **Learning Assistant**:
   - AI chatbot for answering student questions
   - Contextual help based on current subject matter
   - Study schedule optimization

4. **Engagement Analysis**:
   - User engagement metrics and patterns
   - Predictive analytics for student success
   - Early intervention for at-risk students

5. **Content Enhancement**:
   - Automatic summarization of learning materials
   - Key concept extraction from educational content
   - Multimedia content generation aids

## Technical Implementation Details

### Database Schema

The platform uses a relational database with the following key models:

- **User-related**: CustomUser, UserProfile, Education, Experience, Skills, etc.
- **Content-related**: Post, Comment, Like, Subject, SubjectMaterial
- **Educational**: Quiz, Question, Answer, UserAttempt, UserAnswer
- **Communication**: Notification, Contact, Appointment

### API Endpoints

The platform provides a comprehensive REST API with endpoints for:

- User authentication and profile management
- Post creation, retrieval, and interaction
- Subject enrollment and material access
- Quiz taking and result retrieval
- Notification management
- Search functionality

### WebSocket Implementation

Real-time features are implemented using Django Channels:

- Notification delivery via WebSockets
- Connection management with authentication
- Group-based message distribution
- Error handling and reconnection logic

### Security Measures

- JWT authentication with token refresh
- CORS configuration for API access
- Password validation and secure storage
- Permission-based access control
- CSRF protection for web forms
- HTTPS configuration with secure cookies
- HTTP Strict Transport Security (HSTS)
- Protection against XSS and content type sniffing
- Clickjacking prevention with X-Frame-Options

## Development & Deployment

### Development Environment

- Python 3.10+ with virtual environment
- PostgreSQL database
- Required dependencies in requirements.txt
- Development server with Django's runserver

### SSL/HTTPS Configuration

The application includes security settings for both development and production environments:

#### Development Mode (DEBUG = True)

In development mode, HTTPS-related security settings are automatically disabled to allow the application to run without
SSL:

- `SECURE_SSL_REDIRECT = False` - HTTP requests are not redirected to HTTPS
- `SESSION_COOKIE_SECURE = False` - Cookies can be sent over HTTP
- `CSRF_COOKIE_SECURE = False` - CSRF cookies can be sent over HTTP
- HSTS settings are disabled

This configuration allows you to run the application locally without SSL certificates.

#### Production Mode (DEBUG = False)

In production, all security settings are enabled by default:

- `SECURE_SSL_REDIRECT = True` - All HTTP requests are redirected to HTTPS
- `SESSION_COOKIE_SECURE = True` - Cookies are only sent over HTTPS
- `CSRF_COOKIE_SECURE = True` - CSRF cookies are only sent over HTTPS
- `SECURE_HSTS_SECONDS = 31536000` - HSTS is enabled for 1 year
- `SECURE_HSTS_INCLUDE_SUBDOMAINS = True` - HSTS applies to subdomains
- `SECURE_HSTS_PRELOAD = True` - HSTS preloading is enabled

For production deployment, you must configure your web server (e.g., Nginx) with valid SSL certificates. Without proper
SSL configuration, the application will show "connection secure failed" errors in browsers.

### Testing

- Unit tests for models, views, and API endpoints
- Integration tests for key workflows
- Manual testing for UI/UX features

### Deployment Considerations

- Production settings with environment variables
- Static and media file serving configuration
- Database optimization and indexing
- Web server (Gunicorn) with reverse proxy (Nginx)
- Redis for production WebSocket channel layer
- SSL certificate configuration:
    - Obtain valid SSL certificates (e.g., Let's Encrypt)
    - Configure Nginx to serve HTTPS traffic
    - Set up proper SSL certificate renewal
    - Ensure all security headers are properly set

## Future Roadmap

1. **Enhanced AI Integration**:
   - Complete implementation of AI features
   - Integration with external AI services
   - Machine learning models for personalized learning

2. **Advanced Analytics**:
   - Comprehensive learning analytics dashboard
   - Performance tracking and visualization
   - Predictive modeling for student outcomes

3. **Mobile Application**:
   - Flutter-based mobile app development
   - Offline functionality
   - Push notifications

4. **Collaborative Features**:
   - Real-time collaborative document editing
   - Group projects and team management
   - Peer review and assessment

5. **Content Marketplace**:
   - Instructor content publishing
   - Monetization options
   - Quality rating system

## Conclusion

E-Platform represents a modern approach to educational technology, combining traditional learning management features with social networking capabilities and AI augmentation. The prototype demonstrates the potential for creating engaging, interactive learning environments that leverage cutting-edge technologies to enhance the educational experience.

The platform's modular architecture allows for continuous improvement and feature expansion, with a particular focus on AI integration to provide increasingly personalized and effective learning experiences.

## Installation & Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd E_Platform
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**

   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

5. **Database Setup**

   The application can work with either PostgreSQL or SQLite. By default, it uses PostgreSQL.

   **Option 1: Use PostgreSQL (default)**
6.
```bash
sudo -u postgres psql
```
   - Ensure PostgreSQL is installed and running
   - Create a PostgreSQL database named `e_platform_db`
   - Create a user with username `zero` and password `82821931003`
   - Grant all privileges on the database to the user

   ```sql
   CREATE DATABASE e_platform_db;
   CREATE USER zero WITH PASSWORD '82821931003';
   GRANT ALL PRIVILEGES ON DATABASE e_platform_db TO zero;
   ```

    - Use the provided script to run the application with PostgreSQL:

   ```bash
   ./run_with_postgresql.sh
   ```

   - Alternatively, you can set the environment variables manually:

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

   **Option 2: Use SQLite**

   To use SQLite instead of PostgreSQL, set the DB_ENGINE environment variable to 'sqlite3':

   ```bash
   export DB_ENGINE=sqlite3
   python manage.py migrate
   python manage.py runserver
   ```

   No additional setup is required for SQLite.

6. **Initialize migrations**

   ```bash
   python initialize_migrations.py
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Create a superuser (admin)**

   ```bash
   python manage.py createsuperuser
   ```

8. **Run the development server**

   ```bash
   python manage.py runserver
   ```

9. **Access the application**

   Open your browser and navigate to `http://127.0.0.1:8000/`

   Note: The application automatically disables HTTPS requirements in development mode (when DEBUG=True), allowing you
   to access it via HTTP without SSL certificates.

## License

[MIT License](LICENSE)

## Credits

Developed as an educational platform prototype with AI augmentation capabilities.
