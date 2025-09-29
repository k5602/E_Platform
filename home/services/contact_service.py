from home.models import FAQ
from home.forms import ContactForm, AppointmentForm
from authentication.models import CustomUser
import logging

logger = logging.getLogger(__name__)


class ContactService:
    """Service class for contact and appointment business logic."""

    @staticmethod
    def handle_contact_form_submission(form_data):
        """Handle contact form submission."""
        form = ContactForm(form_data)
        if form.is_valid():
            form.save()
            return {
                "success": True,
                "message": "Thank you! Your message has been sent successfully.",
            }
        else:
            return {"success": False, "form": form}

    @staticmethod
    def handle_appointment_form_submission(form_data, user=None):
        """Handle appointment form submission."""
        form = AppointmentForm(form_data)
        if form.is_valid():
            appointment = form.save(commit=False)

            # If user is logged in, associate the appointment with them
            if user and user.is_authenticated:
                appointment.user = user

            # Find the first instructor
            instructors = CustomUser.objects.filter(is_staff=True).first()
            if instructors:
                appointment.instructor = instructors

            appointment.save()
            return {
                "success": True,
                "message": "Thank you! Your appointment request has been submitted. We'll confirm it shortly.",
            }
        else:
            return {"success": False, "form": form}

    @staticmethod
    def get_contact_page_data():
        """Get data needed for the contact page."""
        # Get active FAQs and their unique categories
        faqs = FAQ.objects.filter(is_active=True).order_by("order", "question")
        categories = faqs.values_list("category", flat=True).distinct()

        # Get available instructors for appointment booking
        instructors = CustomUser.objects.filter(is_staff=True)

        return {"faqs": faqs, "categories": categories, "instructors": instructors}
