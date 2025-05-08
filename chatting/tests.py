from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient
from .models import Conversation, Message
import os

User = get_user_model()

class ChatAPITests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user1, self.user2)
        self.client = APIClient()

    def test_add_message_with_file_upload(self):
        """Ensure a user can send a message with a file attachment."""
        self.client.login(username='user1', password='password123')

        # Create a dummy file for upload
        dummy_file_content = b'This is a dummy file content.'
        dummy_file = SimpleUploadedFile(
            name='test_file.txt',
            content=dummy_file_content,
            content_type='text/plain'
        )

        message_content = "Hello, check out this file!"
        url = reverse('chat_api:add_message', kwargs={'pk': self.conversation.id})

        data = {
            'content': message_content,
            'file_attachment': dummy_file
        }

        response = self.client.post(url, data, format='multipart')

        # Check response status
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check if message was created in the database
        self.assertEqual(Message.objects.count(), 1)
        message = Message.objects.first()

        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.conversation, self.conversation)
        self.assertEqual(message.content, message_content)
        self.assertIsNotNone(message.file_attachment)
        self.assertEqual(os.path.basename(message.file_attachment.name), 'test_file.txt')
        self.assertEqual(message.file_name, 'test_file.txt')
        self.assertEqual(message.file_type, 'document') # Based on AddMessageView.determine_file_type
        self.assertEqual(message.file_size, len(dummy_file_content))

        # Check response data
        self.assertEqual(response.data['content'], message_content)
        self.assertEqual(response.data['file_name'], 'test_file.txt')
        self.assertEqual(response.data['file_type'], 'document')
        self.assertTrue('file_url' in response.data)
        self.assertTrue(response.data['file_url'].endswith('/test_file.txt'))

    def test_add_message_file_too_large(self):
        """Test uploading a file that exceeds the size limit."""
        self.client.login(username='user1', password='password123')

        # Create a dummy file larger than 5MB
        large_content = b'a' * (6 * 1024 * 1024) # 6MB
        dummy_file = SimpleUploadedFile(
            name='large_file.txt',
            content=large_content,
            content_type='text/plain'
        )

        url = reverse('chat_api:add_message', kwargs={'pk': self.conversation.id})
        data = {
            'file_attachment': dummy_file,
            'content': 'This file is too big'
        }

        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Message.objects.count(), 0)
        self.assertIn('File exceeds maximum size', response.data.get('error', ''))

    def test_add_message_no_content_no_file(self):
        """Test sending a message with no content and no file."""
        self.client.login(username='user1', password='password123')
        url = reverse('chat_api:add_message', kwargs={'pk': self.conversation.id})
        data = {}
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Message.objects.count(), 0)
        self.assertIn('must have either content or a file attachment', response.data.get('error', ''))

    def tearDown(self):
        # Clean up created files from media directory
        # This is a simplified cleanup. For more robust cleanup, you might need to
        # iterate through specific subdirectories or use a custom storage backend for tests.
        for message in Message.objects.all():
            if message.file_attachment:
                try:
                    # Construct the full path to the file
                    # Note: This assumes MEDIA_ROOT is set and accessible
                    # from django.conf import settings
                    # file_path = os.path.join(settings.MEDIA_ROOT, message.file_attachment.name)
                    if os.path.exists(message.file_attachment.path):
                         os.remove(message.file_attachment.path)
                except Exception as e:
                    print(f"Error deleting file {message.file_attachment.path}: {e}")
