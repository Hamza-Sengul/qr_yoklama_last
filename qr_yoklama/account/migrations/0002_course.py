# Generated by Django 5.1.3 on 2024-12-03 17:58

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('code', models.CharField(max_length=50, unique=True)),
                ('weeks', models.PositiveIntegerField()),
                ('attendance_limit', models.PositiveIntegerField()),
                ('department', models.CharField(max_length=255)),
                ('day_of_week', models.CharField(choices=[('Monday', 'Pazartesi'), ('Tuesday', 'Salı'), ('Wednesday', 'Çarşamba'), ('Thursday', 'Perşembe'), ('Friday', 'Cuma'), ('Saturday', 'Cumartesi'), ('Sunday', 'Pazar')], max_length=15)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('students', models.ManyToManyField(blank=True, to='account.profile')),
            ],
        ),
    ]
