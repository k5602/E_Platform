from django import forms
from django.forms import inlineformset_factory
from .models_quiz import Quiz, Question, Answer, UserAttempt, UserAnswer
from .models import Subject

class QuizForm(forms.ModelForm):
    """Form for quiz creation and editing."""
    
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'subject', 'time_limit', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter quiz title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter quiz description', 'rows': 4}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'time_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 240}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter subjects to show only active ones
        self.fields['subject'].queryset = Subject.objects.filter(is_active=True)
        
        # Add help text
        self.fields['time_limit'].help_text = "Time limit in minutes"
        self.fields['is_active'].label = "Active"
        self.fields['is_active'].help_text = "Inactive quizzes are only visible to staff"


class QuestionForm(forms.ModelForm):
    """Form for question creation and editing."""
    
    class Meta:
        model = Question
        fields = ['text', 'explanation', 'order']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter question text', 'rows': 3}),
            'explanation': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter explanation for the answer (optional)', 'rows': 2}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


class AnswerForm(forms.ModelForm):
    """Form for answer creation and editing."""
    
    class Meta:
        model = Answer
        fields = ['text', 'is_correct']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter answer text', 'rows': 1}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# Formsets for creating multiple answers for a question
QuestionFormSet = inlineformset_factory(
    Quiz, 
    Question, 
    form=QuestionForm, 
    extra=1,
    can_delete=True
)

AnswerFormSet = inlineformset_factory(
    Question, 
    Answer, 
    form=AnswerForm, 
    extra=3,
    min_num=2,
    validate_min=True,
    can_delete=True
)
