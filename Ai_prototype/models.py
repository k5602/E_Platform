from django.db import models
from authentication.models import CustomUser

class MockAIFeedback(models.Model):
    """Model to store mock AI feedback responses."""
    
    FEEDBACK_TYPES = (
        ('general', 'General Feedback'),
        ('assignment', 'Assignment Feedback'),
        ('quiz', 'Quiz Feedback'),
    )
    
    feedback_type = models.CharField(max_length=50, choices=FEEDBACK_TYPES, default='general')
    submission_id = models.CharField(max_length=50)
    feedback_text = models.TextField()
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='ai_feedback', null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"AI Feedback for {self.submission_id} ({self.feedback_type})"
