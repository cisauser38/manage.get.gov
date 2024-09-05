# Generated by Django 4.2.10 on 2024-08-29 23:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("registrar", "0120_add_domainrequest_submission_dates"),
    ]

    operations = [
        migrations.AlterField(
            model_name="domaininformation",
            name="submitter",
            field=models.ForeignKey(
                blank=True,
                help_text='Person listed under "your contact information" in the request form',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="submitted_domain_requests_information",
                to="registrar.contact",
            ),
        ),
        migrations.AlterField(
            model_name="domainrequest",
            name="submitter",
            field=models.ForeignKey(
                blank=True,
                help_text='Person listed under "your contact information" in the request form; will receive email updates',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="submitted_domain_requests",
                to="registrar.contact",
            ),
        ),
    ]
