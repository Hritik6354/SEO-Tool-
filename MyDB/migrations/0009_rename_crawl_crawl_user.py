# Generated by Django 5.1.4 on 2025-04-21 13:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('MyDB', '0008_remove_crawl_user_crawl_crawl'),
    ]

    operations = [
        migrations.RenameField(
            model_name='crawl',
            old_name='crawl',
            new_name='user',
        ),
    ]
