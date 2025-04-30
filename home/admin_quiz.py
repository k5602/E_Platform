from django.contrib import admin  # type: ignore
from .models_quiz import Quiz, Question, Answer, UserAttempt, UserAnswer
from typing import Any, Optional

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1
    fields = ('text', 'is_correct', 'order')

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ('text', 'question_type', 'marks', 'order')
    show_change_link = True

class UserAnswerInline(admin.TabularInline):
    model = UserAnswer
    extra = 0
    fields = ('question', 'selected_answer', 'text_answer', 'marks_obtained')
    readonly_fields = ('question', 'selected_answer', 'text_answer', 'marks_obtained')
    can_delete = False
    max_num = 0
    show_change_link = True

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'is_active', 'passing_score', 'questions_count', 'created_at')
    list_filter = ('is_active', 'subject', 'created_at')
    search_fields = ('title', 'description', 'subject__name')
    date_hierarchy = 'created_at'
    readonly_fields = ('passing_score',)
    inlines = [QuestionInline]
    raw_id_fields = ('subject',)
    list_per_page = 20
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'subject')
        }),
        ('Quiz Settings', {
            'fields': ('time_limit', 'passing_score', 'is_active')
        }),
    )
    
    def questions_count(self, obj: Quiz) -> int:
        return obj.get_questions_count()
    questions_count.short_description = 'Questions'  # type: ignore

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text_preview', 'quiz', 'order', 'answers_count')
    list_filter = ('quiz__subject', 'quiz')
    search_fields = ('text', 'quiz__title')
    inlines = [AnswerInline]
    raw_id_fields = ('quiz',)
    list_per_page = 20
    
    fieldsets = (
        ('Question Details', {
            'fields': ('quiz', 'text', 'order')
        }),
        ('Additional Information', {
            'fields': ('explanation',),
            'classes': ('collapse',)
        }),
    )
    
    def text_preview(self, obj: Question) -> str:
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Question Text'  # type: ignore
    
    def answers_count(self, obj: Question) -> int:
        return obj.answers.count()
    answers_count.short_description = 'Answers'  # type: ignore

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('text_preview', 'question', 'is_correct', 'order')
    list_filter = ('is_correct',)
    search_fields = ('text', 'question__text')
    raw_id_fields = ('question',)
    list_per_page = 20
    
    def text_preview(self, obj: Answer) -> str:
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Answer Text'  # type: ignore

@admin.register(UserAttempt)
class UserAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'status', 'score', 'start_time', 'end_time')
    list_filter = ('status', 'quiz__subject', 'quiz')
    search_fields = ('user__username', 'quiz__title')
    date_hierarchy = 'start_time'
    readonly_fields = ('start_time', 'end_time', 'score')
    inlines = [UserAnswerInline]
    raw_id_fields = ('user', 'quiz')
    list_per_page = 20
    
    fieldsets = (
        ('Attempt Information', {
            'fields': ('user', 'quiz', 'status')
        }),
        ('Scoring and Timing', {
            'fields': ('score', 'start_time', 'end_time')
        }),
    )

@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('user_attempt', 'question', 'answer_preview', 'marks_obtained')
    list_filter = ('user_attempt__quiz',)
    search_fields = ('user_attempt__user__username', 'question__text')
    raw_id_fields = ('user_attempt', 'question', 'selected_answer')
    list_per_page = 20
    
    def answer_preview(self, obj: UserAnswer) -> str:
        if obj.selected_answer:
            return obj.selected_answer.text[:50] + '...' if len(obj.selected_answer.text) > 50 else obj.selected_answer.text
        elif obj.text_answer:
            return obj.text_answer[:50] + '...' if len(obj.text_answer) > 50 else obj.text_answer
        return 'No answer'
    answer_preview.short_description = 'Answer'  # type: ignore
