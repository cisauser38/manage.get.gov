# Generated by Django 4.2.10 on 2024-07-11 19:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registrar", "0112_remove_contact_registrar_c_user_id_4059c4_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="domainrequest",
            name="rejection_reason_email",
            field=models.TextField(blank=True, null=True),
        ),
    ]
