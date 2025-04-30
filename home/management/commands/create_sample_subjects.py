from django.core.management.base import BaseCommand
from home.models import Subject, SubjectMaterial, SubjectEnrollment
from authentication.models import CustomUser
from django.db import transaction

class Command(BaseCommand):
    help = 'Creates sample subjects data for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample subjects...')

        # Get an instructor user
        instructor = None
        try:
            instructor = CustomUser.objects.filter(user_type='instructor').first()
            if not instructor:
                self.stdout.write(self.style.WARNING('No instructor found. Creating subjects without instructor.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error finding instructor: {str(e)}'))

        # Sample subjects data
        subjects_data = [
            {
                'name': 'Introduction to Computer Science',
                'code': 'CS101',
                'description': 'A foundational course covering the basics of computer science, algorithms, and programming concepts.',
                'icon': 'computer',
                'icon_color': '#5349cc',
                'order': 1,
                'icon_name': 'computer',
                'background_icon': 'code'
            },
            {
                'name': 'Web Development',
                'code': 'WEB201',
                'description': 'Learn to build modern web applications using HTML, CSS, JavaScript, and popular frameworks.',
                'icon': 'web',
                'icon_color': '#5349cc',
                'order': 2,
                'icon_name': 'web',
                'background_icon': 'html'
            },
            {
                'name': 'Data Structures and Algorithms',
                'code': 'CS202',
                'description': 'Advanced course on data structures, algorithm design, and analysis of computational complexity.',
                'icon': 'analytics',
                'icon_color': '#5349cc',
                'order': 3,
                'icon_name': 'analytics',
                'background_icon': 'data_object'
            },
            {
                'name': 'Artificial Intelligence',
                'code': 'AI301',
                'description': 'Explore the fundamentals of AI including machine learning, neural networks, and natural language processing.',
                'icon': 'psychology',
                'icon_color': '#5349cc',
                'order': 4,
                'icon_name': 'psychology',
                'background_icon': 'smart_toy'
            },
            {
                'name': 'Mobile App Development',
                'code': 'MOB202',
                'description': 'Design and develop mobile applications for iOS and Android platforms using Flutter and React Native.',
                'icon': 'smartphone',
                'icon_color': '#5349cc',
                'order': 5,
                'icon_name': 'smartphone',
                'background_icon': 'apps'
            },
            {
                'name': 'Database Systems',
                'code': 'DB201',
                'description': 'Learn about database design, SQL, NoSQL, and data modeling for efficient information management.',
                'icon': 'storage',
                'icon_color': '#5349cc',
                'order': 6,
                'icon_name': 'storage',
                'background_icon': 'database'
            }
        ]

        # Create subjects
        with transaction.atomic():
            for subject_data in subjects_data:
                subject, created = Subject.objects.update_or_create(
                    code=subject_data['code'],
                    defaults={
                        'name': subject_data['name'],
                        'description': subject_data['description'],
                        'icon_name': subject_data['icon_name'],
                        'background_icon': subject_data['background_icon'],
                        'instructor': instructor
                    }
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created subject: {subject.name}'))
                else:
                    self.stdout.write(f'Updated subject: {subject.name}')

                # Create sample materials for each subject
                if created:
                    SubjectMaterial.objects.create(
                        subject=subject,
                        title='Course Syllabus',
                        description='Complete course outline and requirements',
                        material_type='document',
                        content='Course syllabus content goes here',
                        order=1,
                        is_active=True
                    )

                    SubjectMaterial.objects.create(
                        subject=subject,
                        title='Introduction Video',
                        description='Welcome to the course and overview',
                        material_type='video',
                        content='Video content description',
                        order=2,
                        is_active=True
                    )

                    SubjectMaterial.objects.create(
                        subject=subject,
                        title='Additional Resources',
                        description='External links and references',
                        material_type='link',
                        external_url='https://example.com/resources',
                        content='Links to additional resources',
                        order=3,
                        is_active=True
                    )

        self.stdout.write(self.style.SUCCESS('Successfully created sample subjects!'))
