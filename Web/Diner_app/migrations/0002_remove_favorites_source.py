# Generated by Django 3.2.3 on 2021-06-04 02:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Diner_app', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='favorites',
            name='source',
        ),
    ]
