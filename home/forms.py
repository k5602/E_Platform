from django import forms
from django.core.validators import FileExtensionValidator
from .models import Post, Comment, Contact, Appointment
import datetime

class PostForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'add-post',
            'placeholder': 'What is in your mind?',
            'rows': 3,
            'maxlength': 500,
            'data-counter': 'char-counter'
        }),
        required=True,
        max_length=500,
        error_messages={
            'required': 'Please enter some content for your post.',
            'max_length': 'Your post cannot exceed 500 characters.'
        }
    )

    image = forms.ImageField(
        widget=forms.FileInput(attrs={
            'class': 'add-img',
            'id': 'add-img',
            'accept': 'image/*',
            'data-max-size': '5242880'  # 5MB in bytes
        }),
        required=False,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'],
                message='Please upload a valid image file (jpg, jpeg, png, gif, webp).'
            )
        ],
        error_messages={
            'invalid_image': 'The uploaded file is not a valid image.',
            'invalid_extension': 'This file type is not supported. Please use jpg, jpeg, png, gif, or webp.'
        }
    )

    video = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'add-video',
            'id': 'add-video',
            'accept': 'video/*',
            'data-max-size': '20971520'  # 20MB in bytes
        }),
        required=False,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['mp4', 'webm', 'ogg', 'mov'],
                message='Please upload a valid video file (mp4, webm, ogg, mov).'
            )
        ],
        error_messages={
            'invalid_extension': 'This file type is not supported. Please use mp4, webm, ogg, or mov.'
        }
    )

    document = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'add-document',
            'id': 'add-document',
            'accept': '.pdf,.md,.docx,.xlsx,.tex,.pptx',
            'data-max-size': '10485760'  # 10MB in bytes
        }),
        required=False,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'md', 'docx', 'xlsx', 'tex', 'pptx'],
                message='Please upload a valid document file (PDF, Markdown, Word, Excel, LaTeX, PowerPoint).'
            )
        ],
        error_messages={
            'invalid_extension': 'This file type is not supported. Please use PDF, Markdown, Word, Excel, LaTeX, or PowerPoint.'
        }
    )

    class Meta:
        model = Post
        fields = ['content', 'image', 'video', 'document']

    def clean(self):
        cleaned_data = super().clean()
        image = cleaned_data.get('image')
        video = cleaned_data.get('video')
        document = cleaned_data.get('document')

        # Check if multiple media types are provided
        media_count = sum(1 for media in [image, video, document] if media)
        if media_count > 1:
            raise forms.ValidationError(
                "Please upload only one type of media (image, video, or document)."
            )

        # Check file sizes
        if image and image.size > 5 * 1024 * 1024:  # 5MB
            self.add_error('image', 'Image file size should not exceed 5MB.')

        if video and video.size > 20 * 1024 * 1024:  # 20MB
            self.add_error('video', 'Video file size should not exceed 20MB.')

        if document and document.size > 10 * 1024 * 1024:  # 10MB
            self.add_error('document', 'Document file size should not exceed 10MB.')

        return cleaned_data

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={
                'class': 'comment-input',
                'placeholder': 'Write a comment...'
            })
        }

class ContactForm(forms.ModelForm):
    name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Name',
            'required': True,
        }),
        max_length=100,
        help_text='Enter your full name',
        error_messages={
            'required': 'Please enter your name.',
            'max_length': 'Name cannot exceed 100 characters.'
        }
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Email',
            'required': True,
        }),
        help_text='Enter your email address',
        error_messages={
            'required': 'Please enter your email address.',
            'invalid': 'Please enter a valid email address.'
        }
    )
    
    subject = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Subject',
            'required': True,
        }),
        max_length=200,
        help_text='Subject of your message',
        error_messages={
            'required': 'Please enter a subject.',
            'max_length': 'Subject cannot exceed 200 characters.'
        }
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Your Message',
            'rows': 6,
            'required': True,
        }),
        help_text='Enter your message',
        error_messages={
            'required': 'Please enter your message.'
        }
    )
    
    class Meta:
        model = Contact
        fields = ['name', 'email', 'subject', 'message']

class AppointmentForm(forms.ModelForm):
    """Form for scheduling appointments with instructors."""
    
    appointment_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date', 
            'class': 'form-control',
            'min': datetime.date.today().strftime('%Y-%m-%d')
        }),
        help_text="Select a date for your appointment"
    )
    
    appointment_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control',
            'min': '09:00',
            'max': '17:00'
        }),
        help_text="Select a time between 9:00 AM and 5:00 PM"
    )
    
    class Meta:
        model = Appointment
        fields = ['name', 'email', 'phone', 'appointment_date', 'appointment_time', 'appointment_type', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your full name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your email address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your phone number (optional)'}),
            'appointment_type': forms.Select(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Describe the purpose of your appointment', 'rows': 4}),
        }
    
    def clean_appointment_date(self):
        """Validate that appointment date is not in the past or on weekends."""
        date = self.cleaned_data.get('appointment_date')
        
        # Check if date is in the past
        if date < datetime.date.today():
            raise forms.ValidationError("Appointment date cannot be in the past.")
        
        # Check if date is on a weekend
        if date.weekday() >= 5:  # 5: Saturday, 6: Sunday
            raise forms.ValidationError("Appointments are not available on weekends.")
            
        return date
    
    def clean_appointment_time(self):
        """Validate that appointment time is during working hours."""
        time = self.cleaned_data.get('appointment_time')
        
        # Define working hours (9 AM to 5 PM)
        start_time = datetime.time(9, 0)
        end_time = datetime.time(17, 0)
        
        if time < start_time or time > end_time:
            raise forms.ValidationError("Appointments are only available between 9:00 AM and 5:00 PM.")
            
        return time
    
    def clean(self):
        """Validate the appointment date and time combination."""
        cleaned_data = super().clean()
        date = cleaned_data.get('appointment_date')
        time = cleaned_data.get('appointment_time')
        
        # Skip further validation if either field had errors
        if not date or not time:
            return cleaned_data
            
        # Check if appointment date is today and time is in the past
        if date == datetime.date.today():
            current_time = datetime.datetime.now().time()
            if time < current_time:
                self.add_error('appointment_time', "Appointment time cannot be in the past.")
                
        return cleaned_data
