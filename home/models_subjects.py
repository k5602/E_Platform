from django.db import models
from authentication.models import CustomUser

class Subject(models.Model):
    """Model representing an academic subject or course."""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    icon_name = models.CharField(max_length=50, help_text="Material icon name")
    background_icon = models.CharField(max_length=50, help_text="Material icon for background")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Optional: Add instructor relationship
    instructor = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='taught_subjects',
        limit_choices_to={'user_type': 'instructor'}
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_enrolled_students_count(self):
        """Get the number of students enrolled in this subject."""
        return self.enrollments.count()
    
    def is_user_enrolled(self, user):
        """Check if a user is enrolled in this subject."""
        if not user.is_authenticated:
            return False
        return self.enrollments.filter(student=user).exists()


class SubjectMaterial(models.Model):
    """Model representing learning materials for a subject."""
    MATERIAL_TYPES = (
        ('document', 'Document'),
        ('video', 'Video'),
        ('link', 'External Link'),
        ('assignment', 'Assignment'),
    )
    
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPES)
    file = models.FileField(upload_to='subject_materials/', null=True, blank=True)
    external_url = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Subject Material"
        verbose_name_plural = "Subject Materials"
    
    def __str__(self):
        return f"{self.title} ({self.get_material_type_display()})"


class SubjectEnrollment(models.Model):
    """Model to track student enrollments in subjects."""
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='enrollments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('student', 'subject')
        verbose_name = "Subject Enrollment"
        verbose_name_plural = "Subject Enrollments"
    
    def __str__(self):
        return f"{self.student.username} enrolled in {self.subject.name}"
