import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.utils import timezone
from django.db import models
from django.db.models import Count, Avg, Q, F, Sum
from django.forms import modelformset_factory, inlineformset_factory
from .models_quiz import Quiz, Question, Answer, UserAttempt, UserAnswer
from .models import Subject, Notification
from .forms_quiz import QuizForm, QuestionForm, AnswerForm, QuestionFormSet, AnswerFormSet

# Set up logger
logger = logging.getLogger(__name__)

@login_required
def quiz_list(request):
    """View for displaying all available quizzes."""
    # Filter quizzes based on is_active status
    if request.user.is_staff or request.user.user_type == 'instructor':
        # Instructors and admins can see all quizzes
        quizzes = Quiz.objects.all()
    else:
        # Students see only active quizzes that are in subjects they're enrolled in
        enrolled_subjects = [
            enrollment.subject.id for enrollment in
            request.user.enrollments.filter(is_active=True)
        ]

        quizzes = Quiz.objects.filter(
            is_active=True,
            subject__id__in=enrolled_subjects
        )

    # Filter by subject if provided
    subject_id = request.GET.get('subject')
    if subject_id:
        try:
            subject = Subject.objects.get(id=subject_id)
            quizzes = quizzes.filter(subject=subject)
            subject_name = subject.name
        except Subject.DoesNotExist:
            subject_name = None
    else:
        subject_name = None

    # Get all subjects for filter dropdown
    subjects = Subject.objects.filter(is_active=True)

    # Paginate results
    paginator = Paginator(quizzes, 10)  # 10 quizzes per page
    page = request.GET.get('page', 1)
    quizzes = paginator.get_page(page)

    context = {
        'quizzes': quizzes,
        'subjects': subjects,
        'selected_subject': subject_id,
        'subject_name': subject_name,
        'active_page': 'quiz'
    }

    return render(request, 'home/quiz/quiz_list.html', context)

@login_required
def my_quizzes(request):
    """View for displaying quizzes created by the user or taken by the user."""

    tab = request.GET.get('tab', 'created')

    try:
        if tab == 'created' and (request.user.is_staff or request.user.user_type == 'instructor'):
            # Quizzes created by the user
            quizzes = Quiz.objects.filter(creator=request.user)
            template = 'home/quiz/my_created_quizzes.html'

            # Paginate results
            paginator = Paginator(quizzes, 10)  # 10 quizzes per page
            page = request.GET.get('page', 1)
            quizzes = paginator.get_page(page)

            context = {
                'quizzes': quizzes,
                'tab': tab,
                'active_page': 'quiz'
            }

            return render(request, template, context)
        else:
            # Quizzes taken by the user
            tab = 'taken'  # Ensure tab is set to 'taken' if not an instructor

            # Check if the UserAttempt table exists in the database
            try:
                attempts = UserAttempt.objects.filter(user=request.user)

                # Filter by status if provided
                status = request.GET.get('status')
                if status:
                    attempts = attempts.filter(status=status)

                # Paginate results
                paginator = Paginator(attempts, 10)  # 10 attempts per page
                page = request.GET.get('page', 1)
                attempts = paginator.get_page(page)

                context = {
                    'attempts': attempts,
                    'tab': tab,
                    'status': status,
                    'active_page': 'quiz'
                }

                return render(request, 'home/quiz/my_taken_quizzes.html', context)
            except Exception as e:
                # Handle database errors gracefully
                messages.error(request, f"Unable to retrieve quiz attempts. Error: {str(e)}")
                context = {
                    'tab': tab,
                    'active_page': 'quiz',
                    'error': str(e)
                }
                return render(request, 'home/quiz/my_taken_quizzes.html', context)
    except Exception as e:
        # Catch any other errors
        messages.error(request, f"An error occurred: {str(e)}")
        return render(request, 'home/error.html', {'error': str(e), 'active_page': 'quiz'})

@login_required
def quiz_detail(request, quiz_id):
    """View for displaying quiz details."""
    quiz = get_object_or_404(Quiz, id=quiz_id)

    # Check if user has permission to view the quiz
    if not quiz.is_available_to_user(request.user):
        messages.error(request, "You do not have permission to view this quiz.")
        return redirect('home:quiz_list')

    # Get user's previous attempts
    user_attempts = UserAttempt.objects.filter(
        user=request.user,
        quiz=quiz
    )

    context = {
        'quiz': quiz,
        'user_attempts': user_attempts,
        'active_page': 'quiz'
    }

    return render(request, 'home/quiz/quiz_detail.html', context)

@login_required
def create_quiz(request):
    """View for creating a new quiz."""
    # Only instructors and admins can create quizzes
    if not (request.user.is_staff or request.user.user_type == 'instructor'):
        messages.error(request, "You do not have permission to create quizzes.")
        return redirect('home:quiz_list')

    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.creator = request.user
            quiz.save()

            messages.success(request, f"Quiz '{quiz.title}' created successfully. Now add questions.")
            return redirect('home:quiz_edit', quiz_id=quiz.id)
    else:
        form = QuizForm()

    context = {
        'form': form,
        'action': 'create',
        'active_page': 'quiz'
    }

    return render(request, 'home/quiz/quiz_form.html', context)

@login_required
def edit_quiz(request, quiz_id):
    """View for editing an existing quiz."""
    quiz = get_object_or_404(Quiz, id=quiz_id)

    # Check if user has permission to edit the quiz
    if not (request.user == quiz.creator or request.user.is_staff):
        messages.error(request, "You do not have permission to edit this quiz.")
        return redirect('home:quiz_list')

    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            messages.success(request, f"Quiz '{quiz.title}' updated successfully.")
            return redirect('home:quiz_detail', quiz_id=quiz.id)
    else:
        form = QuizForm(instance=quiz)

    context = {
        'form': form,
        'quiz': quiz,
        'action': 'edit',
        'active_page': 'quiz'
    }

    return render(request, 'home/quiz/quiz_form.html', context)

@login_required
def delete_quiz(request, quiz_id):
    """View for deleting a quiz."""
    quiz = get_object_or_404(Quiz, id=quiz_id)

    # Check if user has permission to delete the quiz
    if not (request.user == quiz.creator or request.user.is_staff):
        messages.error(request, "You do not have permission to delete this quiz.")
        return redirect('home:quiz_list')

    if request.method == 'POST':
        quiz_title = quiz.title
        quiz.delete()
        messages.success(request, f"Quiz '{quiz_title}' deleted successfully.")
        return redirect('home:my_quizzes')

    context = {
        'quiz': quiz,
        'active_page': 'quiz'
    }

    return render(request, 'home/quiz/quiz_confirm_delete.html', context)

@login_required
def manage_questions(request, quiz_id):
    """View for managing questions in a quiz."""
    quiz = get_object_or_404(Quiz, id=quiz_id)

    # Check if user has permission to edit the quiz
    if not (request.user == quiz.creator or request.user.is_staff):
        messages.error(request, "You do not have permission to manage questions for this quiz.")
        return redirect('home:quiz_list')

    questions = quiz.questions.all().order_by('order')

    context = {
        'quiz': quiz,
        'questions': questions,
        'active_page': 'quiz'
    }

    return render(request, 'home/quiz/manage_questions.html', context)

@login_required
def add_question(request, quiz_id):
    """View for adding a new question to a quiz."""
    quiz = get_object_or_404(Quiz, id=quiz_id)

    # Check if user has permission to edit the quiz
    if not (request.user == quiz.creator or request.user.is_staff):
        messages.error(request, "You do not have permission to add questions to this quiz.")
        return redirect('home:quiz_list')

    if request.method == 'POST':
        question_form = QuestionForm(request.POST, request.FILES)

        if question_form.is_valid():
            question = question_form.save(commit=False)
            question.quiz = quiz
            question.order = quiz.questions.count() + 1
            question.save()

            # For true/false questions, auto-generate answers
            if question.question_type == 'true_false':
                Answer.objects.create(
                    question=question,
                    text='True',
                    is_correct=question_form.cleaned_data.get('correct_option') == 'true',
                    order=1
                )
                Answer.objects.create(
                    question=question,
                    text='False',
                    is_correct=question_form.cleaned_data.get('correct_option') == 'false',
                    order=2
                )
                messages.success(request, "Question added successfully with True/False options.")
                return redirect('home:manage_questions', quiz_id=quiz.id)

            messages.success(request, "Question added successfully. Now add answers.")
            return redirect('home:manage_answers', question_id=question.id)
    else:
        question_form = QuestionForm()

    context = {
        'quiz': quiz,
        'question_form': question_form,
        'action': 'add',
        'active_page': 'quiz'
    }

    return render(request, 'home/quiz/question_form.html', context)

@login_required
def edit_question(request, question_id):
    """View for editing an existing question."""
    question = get_object_or_404(Question, id=question_id)
    quiz = question.quiz

    # Check if user has permission to edit the quiz
    if not (request.user == quiz.creator or request.user.is_staff):
        messages.error(request, "You do not have permission to edit questions in this quiz.")
        return redirect('home:quiz_list')

    if request.method == 'POST':
        question_form = QuestionForm(request.POST, request.FILES, instance=question)

        if question_form.is_valid():
            question = question_form.save()

            # For true/false questions, update answers
            if question.question_type == 'true_false':
                try:
                    true_answer = question.answers.get(text='True')
                    false_answer = question.answers.get(text='False')

                    true_answer.is_correct = question_form.cleaned_data.get('correct_option') == 'true'
                    false_answer.is_correct = question_form.cleaned_data.get('correct_option') == 'false'

                    true_answer.save()
                    false_answer.save()
                except:
                    # If True/False answers don't exist, create them
                    question.answers.all().delete()
                    Answer.objects.create(
                        question=question,
                        text='True',
                        is_correct=question_form.cleaned_data.get('correct_option') == 'true',
                        order=1
                    )
                    Answer.objects.create(
                        question=question,
                        text='False',
                        is_correct=question_form.cleaned_data.get('correct_option') == 'false',
                        order=2
                    )

            messages.success(request, "Question updated successfully.")
            return redirect('home:manage_questions', quiz_id=quiz.id)
    else:
        # For true/false questions, set the correct_option field
        initial = {}
        if question.question_type == 'true_false':
            try:
                true_answer = question.answers.get(text='True')
                if true_answer.is_correct:
                    initial['correct_option'] = 'true'
                else:
                    initial['correct_option'] = 'false'
            except:
                pass

        question_form = QuestionForm(instance=question, initial=initial)

    context = {
        'quiz': quiz,
        'question': question,
        'question_form': question_form,
        'action': 'edit',
        'active_page': 'quiz'
    }

    return render(request, 'home/quiz/question_form.html', context)

@login_required
def delete_question(request, question_id):
    """View for deleting a question."""
    question = get_object_or_404(Question, id=question_id)
    quiz = question.quiz

    # Check if user has permission to edit the quiz
    if not (request.user == quiz.creator or request.user.is_staff):
        messages.error(request, "You do not have permission to delete questions from this quiz.")
        return redirect('home:quiz_list')

    if request.method == 'POST':
        question.delete()
        # Re-order remaining questions
        for i, q in enumerate(quiz.questions.all().order_by('order')):
            q.order = i + 1
            q.save(update_fields=['order'])

        quiz.calculate_total_marks()
        messages.success(request, "Question deleted successfully.")
        return redirect('home:manage_questions', quiz_id=quiz.id)

    context = {
        'quiz': quiz,
        'question': question,
        'active_page': 'quiz'
    }

    return render(request, 'home/quiz/question_confirm_delete.html', context)

@login_required
def manage_answers(request, question_id):
    """View for managing answers to a question."""
    question = get_object_or_404(Question, id=question_id)
    quiz = question.quiz

    # Check if user has permission to edit the quiz
    if not (request.user == quiz.creator or request.user.is_staff):
        messages.error(request, "You do not have permission to manage answers for this quiz.")
        return redirect('home:quiz_list')

    # For true/false questions, redirect to question edit page
    if question.question_type == 'true_false':
        messages.info(request, "True/False questions have fixed answer options.")
        return redirect('home:edit_question', question_id=question.id)

    AnswerFormSet = inlineformset_factory(
        Question,
        Answer,
        form=AnswerForm,
        extra=1,
        can_delete=True
    )

    if request.method == 'POST':
        formset = AnswerFormSet(request.POST, instance=question)

        if formset.is_valid():
            formset.save()

            # Re-order answers
            for i, answer in enumerate(question.answers.all().order_by('order')):
                answer.order = i + 1
                answer.save(update_fields=['order'])

            messages.success(request, "Answers updated successfully.")

            # Check if at least one answer is marked as correct for MCQs
            if question.question_type == 'mcq' and not question.answers.filter(is_correct=True).exists():
                messages.warning(request, "Warning: No correct answer is marked for this question.")

            return redirect('home:manage_questions', quiz_id=quiz.id)
    else:
        formset = AnswerFormSet(instance=question)

    context = {
        'quiz': quiz,
        'question': question,
        'formset': formset,
        'active_page': 'quiz'
    }

    return render(request, 'home/quiz/answer_formset.html', context)

@login_required
def start_quiz(request, quiz_id):
    """View for starting a quiz attempt."""
    quiz = get_object_or_404(Quiz, id=quiz_id)

    # Check if quiz is available to user
    if not quiz.is_available_to_user(request.user):
        messages.error(request, "This quiz is not available to you.")
        return redirect('home:quiz_list')

    # Check if quiz is active
    if not quiz.is_active and not request.user.is_staff:
        messages.error(request, "This quiz is not currently active.")
        return redirect('home:quiz_list')

    # Check if user already has an in-progress attempt
    existing_attempt = UserAttempt.objects.filter(
        user=request.user,
        quiz=quiz,
        status='in_progress'
    ).first()

    if existing_attempt:
        messages.info(request, "You already have an in-progress attempt. Continuing from where you left off.")
        return redirect('home:take_quiz', attempt_id=existing_attempt.id)

    # Create a new attempt
    attempt = UserAttempt.objects.create(
        user=request.user,
        quiz=quiz,
        status='in_progress'
    )

    # Create UserAnswer objects for all questions
    questions = quiz.questions.all()
    for question in questions:
        UserAnswer.objects.create(
            user_attempt=attempt,
            question=question
        )

    # Send notification to quiz subject instructor
    Notification.objects.create(
        recipient=quiz.subject.instructor,
        sender=request.user,
        notification_type='quiz_attempt',
        text=f"{request.user.username} has started your quiz: {quiz.title}"
    )

    messages.success(request, f"You have {quiz.time_limit} minutes to complete this quiz. Good luck!")
    return redirect('home:take_quiz', attempt_id=attempt.id)

@login_required
def take_quiz(request, attempt_id):
    """View for taking a quiz."""
    logger.info(f"User {request.user.username} accessing quiz attempt {attempt_id}")

    try:
        attempt = get_object_or_404(UserAttempt, id=attempt_id)
        quiz = attempt.quiz

        # Check if the attempt belongs to the user
        if attempt.user != request.user:
            logger.warning(f"Unauthorized access: User {request.user.username} tried to access quiz attempt {attempt_id} belonging to {attempt.user.username}")
            messages.error(request, "You do not have permission to access this quiz attempt.")
            return redirect('home:quiz_list')

        # Check if the attempt is already completed
        if attempt.status != 'in_progress':
            logger.info(f"User {request.user.username} tried to access completed quiz attempt {attempt_id}")
            messages.info(request, "This quiz attempt is already completed.")
            return redirect('home:quiz_result', attempt_id=attempt.id)

        # Check for timeout
        if attempt.is_timed_out():
            logger.info(f"Quiz attempt {attempt_id} by user {request.user.username} has timed out")
            attempt.time_out()
            messages.warning(request, "Your quiz time has expired. Your answers have been submitted automatically.")
            return redirect('home:quiz_result', attempt_id=attempt.id)
    except Exception as e:
        logger.error(f"Error in take_quiz view: {str(e)}", exc_info=True)
        messages.error(request, "An error occurred while loading the quiz. Please try again.")
        return redirect('home:quiz_list')

    # Get quiz questions
    questions = quiz.questions.all().order_by('order')

    # If randomized, shuffle the questions
    if quiz.is_randomized:
        questions = questions.order_by('?')

    # Process form submission
    if request.method == 'POST':
        logger.info(f"Processing quiz submission for attempt {attempt_id} by user {request.user.username}")
        try:
            # Process answers
            for question in questions:
                answer_key = f'question_{question.id}'

                if question.question_type == 'mcq' or question.question_type == 'true_false':
                    # Multiple choice or True/False question
                    answer_id = request.POST.get(answer_key)

                    if answer_id:
                        try:
                            selected_answer = Answer.objects.get(id=answer_id, question=question)
                            logger.debug(f"User {request.user.username} selected answer {selected_answer.id} for question {question.id}")

                            # Create or update the user answer
                            user_answer, created = UserAnswer.objects.update_or_create(
                                user_attempt=attempt,
                                question=question,
                                defaults={
                                    'selected_answer': selected_answer,
                                    'text_answer': None
                                }
                            )
                        except Answer.DoesNotExist:
                            logger.warning(f"Invalid answer ID {answer_id} for question {question.id}")
                            pass

                elif question.question_type == 'short_answer':
                    # Short answer question
                    text_answer = request.POST.get(answer_key, '').strip()

                    if text_answer:
                        logger.debug(f"User {request.user.username} provided text answer for question {question.id}")
                        # Create or update the user answer
                        user_answer, created = UserAnswer.objects.update_or_create(
                            user_attempt=attempt,
                            question=question,
                            defaults={
                                'selected_answer': None,
                                'text_answer': text_answer
                            }
                        )

            # Check if the "Submit Quiz" button was clicked
            if 'submit_quiz' in request.POST:
                logger.info(f"User {request.user.username} submitted quiz attempt {attempt_id}")
                attempt.submit()
                messages.success(request, "Quiz submitted successfully!")
                return redirect('home:quiz_result', attempt_id=attempt.id)

            # If just saving progress
            logger.info(f"User {request.user.username} saved progress for quiz attempt {attempt_id}")
            messages.info(request, "Your progress has been saved.")
            return redirect('home:take_quiz', attempt_id=attempt.id)

        except Exception as e:
            logger.error(f"Error processing quiz submission: {str(e)}", exc_info=True)
            messages.error(request, "An error occurred while saving your answers. Please try again.")
            return redirect('home:take_quiz', attempt_id=attempt.id)

    # Get user's existing answers
    user_answers = {
        answer.question_id: answer for answer in
        UserAnswer.objects.filter(user_attempt=attempt)
    }

    # Calculate remaining time
    current_time = timezone.now()
    elapsed_seconds = (current_time - attempt.start_time).total_seconds()
    remaining_seconds = max(0, (quiz.time_limit * 60) - elapsed_seconds)

    context = {
        'quiz': quiz,
        'attempt': attempt,
        'questions': questions,
        'user_answers': user_answers,
        'remaining_seconds': remaining_seconds,
        'active_page': 'quiz'
    }

    return render(request, 'home/quiz/take_quiz.html', context)

@login_required
def quiz_result(request, attempt_id):
    """View for displaying quiz results."""
    logger.info(f"User {request.user.username} viewing quiz result for attempt {attempt_id}")

    try:
        # Get attempt with related quiz in a single query
        attempt = get_object_or_404(
            UserAttempt.objects.select_related('quiz', 'quiz__creator', 'user'),
            id=attempt_id
        )
        quiz = attempt.quiz

        # Check if the attempt belongs to the user or if the user is the quiz creator/admin
        if not (attempt.user == request.user or quiz.creator == request.user or request.user.is_staff):
            logger.warning(f"Unauthorized access: User {request.user.username} tried to view quiz results for attempt {attempt_id} belonging to {attempt.user.username}")
            messages.error(request, "You do not have permission to view these quiz results.")
            return redirect('home:quiz_list')

        # Get all questions with answers in a single query using prefetch_related
        questions = quiz.questions.prefetch_related('answers').order_by('order')

        # Get user's answers with related data in a single query
        user_answers_query = UserAnswer.objects.filter(user_attempt=attempt).select_related('selected_answer')

        # Create a dictionary for faster lookup
        user_answers = {
            answer.question_id: answer for answer in user_answers_query
        }

        # Calculate score percentage
        score_percent = 0
        if quiz.total_marks > 0:
            score_percent = (attempt.score / quiz.total_marks) * 100

        logger.info(f"Quiz result for attempt {attempt_id}: score {attempt.score}/{quiz.total_marks} ({score_percent:.1f}%)")

        context = {
            'quiz': quiz,
            'attempt': attempt,
            'questions': questions,
            'user_answers': user_answers,
            'score_percent': score_percent,
            'active_page': 'quiz'
        }

        return render(request, 'home/quiz/quiz_result.html', context)

    except Exception as e:
        logger.error(f"Error in quiz_result view: {str(e)}", exc_info=True)
        messages.error(request, "An error occurred while loading the quiz results. Please try again.")
        return redirect('home:quiz_list')

@login_required
def quiz_analytics(request, quiz_id):
    """View for displaying quiz analytics."""
    logger.info(f"User {request.user.username} viewing analytics for quiz {quiz_id}")

    try:
        # Get quiz with creator in a single query
        quiz = get_object_or_404(Quiz.objects.select_related('creator', 'subject'), id=quiz_id)

        # Check if user has permission to view analytics
        if not (request.user == quiz.creator or request.user.is_staff):
            logger.warning(f"Unauthorized access: User {request.user.username} tried to view analytics for quiz {quiz_id} created by {quiz.creator.username}")
            messages.error(request, "You do not have permission to view analytics for this quiz.")
            return redirect('home:quiz_list')

        # Get completed attempts with user data in a single query
        completed_attempts = UserAttempt.objects.filter(
            quiz=quiz,
            status__in=['completed', 'timed_out']
        ).select_related('user')

        # Calculate statistics
        total_attempts = completed_attempts.count()

        # Use database aggregation for better performance
        stats = completed_attempts.aggregate(
            avg_score=Avg('score'),
            total_attempts=Count('id')
        )

        average_score = stats['avg_score'] or 0
        total_attempts = stats['total_attempts']

        if quiz.total_marks > 0:
            average_percentage = (average_score / quiz.total_marks) * 100
        else:
            average_percentage = 0

        # Get all questions with a single query
        questions = list(quiz.questions.all().order_by('order'))

        if questions and total_attempts > 0:
            # Get all user answers for these questions in a single query
            question_ids = [q.id for q in questions]

            # Use a more efficient query with annotations
            question_stats_data = UserAnswer.objects.filter(
                user_attempt__in=completed_attempts,
                question_id__in=question_ids
            ).values('question_id').annotate(
                correct_count=Count('id', filter=models.Q(marks_obtained=models.F('question__marks'))),
                total_count=Count('id')
            )

            # Create a lookup dictionary
            question_stats_lookup = {item['question_id']: item for item in question_stats_data}

            # Build the question_stats list
            question_stats = []
            for question in questions:
                stats_data = question_stats_lookup.get(question.id, {'correct_count': 0, 'total_count': 0})
                correct_count = stats_data['correct_count']

                # Calculate percentage correct
                if total_attempts > 0:
                    percent_correct = (correct_count / total_attempts) * 100
                else:
                    percent_correct = 0

                question_stats.append({
                    'question': question,
                    'correct_count': correct_count,
                    'percent_correct': percent_correct
                })
        else:
            question_stats = []

        logger.info(f"Quiz analytics for quiz {quiz_id}: {total_attempts} attempts, avg score: {average_score:.2f}/{quiz.total_marks} ({average_percentage:.1f}%)")

        context = {
            'quiz': quiz,
            'total_attempts': total_attempts,
            'average_score': average_score,
            'average_percentage': average_percentage,
            'question_stats': question_stats,
            'active_page': 'quiz'
        }

        return render(request, 'home/quiz/quiz_analytics.html', context)

    except Exception as e:
        logger.error(f"Error in quiz_analytics view: {str(e)}", exc_info=True)
        messages.error(request, "An error occurred while loading the quiz analytics. Please try again.")
        return redirect('home:quiz_list')

# AJAX API views

@login_required
def update_question_order(request):
    """AJAX view for updating question order."""
    if request.method == 'POST' and request.is_ajax():
        question_ids = request.POST.getlist('question_ids[]')

        # Check if the user has permission to edit these questions
        if not question_ids:
            return JsonResponse({'status': 'error', 'message': 'No questions provided'})

        try:
            first_question = Question.objects.get(id=question_ids[0])
            quiz = first_question.quiz

            if not (request.user == quiz.creator or request.user.is_staff):
                return JsonResponse({
                    'status': 'error',
                    'message': 'You do not have permission to reorder these questions'
                })

            # Update order for all questions
            for i, question_id in enumerate(question_ids):
                question = Question.objects.get(id=question_id, quiz=quiz)
                question.order = i + 1
                question.save(update_fields=['order'])

            return JsonResponse({'status': 'success'})

        except Question.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Question not found'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
def update_answer_order(request):
    """AJAX view for updating answer order."""
    if request.method == 'POST' and request.is_ajax():
        answer_ids = request.POST.getlist('answer_ids[]')

        # Check if the user has permission to edit these answers
        if not answer_ids:
            return JsonResponse({'status': 'error', 'message': 'No answers provided'})

        try:
            first_answer = Answer.objects.get(id=answer_ids[0])
            question = first_answer.question
            quiz = question.quiz

            if not (request.user == quiz.creator or request.user.is_staff):
                return JsonResponse({
                    'status': 'error',
                    'message': 'You do not have permission to reorder these answers'
                })

            # Update order for all answers
            for i, answer_id in enumerate(answer_ids):
                answer = Answer.objects.get(id=answer_id, question=question)
                answer.order = i + 1
                answer.save(update_fields=['order'])

            return JsonResponse({'status': 'success'})

        except Answer.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Answer not found'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
@require_POST
def mark_short_answer(request, answer_id):
    """AJAX view for manually grading short answer responses."""
    if not request.is_ajax():
        return JsonResponse({'status': 'error', 'message': 'Invalid request'})

    try:
        user_answer = UserAnswer.objects.get(id=answer_id)
        question = user_answer.question
        quiz = question.quiz

        # Check if user has permission to grade
        if not (request.user == quiz.creator or request.user.is_staff):
            return JsonResponse({
                'status': 'error',
                'message': 'You do not have permission to grade answers'
            })

        # Get marks from request
        try:
            marks = int(request.POST.get('marks', 0))
            marks = max(0, min(marks, question.marks))  # Ensure marks are within valid range
        except ValueError:
            marks = 0

        # Update marks
        user_answer.marks_obtained = marks
        user_answer.save(update_fields=['marks_obtained'])

        # Update attempt score
        user_answer.user_attempt.calculate_score()

        return JsonResponse({
            'status': 'success',
            'new_score': user_answer.user_attempt.score
        })

    except UserAnswer.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Answer not found'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
