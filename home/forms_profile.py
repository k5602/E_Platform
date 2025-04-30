from django import forms
from django.utils.translation import gettext_lazy as _
from authentication.models import CustomUser
from .models_profile import ProfileUserProfile, ProfileEducation, ProfileExperience, ProfileSkill, ProfileProject, ProfileCertification


class ProfileForm(forms.ModelForm):
    """Form for editing basic profile information."""
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'input'})
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'input'})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'input'})
    )
    birthdate = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'input', 'type': 'date'})
    )

    class Meta:
        model = ProfileUserProfile
        fields = ['bio', 'location', 'website']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'input', 'rows': 4}),
            'location': forms.TextInput(attrs={'class': 'input'}),
            'website': forms.URLInput(attrs={'class': 'input'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email
            self.fields['birthdate'].initial = self.user.birthdate

    def save(self, commit=True):
        profile = super().save(commit=False)

        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.email = self.cleaned_data['email']
            self.user.birthdate = self.cleaned_data['birthdate']

            if commit:
                self.user.save()
                profile.user = self.user
                profile.save()

        return profile


class SocialLinksForm(forms.Form):
    """Form for editing social media links."""
    linkedin = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'input', 'placeholder': 'LinkedIn URL'})
    )
    github = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'input', 'placeholder': 'GitHub URL'})
    )
    twitter = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'input', 'placeholder': 'Twitter URL'})
    )
    facebook = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'input', 'placeholder': 'Facebook URL'})
    )
    instagram = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'input', 'placeholder': 'Instagram URL'})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user and hasattr(self.user, 'profile') and self.user.profile.social_links:
            social_links = self.user.profile.social_links
            for field_name in self.fields:
                if field_name in social_links:
                    self.fields[field_name].initial = social_links[field_name]

    def save(self):
        if not self.user or not hasattr(self.user, 'profile'):
            return None

        social_links = {}
        for field_name, field_value in self.cleaned_data.items():
            if field_value:  # Only save non-empty values
                social_links[field_name] = field_value

        self.user.profile.social_links = social_links
        self.user.profile.save()
        return self.user.profile


class EducationForm(forms.ModelForm):
    """Form for adding/editing education entries."""
    class Meta:
        model = ProfileEducation
        fields = ['institution', 'degree', 'field_of_study', 'start_date', 'end_date', 'description', 'is_visible']
        widgets = {
            'institution': forms.TextInput(attrs={'class': 'input'}),
            'degree': forms.TextInput(attrs={'class': 'input'}),
            'field_of_study': forms.TextInput(attrs={'class': 'input'}),
            'start_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'input', 'rows': 3}),
            'is_visible': forms.CheckboxInput(attrs={'class': 'checkbox'}),
        }


class ExperienceForm(forms.ModelForm):
    """Form for adding/editing experience entries."""
    class Meta:
        model = ProfileExperience
        fields = ['company', 'position', 'location', 'start_date', 'end_date', 'description', 'is_visible']
        widgets = {
            'company': forms.TextInput(attrs={'class': 'input'}),
            'position': forms.TextInput(attrs={'class': 'input'}),
            'location': forms.TextInput(attrs={'class': 'input'}),
            'start_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'input', 'rows': 3}),
            'is_visible': forms.CheckboxInput(attrs={'class': 'checkbox'}),
        }


class SkillForm(forms.ModelForm):
    """Form for adding/editing skills."""
    class Meta:
        model = ProfileSkill
        fields = ['name', 'proficiency', 'is_visible']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input'}),
            'proficiency': forms.Select(attrs={'class': 'select'}),
            'is_visible': forms.CheckboxInput(attrs={'class': 'checkbox'}),
        }


class ProjectForm(forms.ModelForm):
    """Form for adding/editing projects."""
    class Meta:
        model = ProfileProject
        fields = ['title', 'description', 'url', 'image', 'technologies', 'start_date', 'end_date', 'is_visible']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'input'}),
            'description': forms.Textarea(attrs={'class': 'input', 'rows': 3}),
            'url': forms.URLInput(attrs={'class': 'input'}),
            'technologies': forms.TextInput(attrs={'class': 'input', 'placeholder': 'e.g., Python, Django, JavaScript'}),
            'start_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'is_visible': forms.CheckboxInput(attrs={'class': 'checkbox'}),
        }


class CertificationForm(forms.ModelForm):
    """Form for adding/editing certifications."""
    class Meta:
        model = ProfileCertification
        fields = ['name', 'issuing_organization', 'issue_date', 'expiration_date', 'credential_id', 'credential_url', 'is_visible']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input'}),
            'issuing_organization': forms.TextInput(attrs={'class': 'input'}),
            'issue_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'expiration_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'credential_id': forms.TextInput(attrs={'class': 'input'}),
            'credential_url': forms.URLInput(attrs={'class': 'input'}),
            'is_visible': forms.CheckboxInput(attrs={'class': 'checkbox'}),
        }


class PrivacySettingsForm(forms.Form):
    """Form for managing privacy settings."""
    PRIVACY_CHOICES = (
        ('public', _('Public - Anyone can see')),
        ('registered', _('Registered Users - Only logged-in users can see')),
        ('private', _('Private - Only you can see')),
    )

    bio = forms.ChoiceField(
        choices=PRIVACY_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'radio-group'})
    )
    location = forms.ChoiceField(
        choices=PRIVACY_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'radio-group'})
    )
    website = forms.ChoiceField(
        choices=PRIVACY_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'radio-group'})
    )
    social_links = forms.ChoiceField(
        choices=PRIVACY_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'radio-group'})
    )
    education = forms.ChoiceField(
        choices=PRIVACY_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'radio-group'})
    )
    experience = forms.ChoiceField(
        choices=PRIVACY_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'radio-group'})
    )
    skills = forms.ChoiceField(
        choices=PRIVACY_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'radio-group'})
    )
    projects = forms.ChoiceField(
        choices=PRIVACY_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'radio-group'})
    )
    certifications = forms.ChoiceField(
        choices=PRIVACY_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'radio-group'})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user and hasattr(self.user, 'profile') and self.user.profile.privacy_settings:
            privacy_settings = self.user.profile.privacy_settings
            for field_name in self.fields:
                if field_name in privacy_settings:
                    self.fields[field_name].initial = privacy_settings[field_name]

    def save(self):
        if not self.user or not hasattr(self.user, 'profile'):
            return None

        privacy_settings = {}
        for field_name, field_value in self.cleaned_data.items():
            privacy_settings[field_name] = field_value

        self.user.profile.privacy_settings = privacy_settings
        self.user.profile.save()
        return self.user.profile


class ProfilePictureForm(forms.ModelForm):
    """Form for uploading profile picture."""
    class Meta:
        model = CustomUser
        fields = ['profile_picture']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'file-input', 'accept': 'image/*'})
        }
