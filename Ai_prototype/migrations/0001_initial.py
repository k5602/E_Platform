# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MockAIFeedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('feedback_type', models.CharField(choices=[('general', 'General Feedback'), ('assignment', 'Assignment Feedback'), ('quiz', 'Quiz Feedback')], default='general', max_length=50)),
                ('submission_id', models.CharField(max_length=50)),
                ('feedback_text', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ai_feedback', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
