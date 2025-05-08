from django.db import migrations
from django.db.models import Index

class Migration(migrations.Migration):

    dependencies = [
        ('home', '0001_initial'),  # Update this to the latest migration in your home app
        ('chatting', '0001_initial'),  # Update this to the latest migration in your chatting app
        ('authentication', '0001_initial'),  # Update this to the latest migration in your authentication app
    ]

    operations = [
        # Home app indices
        migrations.AddIndex(
            model_name='post',
            index=Index(fields=['created_at'], name='post_created_idx'),
        ),
        migrations.AddIndex(
            model_name='post',
            index=Index(fields=['user'], name='post_user_idx'),
        ),
        migrations.AddIndex(
            model_name='comment',
            index=Index(fields=['post', 'created_at'], name='comment_post_created_idx'),
        ),
        migrations.AddIndex(
            model_name='like',
            index=Index(fields=['post', 'user'], name='like_post_user_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=Index(fields=['recipient', 'is_read', 'created_at'], name='notification_recipient_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=Index(fields=['notification_type'], name='notification_type_idx'),
        ),
        migrations.AddIndex(
            model_name='subject',
            index=Index(fields=['name'], name='subject_name_idx'),
        ),
        migrations.AddIndex(
            model_name='subject',
            index=Index(fields=['code'], name='subject_code_idx'),
        ),
        migrations.AddIndex(
            model_name='subject',
            index=Index(fields=['is_active'], name='subject_active_idx'),
        ),
        migrations.AddIndex(
            model_name='subjectenrollment',
            index=Index(fields=['student', 'subject', 'is_active'], name='enrollment_student_subject_idx'),
        ),
        migrations.AddIndex(
            model_name='appointment',
            index=Index(fields=['appointment_date', 'status'], name='appointment_date_status_idx'),
        ),
        migrations.AddIndex(
            model_name='appointment',
            index=Index(fields=['user', 'instructor'], name='appointment_user_instructor_idx'),
        ),

        # Chatting app indices
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS conversation_updated_idx ON chatting_conversation(updated_at DESC);
            CREATE INDEX IF NOT EXISTS message_conversation_timestamp_idx ON chatting_message(conversation_id, timestamp);
            CREATE INDEX IF NOT EXISTS message_sender_idx ON chatting_message(sender_id);
            CREATE INDEX IF NOT EXISTS message_read_status_idx ON chatting_message(conversation_id, is_read) 
                WHERE is_read = false;
            CREATE INDEX IF NOT EXISTS message_delivery_status_idx ON chatting_message(delivery_status) 
                WHERE delivery_status = 'pending';
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS conversation_updated_idx;
            DROP INDEX IF EXISTS message_conversation_timestamp_idx;
            DROP INDEX IF EXISTS message_sender_idx;
            DROP INDEX IF EXISTS message_read_status_idx;
            DROP INDEX IF EXISTS message_delivery_status_idx;
            """
        ),

        # Authentication app indices
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS user_type_idx ON authentication_customuser(user_type);
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS user_type_idx;
            """
        ),
    ]