# Generated by Django 3.1 on 2021-09-11 02:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tag',
            name='slug',
            field=models.CharField(max_length=200, unique=True, verbose_name='Уникальный слаг'),
        ),
    ]
