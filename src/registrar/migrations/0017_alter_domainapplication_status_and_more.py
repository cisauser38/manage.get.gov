# Generated by Django 4.1.6 on 2023-04-13 18:38

from django.db import migrations
import django_fsm  # type: ignore


class Migration(migrations.Migration):
    dependencies = [
        ("registrar", "0016_domaininvitation"),
    ]

    operations = [
        migrations.AlterField(
            model_name="domainapplication",
            name="status",
            field=django_fsm.FSMField(
                choices=[
                    ("started", "started"),
                    ("submitted", "submitted"),
                    ("investigating", "investigating"),
                    ("approved", "approved"),
                    ("withdrawn", "withdrawn"),
                ],
                default="started",
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name="domaininvitation",
            name="status",
            field=django_fsm.FSMField(
                choices=[("invited", "invited"), ("retrieved", "retrieved")],
                default="invited",
                max_length=50,
                protected=True,
            ),
        ),
    ]
