# Generated manually

from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profileproject',
            name='technologies',
            field=models.CharField(blank=True, max_length=200, verbose_name='Technologies'),
        ),
    ]
