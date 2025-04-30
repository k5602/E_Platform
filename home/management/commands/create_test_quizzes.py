import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from authentication.models import CustomUser
from home.models import Subject
from home.models_quiz import Quiz, Question, Answer


class Command(BaseCommand):
    help = 'Creates test quizzes with questions and answers for the E-Platform'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=2,
            help='Number of test quizzes to create (default: 2)',
        )

    def handle(self, *args, **options):
        count = options['count']
        self.stdout.write(self.style.SUCCESS(f'Creating {count} test quizzes...'))
        
        # Get or create test data dependencies
        instructor = self._get_instructor()
        subjects = self._get_subjects(instructor)
        
        # Create test quizzes
        with transaction.atomic():
            for i in range(count):
                quiz = self._create_quiz(i, instructor, subjects)
                self._create_questions_and_answers(quiz)
                
                self.stdout.write(self.style.SUCCESS(f'Created quiz {i+1}/{count}: {quiz.title}'))
        
        if count > 0:
            self.stdout.write(self.style.SUCCESS(f'Successfully created {count} test quizzes with questions and answers!'))
        else:
            self.stdout.write(self.style.SUCCESS('No test quizzes were created.'))
    
    def _get_instructor(self):
        """Get an instructor user for test quizzes."""
        instructor = CustomUser.objects.filter(user_type='instructor').first()
        
        if not instructor:
            # If no instructor exists, use the first admin or superuser
            instructor = CustomUser.objects.filter(is_staff=True).first()
            
            if not instructor:
                # If still no suitable user, use the first user available
                instructor = CustomUser.objects.first()
                
                if not instructor:
                    # If no users at all, create one
                    self.stdout.write(self.style.WARNING('No users found, creating test instructor...'))
                    instructor = CustomUser.objects.create_user(
                        username='testinstructor',
                        email='instructor@example.com',
                        password='Password123',
                        first_name='Test',
                        last_name='Instructor',
                        user_type='instructor',
                        is_staff=True
                    )
        
        self.stdout.write(f'Using instructor: {instructor.username}')
        return instructor
    
    def _get_subjects(self, instructor):
        """Get or create test subjects for quizzes."""
        subjects = Subject.objects.all()
        
        if not subjects.exists():
            self.stdout.write(self.style.WARNING('No subjects found, creating test subjects...'))
            
            subjects_data = [
                {
                    'name': 'Mathematics',
                    'code': 'MATH-101',
                    'description': 'Basic mathematics concepts including algebra, geometry, and calculus.',
                    'icon': 'calculate',
                    'icon_color': '#4285f4',
                    'icon_name': 'calculate',
                    'background_icon': 'functions'
                },
                {
                    'name': 'Computer Science',
                    'code': 'CS-101',
                    'description': 'Introduction to computer science principles and programming.',
                    'icon': 'computer',
                    'icon_color': '#0f9d58',
                    'icon_name': 'computer',
                    'background_icon': 'code'
                }
            ]
            
            subjects = []
            for data in subjects_data:
                subject = Subject.objects.create(
                    instructor=instructor,
                    **data
                )
                subjects.append(subject)
        
        return list(subjects)
    
    def _create_quiz(self, index, instructor, subjects):
        """Create a test quiz."""
        subject = random.choice(subjects)
        
        quiz_data = [
            {
                'title': 'Mathematics Fundamentals',
                'description': 'Test your knowledge of basic mathematics concepts including arithmetic, algebra, and geometry.',
                'time_limit': 30,
                'is_active': True,
            },
            {
                'title': 'Introduction to Programming',
                'description': 'A quiz on basic programming concepts, algorithms, and problem-solving techniques. Perfect for beginners.',
                'time_limit': 45,
                'is_active': True,
            },
            {
                'title': 'Advanced Data Structures',
                'description': 'Test your knowledge of complex data structures and their applications in software development.',
                'time_limit': 60,
                'is_active': False,
            }
        ]
        
        # Select quiz data based on index, or randomly if index exceeds list length
        data = quiz_data[index % len(quiz_data)]
        
        # Create and return the quiz
        quiz = Quiz.objects.create(
            subject=subject,
            **data
        )
        
        return quiz
    
    def _create_questions_and_answers(self, quiz):
        """Create test questions and answers for a quiz."""
        # Question data based on quiz title
        if 'Mathematics' in quiz.title:
            questions_data = self._get_math_questions()
        elif 'Programming' in quiz.title:
            questions_data = self._get_programming_questions()
        else:
            questions_data = self._get_data_structure_questions()
        
        # Create questions and answers
        for i, q_data in enumerate(questions_data):
            question = Question.objects.create(
                quiz=quiz,
                text=q_data['text'],
                explanation=q_data.get('explanation', ''),
                order=i + 1
            )
            
            # Create answers for the question
            for j, a_data in enumerate(q_data['answers']):
                Answer.objects.create(
                    question=question,
                    text=a_data['text'],
                    is_correct=a_data['is_correct'],
                    order=j + 1
                )
    
    def _get_math_questions(self):
        """Return a list of mathematics questions."""
        return [
            {
                'text': 'What is the value of π (pi) rounded to two decimal places?',
                'explanation': 'The mathematical constant π (pi) is approximately equal to 3.14159...',
                'answers': [
                    {'text': '3.14', 'is_correct': True},
                    {'text': '3.12', 'is_correct': False},
                    {'text': '3.16', 'is_correct': False},
                    {'text': '3.18', 'is_correct': False}
                ]
            },
            {
                'text': 'What is the formula for the area of a circle?',
                'explanation': 'The formula for the area of a circle is πr², where r is the radius of the circle.',
                'answers': [
                    {'text': 'πr²', 'is_correct': True},
                    {'text': '2πr', 'is_correct': False},
                    {'text': 'πd', 'is_correct': False},
                    {'text': '2πr²', 'is_correct': False}
                ]
            },
            {
                'text': 'Solve for x: 2x + 5 = 13',
                'explanation': 'To solve for x, subtract 5 from both sides to get 2x = 8, then divide both sides by 2 to get x = 4.',
                'answers': [
                    {'text': 'x = 4', 'is_correct': True},
                    {'text': 'x = 3', 'is_correct': False},
                    {'text': 'x = 5', 'is_correct': False},
                    {'text': 'x = 9', 'is_correct': False}
                ]
            },
            {
                'text': 'Is every square a rectangle?',
                'explanation': 'A square is a special case of a rectangle where all sides are equal.',
                'answers': [
                    {'text': 'True', 'is_correct': True},
                    {'text': 'False', 'is_correct': False}
                ]
            },
            {
                'text': 'Explain what a prime number is and give three examples.',
                'explanation': 'A prime number is a natural number greater than 1 that cannot be formed by multiplying two smaller natural numbers. Examples include 2, 3, 5, 7, 11, 13, etc.',
                'answers': [
                    {'text': 'Sample answer: A prime number is a number greater than 1 that is only divisible by 1 and itself. Examples: 2, 3, 5, 7, 11.', 'is_correct': True}
                ]
            }
        ]
    
    def _get_programming_questions(self):
        """Return a list of programming questions."""
        return [
            {
                'text': 'What is the output of the following Python code?\n\nx = 5\ny = 3\nprint(x + y)',
                'explanation': 'In this code, x is assigned the value 5 and y is assigned the value 3. The print statement outputs the sum of x and y, which is 8.',
                'answers': [
                    {'text': '8', 'is_correct': True},
                    {'text': '53', 'is_correct': False},
                    {'text': '2', 'is_correct': False},
                    {'text': '15', 'is_correct': False}
                ]
            },
            {
                'text': 'Which of the following is NOT a programming language?',
                'explanation': 'HTML is a markup language used for creating web pages, not a programming language.',
                'answers': [
                    {'text': 'HTML', 'is_correct': True},
                    {'text': 'Python', 'is_correct': False},
                    {'text': 'Java', 'is_correct': False},
                    {'text': 'JavaScript', 'is_correct': False}
                ]
            },
            {
                'text': 'What does the acronym "API" stand for?',
                'explanation': 'API stands for Application Programming Interface. It allows different software applications to communicate with each other.',
                'answers': [
                    {'text': 'Application Programming Interface', 'is_correct': True},
                    {'text': 'Advanced Programming Implementation', 'is_correct': False},
                    {'text': 'Automated Processing Interface', 'is_correct': False},
                    {'text': 'Application Protocol Interface', 'is_correct': False}
                ]
            },
            {
                'text': 'In programming, a loop that never ends is called an infinite loop.',
                'explanation': 'An infinite loop is a sequence of instructions that continuously repeats indefinitely.',
                'answers': [
                    {'text': 'True', 'is_correct': True},
                    {'text': 'False', 'is_correct': False}
                ]
            },
            {
                'text': 'Write a simple Python function to calculate the factorial of a number.',
                'explanation': 'A factorial function calculates the product of all positive integers less than or equal to n. For example, factorial(5) = 5 * 4 * 3 * 2 * 1 = 120.',
                'answers': [
                    {'text': 'Sample answer: def factorial(n):\n    if n == 0 or n == 1:\n        return 1\n    else:\n        return n * factorial(n-1)', 'is_correct': True}
                ]
            }
        ]
    
    def _get_data_structure_questions(self):
        """Return a list of data structure questions."""
        return [
            {
                'text': 'Which data structure operates on a Last In, First Out (LIFO) principle?',
                'explanation': 'A stack follows the Last In, First Out (LIFO) principle, where the last element added is the first one to be removed.',
                'answers': [
                    {'text': 'Stack', 'is_correct': True},
                    {'text': 'Queue', 'is_correct': False},
                    {'text': 'Array', 'is_correct': False},
                    {'text': 'Linked List', 'is_correct': False}
                ]
            },
            {
                'text': 'What is the time complexity of searching for an element in a balanced binary search tree?',
                'explanation': 'The time complexity for searching in a balanced binary search tree is O(log n) because at each step, the search space is halved.',
                'answers': [
                    {'text': 'O(log n)', 'is_correct': True},
                    {'text': 'O(n)', 'is_correct': False},
                    {'text': 'O(1)', 'is_correct': False},
                    {'text': 'O(n²)', 'is_correct': False}
                ]
            },
            {
                'text': 'A hash table uses a hash function to compute an index into an array of buckets or slots.',
                'explanation': 'A hash table is a data structure that implements an associative array abstract data type, using a hash function to compute an index into an array of buckets or slots.',
                'answers': [
                    {'text': 'True', 'is_correct': True},
                    {'text': 'False', 'is_correct': False}
                ]
            },
            {
                'text': 'Explain the difference between a stack and a queue with examples of their real-world applications.',
                'explanation': 'A stack follows LIFO (Last In, First Out), while a queue follows FIFO (First In, First Out). Stacks are used in function calls, undo operations in text editors, browser history, etc. Queues are used in printing tasks, CPU scheduling, message queues, etc.',
                'answers': [
                    {'text': 'Sample answer: A stack follows LIFO (Last In, First Out) principle where the last element inserted is the first to be removed. Examples include browser history, function call stack. A queue follows FIFO (First In, First Out) where the first element inserted is the first to be removed. Examples include print queues, CPU task scheduling.', 'is_correct': True}
                ]
            },
            {
                'text': 'What is the main advantage of using a linked list over an array?',
                'explanation': 'Unlike arrays, linked lists allow efficient insertion and removal of elements at any position without reallocating or reorganizing the entire structure.',
                'answers': [
                    {'text': 'Dynamic size and efficient insertions/deletions', 'is_correct': True},
                    {'text': 'Faster random access to elements', 'is_correct': False},
                    {'text': 'Lower memory usage', 'is_correct': False},
                    {'text': 'Better cache locality', 'is_correct': False}
                ]
            }
        ]
