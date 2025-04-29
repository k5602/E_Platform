from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('instructor', 'Instructor'),
        ('admin', 'Administrator'),
    )

    user_type = models.CharField(
        _('User Type'),
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='student',
    )
    birthdate = models.DateField(_('Birth Date'), null=True, blank=True)
    profile_picture = models.ImageField(
        _('Profile Picture'),
        upload_to='profile_pictures/',
        null=True,
        blank=True,
        help_text=_('Profile picture for the user')
    )

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.username
