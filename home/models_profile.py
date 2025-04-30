from django.db import models
from django.conf import settings
from authentication.models import CustomUser
from django.utils.translation import gettext_lazy as _

class ProfileUserProfile(models.Model):
    """Extended profile information for a user."""
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    bio = models.TextField(
        _('Biography'),
        blank=True,
        help_text=_('Tell us about yourself')
    )
    location = models.CharField(
        _('Location'),
        max_length=100,
        blank=True,
        help_text=_('City, Country')
    )
    website = models.URLField(
        _('Website'),
        blank=True,
        help_text=_('Your personal or professional website')
    )
    social_links = models.JSONField(
        _('Social Media Links'),
        default=dict,
        blank=True,
        help_text=_('Your social media profiles')
    )
    privacy_settings = models.JSONField(
        _('Privacy Settings'),
        default=dict,
        blank=True,
        help_text=_('Control who can see your profile information')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_completion_percentage(self):
        """Calculate profile completion percentage."""
        fields = [
            bool(self.bio),
            bool(self.location),
            bool(self.website),
            bool(self.social_links),
            bool(self.user.profile_picture),
            bool(ProfileEducation.objects.filter(user=self.user).exists()),
            bool(ProfileExperience.objects.filter(user=self.user).exists()),
            bool(ProfileSkill.objects.filter(user=self.user).exists()),
            bool(ProfileProject.objects.filter(user=self.user).exists()),
            bool(ProfileCertification.objects.filter(user=self.user).exists()),
        ]
        completed = sum(fields)
        return int((completed / len(fields)) * 100)

    def save(self, *args, **kwargs):
        """Initialize default privacy settings if not set."""
        if not self.privacy_settings:
            self.privacy_settings = {
                'bio': 'public',
                'location': 'public',
                'website': 'public',
                'social_links': 'public',
                'education': 'public',
                'experience': 'public',
                'skills': 'public',
                'projects': 'public',
                'certifications': 'public',
            }
        super().save(*args, **kwargs)


class ProfileEducation(models.Model):
    """Educational background of a user."""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile_education',
        null=True  # Allow null for migration purposes
    )
    institution = models.CharField(_('Institution'), max_length=100)
    degree = models.CharField(_('Degree'), max_length=100)
    field_of_study = models.CharField(_('Field of Study'), max_length=100)
    start_date = models.DateField(_('Start Date'), null=True, blank=True)  # Allow null for migration purposes
    end_date = models.DateField(_('End Date'), null=True, blank=True)
    description = models.TextField(_('Description'), blank=True)
    is_visible = models.BooleanField(_('Visible'), default=True)
    order = models.IntegerField(_('Order'), default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-end_date', '-start_date', 'order']
        verbose_name = _('Education')
        verbose_name_plural = _('Education')

    def __str__(self):
        return f"{self.degree} in {self.field_of_study} at {self.institution}"


class ProfileExperience(models.Model):
    """Work experience of a user."""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile_experience',
        null=True  # Allow null for migration purposes
    )
    company = models.CharField(_('Company'), max_length=100)
    position = models.CharField(_('Position'), max_length=100)
    location = models.CharField(_('Location'), max_length=100, blank=True)
    start_date = models.DateField(_('Start Date'), null=True, blank=True)  # Allow null for migration purposes
    end_date = models.DateField(_('End Date'), null=True, blank=True)
    description = models.TextField(_('Description'), blank=True)
    is_visible = models.BooleanField(_('Visible'), default=True)
    order = models.IntegerField(_('Order'), default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-end_date', '-start_date', 'order']
        verbose_name = _('Experience')
        verbose_name_plural = _('Experience')

    def __str__(self):
        return f"{self.position} at {self.company}"


class ProfileSkill(models.Model):
    """Skills of a user."""
    PROFICIENCY_CHOICES = (
        (1, _('Beginner')),
        (2, _('Elementary')),
        (3, _('Intermediate')),
        (4, _('Advanced')),
        (5, _('Expert')),
    )

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile_skills',
        null=True  # Allow null for migration purposes
    )
    name = models.CharField(_('Skill Name'), max_length=50)
    proficiency = models.IntegerField(
        _('Proficiency'),
        choices=PROFICIENCY_CHOICES,
        default=3
    )
    is_visible = models.BooleanField(_('Visible'), default=True)
    order = models.IntegerField(_('Order'), default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-proficiency', 'order', 'name']
        verbose_name = _('Skill')
        verbose_name_plural = _('Skills')
        unique_together = ('user', 'name')

    def __str__(self):
        return f"{self.name} ({self.get_proficiency_display()})"


class ProfileProject(models.Model):
    """Projects of a user."""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile_projects',
        null=True  # Allow null for migration purposes
    )
    title = models.CharField(_('Title'), max_length=100)
    description = models.TextField(_('Description'))
    url = models.URLField(_('URL'), blank=True)
    image = models.ImageField(
        _('Image'),
        upload_to='profile/projects/',
        null=True,
        blank=True
    )
    technologies = models.CharField(_('Technologies'), max_length=200, blank=True)
    start_date = models.DateField(_('Start Date'), null=True, blank=True)  # Allow null for migration purposes
    end_date = models.DateField(_('End Date'), null=True, blank=True)
    is_visible = models.BooleanField(_('Visible'), default=True)
    order = models.IntegerField(_('Order'), default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-end_date', '-start_date', 'order']
        verbose_name = _('Project')
        verbose_name_plural = _('Projects')

    def __str__(self):
        return self.title


class ProfileCertification(models.Model):
    """Certifications of a user."""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile_certifications',
        null=True  # Allow null for migration purposes
    )
    name = models.CharField(_('Certification Name'), max_length=100)
    issuing_organization = models.CharField(_('Issuing Organization'), max_length=100, default='')
    issue_date = models.DateField(_('Issue Date'), null=True, blank=True)  # Allow null for migration purposes
    expiration_date = models.DateField(_('Expiration Date'), null=True, blank=True)
    credential_id = models.CharField(_('Credential ID'), max_length=100, blank=True)
    credential_url = models.URLField(_('Credential URL'), blank=True)
    is_visible = models.BooleanField(_('Visible'), default=True)
    order = models.IntegerField(_('Order'), default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issue_date', 'order']
        verbose_name = _('Certification')
        verbose_name_plural = _('Certifications')

    def __str__(self):
        return f"{self.name} by {self.issuing_organization}"
