# Generated by Django 4.0.6 on 2023-02-16 16:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('find_daikou', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='driver',
            old_name='is_active',
            new_name='is_available',
        ),
    ]