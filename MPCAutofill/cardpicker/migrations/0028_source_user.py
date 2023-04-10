# Generated by Django 4.1.1 on 2022-10-23 12:01

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("cardpicker", "0027_project_projectmember_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="source",
            name="user",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
