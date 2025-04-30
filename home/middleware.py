import logging
import traceback
import sys
from django.db.utils import DatabaseError, ProgrammingError, OperationalError, IntegrityError
from django.http import HttpResponse, Http404
from django.template.loader import render_to_string
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist, ValidationError
from django.conf import settings

logger = logging.getLogger(__name__)

class GlobalErrorMiddleware:
    """
    Middleware to catch various types of errors and display friendly error pages.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        # Get the active page for navigation highlighting
        active_page = request.path.split('/')[1] if len(request.path.split('/')) > 1 else 'home'

        # Database errors
        if isinstance(exception, (DatabaseError, ProgrammingError, OperationalError, IntegrityError)):
            error_type = 'Database Error'
            status_code = 500

            # Log the error with traceback
            logger.error(f"{error_type}: {str(exception)}\n{traceback.format_exc()}")

            # Add a message for the user
            messages.error(request, f"A database error occurred. Our team has been notified.")

            # More user-friendly message for production
            user_message = str(exception) if settings.DEBUG else "There was a problem with our database. Please try again later."

        # Permission errors
        elif isinstance(exception, PermissionDenied):
            error_type = 'Permission Denied'
            status_code = 403

            logger.warning(f"Permission denied: {request.path} - User: {request.user}")
            messages.warning(request, "You don't have permission to access this resource.")

            user_message = "You don't have permission to access this page. If you believe this is an error, please contact support."

        # Not found errors
        elif isinstance(exception, (Http404, ObjectDoesNotExist)):
            error_type = 'Not Found'
            status_code = 404

            logger.info(f"Not found: {request.path} - User: {request.user}")

            user_message = "The requested resource could not be found. It may have been moved or deleted."

        # Validation errors
        elif isinstance(exception, ValidationError):
            error_type = 'Validation Error'
            status_code = 400

            logger.warning(f"Validation error: {str(exception)}")
            messages.error(request, f"There was a problem with your input: {str(exception)}")

            user_message = f"There was a problem with your input: {str(exception)}"

        # Other exceptions
        else:
            error_type = 'Server Error'
            status_code = 500

            # Log the full traceback for unknown errors
            logger.error(f"Unhandled exception: {str(exception)}\n{traceback.format_exc()}")

            # Add a message for the user
            messages.error(request, "An unexpected error occurred. Our team has been notified.")

            # More user-friendly message for production
            user_message = str(exception) if settings.DEBUG else "An unexpected error occurred. Please try again later."

        # Render the error page
        context = {
            'error': user_message,
            'error_type': error_type,
            'active_page': active_page,
            'status_code': status_code,
            'debug': settings.DEBUG,
            'traceback': traceback.format_exc() if settings.DEBUG else None
        }

        html = render_to_string('home/error.html', context, request)
        return HttpResponse(html, status=status_code)


class DatabaseErrorMiddleware(GlobalErrorMiddleware):
    """
    Legacy middleware name for backward compatibility.
    """
    pass
