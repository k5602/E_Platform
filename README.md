# E-Platform

A Django-based educational platform with user authentication, social features, and content sharing capabilities.

## Features

- **User Authentication System**
  - Custom user model with different user types (student, instructor, admin)
  - Login, signup, and logout functionality
  - Form validation and password visibility toggle

- **Home Feed**
  - Post creation with text content
  - Media upload support (images, videos, documents)
  - Like and comment functionality
  - Read more/less for long posts

- **UI/UX Features**
  - Responsive design for mobile and desktop
  - Dark/light mode toggle
  - Toast notifications
  - Modern input styling with focus states

## Prerequisites

- Python 3.10 or higher
- PostgreSQL 14 or higher
- pip (Python package manager)

## Installation

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

5. **Set up PostgreSQL database**

   - Create a PostgreSQL database named `e_platform_db`
   - Create a user with username `zero` and password `82821931003`
   - Grant all privileges on the database to the user

   ```sql
   CREATE DATABASE e_platform_db;
   CREATE USER zero WITH PASSWORD '82821931003';
   GRANT ALL PRIVILEGES ON DATABASE e_platform_db TO zero;
   ```

6. **Apply migrations**

   ```bash
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

## Project Structure

```
E_Platform/
├── E_Platform/              # Main project settings
├── authentication/          # User authentication app
├── home/                    # Home feed app
├── static/                  # Global static files
├── media/                   # User uploaded files
├── templates/               # Global templates
├── manage.py                # Django management script
├── requirements.txt         # Project dependencies
└── README.md                # Project documentation
```

## Setup & Development

1. Clone this repository to your device.
2. Ensure Python 3.10+ and pip are installed.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up PostgreSQL and create a database/user.
5. Configure your database settings in `E_Platform/settings.py`.
6. Run migrations:
   ```bash
   python manage.py migrate
   ```
7. (Optional) Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```
8. Collect static files:
   ```bash
   python manage.py collectstatic
   ```
9. Run the development server:
   ```bash
   python manage.py runserver
   ```
10. Access the app at http://localhost:8000

## Testing
- Run all tests:
  ```bash
  python manage.py test
  ```
- Ensure `media/` and `static/` folders are writable.
- For file uploads, check that `media/` is properly configured in settings.

## Notes
- For production, configure environment variables and secure static/media file serving.
- Add any extra dependencies you use to `requirements.txt`.

## Development

### Running Tests

```bash
python manage.py test
```

### Creating New Apps

```bash
python manage.py startapp app_name
```

Don't forget to add the new app to `INSTALLED_APPS` in `settings.py`.

## Deployment

For production deployment:

1. Set `DEBUG = False` in settings.py
2. Configure a proper secret key
3. Set up proper database credentials
4. Configure static files serving
5. Set up a production web server (Gunicorn, uWSGI)
6. Configure a reverse proxy (Nginx, Apache)

## License

[MIT License](LICENSE)

## Credits

Developed as an educational platform project.
