# Generated by Django 3.2.3 on 2021-06-04 14:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('User_app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='password',
            field=models.CharField(max_length=500),
        ),
    ]
