# Generated by Django 4.0.6 on 2023-03-07 01:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('find_daikou', '0010_alter_order_eta'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='eta',
        ),
    ]
