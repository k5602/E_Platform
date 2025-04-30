import logging
from django.db.utils import DatabaseError, ProgrammingError, OperationalError
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib import messages

logger = logging.getLogger(__name__)

class DatabaseErrorMiddleware:
    """
    Middleware to catch database errors and display a friendly error page.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        return self.get_response(request)
    
    def process_exception(self, request, exception):
        if isinstance(exception, (DatabaseError, ProgrammingError, OperationalError)):
            # Log the error
            logger.error(f"Database error: {str(exception)}")
            
            # Add a message for the user
            messages.error(request, f"A database error occurred: {str(exception)}")
            
            # Render a friendly error page
            context = {
                'error': str(exception),
                'error_type': 'Database Error',
                'active_page': request.path.split('/')[1] if len(request.path.split('/')) > 1 else 'home'
            }
            
            html = render_to_string('home/error.html', context, request)
            return HttpResponse(html, status=500)
        
        return None
