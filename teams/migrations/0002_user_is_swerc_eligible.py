# Generated by Django 4.2.7 on 2023-11-09 20:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("teams", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_swerc_eligible",
            field=models.BooleanField(blank=True, default=False),
        ),
    ]
