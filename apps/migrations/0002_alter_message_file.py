# Generated by Django 5.1.6 on 2025-02-18 07:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='file',
            field=models.ManyToManyField(blank=True, null=True, related_name='messages', to='apps.attachments'),
        ),
    ]
