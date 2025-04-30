from django.db import models
from django.utils import timezone
from authentication.models import CustomUser
from .models import Subject

class Quiz(models.Model):
    """Model representing a quiz."""

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='quizzes')
    creator = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_quizzes', null=True)
    time_limit = models.PositiveIntegerField(help_text="Time limit in minutes", default=30)
    passing_score = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_randomized = models.BooleanField(default=False, help_text="Randomize question order for each attempt")
    total_marks = models.PositiveIntegerField(default=0, help_text="Total possible marks for this quiz")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"
        indexes = [
            models.Index(fields=['subject']),
        ]

    def __str__(self):
        return self.title

    def get_questions_count(self):
        """Return the count of questions in this quiz."""
        return self.questions.count()

    def calculate_total_marks(self):
        """Calculate and update the total marks based on question count."""
        # Each question is worth 1 point
        question_count = self.questions.count()
        # Update total_marks and passing_score if there are questions
        if question_count > 0:
            self.total_marks = question_count
            self.passing_score = max(int(question_count * 0.6), 1)  # 60% to pass, minimum 1
            self.save(update_fields=['total_marks', 'passing_score'])
        return question_count

    def is_available_to_user(self, user):
        """Check if the quiz is available to the specified user."""
        if not self.is_active:
            # Only staff can access inactive quizzes
            return user.is_staff

        # For active quizzes, check if user is enrolled in the subject
        return self.subject.is_user_enrolled(user)


class Question(models.Model):
    """Model representing a question in a quiz."""

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    explanation = models.TextField(blank=True, help_text="Explanation shown after answering")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['order']
        verbose_name = "Question"
        verbose_name_plural = "Questions"

    def __str__(self):
        return f"{self.text[:50]}..."

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # After saving the question, update the quiz's total marks
        self.quiz.calculate_total_marks()


class Answer(models.Model):
    """Model representing an answer to a question."""

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.TextField()
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = "Answer"
        verbose_name_plural = "Answers"

    def __str__(self):
        return f"{self.text[:50]}..."


class UserAttempt(models.Model):
    """Model representing a user's attempt at a quiz."""

    STATUS_CHOICES = (
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('timed_out', 'Timed Out'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    score = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')

    class Meta:
        ordering = ['-start_time']
        verbose_name = "User Attempt"
        verbose_name_plural = "User Attempts"
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['quiz']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.user.username}'s attempt of {self.quiz.title} ({self.get_status_display()})"

    def calculate_score(self):
        """Calculate and update the score for this attempt."""
        total_score = 0
        for user_answer in self.user_answers.all():
            total_score += user_answer.marks_obtained

        self.score = total_score
        self.save(update_fields=['score'])
        return total_score

    def submit(self):
        """Mark the attempt as completed and calculate the score."""
        self.status = 'completed'
        self.end_time = timezone.now()
        self.save(update_fields=['status', 'end_time'])
        self.calculate_score()

    def time_out(self):
        """Mark the attempt as timed out and calculate the score."""
        self.status = 'timed_out'
        self.end_time = timezone.now()
        self.save(update_fields=['status', 'end_time'])
        self.calculate_score()

    def is_timed_out(self):
        """Check if the attempt has timed out based on quiz duration."""
        # If already completed or timed out, it's not in progress anymore
        if self.status != 'in_progress':
            return False

        duration_seconds = self.quiz.time_limit * 60
        elapsed_seconds = (timezone.now() - self.start_time).total_seconds()
        return elapsed_seconds > duration_seconds


class UserAnswer(models.Model):
    """Model representing a user's answer to a question in a quiz attempt."""

    user_attempt = models.ForeignKey(UserAttempt, on_delete=models.CASCADE, related_name='user_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='user_answers')
    selected_answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True, blank=True, related_name='user_selections')
    text_answer = models.TextField(blank=True, null=True, help_text="For short answer questions")
    marks_obtained = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "User Answer"
        verbose_name_plural = "User Answers"
        unique_together = ['user_attempt', 'question']

    def __str__(self):
        return f"Answer to {self.question} by {self.user_attempt.user.username}"

    def save(self, *args, **kwargs):
        # Auto-calculate marks based on the question type and selected answer
        if not self.pk:  # Only on creation
            self.calculate_marks()
        super().save(*args, **kwargs)

    def calculate_marks(self):
        """Calculate marks based on answer correctness."""
        # Since we don't have a question_type field anymore, we'll simply check if the selected answer is correct
        if self.selected_answer and self.selected_answer.is_correct:
            self.marks_obtained = 1  # Each question is worth 1 point
        else:
            self.marks_obtained = 0
