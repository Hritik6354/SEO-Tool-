# Generated by Django 5.1.4 on 2025-04-10 07:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MyDB', '0006_rename_user_crawl_username'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='crawl',
            name='username',
        ),
        migrations.AddField(
            model_name='crawl',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='MyDB.signup'),
        ),
    ]
