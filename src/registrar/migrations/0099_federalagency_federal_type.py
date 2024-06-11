# Generated by Django 4.2.10 on 2024-06-11 15:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registrar", "0098_alter_domainrequest_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="federalagency",
            name="federal_type",
            field=models.CharField(
                blank=True,
                choices=[("executive", "Executive"), ("judicial", "Judicial"), ("legislative", "Legislative")],
                help_text="Federal agency type (executive, judicial, legislative, etc.)",
                max_length=20,
                null=True,
            ),
        ),
    ]
